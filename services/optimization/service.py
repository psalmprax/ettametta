from .models import PostMetadata
from api.config import settings
from api.utils.os_worker import ai_worker
from api.utils.database import SessionLocal
from api.utils.models import AffiliateLinkDB, SystemSettings
from services.monetization.service import base_monetization_engine
import json
import logging
import random

class OptimizationService:
    async def generate_viral_package(self, content_id: str, niche: str, platform: str) -> PostMetadata:
        """
        Uses shared AIWorker to generate SEO-optimized title, description, and hashtags.
        Automatically injects relevant affiliate links and CTAs if available.
        """
        db = SessionLocal()
        affiliate_info = ""
        commerce_info = ""
        aggression = 100 # Default
        
        try:
            # 1. Check Monetization Aggression
            agg_setting = db.query(SystemSettings).filter(SystemSettings.key == "monetization_aggression").first()
            if agg_setting:
                aggression = int(agg_setting.value)
            
            # Determine if we should harvest this time (Probability check)
            should_harvest = random.randint(1, 100) <= aggression

            if should_harvest:
                # 2. Source Commerce Product (Priority)
                product = await base_monetization_engine.match_viral_to_product(niche, content_id)
                if product:
                    commerce_info = f"\n- COMMERCE_PRODUCT: {product['name']}\n- CHECKOUT_LINK: {product['url']}"
                
                # 3. Source Affiliate Link (Secondary/Fallback)
                if not commerce_info:
                    aff_product = db.query(AffiliateLinkDB).filter(AffiliateLinkDB.niche == niche).order_by(AffiliateLinkDB.created_at.desc()).first()
                    if aff_product:
                        affiliate_info = f"\n- AFFILIATE_LINK: {aff_product.link}\n- PRODUCT_CTA: {aff_product.cta_text or 'Check it out here'}"

            # Fallback if no real key is configured
            if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_key_here":
                # We still want UI to look good, so we try fallback via AIWorker if possible or default hardcoded
                return self._get_fallback_package(niche, platform, None)

            prompt = f"""
            You are a viral content strategist. Generate a high-velocity viral metadata package for a {platform} video in the {niche} niche.
            
            {f"IMPORTANT: You MUST naturally weave the following product recommendation into the description: {commerce_info or affiliate_info}. Do NOT make it look like a generic ad; make it feel like a helpful resource." if (commerce_info or affiliate_info) else "Focus on high engagement and retention hooks."}
            
            Provide the result in JSON format with the following keys:
            - title: A hook-driven, high-CTR title (max 50 chars)
            - description: A compelling description with highly relevant hashtags and the CTA/link merged naturally (max 250 chars)
            - hashtags: A list of 4 highly relevant trending hashtags
            - cta: A strong, urgent call to action
            """

            response_content = await ai_worker.analyze_viral_pattern(prompt)
            
            if "Error" in response_content:
                return self._get_fallback_package(niche, platform)

            try:
                # Attempt to parse JSON if model returned it
                if "{" in response_content:
                    start = response_content.find("{")
                    end = response_content.rfind("}") + 1
                    data = json.loads(response_content[start:end])
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError):
                # Fallback to simple parsing or just use defaults
                return self._get_fallback_package(niche, platform)
            
            return PostMetadata(
                title=data.get("title", f"Secret of {niche} in 2026"),
                description=data.get("description", f"Uncovering the reality of {niche}."),
                hashtags=data.get("hashtags", ["Viral", niche.replace(" ", "")]),
                cta=data.get("cta", "Follow for more!"),
                best_posting_time="Optimal Time Identified",
                platform=platform
            )
        except Exception as e:
            logging.error(f"Optimization Job Error: {e}")
            return self._get_fallback_package(niche, platform)
        finally:
            db.close()

    def _get_fallback_package(self, niche, platform, product=None):
        description = f"Level up your {niche} game with this unique strategy."
        if product:
            description += f" \n\n{product.cta_text}: {product.link}"
        
        return PostMetadata(
            title=f"Viral {niche} Insight",
            description=description,
            hashtags=["Viral", niche.replace(" ", "")],
            cta="Subscribe for more!",
            best_posting_time="Now",
            platform=platform
        )

base_optimization_service = OptimizationService()
