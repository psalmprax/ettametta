import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from api.config import settings
from .memory import memory_skill

logger = logging.getLogger(__name__)


class TrendPredictionSkill:
    def __init__(self):
        self.api_url = f"{settings.API_URL}"
        self.prediction_history: List[Dict] = []

    def _get_headers(self):
        headers = {}
        if settings.INTERNAL_API_TOKEN:
            headers["Authorization"] = f"Bearer {settings.INTERNAL_API_TOKEN}"
        return headers

    def predict_trend(self, niche: str = "general", horizon_days: int = 7) -> str:
        try:
            resp = requests.get(
                f"{self.api_url}/discovery/niche-trends/{niche}",
                headers=self._get_headers(),
                timeout=15,
            )

            current_trends = []
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    current_trends = data[:10]
                elif isinstance(data, dict):
                    current_trends = data.get("trends", data.get("results", []))[:10]

            recent_memories = memory_skill.episodic.search(
                event_type="discovery_result", since_hours=168, limit=50
            )

            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a viral trend prediction expert. Analyze current trends and historical patterns "
                            "to predict what will go viral in the next 7-14 days. Consider:\n"
                            "1. Trend velocity (how fast it's growing)\n"
                            "2. Cross-platform signals (same topic appearing on multiple platforms)\n"
                            "3. Seasonal patterns and recurring themes\n"
                            "4. Emerging topics with low competition\n"
                            "5. Audience fatigue on over-saturated topics\n\n"
                            "Return predictions ranked by confidence with actionable content ideas."
                        ),
                    },
                    {
                        "role": "user",
                        "content": self._build_prediction_prompt(
                            niche, current_trends, recent_memories, horizon_days
                        ),
                    },
                ],
                "model": settings.MODEL,
                "temperature": 0.6,
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
                prediction = groq_resp.json()["choices"][0]["message"]["content"]

                memory_skill.record_event(
                    "trend_prediction",
                    {
                        "niche": niche,
                        "horizon_days": horizon_days,
                        "prediction": prediction[:500],
                    },
                )

                memory_skill.store_fact(
                    f"prediction_{niche}_{datetime.now().strftime('%Y%m%d')}",
                    prediction[:1000],
                    category="trend",
                    confidence=0.7,
                )

                return f"🔮 **Trend Prediction: {niche}** (Next {horizon_days} days)\n\n{prediction}"
            else:
                return f"⚠️ Prediction failed: {groq_resp.status_code}"

        except Exception as e:
            logger.error(f"Trend Prediction Error: {e}")
            return f"⚠️ Prediction Error: {e}"

    def _build_prediction_prompt(
        self, niche: str, current_trends: List, recent_memories: List, horizon_days: int
    ) -> str:
        prompt = f"Predict viral trends for niche '{niche}' over the next {horizon_days} days.\n\n"

        if current_trends:
            prompt += "**Current Trends:**\n"
            for i, t in enumerate(current_trends[:5], 1):
                title = t.get("title", t.get("topic", "Unknown"))
                score = t.get("score", t.get("engagement", "N/A"))
                prompt += f"{i}. {title} (Score: {score})\n"
            prompt += "\n"

        if recent_memories:
            prompt += (
                f"**Recent Activity** ({len(recent_memories)} events in 7 days):\n"
            )
            for m in recent_memories[:5]:
                prompt += f"• {m['event_type']}: {json.dumps(m['data'])[:150]}\n"
            prompt += "\n"

        prompt += "Provide:\n1. Top 5 predicted trends with confidence scores\n2. Content ideas for each\n3. Best platform for each\n4. Timing recommendations"
        return prompt

    def get_trend_velocity(self, topic: str) -> str:
        try:
            resp = requests.get(
                f"{self.api_url}/discovery/search",
                params={"q": topic, "platform": "all", "limit": 20},
                headers=self._get_headers(),
                timeout=10,
            )

            if resp.status_code != 200:
                return f"⚠️ Could not fetch trend data: {resp.status_code}"

            results = resp.json()
            if not results:
                return f"📉 No data found for '{topic}'."

            scores = [
                r.get("score", 0)
                for r in results
                if isinstance(r.get("score"), (int, float))
            ]
            if len(scores) < 2:
                return f"📊 **Trend: {topic}**\nInsufficient data points for velocity analysis.\nCurrent score: {scores[0] if scores else 'N/A'}"

            avg_recent = sum(scores[:5]) / min(5, len(scores))
            avg_older = sum(scores[-5:]) / min(5, len(scores))
            velocity = ((avg_recent - avg_older) / max(avg_older, 0.01)) * 100

            if velocity > 20:
                direction = "🔥 EXPLODING"
            elif velocity > 5:
                direction = "📈 RISING"
            elif velocity > -5:
                direction = "➡️ STABLE"
            elif velocity > -20:
                direction = "📉 DECLINING"
            else:
                direction = "💀 DYING"

            memory_skill.store_fact(
                f"velocity_{topic}",
                {
                    "velocity": velocity,
                    "direction": direction,
                    "avg_recent": avg_recent,
                    "avg_older": avg_older,
                    "timestamp": datetime.now().isoformat(),
                },
                category="trend",
            )

            return (
                f"📊 **Trend Velocity: {topic}**\n"
                f"• Direction: {direction}\n"
                f"• Velocity: {velocity:+.1f}%\n"
                f"• Recent Avg Score: {avg_recent:.1f}\n"
                f"• Older Avg Score: {avg_older:.1f}\n"
                f"• Data Points: {len(scores)}"
            )

        except Exception as e:
            logger.error(f"Trend Velocity Error: {e}")
            return f"⚠️ Velocity Error: {e}"

    def get_cross_platform_signals(self, topic: str) -> str:
        platforms = ["youtube", "tiktok", "reddit", "twitter", "instagram"]
        results = {}

        for platform in platforms:
            try:
                resp = requests.get(
                    f"{self.api_url}/discovery/search",
                    params={"q": topic, "platform": platform, "limit": 5},
                    headers=self._get_headers(),
                    timeout=8,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results[platform] = len(data) if isinstance(data, list) else 1
                else:
                    results[platform] = 0
            except Exception:
                results[platform] = 0

        active_platforms = [p for p, c in results.items() if c > 0]
        signal_strength = len(active_platforms)

        if signal_strength >= 4:
            assessment = "🔥 CROSS-PLATFORM VIRAL — Act now!"
        elif signal_strength >= 3:
            assessment = "📈 Strong multi-platform signal"
        elif signal_strength >= 2:
            assessment = "📊 Emerging — monitor closely"
        else:
            assessment = "📉 Weak signal — not yet trending"

        lines = [
            f"🌐 **Cross-Platform Signal: {topic}**",
            f"• Assessment: {assessment}",
            f"• Active Platforms: {signal_platforms}/{len(platforms)}",
            "",
        ]
        for p, c in results.items():
            bar = "█" * c + "░" * max(0, 5 - c)
            lines.append(f"  {p:12s} [{bar}] {c}")

        memory_skill.store_fact(
            f"cross_platform_{topic}",
            {
                "platforms": results,
                "signal_strength": signal_strength,
                "timestamp": datetime.now().isoformat(),
            },
            category="trend",
        )

        return "\n".join(lines)

    def get_prediction_history(self, limit: int = 10) -> str:
        predictions = memory_skill.episodic.search(
            event_type="trend_prediction", limit=limit
        )
        if not predictions:
            return "📋 No prediction history available."

        lines = [f"📋 **Prediction History** ({len(predictions)}):"]
        for p in reversed(predictions):
            ts = p["timestamp"][:19]
            niche = p["data"].get("niche", "unknown")
            preview = p["data"].get("prediction", "")[:100]
            lines.append(f"• [{ts}] {niche}: {preview}...")
        return "\n".join(lines)


trend_prediction_skill = TrendPredictionSkill()
