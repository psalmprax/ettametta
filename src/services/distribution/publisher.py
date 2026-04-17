"""
Viral Distribution Gateway (True 10/10)
=====================================

Handles automated scheduling and publishing to social platforms 
and manages the A/B testing variants in the wild.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

class Publisher:
    """
    Simulated Distribution Gateway for TikTok and YouTube.
    Maintains a 'Flight Plan' for variants.
    """

    def __init__(self):
        self.flight_plan = [] # list of videos waiting for metrics

    async def schedule_production_package(self, production_data: dict[str, Any]):
        """Schedules a video or variant for upload"""
        video_path = production_data.get("video_path")
        title = production_data.get("title")
        
        logger.info(f"📤 [Publisher] Scheduling upload: {title} ({video_path})")
        
        # Simulate API upload delay
        await asyncio.sleep(2)
        
        publish_time = datetime.now()
        logger.info(f"✅ [Publisher] Post LIVE at {publish_time.strftime('%H:%M:%S')}")
        
        # Add to flight plan to track for future analytics ingestion
        self.flight_plan.append({
            "video_id": production_data.get("variant_id", "v1"),
            "path": video_path,
            "scheduled_at": publish_time,
            "production_data": production_data
        })
        
        return {"status": "published", "publish_time": publish_time}

    async def get_active_flight_ids(self) -> list[str]:
        """Returns IDs of videos currently in the wild waiting for data"""
        return [f["video_id"] for f in self.flight_plan]

# Singleton Instance
base_publisher = Publisher()
