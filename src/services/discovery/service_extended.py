"""
Extended Discovery Service
Consolidates all discovery-related database operations from routes into service layer.
Follows Clean Architecture principles for better testability and separation of concerns.
"""

import logging
import datetime
from typing import Any, Dict, List
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.utils.models import (
    ContentCandidateDB,
    MonitoredNiche,
    DiscoveryAlertDB,
)

logger = logging.getLogger(__name__)


class DiscoveryServiceExtended:
    """
    Service layer for discovery operations.
    Consolidates all database query logic from discovery routes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get discovery module summary statistics.
        
        Returns:
            Dictionary with discovery statistics
        """
        try:
            # Total candidates discovered
            stmt_total = select(func.count()).select_from(ContentCandidateDB)
            total_candidates = await self.db.execute(stmt_total)
            total_count = total_candidates.scalar() or 0

            # High viral score candidates (> 80)
            stmt_high = (
                select(func.count())
                .select_from(ContentCandidateDB)
                .where(ContentCandidateDB.viral_score >= 80)
            )
            high_count_res = await self.db.execute(stmt_high)
            high_count = high_count_res.scalar() or 0

            # Platform distribution
            stmt_platforms = select(
                ContentCandidateDB.platform, func.count()
            ).group_by(ContentCandidateDB.platform)
            platforms_res = await self.db.execute(stmt_platforms)
            platform_dist = {row[0]: row[1] for row in platforms_res.all()}

            return {
                "total_candidates": total_count,
                "high_velocity_candidates": high_count,
                "platform_distribution": platform_dist,
                "last_scan": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.exception(f"Discovery summary service failed: {e}")
            return {"total_candidates": 0, "status": "partial_offline"}

    async def list_monitored_niches(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all monitored niches for a specific user with their alert status.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of dictionaries with niche and alert information
        """
        try:
            # Join MonitoredNiche with DiscoveryAlertDB to get alert status
            stmt = (
                select(
                    MonitoredNiche.niche,
                    MonitoredNiche.is_active,
                    DiscoveryAlertDB.threshold,
                    DiscoveryAlertDB.is_active.label("alert_enabled"),
                )
                .outerjoin(
                    DiscoveryAlertDB,
                    and_(
                        DiscoveryAlertDB.niche == MonitoredNiche.niche,
                        DiscoveryAlertDB.user_id == MonitoredNiche.user_id,
                    ),
                )
                .filter(MonitoredNiche.user_id == user_id)
                .order_by(MonitoredNiche.niche)
            )

            result = await self.db.execute(stmt)
            rows = result.all()
            
            return [
                {
                    "niche": r[0],
                    "is_active": r[1],
                    "threshold": r[2] or 7,
                    "alert_enabled": r[3] if r[3] is not None else False,
                }
                for r in rows
            ]
        except Exception as e:
            logger.exception(f"List monitored niches service failed: {e}")
            raise e

    async def watch_niche(
        self, user_id: str, niche: str, threshold: int, enabled: bool
    ) -> Dict[str, Any]:
        """
        Persistently watch/monitor a niche for a user.
        Also creates or updates an alert for the niche.
        
        Args:
            user_id: ID of the user
            niche: Niche to watch
            threshold: Viral score threshold for alerts
            enabled: Whether the alert is enabled
            
        Returns:
            Dictionary with the status of the operation
        """
        try:
            # 1. Handle MonitoredNiche
            stmt = select(MonitoredNiche).filter(
                and_(
                    MonitoredNiche.user_id == user_id,
                    MonitoredNiche.niche == niche,
                )
            )
            result = await self.db.execute(stmt)
            existing_monitor = result.scalar_one_or_none()

            if not existing_monitor:
                new_monitor = MonitoredNiche(
                    user_id=user_id, niche=niche, is_active=True
                )
                self.db.add(new_monitor)
            else:
                existing_monitor.is_active = True

            # 2. Handle DiscoveryAlert
            stmt_alert = select(DiscoveryAlertDB).filter(
                and_(
                    DiscoveryAlertDB.user_id == user_id,
                    DiscoveryAlertDB.niche == niche,
                )
            )
            alert_result = await self.db.execute(stmt_alert)
            existing_alert = alert_result.scalar_one_or_none()

            if not existing_alert:
                new_alert = DiscoveryAlertDB(
                    user_id=user_id,
                    niche=niche,
                    threshold=threshold,
                    is_active=enabled,
                )
                self.db.add(new_alert)
            else:
                existing_alert.is_active = enabled
                existing_alert.threshold = threshold

            await self.db.commit()
            return {
                "status": "Niche Watch Established",
                "niche": niche,
                "threshold": threshold,
                "enabled": enabled
            }
        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Watch niche service failed: {e}")
            raise e


from src.api.utils.database import get_db
from fastapi import Depends

def get_discovery_service_extended(db: AsyncSession = Depends(get_db)) -> DiscoveryServiceExtended:
    """Factory for DiscoveryServiceExtended"""
    return DiscoveryServiceExtended(db)
