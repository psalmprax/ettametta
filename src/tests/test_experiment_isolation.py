import pytest
import asyncio
from api.utils.database import AsyncSessionLocal
from api.utils.models import StrategyRegistryDB, ExperimentCohortDB
from services.distribution.experiment_batcher import base_experiment_batcher
from sqlalchemy import insert

@pytest.mark.asyncio
async def test_experiment_isolation_duplicates():
    """Verify that a video cannot be assigned to two experiments simultaneously."""
    # 1. Create two batches
    await base_experiment_batcher.create_cohort_batch("strat_a", size=10)
    await base_experiment_batcher.create_cohort_batch("strat_b", size=10)
    
    # 2. Assign to first
    vid = "dual_video_test_id"
    await base_experiment_batcher.assign_to_batch(vid)
    
    # 3. Attempt assign to second (should be blocked by isolation check)
    # The logic in ExperimentBatcher now checks all active_batches
    await base_experiment_batcher.assign_to_batch(vid)
    
    # 4. Verify isolation in memory
    match_count = 0
    for batch in base_experiment_batcher.active_batches:
        if vid in batch["participants"]:
            match_count += 1
    
    assert match_count == 1, "Isolation Breach! Video assigned to multiple batches."

@pytest.mark.asyncio
async def test_killed_strategy_rejection():
    """Verify that 'Killed' strategies cannot spawn new cohorts."""
    strat_name = "dead_strat_99"
    
    # 1. Manually insert a KILLED strategy into the registry
    async with AsyncSessionLocal() as db:
        new_strat = StrategyRegistryDB(name=strat_name, status="KILLED")
        db.add(new_strat)
        await db.commit()
    
    # 2. Try to create cohort
    batch = await base_experiment_batcher.create_cohort_batch(strat_name)
    
    # 3. Verify rejection
    assert batch == {}, "Security Breach! KILLED strategy allowed to create cohort."
