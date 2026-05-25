#!/usr/bin/env python3
"""Kill any Nexus jobs stuck in COMPOSING status on the production server."""

import asyncio
import os

os.environ["USE_OS_MODELS"] = "true"

from dotenv import load_dotenv
load_dotenv()

from src.api.utils.database import async_session_factory
from src.api.utils.models import NexusJobDB
from src.shared.enums import SystemJobStatus
from sqlalchemy import select


async def kill_stuck_jobs():
    async with async_session_factory() as db:
        stmt = select(NexusJobDB).where(NexusJobDB.status == SystemJobStatus.COMPOSING).limit(10)
        result = await db.execute(stmt)
        jobs = result.scalars().all()
        print(f"Found {len(jobs)} stuck composing jobs")
        for j in jobs:
            print(f"  Job {j.id}: niche={j.niche}, created={j.created_at}")
            j.status = SystemJobStatus.FAILED
            j.error_log = "Killed - compose job timed out at COMPOSING/0% (infinite LLM failover loop due to placeholder API keys)"
            j.progress = 0
        await db.commit()
        print(f"Killed {len(jobs)} stuck jobs")


if __name__ == "__main__":
    asyncio.run(kill_stuck_jobs())
