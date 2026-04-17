import requests
import logging
import json
from typing import Any
from src.api.config import settings

logger = logging.getLogger(__name__)


class DiscoverySkill:
    """
    Enhanced Discovery Skill for OpenClaw agents.
    Can perform intelligent discovery, trend analysis, and content ideation.
    """

    def __init__(self):
        self.api_url = f"{settings.API_URL}/discovery"
        self.groq_client = None
        try:
            from groq import Groq

            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        except:
            logger.warning("Groq client not available for discovery analysis")

    def _get_headers(self):
        headers = {}
        if settings.INTERNAL_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"
        return headers

    def search_trends(self, topic: str, limit: int = 5, analyze: bool = False) -> str:
        """
        Enhanced search with optional AI analysis.
        """
        try:
            payload = {"q": topic, "size": limit}
            response = requests.get(
                f"{self.api_url}/search",
                params=payload,
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                results = response.json()

                if not isinstance(results, list) or not results:
                    return f"No trends found for '{topic}'."

                summary = f"🔎 **Discovery Results for '{topic}':**\n"
                for i, item in enumerate(results[:limit], 1):
                    title = item.get("title", "No Title")
                    platform = item.get("platform", "Unknown")
                    viral_score = item.get("viral_score", 0)
                    url = item.get("url", "#")
                    summary += (
                        f"{i}. [{title}]({url}) - {platform} (Viral: {viral_score})\n"
                    )

                if analyze and self.groq_client:
                    analysis = self._analyze_trends(results[:limit], topic)
                    summary += f"\n🤖 **AI Analysis:** {analysis}"

                return summary
            else:
                return f"⚠️ API Error: {response.status_code} - {response.text}"

        except Exception as e:
            logger.error(f"Discovery Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

    def get_trending_content(self, niche: str, min_viral_score: int = 75) -> str:
        """
        Get trending content for a specific niche.
        """
        try:
            payload = {"niche": niche, "min_viral_score": min_viral_score, "size": 10}
            response = requests.get(
                f"{self.api_url}/trends",
                params=payload,
                headers=self._get_headers(),
                timeout=10,
            )

            if response.status_code == 200:
                results = response.json()

                if not results:
                    return f"No trending content found for '{niche}' with viral score > {min_viral_score}."

                summary = (
                    f"📈 **Trending in '{niche}' (Viral Score > {min_viral_score}):**\n"
                )
                for i, item in enumerate(results, 1):
                    title = item.get("title", "No Title")
                    platform = item.get("platform", "Unknown")
                    viral_score = item.get("viral_score", 0)
                    views = item.get("views", 0)
                    url = item.get("url", "#")
                    summary += f"{i}. [{title}]({url}) - {platform} (Viral: {viral_score}, Views: {views:,})\n"

                return summary
            else:
                return f"⚠️ API Error: {response.status_code}"

        except Exception as e:
            logger.error(f"Trending content error: {e}")
            return f"⚠️ Error getting trending content: {str(e)}"

    def scan_for_opportunities(self, niche: str, deep: bool = False) -> str:
        """
        Trigger a discovery scan and analyze opportunities.
        """
        try:
            payload = {"niches": [niche], "deep": deep}
            response = requests.post(
                f"{self.api_url}/scan",
                json=payload,
                headers=self._get_headers(),
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id", "unknown")

                if deep:
                    return f"🔬 **Deep Discovery Scan Started for '{niche}'**\nTask ID: {task_id}\nThis will analyze trends, competitors, and monetization opportunities using AI."
                else:
                    return f"🔍 **Quick Discovery Scan Started for '{niche}'**\nTask ID: {task_id}\nChecking recent trends and viral content."

            else:
                return f"⚠️ Scan failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Scan error: {e}")
            return f"⚠️ Scan error: {str(e)}"

    def analyze_competitor_strategy(self, competitor_url: str) -> str:
        """
        Analyze a competitor's content strategy.
        """
        try:
            # This would call the competitor analysis endpoint
            payload = {"url": competitor_url}
            response = requests.post(
                f"{settings.API_URL}/agent/crew",
                json={
                    "task": f"Analyze competitor strategy for: {competitor_url}",
                    "agents": ["researcher", "analyst"],
                },
                headers=self._get_headers(),
                timeout=60,
            )

            if response.status_code == 200:
                result = response.json()
                return f"🎯 **Competitor Analysis:** {result.get('result', 'Analysis in progress...')}"
            else:
                return f"⚠️ Competitor analysis failed: {response.status_code}"

        except Exception as e:
            logger.error(f"Competitor analysis error: {e}")
            return f"⚠️ Competitor analysis error: {str(e)}"

    def predict_trends(self, niche: str, timeframe: str = "1week") -> str:
        """
        Predict upcoming trends using AI analysis.
        """
        if not self.groq_client:
            return "⚠️ AI analysis unavailable - Groq API key not configured."

        try:
            # Get current trending data
            current_trends = self.get_trending_content(niche, min_viral_score=50)

            # Use AI to predict trends
            prompt = f"""Based on current trending content in '{niche}', predict what will trend in the next {timeframe}.

Current trends:
{current_trends}

Provide 3 specific trend predictions with reasoning. Format as:
1. Trend: [prediction] - Why: [reasoning]
2. Trend: [prediction] - Why: [reasoning]
3. Trend: [prediction] - Why: [reasoning]"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7,
            )

            prediction = response.choices[0].message.content
            return f"🔮 **Trend Predictions for '{niche}' (Next {timeframe}):**\n\n{prediction}"

        except Exception as e:
            logger.error(f"Trend prediction error: {e}")
            return f"⚠️ Trend prediction failed: {str(e)}"

    def _analyze_trends(self, trends: list[dict], topic: str) -> str:
        """
        Use AI to analyze discovered trends.
        """
        if not self.groq_client or not trends:
            return "No AI analysis available."

        try:
            trends_text = "\n".join(
                [
                    f"- {t.get('title', 'Unknown')}: {t.get('description', '')[:100]}"
                    for t in trends[:5]
                ]
            )

            prompt = f"""Analyze these trending results for '{topic}' and provide insights:

{trends_text}

Provide a brief analysis (2-3 sentences) on:
1. Why these trends are working
2. What patterns you notice
3. Content creation recommendations"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.6,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Trend analysis error: {e}")
            return "AI analysis temporarily unavailable."

    def generate_content_ideas(self, niche: str, num_ideas: int = 5) -> str:
        """
        Generate content ideas based on discovered trends.
        """
        if not self.groq_client:
            return "⚠️ Content ideation requires Groq API key."

        try:
            # Get trending topics first
            trends = self.get_trending_content(niche, min_viral_score=60)

            prompt = f"""Based on trending content in '{niche}', generate {num_ideas} creative content ideas.

Trending context:
{trends}

Generate specific, actionable content ideas that could go viral. Format as:
1. [Hook/Title]: [Brief description]
2. [Hook/Title]: [Brief description]
etc."""

            response = self.groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600,
                temperature=0.8,
            )

            ideas = response.choices[0].message.content
            return f"💡 **Content Ideas for '{niche}':**\n\n{ideas}"

        except Exception as e:
            logger.error(f"Content ideation error: {e}")
            return f"⚠️ Content ideation failed: {str(e)}"


discovery_skill = DiscoverySkill()
