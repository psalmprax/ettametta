import logging
import random
from typing import Any
from .base import BaseMonetizationStrategy
from src.api.utils.models import SystemSettings

class CourseStrategy(BaseMonetizationStrategy):
    """
    Course/Education strategy - Sell online courses and tutorials
    """
    
    async def get_assets(self, niche: str) -> list[dict[str, Any]]:
        """
        Fetches course platform URL from database configuration.
        """
        from sqlalchemy import select
        from src.api.utils.database import async_session_factory
        
        async with async_session_factory() as db:
            stmt = select(SystemSettings).filter(SystemSettings.key == "course_platform_uri")
            result = await db.execute(stmt)
            setting = result.scalar_one_or_none()
            platform_uri = setting.value if setting else "https://ettametta.ai/academy"

            return [
                {
                    "id": "course_1",
                    "name": f"Complete {niche.title()} Masterclass",
                    "url": platform_uri,
                    "cta_text": "Enroll Now",
                    "price": "$97",
                    "description": f"Learn everything about {niche} from scratch to advanced",
                    "source": "course"
                },
                {
                    "id": "course_2",
                    "name": f"{niche.title()} Crash Course",
                    "url": platform_uri,
                    "cta_text": "Get Started",
                    "price": "$47",
                    "description": f"Quickstart guide to {niche}",
                    "source": "course"
                },
                {
                    "id": "course_3",
                    "name": f"Advanced {niche.title()} Strategies",
                    "url": platform_uri,
                    "cta_text": "Learn More",
                    "price": "$197",
                    "description": f"Master advanced {niche} techniques",
                    "source": "course"
                }
            ]

    async def generate_cta(self, niche: str, context: str) -> str:
        """
        Generates a call to action for course sales.
        """
        assets = await self.get_assets(niche)
        
        if not assets:
            logging.warning("[CourseStrategy] No course platform configured. Set 'course_platform_uri' in settings.")
            return ""
        
        platform_uri = assets[0].get("url", "")
        assets[0].get("name", f"{niche} course")
        
        options = [
            f"Want to master {niche}? Check out my comprehensive course: \n🔗 {platform_uri}",
            f"Learn {niche} the right way! Full course available: \n🔗 {platform_uri}",
            f"Take your {niche} skills to the next level! Enroll now: \n🔗 {platform_uri}",
            f"Ready to become an expert in {niche}? Join my course: \n🔗 {platform_uri}"
        ]
        return random.choice(options)
