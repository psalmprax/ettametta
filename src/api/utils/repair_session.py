import sys
import os
import asyncio

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.api.utils.database import async_session_factory
from sqlalchemy import select
from src.api.utils.user_models import UserDB, UserRole, SubscriptionTier
from src.api.utils.security import get_password_hash
from src.api.config import settings


async def repair_admin_async():
    async with async_session_factory() as db:
        try:
            # Get credentials from environment variables - fail if not set
            username = os.getenv("ADMIN_USERNAME")
            email = os.getenv("ADMIN_EMAIL")
            password = os.getenv("ADMIN_PASSWORD")
            
            if not username or not email or not password:
                print("[REPAIR] ERROR: ADMIN_USERNAME, ADMIN_EMAIL, and ADMIN_PASSWORD environment variables must be set.")
                return
                
            # Check if user exists
            stmt = select(UserDB).where(UserDB.username == username)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                print(f"[REPAIR] User {username} already exists.")
                return

            print(f"[REPAIR] Creating admin user: {username}")
            hashed_pwd = get_password_hash(password)
            
            admin_user = UserDB(
                username=username,
                email=email,
                hashed_password=hashed_pwd,
                role=UserRole.ADMIN,
                subscription=SubscriptionTier.PREMIUM
            )
            db.add(admin_user)
            await db.commit()
            print("[REPAIR] Admin user created successfully.")
        except Exception as e:
            print(f"[REPAIR] Error creating user: {e}")

def repair_admin():
    asyncio.run(repair_admin_async())

if __name__ == "__main__":
    repair_admin()
