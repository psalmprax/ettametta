import asyncio
import os
import sys

# Add /app to sys.path if running inside docker
sys.path.append("/app")

from src.api.utils.database import AsyncSessionLocal
from src.api.utils.models import SelfHealingAuditDB
from sqlalchemy import select

async def run():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(SelfHealingAuditDB).order_by(SelfHealingAuditDB.created_at.desc()).limit(10))
            audits = result.scalars().all()
            if not audits:
                print("No audits found.")
                return
            for a in audits:
                print("-" * 40)
                print(f"ID: {a.id}")
                print(f"Path: {a.path} | Method: {a.method}")
                print(f"Type: {a.exception_type} | Created: {a.created_at}")
                print(f"Message: {a.message}")
                # print(f"Traceback: {a.traceback[:500]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run())
