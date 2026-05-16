import asyncio
import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from sqlalchemy import select, func
from src.api.utils.database import async_session_factory
from src.api.utils.user_models import UserDB
from src.api.utils.models import NexusJobDB

async def debug_db():
    async with async_session_factory() as session:
        # Check users
        user_count = await session.execute(select(func.count(UserDB.id)))
        print(f"Total Users: {user_count.scalar()}")
        
        # List users
        users = await session.execute(select(UserDB).limit(10))
        for u in users.scalars().all():
            print(f"User: {u.username} (ID: {u.id})")
        
        # Check jobs
        job_count = await session.execute(select(func.count(NexusJobDB.id)))
        print(f"Total Nexus Jobs: {job_count.scalar()}")
        
        # List latest jobs
        jobs = await session.execute(select(NexusJobDB).order_by(NexusJobDB.created_at.desc()).limit(10))
        for j in jobs.scalars().all():
            print(f"Job ID: {j.id}, Status: {j.status}, User: {j.user_id}")

if __name__ == "__main__":
    asyncio.run(debug_db())
