import json
import logging
import requests
from datetime import datetime
from src.api.config import settings
from .memory import memory_skill
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class CompetitorSkill(OpenClawBaseSkill):
    def execute(
        self,
        action: str = "analyze",
        channel_name: str = "",
        platform: str = "YouTube",
        competitors: list = None,
        **kwargs,
    ) -> str:
        """
        Standardized mission execution.
        Routes to analyze or compare based on action.
        """
        mode = action or kwargs.get("mode", "analyze")
        ch = channel_name or kwargs.get("channel_name", "")
        plt = platform or kwargs.get("platform", "YouTube")
        
        if mode == "compare" and (competitors or kwargs.get("competitors")):
            return self.compare_competitors(competitors or kwargs.get("competitors"))
        return self.analyze_competitor(ch, plt)

    def analyze_competitor(self, channel_name: str, platform: str = "YouTube") -> str:
        try:
            platform_lower = platform.lower()
            if platform_lower in ("youtube", "yt"):
                return self._analyze_youtube(channel_name)
            elif platform_lower in ("tiktok", "tt"):
                return self._analyze_tiktok(channel_name)
            elif platform_lower in ("instagram", "ig"):
                return self._analyze_instagram(channel_name)
            else:
                return self._analyze_generic(channel_name, platform)
        except Exception as e:
            logger.error(f"Intelligent workflow skill error: {e}")
            return f"⚠️ Error: {str(e)}"

    def _analyze_youtube(self, channel_name: str) -> str:
        try:
            resp = requests.get(
                f"{self.api_url}/discovery/search",
                params={"query": channel_name, "platform": "youtube", "limit": 10},
                headers=self._get_headers(),
                timeout=10,
            )

            channel_data = {}
            videos = []
            if resp.status_code == 200:
                results = resp.json()
                if isinstance(results, dict):
                    results = results.get("data", [])
                if isinstance(results, list):
                    videos = results
                    if results:
                        channel_data = results[0].get("channel", {})

            total_views = sum(
                v.get("views", v.get("score", 0))
                for v in videos
                if isinstance(v.get("views", v.get("score", 0)), (int, float))
            )
            avg_views = total_views / max(len(videos), 1)

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a YouTube competitor analysis expert. Analyze the provided channel data "
                            "and provide actionable insights including:\n"
                            "1. Content strategy breakdown\n"
                            "2. Posting frequency and optimal times\n"
                            "3. Top-performing formats and topics\n"
                            "4. Audience engagement patterns\n"
                            "5. Gaps and opportunities for us to exploit\n"
                            "6. Recommended counter-strategy"
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Analyze YouTube channel: {channel_name}\n"
                            f"Videos found: {len(videos)}\n"
                            f"Total views: {total_views:,}\n"
                            f"Average views: {avg_views:,.0f}\n\n"
                            f"Recent videos:\n{json.dumps(videos[:5], indent=2)[:1000]}"
                        ),
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.5,
                "max_tokens": 1500,
            }
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            groq_resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=20,
            )

            if groq_resp.status_code == 200:
                analysis = groq_resp.json()["choices"][0]["message"]["content"]

                memory_skill.record_event(
                    "competitor_analysis",
                    {
                        "channel": channel_name,
                        "platform": "YouTube",
                        "videos_analyzed": len(videos),
                        "total_views": total_views,
                    },
                )

                return f"🎯 **Competitor Analysis: {channel_name}** (YouTube)\n\n{analysis}"
            else:
                return f"⚠️ Analysis failed: {groq_resp.status_code}"

        except Exception as e:
            return f"⚠️ YouTube Analysis Error: {e}"

    def _analyze_tiktok(self, username: str) -> str:
        try:
            metrics_resp = requests.get(
                f"https://www.tiktok.com/@{username}",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a TikTok competitor analysis expert. Provide a detailed breakdown of "
                            "the competitor's strategy including:\n"
                            "1. Content themes and formats\n"
                            "2. Hook patterns and video structure\n"
                            "3. Posting schedule and frequency\n"
                            "4. Engagement tactics\n"
                            "5. Hashtag strategy\n"
                            "6. Opportunities for us to differentiate"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Analyze TikTok competitor: @{username}",
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.5,
                "max_tokens": 1200,
            }
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            groq_resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15,
            )

            if groq_resp.status_code == 200:
                analysis = groq_resp.json()["choices"][0]["message"]["content"]
                return f"🎯 **Competitor Analysis: @{username}** (TikTok)\n\n{analysis}"
            else:
                return f"⚠️ Analysis failed: {groq_resp.status_code}"

        except Exception as e:
            return f"⚠️ TikTok Analysis Error: {e}"

    def _analyze_instagram(self, username: str) -> str:
        try:
            from .metrics import social_metrics_skill

            profile = social_metrics_skill.get_instagram_profile(username)

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Analyze this Instagram competitor profile and provide:\n"
                            "1. Content strategy (Reels vs Posts vs Stories)\n"
                            "2. Engagement rate analysis\n"
                            "3. Visual style and branding\n"
                            "4. Hashtag and caption patterns\n"
                            "5. Growth tactics and opportunities for us"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Analyze Instagram competitor: @{username}\n\nProfile data: {profile[:1000]}",
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.5,
                "max_tokens": 1200,
            }
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            groq_resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15,
            )

            if groq_resp.status_code == 200:
                analysis = groq_resp.json()["choices"][0]["message"]["content"]
                return (
                    f"🎯 **Competitor Analysis: @{username}** (Instagram)\n\n{analysis}"
                )
            else:
                return f"⚠️ Analysis failed: {groq_resp.status_code}"

        except Exception as e:
            return f"⚠️ Instagram Analysis Error: {e}"

    def _analyze_generic(self, name: str, platform: str) -> str:
        try:
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": f"Analyze this {platform} competitor and provide actionable insights.",
                    },
                    {
                        "role": "user",
                        "content": f"Analyze {platform} competitor: {name}",
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.5,
                "max_tokens": 1000,
            }
            headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
            groq_resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15,
            )

            if groq_resp.status_code == 200:
                analysis = groq_resp.json()["choices"][0]["message"]["content"]
                return f"🎯 **Competitor Analysis: {name}** ({platform})\n\n{analysis}"
            else:
                return f"⚠️ Analysis failed: {groq_resp.status_code}"

        except Exception as e:
            return f"⚠️ Analysis Error: {e}"

    def compare_competitors(self, competitors: list[dict]) -> str:
        if len(competitors) < 2:
            return "⚠️ Provide at least 2 competitors to compare. Format: [{name, platform}, ...]"

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Compare these competitors and provide:\n"
                        "1. Side-by-side strengths/weaknesses\n"
                        "2. Market gaps none of them are filling\n"
                        "3. Best practices we should adopt\n"
                        "4. Unique positioning opportunities\n"
                        "5. Recommended content strategy to outperform all of them"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Compare these competitors:\n{json.dumps(competitors, indent=2)}",
                },
            ],
            "model": settings.MODEL,
            "temperature": 0.5,
            "max_tokens": 1500,
        }
        headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
        try:
            groq_resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=20,
            )
            if groq_resp.status_code == 200:
                comparison = groq_resp.json()["choices"][0]["message"]["content"]
                return f"⚔️ **Competitor Comparison**\n\n{comparison}"
            else:
                return f"⚠️ Comparison failed: {groq_resp.status_code}"
        except Exception as e:
            return f"⚠️ Comparison Error: {e}"

    def get_analysis_history(self, limit: int = 10) -> str:
        analyses = memory_skill.episodic.search(
            event_type="competitor_analysis", limit=limit
        )
        if not analyses:
            return "📋 No competitor analyses recorded."

        lines = [f"📋 **Competitor Analysis History** ({len(analyses)}):"]
        for a in reversed(analyses):
            ts = a["timestamp"][:19]
            channel = a["data"].get("channel", "unknown")
            platform = a["data"].get("platform", "unknown")
            lines.append(f"• [{ts}] {channel} ({platform})")
        return "\n".join(lines)


competitor_skill = CompetitorSkill()
