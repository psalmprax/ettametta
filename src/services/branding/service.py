import os
import logging
import httpx
import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from api.utils.models import BrandIdentityDB
from api.config import settings

logger = logging.getLogger(__name__)


class BrandingService:
    def __init__(self, branding_dir: str = "assets/branding"):
        self.branding_dir = branding_dir
        os.makedirs(branding_dir, exist_ok=True)

    async def generate_brand_identity(
        self,
        user_id: str | int,
        niche: str,
        account_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Autonomous Brand Factory:
        Calls OpenClaw execute-tool to run the branding_skill (which has playwright).

        Args:
            user_id: User ID (supports both str and int for compatibility with UserDB.id)
            niche: Brand niche/topic
            account_id: Optional account ID
            db: Database session for persistence
        """
        # Normalize user_id to string for consistent DB lookups
        user_id_str = str(user_id)

        logger.info(f"[Branding] Requesting identity generation for niche: {niche}")

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "http://openclaw:3001/execute-tool",
                    json={
                        "tool": "BRANDING",
                        "params": {"niche": niche},
                        "internal_token": settings.INTERNAL_API_TOKEN,
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        f"[Branding] OpenClaw returned error: {response.status_code}"
                    )
                    return {
                        "status": "error",
                        "message": f"OpenClaw error {response.status_code}",
                    }

                data = response.json()
                if data.get("status") != "success":
                    logger.error(
                        f"[Branding] Tool execution failed: {data.get('message')}"
                    )
                    return {"status": "error", "message": data.get("message")}

                brand_result = data["result"]
                brand_name = brand_result.get("brand_name")
                logo_url = brand_result.get("logo_url")
                primary_color = brand_result.get("primary_color")

                # Persistence
                if db:
                    # Check if active brand exists for this niche/account
                    stmt = select(BrandIdentityDB).where(
                        and_(
                            BrandIdentityDB.user_id == user_id_str,
                            BrandIdentityDB.niche == niche,
                            BrandIdentityDB.is_active == True,
                        )
                    )
                    res = await db.execute(stmt)
                    existing = res.scalar_one_or_none()

                    if existing:
                        existing.is_active = False  # Deactivate old one

                    new_brand = BrandIdentityDB(
                        user_id=user_id_str,
                        account_id=account_id,
                        niche=niche,
                        logo_url=logo_url,
                        brand_name=brand_name,
                        primary_color=primary_color,
                        is_active=True,
                    )
                    db.add(new_brand)
                    await db.commit()
                    await db.refresh(new_brand)

                    return {
                        "id": new_brand.id,
                        "brand_name": brand_name,
                        "logo_url": logo_url,
                        "primary_color": primary_color,
                        "status": "success",
                    }

                return {
                    "brand_name": brand_name,
                    "logo_url": logo_url,
                    "primary_color": primary_color,
                    "status": "success_no_db",
                }
        except Exception as e:
            logger.error(f"[Branding] Failed to call OpenClaw: {e}")
            return {"status": "error", "message": str(e)}

    async def get_active_brand(
        self, user_id: str | int, niche: str, db: AsyncSession
    ) -> Optional[BrandIdentityDB]:
        """Fetch active brand for the given user and niche."""
        # Normalize user_id to string
        user_id_str = str(user_id)

        stmt = (
            select(BrandIdentityDB)
            .where(
                and_(
                    BrandIdentityDB.user_id == user_id_str,
                    BrandIdentityDB.niche == niche,
                    BrandIdentityDB.is_active == True,
                )
            )
            .order_by(BrandIdentityDB.created_at.desc())
        )

        result = await db.execute(stmt)
        return result.scalars().first()


base_branding_service = BrandingService()
