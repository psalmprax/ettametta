import logging
import asyncio
import json
from typing import List, Dict, Any
from groq import Groq
from services.openclaw.config import settings
from .tools.discovery import discovery_tool
from .tools.render import render_tool
from .tools.publish import publish_tool
from .tools.affiliate import affiliate_tool
from .tools.market_screener import market_screener_tool

logger = logging.getLogger(__name__)

class AgentZero:
    """
    The Autonomous Director of ettametta.
    Orchestrates Discovery, Analysis, Production, and Publishing.
    """
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.MODEL
        self.is_running = False
        self.tools = {
            "discovery": discovery_tool,
            "render": render_tool,
            "publish": publish_tool,
            "affiliate": affiliate_tool,
            "screener": market_screener_tool
        }

    async def start(self):
        """Starts the autonomous production loop."""
        self.is_running = True
        logger.info("[AgentZero] Autonomous Loop Started.")
        
        while self.is_running:
            try:
                await self.run_iteration()
                # Wait for 4 hours between iterations (configurable)
                await asyncio.sleep(4 * 3600)
            except Exception as e:
                logger.error(f"[AgentZero] Loop Error: {e}")
                await asyncio.sleep(300) # Wait 5 mins before retry on error

    def stop(self):
        """Stops the autonomous loop."""
        self.is_running = False
        logger.info("[AgentZero] Autonomous Loop Stopped.")

    async def run_iteration(self):
        """A single iteration of the autonomous cycle."""
        logger.info("[AgentZero] Starting iteration: Trend Discovery...")
        
        # 1. Discover Trends
        trends = discovery_tool.run(topic="Viral Tech Trends", limit=5)
        
        if "error" in trends or not trends.get("valid_candidates"):
            logger.warning("[AgentZero] No trends found, skipping iteration.")
            return

        # 2. Screen Trends for Monetization Potential
        logger.info("[AgentZero] Screening trends for market potential...")
        raw_trends = json.dumps(trends["valid_candidates"])
        analysis = market_screener_tool.run(raw_trends)
        
        if analysis.get("monetization_potential") == "Low":
            logger.info("[AgentZero] Skipping iteration due to low conversion potential.")
            return

        top_trend = trends["valid_candidates"][0]
        logger.info(f"[AgentZero] Found Winning Trend: {top_trend['title']} (Sentiment: {analysis.get('sentiment_score')})")

        # 3. Ideate Strategy and Affiliate Links
        strategy = await self._brainstorm(top_trend, analysis)
        
        # 4. Produce and Render
        logger.info(f"[AgentZero] Triggering Render: {strategy['title']}")
        render_res = render_tool.run(
            title=strategy["title"],
            subtitle=strategy["subtitle"]
        )

        if "error" in render_res:
            logger.error(f"[AgentZero] Render Failed: {render_res['error']}")
            return

        # 5. Register Affiliate Link for this production
        affiliate_tool.create_link(
            product_name=strategy.get("recommended_product", "General Tech"),
            niche="Tech",
            link="https://amazon.com/example-referral" # In production, this would be dynamic
        )

        logger.info(f"[AgentZero] Iteration Complete. Render Job ID: {render_res.get('job_id')}")

    async def _brainstorm(self, trend: Dict, analysis: Dict) -> Dict:
        """Uses LLM to decide on video title, hooks, and product alignment."""
        prompt = f"""
        Act as a Viral Content Strategist and Elite Affiliate Marketer.
        Trend: {trend['title']}
        Sentiment analysis: {json.dumps(analysis)}
        
        Generate a cinematic video strategy.
        Return ONLY a JSON object with:
        {{
            "title": "Stunning Short Title",
            "subtitle": "Punchy subtitle",
            "hook": "Opening line",
            "recommended_product": "Specific product name to promote"
        }}
        """
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
            response_format={"type": "json_object"}
        )
        return json.loads(chat_completion.choices[0].message.content)

base_agent_zero = AgentZero()
