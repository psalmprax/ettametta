from api.utils.database import Base, async_engine
import asyncio


async def run():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully")


asyncio.run(run())
