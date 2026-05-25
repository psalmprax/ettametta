from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from src.api.utils.models import AuditLogDB
from src.api.utils.database import async_session_factory


class AuditService:
    @staticmethod
    async def log(
        action: str,
        user_id: str | None = None,
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
            created_at=datetime.now(timezone.utc),
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

    # ── EU AI Act Compliance Logging ──────────────────────────────────

    @staticmethod
    async def log_ai_decision(
        model: str,
        decision_type: str,
        input_summary: str,
        output_summary: str,
        user_id: str | None = None,
        confidence: float | None = None,
        reasoning: str | None = None,
        db: AsyncSession | None = None,
    ):
        """
        Log an AI model decision for EU AI Act Art. 13 transparency.
        Records what model was used, what it decided, and why.
        """
        await AuditService.log(
            action="AI_DECISION",
            resource_type="AI_MODEL",
            resource_id=model,
            user_id=user_id,
            details={
                "decision_type": decision_type,
                "input_summary": input_summary[:500],
                "output_summary": output_summary[:500],
                "confidence": confidence,
                "reasoning": reasoning[:500] if reasoning else None,
                "model": model,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            db=db,
        )

    @staticmethod
    async def log_content_moderation(
        content_id: str,
        content_type: str,
        moderation_result: str,
        flags: list[str] | None = None,
        user_id: str | None = None,
        db: AsyncSession | None = None,
    ):
        """
        Log content moderation decisions for EU AI Act Art. 14 human oversight.
        """
        await AuditService.log(
            action="CONTENT_MODERATION",
            resource_type="CONTENT",
            resource_id=content_id,
            user_id=user_id,
            details={
                "content_type": content_type,
                "moderation_result": moderation_result,
                "flags": flags or [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            db=db,
        )

    @staticmethod
    async def log_model_card(
        model: str,
        version: str,
        capabilities: list[str],
        limitations: list[str],
        training_data_summary: str | None = None,
        db: AsyncSession | None = None,
    ):
        """
        Register a model card for EU AI Act Art. 11 documentation.
        """
        await AuditService.log(
            action="MODEL_CARD_REGISTERED",
            resource_type="AI_MODEL",
            resource_id=f"{model}:{version}",
            details={
                "model": model,
                "version": version,
                "capabilities": capabilities,
                "limitations": limitations,
                "training_data_summary": training_data_summary,
                "registered_at": datetime.now(timezone.utc).isoformat(),
            },
            db=db,
        )

    @staticmethod
    async def log_human_oversight(
        action: str,
        human_id: str,
        ai_decision_id: str | None = None,
        override: bool = False,
        reason: str | None = None,
        db: AsyncSession | None = None,
    ):
        """
        Log human oversight actions for EU AI Act Art. 14.
        Records when humans review, approve, or override AI decisions.
        """
        await AuditService.log(
            action="HUMAN_OVERSIGHT",
            resource_type="AI_DECISION",
            resource_id=ai_decision_id,
            user_id=human_id,
            details={
                "oversight_action": action,
                "override": override,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            db=db,
        )


audit_service = AuditService()
