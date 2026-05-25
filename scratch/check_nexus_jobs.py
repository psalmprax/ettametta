import asyncio
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from sqlalchemy import select
from src.api.utils.database import async_session_factory
from src.api.utils.models import NexusJobDB

async def check_nexus_jobs():
    async with async_session_factory() as session:
        stmt = select(NexusJobDB).order_by(NexusJobDB.created_at.desc()).limit(5)
        result = await session.execute(stmt)
        jobs = result.scalars().all()
        
        print("Checking latest 5 Nexus jobs...")
        for job in jobs:
            print(f"ID: {job.id}")
            print(f"  Status: {job.status}")
            print(f"  Niche: {job.niche}")
            print(f"  Error Log: {job.error_log}")
            print(f"  Metadata: {job.job_metadata}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(check_nexus_jobs())
