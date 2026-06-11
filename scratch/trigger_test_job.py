
import asyncio
from src.services.video_engine.tasks import generate_video_task
from src.shared.enums import SystemJobStatus
from src.api.utils.models import VideoJobDB
import uuid

async def test_trigger():
    user_id = "78dc9df0-ad7f-4788-b86d-f4e98659c889" # demo@example.com
    prompt = "A beautiful sunset over the mountains"
    
    # 1. Dispatch task to get ID
    task_id = str(uuid.uuid4())
    
    # 2. Create job in DB
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from src.api.config import settings
    
    db_url = settings.DATABASE_URL.replace("localhost:7203", "db:5432")
    if "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        new_job = VideoJobDB(
            id=task_id,
            title="Test Generation",
            status=SystemJobStatus.QUEUED,
            progress=0,
            source_uri=prompt,
            user_id=user_id,
            job_metadata={"prompt": prompt, "engine": "ltx-video"}
        )
        session.add(new_job)
        await session.commit()
    
    print(f"Job created in DB: {task_id}")

    # 3. Trigger task with specific ID
    task = generate_video_task.apply_async(
        kwargs={
            "prompt": prompt,
            "engine": "ltx-video",
            "style": "Cinematic",
            "aspect_ratio": "9:16",
            "user_id": user_id,
            "request_id": str(uuid.uuid4())
        },
        task_id=task_id
    )
    print(f"Task dispatched: {task.id}")

if __name__ == "__main__":
    asyncio.run(test_trigger())
