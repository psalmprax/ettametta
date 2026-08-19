import httpx
import hmac
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from src.api.utils.database import AsyncSessionLocal
from src.api.utils.models import IncidentWebhookDB
from src.api.config import settings

logger = logging.getLogger("IncidentReporting")

class IncidentReportingService:
    """
    Standard 3.12: Compliance Hardening (EU AI Act Article 71).
    Handles the dissemination of serious incident reports to external authorities via webhooks.
    """

    async def report_incident(self, incident_type: str, details: dict[str, Any], severity: str = "CRITICAL"):
        """
        Triggers all active incident webhooks.
        """
        payload = {
            "version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "incident_type": incident_type,
            "severity": severity,
            "platform_id": settings.APP_NAME,
            "details": details
        }

        async with AsyncSessionLocal() as db:
            stmt = select(IncidentWebhookDB).where(IncidentWebhookDB.is_active)
            result = await db.execute(stmt)
            webhooks = result.scalars().all()

            if not webhooks:
                logger.info("No active incident webhooks registered.")
                return

            async with httpx.AsyncClient(timeout=15) as client:
                for webhook in webhooks:
                    try:
                        headers = {"Content-Type": "application/json"}

                        # Apply HMAC signature if secret exists
                        if webhook.secret:
                            signature = hmac.new(
                                webhook.secret.encode(),
                                json.dumps(payload).encode(),
                                hashlib.sha256
                            ).hexdigest()
                            headers["X-AlphaHecta-Signature"] = signature

                        resp = await client.post(webhook.url, json=payload, headers=headers)

                        if resp.status_code < 300:
                            webhook.last_triggered_at = datetime.now(timezone.utc)
                            await db.commit()
                            logger.info(f"Incident report sent to {webhook.url}")
                        else:
                            logger.error(f"Failed to send incident report to {webhook.url}: {resp.status_code}")

                    except Exception as e:
                        logger.exception(f"Error triggering webhook {webhook.url}: {e}")

    def trigger_incident_sync(self, incident_type: str, details: dict[str, Any], severity: str = "CRITICAL"):
        """Sync wrapper for use in Celery or non-async contexts."""
        import asyncio
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(self.report_incident(incident_type, details, severity))
        else:
            loop.run_until_complete(self.report_incident(incident_type, details, severity))

# Global instance
base_incident_service = IncidentReportingService()
