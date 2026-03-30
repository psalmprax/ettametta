import logging
from typing import List, Dict, Any
from .base import BaseMonetizationStrategy

logger = logging.getLogger(__name__)


class LeadGenStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche: str) -> List[Dict[str, Any]]:
        """
        Get lead magnet assets for the given niche.
        """
        from api.config import settings
        from api.utils.database import SessionLocal
        from api.utils.models import LeadMagnetDB # Assuming this exists or using generic settings
        
        db = SessionLocal()
        try:
            # Check for configured lead magnets
            from api.utils.models import SystemSettings
            magnet_url = db.query(SystemSettings).filter(SystemSettings.key == f"lead_magnet_{niche}").first()
            
            if magnet_url:
                return [{
                    "id": f"magnet_{niche}",
                    "name": f"Free {niche.title()} Guide",
                    "url": magnet_url.value,
                    "type": "lead_magnet"
                }]
            
            # Fallback: check if Mailchimp/ConvertKit is configured
            if settings.MAILCHIMP_API_KEY or settings.CONVERTKIT_API_KEY:
                return [{
                    "id": "newsletter",
                    "name": "Weekly Newsletter",
                    "type": "email_signup",
                    "service": "mailchimp" if settings.MAILCHIMP_API_KEY else "convertkit"
                }]
                
            return []
        finally:
            db.close()

    async def subscribe_lead(self, email: str, niche: str) -> bool:
        """
        Subscribes a lead to the configured email marketing service.
        """
        from api.config import settings
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
                return response.status_code == 200

        logger.warning("[LeadGen] No email marketing service configured for subscription.")
        return False

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generate a call-to-action for lead capture.
        """
        # In a real setup, we would call an AI worker to generate this
        from api.utils.os_worker import ai_worker
        prompt = f"Generate a short viral video CTA for a {niche} lead magnet. Context: {context}. Max 10 words."
        
        try:
            cta = await ai_worker.generate_text(prompt)
            if cta: return cta.strip()
        except:
            pass
            
        return f"Download our FREE {niche} guide! Link in bio 🚀"
