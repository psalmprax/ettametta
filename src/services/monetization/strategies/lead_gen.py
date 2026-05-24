import logging
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import BaseMonetizationStrategy

logger = logging.getLogger(__name__)


class LeadGenStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> list[dict[str, Any]]:
        """
        Get lead magnet assets for the given niche from LeadGenDB.
        """
        from src.api.utils.database import async_session_factory
        from src.api.utils.models import LeadGenDB
        from sqlalchemy import select

        async with async_session_factory() as db:
            try:
                stmt = select(LeadGenDB).where(LeadGenDB.niche == niche)
                result = await db.execute(stmt)
                configs = result.scalars().all()
                
                if configs:
                    return [{
                        "id": str(config.id),
                        "name": config.name,
                        "url": config.form_uri,
                        "cta_text": config.cta_text or "Sign Up",
                        "source": "lead_gen"
                    } for config in configs]

                # Fallback to default newsletter if no specific config
                from src.api.config import settings
                return [{
                    "id": "newsletter",
                    "name": "Weekly Newsletter",
                    "url": "#",
                    "cta_text": "Join Newsletter",
                    "type": "email_signup",
                    "source": "lead_gen_default"
                }]
            except Exception as e:
                logger.error(f"[LeadGenStrategy] Error fetching assets: {e}")
                return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def subscribe_lead(self, email: str, niche: str) -> bool:
        """
        Subscribes a lead to the configured email marketing service.
        """
        from src.api.config import settings
        import httpx
        import hashlib

        # 1. Mailchimp Integration
        if settings.MAILCHIMP_API_KEY and settings.MAILCHIMP_LIST_ID:
            logger.info(f"[LeadGen] Subscribing {email} to Mailchimp list {settings.MAILCHIMP_LIST_ID}")
            # datacenter is the last part of the API key (e.g., us19)
            dc = settings.MAILCHIMP_API_KEY.split("-")[-1]
            url = f"https://{dc}.api.mailchimp.com/3.0/lists/{settings.MAILCHIMP_LIST_ID}/members"
            
            data = {
                "email_address": email,
                "status": "subscribed",
                "merge_fields": {"NICHE": niche}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, auth=("apikey", settings.MAILCHIMP_API_KEY), json=data, timeout=10.0)
                if response.status_code >= 500: # Trigger retry on server errors
                    response.raise_for_status()
                return response.status_code in [200, 201]

        # 2. ConvertKit Integration
        if settings.CONVERTKIT_API_KEY:
            logger.info(f"[LeadGen] Subscribing {email} to ConvertKit")
            url = f"https://api.convertkit.com/v3/forms/YOUR_FORM_ID/subscribe"
            data = {
                "api_key": settings.CONVERTKIT_API_KEY,
                "email": email,
                "tags": [niche]
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=10.0)
                if response.status_code >= 500:
                    response.raise_for_status()
                return response.status_code == 200

        logger.warning("[LeadGen] No email marketing service configured for subscription.")
        return False

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generate a call-to-action for lead capture.
        """
        # In a real setup, we would call an AI worker to generate this
        from src.api.utils.os_worker import ai_worker
        prompt = f"Generate a short viral video CTA for a {niche} lead magnet. Context: {context}. Max 10 words."
        
        try:
            cta = await ai_worker.generate_text(prompt)
            if cta: return cta.strip()
        except Exception:
            pass
            
        return f"Download our FREE {niche} guide! Link in bio 🚀"
