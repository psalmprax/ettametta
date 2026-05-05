import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append("/root/ettametta")

from src.services.optimization.viral_loop import base_viral_loop
from src.api.utils.database import async_session_factory
from src.api.utils.models import SystemSettings
from sqlalchemy import select, update

async def test_viral_loop(niche="Motivation"):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("TestViralLoop")
    
    logger.info(f"Starting test for niche: {niche}")
    
    # 1. Trigger the autonomous cycle
    await base_viral_loop.execute_autonomous_cycle(niche)
    
    logger.info("Test execution finished. Check logs for dispatched tasks.")

if __name__ == "__main__":
    niche = sys.argv[1] if len(sys.argv) > 1 else "Motivation"
    asyncio.run(test_viral_loop(niche))
