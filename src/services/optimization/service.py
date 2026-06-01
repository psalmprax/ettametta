from .models import PostMetadata
from src.api.config import settings
from src.api.utils.os_worker import ai_worker
from src.api.utils.database import async_session_factory
from src.api.utils.models import AffiliateLinkDB, SystemSettings
from src.services.monetization.service import base_monetization_service
import json
import logging
import random
import redis
from typing import Any
from sqlalchemy import select
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from src.services.monetization.auto_merch import base_auto_merch_service


from src.api.utils.resilience import CircuitBreaker


class OptimizationService:
    def __init__(self):
        self.logger = logging.getLogger("OptimizationService")
        self.groq_circuit_breaker = CircuitBreaker(
            failure_threshold=3, recovery_timeout=120
        )
        self._redis_client = None

    @property
    def redis(self):
        if not self._redis_client:
            from src.api.utils.redis import get_sync_redis
            self._redis_client = get_sync_redis()
        return self._redis_client

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(
            (TimeoutError, ConnectionError, json.JSONDecodeError)
        ),
        reraise=False,
    )
    async def _call_groq(self, prompt: str, max_tokens: int = 1000) -> str | None:
        """Call Groq API with circuit breaking and retries"""
        if self.groq_circuit_breaker.is_open():
            self.logger.warning("Groq API circuit breaker is OPEN - using fallback")
            return None

        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_key_here":
            return None

        try:
            from groq import AsyncGroq

            client = AsyncGroq(api_key=settings.GROQ_API_KEY, timeout=15.0)

            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=max_tokens,
                timeout=30.0,
            )

            self.groq_circuit_breaker.record_success()
            return response.choices[0].message.content
        except Exception as e:
            self.groq_circuit_breaker.record_failure()
            self.logger.warning(f"Groq API call failed: {e}")
            return None

    async def generate_viral_package(
        self, content_id: str, niche: str, platform: str
    ) -> PostMetadata:
        """
        Uses shared AIWorker to generate SEO-optimized title, description, and hashtags.
        Automatically injects relevant affiliate links and CTAs if available.
        Production-grade with caching, circuit breaking, and retries.
        """
        # Check cache first
        cache_key = f"optimization:viral_package:{content_id}:{niche}:{platform}"
        try:
            cached = self.redis.get(cache_key)
            if cached:
                self.logger.info(
                    f"[Optimization] Serving cached viral package for {content_id}"
                )
                data = json.loads(cached)
                return PostMetadata(**data)
        except Exception as e:
            self.logger.warning(f"[Optimization] Cache read failed: {e}")

        affiliate_info = ""
        commerce_info = ""
        aggression = 100  # Default

        try:
            async with async_session_factory() as db:
                # 1. Check Monetization Settings
                agg_stmt = select(SystemSettings).where(
                    SystemSettings.key == "monetization_aggression"
                )
                agg_result = await db.execute(agg_stmt)
                agg_setting = agg_result.scalar_one_or_none()

                if agg_setting:
                    aggression = int(agg_setting.value)

                strategy_stmt = select(SystemSettings).where(
                    SystemSettings.key == "active_monetization_strategy"
                )
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
                        product = await base_monetization_service.match_viral_to_product(
                            niche, content_id
                        )
                        if product:
                            from src.services.monetization.strategies.commerce import (
                                CommerceStrategy,
                            )

                            strategy = CommerceStrategy()
                            commerce_cta = await strategy.generate_cta(
                                niche, content_id
                            )
                            commerce_info = f"\n- MONETIZATION CTA: {commerce_cta}"

                    elif active_strategy == "affiliate":
                        aff_stmt = (
                            select(AffiliateLinkDB)
                            .where(AffiliateLinkDB.niche == niche)
                            .order_by(AffiliateLinkDB.created_at.desc())
                        )
                        aff_result = await db.execute(aff_stmt)
                        aff_product = aff_result.scalar_one_or_none()

                        if aff_product:
                            from src.services.monetization.strategies.affiliate import (
                                AffiliateStrategy,
                            )

                            strategy = AffiliateStrategy()
                            affiliate_cta = await strategy.generate_cta(
                                niche, content_id
                            )
                            affiliate_info = f"\n- MONETIZATION CTA: {affiliate_cta}"

                    # 3. Monetization Arbitrage (Reverse Strategy)
                    # If content is deemed high-potential, recommend creating a custom merch design
                    if aggression > 50:  # Only for aggressive growth accounts
                        # Check viral potential from discovery engagement score
                        try:
                            from src.services.discovery.service import (
                                base_discovery_service,
                            )

                            recent_content = (
                                await base_discovery_service.search_content(
                                    query=niche, limit=10
                                )
                            )
                            if recent_content and any(
                                getattr(c, "engagement_score", 0) > 0.7 for c in recent_content
                            ):
                                arbitrage_data = (
                                    await base_auto_merch_service.generate_and_publish_merch(
                                        niche
                                    )
                                )
                                if arbitrage_data:
                                    arbitrage_suggestion = arbitrage_data.get("url", "Product Generated")
                                    commerce_info += (
                                        f"\n- ARBITRAGE SUGGESTION: {arbitrage_suggestion}"
                                    )
                        except Exception as e:
                            self.logger.debug(
                                f"Discovery unavailable, skipping arbitrage: {e}"
                            )

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

            response_content = await self._call_groq(prompt)

            if not response_content:
                # Fallback to AIWorker if Groq failed
                response_content = await ai_worker.analyze_viral_pattern(prompt)

            if "Error" in response_content or not response_content:
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
                self.logger.warning(
                    f"Failed to parse optimization response: {response_content[:100]}..."
                )
                return self._get_fallback_package(niche, platform)

            result = PostMetadata(
                title=data.get("title", f"Secret of {niche} in 2026"),
                description=data.get(
                    "description", f"Uncovering the reality of {niche}."
                ),
                hashtags=data.get("hashtags", ["Viral", niche.replace(" ", "")]),
                cta=data.get("cta", "Follow for more!"),
                best_posting_time="Optimal Time Identified",
                platform=platform,
            )

            # Cache result for 1 hour
            try:
                self.redis.setex(cache_key, 3600, result.json())
            except Exception as e:
                self.logger.warning(f"Failed to cache optimization result: {e}")

            return result
        except Exception as e:
            self.logger.error(f"Optimization Job Error: {e}")
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
            logging.exception(f"Optimization Job Error: {e}")
            return self._get_fallback_package(niche, platform)

    def _get_fallback_package(self, niche, platform, product=None):
        # Return minimal/empty package when API key is not configured
        description = f"Generate content for your {niche} niche."
        if product:
            description += f" \n\n{product.cta_text}: {product.link}"

        return PostMetadata(
            title=f"Secret of {niche} in 2026",
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
    ) -> dict[str, Any]:
        """
        Complete SEO optimization using AI for viral content.
        Returns optimized title, description, hashtags, and SEO metadata.
        Production-grade with retries and circuit breaking.
        """
        # Use Groq for AI-powered SEO optimization
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_key_here":
            # Fallback to basic optimization
            return self._basic_seo_optimization(title, description, platform, niche)

        try:
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

            result_text = await self._call_groq(seo_prompt, max_tokens=1000)

            if not result_text:
                return self._basic_seo_optimization(title, description, platform, niche)

            # Parse JSON response
            try:
                seo_result = json.loads(result_text)
                return seo_result
            except json.JSONDecodeError:
                # Fallback to basic optimization if JSON parsing fails
                self.logger.warning(
                    f"Failed to parse SEO response: {result_text[:100]}..."
                )
                return self._basic_seo_optimization(title, description, platform, niche)

        except Exception as e:
            self.logger.warning(f"[SEO] AI optimization failed: {e}")
            return self._basic_seo_optimization(title, description, platform, niche)

    def _basic_seo_optimization(
        self, title: str, description: str, platform: str, niche: str
    ) -> dict[str, Any]:
        """Fallback basic SEO optimization when AI is unavailable"""
        # Basic keyword insertion
        niche.lower().split()
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
        self, niche: str, platform: str, count: int = 5
    ) -> list[str]:
        """
        Generate viral hook suggestions for content creation.
        Production-grade with retries and circuit breaking.
        """
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_key_here":
            return self._basic_hook_suggestions(niche, platform, count)

        try:
            hooks_prompt = f"""
            Generate {count} viral hook suggestions for {platform} content about: {niche}

            Each hook should be:
            - Attention-grabbing in first 3 seconds
            - Create curiosity gap
            - Promise value
            - Under 15 words
            - Platform-appropriate

            Return as a JSON array of strings.
            """

            result_text = await self._call_groq(hooks_prompt, max_tokens=500)

            if not result_text:
                return self._basic_hook_suggestions(niche, platform, count)

            try:
                hooks = json.loads(result_text)
                return (
                    hooks
                    if isinstance(hooks, list)
                    else self._basic_hook_suggestions(niche, platform, count)
                )
            except Exception as e:
                self.logger.warning(f"Failed to parse hooks response: {e}")
                return self._basic_hook_suggestions(niche, platform, count)

        except Exception as e:
            self.logger.warning(f"[Hooks] Generation failed: {e}")
            return self._basic_hook_suggestions(niche, platform, count)

    def _basic_hook_suggestions(
        self, niche: str, platform: str, count: int
    ) -> list[str]:
        """Basic hook suggestions when AI is unavailable"""
        base_hooks = [
            f"You won't believe what happened with {niche}",
            f"The secret to {niche} no one talks about",
            f"{niche} changed my life - you need to know this",
            f"Stop doing {niche} wrong - watch this",
            f"I tried {niche} for 30 days - here's what happened",
        ]
        return base_hooks[:count]


base_optimization_service = OptimizationService()
