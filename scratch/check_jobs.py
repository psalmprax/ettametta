import asyncio
import sys

sys.path.append("/app")

from src.api.utils.database import AsyncSessionLocal
from src.api.utils.models import VideoJobDB
from sqlalchemy import select

async def run():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(VideoJobDB).order_by(VideoJobDB.created_at.desc()).limit(5))
            jobs = result.scalars().all()
            if not jobs:
                print("No jobs found.")
                return
            for j in jobs:
                print("-" * 40)
                print(f"ID: {j.id}")
                print(f"Status: {j.status}")
                print(f"Output Path: {j.output_path}")
                print(f"Created At: {j.created_at}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
