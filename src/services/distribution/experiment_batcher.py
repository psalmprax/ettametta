import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from api.utils.database import AsyncSessionLocal
from api.utils.models import ExperimentCohortDB
from api.utils.redis import get_redis

logger = logging.getLogger("ExperimentBatcher")

class ExperimentBatcher:
    """
    10/10 Production: The Gated Rollout Engine (Stateful).
    Groups videos into strategic cohorts with persistent database backing.
    """
    def __init__(self):
        self.active_batches = [] # In-memory cache for fast lookup

    async def sync_from_db(self):
        """
        Standard: Stateful Recovery.
        Loads all 'ROLLING_OUT' batches from Postgres.
        """
        async with AsyncSessionLocal() as db:
            try:
                stmt = select(ExperimentCohortDB).where(ExperimentCohortDB.status == "ROLLING_OUT")
                result = await db.execute(stmt)
                batches = result.scalars().all()
                self.active_batches = [
                    {
                        "batch_id": b.id,
                        "strategy": b.strategy,
                        "size": b.size,
                        "status": b.status,
                        "participants": b.participants,
                        "created_at": str(b.created_at)
                    } for b in batches
                ]
                logger.info(f"🧪 [Batcher] State Reconstructed: {len(self.active_batches)} active cohorts loaded.")
            except Exception as e:
                logger.error(f"Failed to sync batcher state from DB: {e}")

    async def create_cohort_batch(self, strategy_name: str, size: int = 5) -> Dict[str, Any]:
        """
        Creates a new experiment cohort and persists to Postgres.
        Checks StrategyRegistryDB to ensure the strategy isn't 'KILLED'.
        """
        async with AsyncSessionLocal() as db:
            from api.utils.models import StrategyRegistryDB
            stmt = select(StrategyRegistryDB).where(StrategyRegistryDB.name == strategy_name)
            result = await db.execute(stmt)
            strat = result.scalar_one_or_none()
            
            if strat and strat.status == "KILLED":
                logger.error(f"❌ [Batcher] Cannot create cohort for KILLED strategy: {strategy_name}")
                return {}

        batch_id = f"batch_{int(datetime.now().timestamp())}_{strategy_name[:5]}"
        
        batch_data = {
            "batch_id": batch_id,
            "strategy": strategy_name,
            "size": size,
            "status": "ROLLING_OUT",
            "participants": [],
            "created_at": str(datetime.now())
        }

        # 1. Persist to Source of Truth
        async with AsyncSessionLocal() as db:
            try:
                new_cohort = ExperimentCohortDB(
                    id=batch_id,
                    strategy=strategy_name,
                    size=size,
                    status="ROLLING_OUT",
                    participants=[]
                )
                db.add(new_cohort)
                await db.commit()
                
                # 2. Update local cache
                self.active_batches.append(batch_data)
                
                # 3. Global Hot State: Store latest batch ID in Redis for distribution
                redis = await get_redis()
                await redis.set(f"active_batch:{strategy_name}", batch_id, ex=86400)
                
                logger.info(f"🧪 [Batcher] Persistent Cohort Created: {batch_id}")
                return batch_data
            except Exception as e:
                logger.error(f"Failed to create persistent cohort: {e}")
                await db.rollback()
                return {}

    async def assign_to_batch(self, video_id: str) -> Optional[str]:
        """
        Assigns a video to the current open cohort with persistent state update.
        Implements strict isolation: prevents a video from entering multiple experiments.
        """
        # 1. Isolation Check: Is video already in an active cohort?
        for existing_batch in self.active_batches:
            if video_id in existing_batch["participants"]:
                logger.warning(f"⚠️ [Batcher] Isolation Breach! Video {video_id} already in cohort {existing_batch['batch_id']}. Skipping.")
                return existing_batch["batch_id"]

        # 2. Normal Assignment
        for batch in self.active_batches:
            if batch["status"] == "ROLLING_OUT" and len(batch["participants"]) < batch["size"]:
                batch["participants"].append(video_id)
                
                # Update Database
                async with AsyncSessionLocal() as db:
                    try:
                        stmt = update(ExperimentCohortDB).where(
                            ExperimentCohortDB.id == batch["batch_id"]
                        ).values(participants=batch["participants"])
                        
                        if len(batch["participants"]) >= batch["size"]:
                            batch["status"] = "FULL_WAITING_DATA"
                            stmt = stmt.values(status="FULL_WAITING_DATA")
                            
                        await db.execute(stmt)
                        await db.commit()
                        logger.info(f"🧪 [Batcher] Assigned {video_id} to cohort {batch['batch_id']}. Fill: {len(batch['participants'])}/{batch['size']}")
                        return batch["batch_id"]
                    except Exception as e:
                        logger.error(f"Failed to update cohort participants in DB: {e}")
                        await db.rollback()
        return None

    def get_batch_vitals(self) -> List[Dict]:
        return [
            {"id": b["batch_id"], "strategy": b["strategy"], "fill": f"{len(b['participants'])}/{b['size']}"}
            for b in self.active_batches[-3:]
        ]

base_experiment_batcher = ExperimentBatcher()
