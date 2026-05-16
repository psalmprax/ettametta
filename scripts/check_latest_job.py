import asyncio
import sys
from pathlib import Path
PROJECT_DIR = "/home/psalmprax/ALL_PROJECTS/ettametta"
sys.path.insert(0, PROJECT_DIR)

from src.api.utils.database import async_session_factory
from src.api.utils.models import NexusJobDB
from sqlalchemy import select

async def check():
    async with async_session_factory() as db:
        stmt = select(NexusJobDB).order_by(NexusJobDB.created_at.desc()).limit(1)
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if job:
            print(f"Job {job.id}: Status={job.status}, Node={job.current_node}, Progress={job.progress}%")
            print(f"Node Status: {job.node_status}")
        else:
            print("No jobs found.")

if __name__ == "__main__":
    asyncio.run(check())
