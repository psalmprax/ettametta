import logging
import asyncio
import json
from typing import List, Dict, Any
from groq import Groq
from api.config import settings
from .tools.discovery import discovery_tool
from .tools.render import render_tool
from .tools.publish import publish_tool
from .tools.affiliate import affiliate_tool
from .tools.market_screener import market_screener_tool
from api.routes.ws import notify_system_log_async

logger = logging.getLogger(__name__)

class AgentZero:
    """
    The Autonomous Director of ettametta.
    Orchestrates Discovery, Analysis, Production, and Publishing.
    """
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"
        self.is_running = False
        self.current_step = "IDLE"
        self.last_run_at = None
        self.next_run_at = None
        self.latest_insights = None
        self.tools = {
            "discovery": discovery_tool,
            "render": render_tool,
            "publish": publish_tool,
            "affiliate": affiliate_tool,
            "screener": market_screener_tool
        }

    async def _log(self, message: str, level: str = "INFO"):
        """Broadcasts a log message to the UI console."""
        await notify_system_log_async(message, level=level, module="AGENT_ZERO")
        logger.info(f"[AgentZero] {message}")

    async def start(self):
        """Starts the autonomous production loop."""
        if self.is_running:
            return
        self.is_running = True
        self.current_step = "IDLE"
        await self._log("Autonomous Loop Ignition Sequence Initiated.", "SYSTEM")
        
        while self.is_running:
            try:
                self.last_run_at = asyncio.get_event_loop().time()
                self.next_run_at = self.last_run_at + (4 * 3600)
                await self.run_iteration()
                self.current_step = "WAITING"
                await self._log(f"Cycle Complete. Engine entering standby. Next run in 4 hours.", "SUCCESS")
                # Wait for 4 hours between iterations (configurable)
                for _ in range(4 * 3600):
                    if not self.is_running: break
                    await asyncio.sleep(1)
            except Exception as e:
                self.current_step = "ERROR"
                await self._log(f"Loop Integrity Failure: {e}", "ERROR")
                await asyncio.sleep(300) # Wait 5 mins before retry on error

    def stop(self):
        """Stops the autonomous loop."""
        self.is_running = False
        logger.info("[AgentZero] Autonomous Loop Stopped.")

    async def run_iteration(self):
        """A single iteration of the autonomous cycle."""
        await self._log("Iteration Started: Scouting for market trends...")
        
        # 1. Discover Trends
        self.current_step = "SCOUTING"
        trends = discovery_tool.run(topic="Viral Tech Trends", limit=5)
        
        if "error" in trends or not trends.get("valid_candidates"):
            await self._log("No viable trends detected in current cluster. Retrying later.", "WARNING")
            self.current_step = "WAITING"
            return

        # 2. Screen Trends for Monetization Potential
        self.current_step = "SCREENING"
        await self._log(f"Scanned {len(trends['valid_candidates'])} candidates. Analyzing monetization velocity...")
        raw_trends = json.dumps(trends["valid_candidates"])
        analysis = market_screener_tool.run(raw_trends)
        
        if analysis.get("monetization_potential") == "Low":
            await self._log("Market potential below threshold (Low). Terminating current branch.", "NEUTRAL")
            self.current_step = "WAITING"
            return

        top_trend = trends["valid_candidates"][0]
        await self._log(f"High-Velocity Signal Detected: {top_trend['title']} (Score: {analysis.get('sentiment_score')})", "SUCCESS")

        # 3. Ideate Strategy and Affiliate Links
        self.current_step = "BRAINSTORMING"
        await self._log("Synthesizing cinematic strategy and affiliate alignment...")
        strategy = await self._brainstorm(top_trend, analysis)
        self.latest_insights = strategy
        
        # Real-First Affiliate Integration
        recommendations = affiliate_tool.recommend_links(
            niche="Tech", 
            script_text=f"{strategy['title']} - {strategy['hook']}"
        )
        
        selected_link = "https://viralforge.ai/monetize"
        if recommendations.get("available_links") and len(recommendations["available_links"]) > 0:
            best_link = recommendations["available_links"][0]
            selected_link = best_link.get("link", selected_link)
            await self._log(f"Selected conversion vector: {best_link.get('product_name')}", "SUCCESS")
        else:
             await self._log("No existing affiliate links for target niche. Proceeding with generic monetization.", "WARNING")

        # 4. Produce and Render
        self.current_step = "RENDERING"
        await self._log(f"Triggering Neural Render: {strategy['title']}", "SYSTEM")
        render_res = render_tool.run(
            title=strategy["title"],
            subtitle=strategy["subtitle"]
        )

        if "error" in render_res:
             await self._log(f"Render Pipeline Fault: {render_res['error']}", "ERROR")
             return

        await self._log(f"Render Job Serialized: {render_res.get('job_id')}", "SUCCESS")

        # 5. Publishing (Real Integration)
        self.current_step = "PUBLISHING"
        video_path = render_res.get("output_path", "")
        if video_path:
            await self._log(f"Initiating Broadcast to Platform Mesh...", "SYSTEM")
            publish_res = publish_tool.run(
                video_path=video_path,
                platform="YouTube", # Optimized for primary node
                title=strategy["title"],
                description=f"{strategy['subtitle']}\n\nGet it here: {selected_link}"
            )
            
            if "error" in publish_res:
                await self._log(f"Publishing Hub Error: {publish_res['error']}", "ERROR")
            else:
                await self._log("Content Successfully Deployed to Production.", "SUCCESS")
        else:
            await self._log("No output asset detected. Video rendering in background. Skipping immediate publish.", "INFO")

        # 6. Register Activity
        await self._log(f"Agent Zero Iteration Finalized. JobID: {render_res.get('job_id')}", "SUCCESS")

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
