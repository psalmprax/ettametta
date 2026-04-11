from .models import PostMetadata
from api.config import settings
from api.utils.os_worker import ai_worker
from api.utils.database import async_session_factory
from api.utils.models import AffiliateLinkDB, SystemSettings
from services.monetization.service import base_monetization_engine
import json
import logging
import random
import asyncio
from typing import Dict, Any, List
from sqlalchemy import select
from services.monetization.auto_merch import base_auto_merch_service


class OptimizationService:
    async def generate_viral_package(
        self, content_id: str, niche: str, platform: str
    ) -> PostMetadata:
        """
        Uses shared AIWorker to generate SEO-optimized title, description, and hashtags.
        Automatically injects relevant affiliate links and CTAs if available.
        """
        affiliate_info = ""
        commerce_info = ""
        aggression = 100  # Default

        try:
            async with async_session_factory() as db:
                # 1. Check Monetization Settings
                agg_stmt = select(SystemSettings).where(SystemSettings.key == "monetization_aggression")
                agg_result = await db.execute(agg_stmt)
                agg_setting = agg_result.scalar_one_or_none()
                
                if agg_setting:
                    aggression = int(agg_setting.value)

                strategy_stmt = select(SystemSettings).where(SystemSettings.key == "active_monetization_strategy")
                strategy_result = await db.execute(strategy_stmt)
                strategy_setting = strategy_result.scalar_one_or_none()
                
                active_strategy = (
                    strategy_setting.value if strategy_setting else "affiliate"
                )

                # Determine if we should harvest this time (Probability check)
                should_harvest = random.randint(1, 100) <= aggression

                if should_harvest:
                    # 2. Source Monetization based on Strategy
                    if active_strategy == "commerce":
                        product = await base_monetization_engine.match_viral_to_product(
                            niche, content_id
                        )
                        if product:
                            from services.monetization.strategies.commerce import (
                                CommerceStrategy,
                            )

                            strategy = CommerceStrategy()
                            commerce_cta = await strategy.generate_cta(niche, content_id)
                            commerce_info = f"\n- MONETIZATION CTA: {commerce_cta}"

                    elif active_strategy == "affiliate":
                        aff_stmt = select(AffiliateLinkDB).where(AffiliateLinkDB.niche == niche).order_by(AffiliateLinkDB.created_at.desc())
                        aff_result = await db.execute(aff_stmt)
                        aff_product = aff_result.scalar_one_or_none()
                        
                        if aff_product:
                            from services.monetization.strategies.affiliate import (
                                AffiliateStrategy,
                            )

                            strategy = AffiliateStrategy()
                            affiliate_cta = await strategy.generate_cta(niche, content_id)
                            affiliate_info = f"\n- MONETIZATION CTA: {affiliate_cta}"

                    # 3. Monetization Arbitrage (Reverse Strategy)
                    # If content is deemed high-potential, recommend creating a custom merch design
                    if aggression > 50:  # Only for aggressive growth accounts
                        # Check viral potential from discovery engagement score
                        try:
                            from services.discovery.service import base_discovery_service

                            recent_content = await base_discovery_service.discover_niche(
                                niche, platform
                            )
                            if recent_content and any(
                                c.engagement_rate > 0.7 for c in recent_content
                            ):
                                arbitrage_suggestion = (
                                    await base_auto_merch_service.trigger_auto_merch(niche)
                                )
                                commerce_info += (
                                    f"\n- ARBITRAGE SUGGESTION: {arbitrage_suggestion}"
                                )
                        except Exception:
                            pass  # Discovery unavailable, skip arbitrage

            # Fallback if no real key is configured
            if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_key_here":
                # We still want UI to look good, so we try fallback via AIWorker if possible or default hardcoded
                return self._get_fallback_package(niche, platform, None)

            prompt = f"""
            You are a viral content strategist. Generate a high-velocity viral metadata package for a {platform} video in the {niche} niche.
            
            {f"IMPORTANT: You MUST append the following monetization CTA to the very end of the description exactly as written: {commerce_info or affiliate_info}" if (commerce_info or affiliate_info) else "Focus on high engagement and retention hooks."}
            
            Provide the result in JSON format with the following keys:
            - title: A hook-driven, high-CTR title (max 50 chars)
            - description: A compelling description with highly relevant hashtags. If a MONETIZATION CTA was provided, it MUST be the final sentence. (max 250 chars)
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
                description=data.get(
                    "description", f"Uncovering the reality of {niche}."
                ),
                hashtags=data.get("hashtags", ["Viral", niche.replace(" ", "")]),
                cta=data.get("cta", "Follow for more!"),
                best_posting_time="Optimal Time Identified",
                platform=platform,
            )
        except Exception as e:
            logging.error(f"Optimization Job Error: {e}")
            return self._get_fallback_package(niche, platform)

    def _get_fallback_package(self, niche, platform, product=None):
        # Return minimal/empty package when API key is not configured
        description = f"Generate content for your {niche} niche."
        if product:
            description += f" \n\n{product.cta_text}: {product.link}"

        return PostMetadata(
            title=title,
            description=description,
            hashtags=[niche.replace(" ", "")],
            cta="Subscribe for more!",
            best_posting_time="Configure API to enable",
            platform=platform,
        )

    async def optimize_seo_content(
        self,
        title: str,
        description: str,
        platform: str,
        niche: str,
        target_audience: str = "general",
    ) -> Dict[str, Any]:
        """
        Complete SEO optimization using AI for viral content.
        Returns optimized title, description, hashtags, and SEO metadata.
        """
        from api.config import settings

        # Use Groq for AI-powered SEO optimization
        if not settings.GROQ_API_KEY:
            # Fallback to basic optimization
            return self._basic_seo_optimization(title, description, platform, niche)

        try:
            from groq import Groq

            client = Groq(api_key=settings.GROQ_API_KEY)

            # Platform-specific optimization prompts
            platform_prompts = {
                "youtube": """
                Optimize for YouTube algorithm: Focus on keywords in first 60 characters of title.
                Use emotional hooks, numbers, and curiosity gaps. Include calls-to-action.
                """,
                "tiktok": """
                Optimize for TikTok FYP: Short, punchy titles with trending sounds/audios.
                Use emojis, questions, and trending challenges. Keep under 2200 characters.
                """,
                "instagram": """
                Optimize for Instagram feed: Visual keywords, emojis, location tags.
                Focus on scroll-stopping hooks and community building.
                """,
                "twitter": """
                Optimize for Twitter/X: Use trending hashtags, mentions, and timing.
                Keep under 280 characters, focus on shareability.
                """,
            }

            platform_context = platform_prompts.get(
                platform.lower(), "General viral content optimization"
            )

            seo_prompt = f"""
            Optimize the following content for {platform} in the {niche} niche for audience: {target_audience}.

            Original Title: {title}
            Original Description: {description}

            Platform Context: {platform_context}

            Please provide:
            1. Optimized Title (max 100 chars for title)
            2. Optimized Description (platform-appropriate length)
            3. 5-10 relevant hashtags
            4. SEO Score (1-100) with reasoning
            5. CTR Prediction (percentage)
            6. Viral Potential (Low/Medium/High) with explanation

            Format as JSON with keys: title, description, hashtags, seo_score, ctr_prediction, viral_potential, reasoning
            """

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": seo_prompt}],
                    temperature=0.7,
                    max_tokens=1000,
                ),
            )

            result_text = response.choices[0].message.content
            # Parse JSON response
            import json

            try:
                seo_result = json.loads(result_text)
                return seo_result
            except json.JSONDecodeError:
                # Fallback to basic optimization if JSON parsing fails
                return self._basic_seo_optimization(title, description, platform, niche)

        except Exception as e:
            logging.warning(f"[SEO] AI optimization failed: {e}")
            return self._basic_seo_optimization(title, description, platform, niche)

    def _basic_seo_optimization(
        self, title: str, description: str, platform: str, niche: str
    ) -> Dict[str, Any]:
        """Fallback basic SEO optimization when AI is unavailable"""
        # Basic keyword insertion
        niche_keywords = niche.lower().split()
        optimized_title = f"{title} - {niche.title()} Tips"

        # Basic hashtags
        hashtags = [
            f"#{niche.replace(' ', '')}",
            f"#{platform}",
            "#viral",
            "#content",
            "#tips",
        ]

        return {
            "title": optimized_title,
            "description": description,
            "hashtags": hashtags,
            "seo_score": 65,
            "ctr_prediction": "8-12%",
            "viral_potential": "Medium",
            "reasoning": "Basic optimization applied - AI optimization unavailable",
        }

    async def generate_viral_hooks(
        self, topic: str, platform: str, count: int = 5
    ) -> List[str]:
        """
        Generate viral hook suggestions for content creation.
        """
        from api.config import settings

        if not settings.GROQ_API_KEY:
            return self._basic_hook_suggestions(topic, platform, count)

        try:
            from groq import Groq

            client = Groq(api_key=settings.GROQ_API_KEY)

            hooks_prompt = f"""
            Generate {count} viral hook suggestions for {platform} content about: {topic}

            Each hook should be:
            - Attention-grabbing in first 3 seconds
            - Create curiosity gap
            - Promise value
            - Under 15 words
            - Platform-appropriate

            Return as a JSON array of strings.
            """

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": hooks_prompt}],
                    temperature=0.8,
                    max_tokens=500,
                ),
            )

            result_text = response.choices[0].message.content
            import json

            try:
                hooks = json.loads(result_text)
                return (
                    hooks
                    if isinstance(hooks, list)
                    else self._basic_hook_suggestions(topic, platform, count)
                )
            except:
                return self._basic_hook_suggestions(topic, platform, count)

        except Exception as e:
            logging.warning(f"[Hooks] Generation failed: {e}")
            return self._basic_hook_suggestions(topic, platform, count)

    def _basic_hook_suggestions(
        self, topic: str, platform: str, count: int
    ) -> List[str]:
        """Basic hook suggestions when AI is unavailable"""
        base_hooks = [
            f"You won't believe what happened with {topic}",
            f"The secret to {topic} no one talks about",
            f"{topic} changed my life - you need to know this",
            f"Stop doing {topic} wrong - watch this",
            f"I tried {topic} for 30 days - here's what happened",
        ]
        return base_hooks[:count]


base_optimization_service = OptimizationService()
