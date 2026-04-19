import asyncio
import sys
import os

# Add root to sys.path
sys.path.append(os.getcwd())

from src.api.utils.database import async_engine, Base
from src.api.utils.user_models import UserDB  # Import models to ensure they are registered
from src.api.utils.models import ScheduledPostDB, PublishedContentDB

async def init_db():
    print("--- Initializing Database Schema ---")
    async with async_engine.begin() as conn:
        # This will create all tables defined in models that inherit from Base
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database schema initialized.")

if __name__ == "__main__":
    asyncio.run(init_db())
