import asyncio
from sqlalchemy import select
from src.api.utils.database import AsyncSessionLocal
from src.api.utils.user_models import UserDB
from src.api.utils.security import get_password_hash

async def reset_password():
    async with AsyncSessionLocal() as db:
        stmt = select(UserDB).where(UserDB.email == 'test@example.com')
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            user.hashed_password = get_password_hash('testpassword')
            await db.commit()
            print("Successfully reset password for test@example.com to 'testpassword'")
        else:
            print("User test@example.com not found")

if __name__ == "__main__":
    asyncio.run(reset_password())
