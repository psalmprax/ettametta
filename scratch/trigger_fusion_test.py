import asyncio
import logging
from src.api.utils.database import async_session_factory
from src.api.utils.models import NexusJobDB, UserDB, SystemJobStatus
from src.api.routes.nexus import run_nexus_composition, NexusComposeRequest
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)

async def trigger_test():
    async with async_session_factory() as db:
        # Get a user
        stmt = select(UserDB).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("No user found in DB. Creating a test user...")
            from src.api.utils.security import get_password_hash
            user = UserDB(
                email="test_fusion@ettametta.com",
                full_name="Fusion Tester",
                hashed_password=get_password_hash("testpassword"),
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Create a new job
        job = NexusJobDB(
            niche="Nature",
            user_id=user.id,
            status=SystemJobStatus.QUEUED,
            job_metadata={
                "blueprint_id": "topic-fusion",
                "test_mode": True
            }
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        job_id = str(job.id)
        print(f"Created job {job_id}")

        # Create the request
        request = NexusComposeRequest(
            niche="Nature",
            topic="The majestic wildlife of the African savanna",
            blueprint_id="topic-fusion"
        )

        # Run composition
        print("Starting composition background task...")
        await run_nexus_composition(job_id, request)
        print("Composition task completed.")
        
        # Verify result
        await db.refresh(job)
        print(f"Final Job Status: {job.status}")
        print(f"Output Path: {job.output_path}")

if __name__ == "__main__":
    asyncio.run(trigger_test())
