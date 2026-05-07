import asyncio
import sys

sys.path.append("/app")

from src.api.utils.database import AsyncSessionLocal
from src.api.utils.models import VideoJobDB
from sqlalchemy import select

async def run():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(VideoJobDB).where(VideoJobDB.id == 'f348e0d4-9d04-4ff8-af47-9ea7ade9ea15'))
            job = result.scalar_one_or_none()
            if not job:
                print("Job not found.")
                return
            print(f"ID: {job.id}")
            print(f"Status: {job.status}")
            print(f"Error: {job.error_message}")
            print(f"Metadata: {job.job_metadata}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
