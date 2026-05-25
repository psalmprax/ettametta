import asyncio
import sqlalchemy.types
from datetime import datetime, timezone
from sqlalchemy import select

# Apply monkeypatch
_original_bind_processor = sqlalchemy.types.DateTime.bind_processor

def _safe_bind_processor(self, dialect):
    parent_processor = _original_bind_processor(self, dialect)
    def process(value):
        if value is not None and getattr(value, "tzinfo", None) is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        if parent_processor:
            return parent_processor(value)
        return value
    return process

sqlalchemy.types.DateTime.bind_processor = _safe_bind_processor

from src.api.utils.database import async_session_factory
from src.api.utils.models import NexusJobDB

async def test_update():
    async with async_session_factory() as db:
        stmt = select(NexusJobDB).where(NexusJobDB.id == '594aa18c-ae19-4b89-ad1c-6f61a5b6d24d')
        res = await db.execute(stmt)
        job = res.scalar_one_or_none()
        if job:
            job.current_node = 'ingress_patched'
            current_status = dict(job.node_status or {})
            current_status['ingress_patched'] = 'ACTIVE'
            job.node_status = current_status
            job.progress = 15
            # Assign timezone-aware datetime to verify the monkeypatch strips it
            job.updated_at = datetime.now(timezone.utc)
            await db.commit()
            print("Monkeypatch verification: Success!")
        else:
            print("Job not found to update!")

asyncio.run(test_update())
