from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Any
from .models import AuditLogDB
from .database import SessionLocal
import json

class AuditService:
    @staticmethod
    def log(
        action: str,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Optional[Session] = None
    ):
        """
        Record an audit log entry.
        Can be used with an existing DB session or it will create a temporary one.
        """
        log_entry = AuditLogDB(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )

        if db:
            db.add(log_entry)
            db.commit()
        else:
            with SessionLocal() as session:
                session.add(log_entry)
                session.commit()

audit_service = AuditService()
