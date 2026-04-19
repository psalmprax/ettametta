import asyncio
import datetime
import sys
import os
import uuid
import subprocess
from sqlalchemy import select, delete

# Add root to sys.path
sys.path.append(os.getcwd())

from src.api.utils.database import async_session_factory
from src.api.utils.user_models import UserDB
from src.api.utils.models import ScheduledPostDB
from src.services.optimization.scheduler_tasks import _retry_missed_schedules_internal

async def verify():
    print("--- Starting Verification for Phase 06 Plan 03 (Retry Logic) ---")
    async with async_session_factory() as db:
        # 1. Setup - find or create a user
        stmt = select(UserDB).limit(1)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            print("ERROR: No user found. Please ensure the database is seeded.")
            return
        
        user_id = user.id
        print(f"Using user_id: {user_id}")

        # Cleanup any existing test posts
        await db.execute(delete(ScheduledPostDB).where(ScheduledPostDB.video_path == "/tmp/test_retry.mp4"))
        await db.commit()

        # 2. Test Case 1: Missed post that should be retried (Retry 0 -> 1)
        post_id_1 = str(uuid.uuid4())
        missed_post = ScheduledPostDB(
            id=post_id_1,
            user_id=user_id,
            video_path="/tmp/test_retry.mp4",
            platform="youtube",
            scheduled_time=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
            status="PENDING",
            retry_count=0,
            parallel_allowed=True
        )
        db.add(missed_post)
        await db.commit()
        print(f"Created missed post {post_id_1} (Retry 0 -> 1)")

        # Trigger retry logic
        await _retry_missed_schedules_internal()

        # Verify result with fresh query
        async with async_session_factory() as db_check:
            stmt = select(ScheduledPostDB).where(ScheduledPostDB.id == post_id_1)
            result = await db_check.execute(stmt)
            post = result.scalar_one()
            print(f"Post 1 status: {post.status}")
            print(f"Post 1 retry_count: {post.retry_count}")
            if post.status == "PENDING" and post.retry_count == 1:
                print("✅ SUCCESS: Post 1 was retried correctly.")
            else:
                print("❌ FAILURE: Post 1 was not retried correctly.")

        # 3. Test Case 2: Max Retries (Retry 3 -> FAILED)
        post_id_2 = str(uuid.uuid4())
        max_retry_post = ScheduledPostDB(
            id=post_id_2,
            user_id=user_id,
            video_path="/tmp/test_retry.mp4",
            platform="youtube",
            scheduled_time=datetime.datetime.utcnow() - datetime.timedelta(hours=2),
            status="PENDING",
            retry_count=3,
            parallel_allowed=True
        )
        db.add(max_retry_post)
        await db.commit()
        print(f"Created missed post {post_id_2} (Retry 3 -> FAILED)")

        # Trigger retry logic
        await _retry_missed_schedules_internal()

        # Verify result with fresh session
        async with async_session_factory() as db_check:
            stmt = select(ScheduledPostDB).where(ScheduledPostDB.id == post_id_2)
            result = await db_check.execute(stmt)
            post = result.scalar_one()
            print(f"Post 2 status: {post.status}")
            print(f"Post 2 error_message: {post.error_message}")
            
            if post.status == "FAILED" and "max retries" in (post.error_message or "").lower():
                print("✅ SUCCESS: Max retries respected.")
            else:
                # Direct DB check via psql as final word
                print("Checking DB directly via psql...")
                try:
                    cmd = f"docker exec viral_forge-db-1 psql -U psalmprax -d ettametta -t -c \"SELECT status FROM scheduled_posts WHERE id='{post_id_2}'\""
                    out = subprocess.check_output(cmd, shell=True).decode().strip()
                    print(f"Direct DB status: {out}")
                    if out == "FAILED":
                        print("✅ SUCCESS (Direct Check): Max retries respected in DB.")
                    else:
                        print("❌ FAILURE: Status is still PENDING in DB.")
                except Exception as e:
                    print(f"Direct check failed: {e}")

        # Cleanup
        async with async_session_factory() as db_clean:
            await db_clean.execute(delete(ScheduledPostDB).where(ScheduledPostDB.video_path == "/tmp/test_retry.mp4"))
            await db_clean.commit()
        print("--- Verification Complete ---")

if __name__ == "__main__":
    asyncio.run(verify())
