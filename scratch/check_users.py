import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.api.utils.database import async_session_factory
from src.api.utils.user_models import UserDB
from sqlalchemy import select

async def check_users():
    async with async_session_factory() as db:
        try:
            stmt = select(UserDB)
            result = await db.execute(stmt)
            users = result.scalars().all()
            print(f"Found {len(users)} users:")
            for u in users:
                print(f" - {u.email} | Role: {u.role}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_users())
