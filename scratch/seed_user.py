import asyncio
import sys
import os
import bcrypt

# Add root to sys.path
sys.path.append(os.getcwd())

from src.api.utils.database import async_session_factory
from src.api.utils.user_models import UserDB

async def seed_user():
    print("--- Seeding Test User ---")
    async with async_session_factory() as db:
        # Check if user already exists
        from sqlalchemy import select
        stmt = select(UserDB).where(UserDB.email == "test@example.com")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            print("User test@example.com already exists.")
            return

        hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = UserDB(
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
            is_active=True,
            role="ADMIN"
        )
        db.add(new_user)
        await db.commit()
        print("✅ Test user test@example.com created with password 'password123'.")

if __name__ == "__main__":
    asyncio.run(seed_user())
