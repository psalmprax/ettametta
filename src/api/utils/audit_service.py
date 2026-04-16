from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from typing import Optional, Any
from api.utils.models import AuditLogDB
from api.utils.database import async_session_factory
import json


class AuditService:
    @staticmethod
    async def log(
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Optional[AsyncSession] = None,
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
        provider: str, metadata: dict, db: Optional[AsyncSession] = None
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
