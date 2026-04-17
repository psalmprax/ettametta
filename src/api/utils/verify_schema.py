import asyncio
from src.api.utils.database import async_session_factory
from sqlalchemy import text

async def verify_async():
    async with async_session_factory() as db:
        try:
            # Check if 'views' column exists in 'content_candidates'
            stmt = text("SELECT column_name FROM information_schema.columns WHERE table_name='content_candidates' AND column_name='views';")
            result = await db.execute(stmt)
            column = result.fetchone()
            if column:
                print("✅ 'views' column exists.")
            else:
                print("❌ 'views' column MISSING.")
        except Exception as e:
            print(f"❌ Verification failed: {e}")

def verify():
    asyncio.run(verify_async())

if __name__ == "__main__":
    verify()
