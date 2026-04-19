from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Any
from api.utils.models import AuditLogDB
from api.utils.database import async_session_factory
import json


class AuditService:
    @staticmethod
    async def log(
        action: str,
        user_id: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        db: AsyncSession | None = None,
    ):
        """
        Record an audit log entry.
        Can be used with an existing Async DB session or it will create a temporary one.
        """
        log_entry = AuditLogDB(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow(),
        )

        if db:
            db.add(log_entry)
            await db.commit()
        else:
            async with async_session_factory() as session:
                session.add(log_entry)
                await session.commit()

    @staticmethod
    async def log_provider_success(
        provider: str, metadata: dict, db: AsyncSession | None = None
    ):
        """Log successful provider metadata fetch"""
        await AuditService.log(
            action="PROVIDER_FETCH_SUCCESS",
            resource_type="AI_PROVIDER",
            resource_id=provider,
            details=metadata,
            db=db,
        )


audit_service = AuditService()
