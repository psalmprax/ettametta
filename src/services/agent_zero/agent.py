import logging
import asyncio
import json
import time
from typing import Any
from groq import Groq
from src.api.config import settings
from .tools.discovery import discovery_tool
from .tools.render import render_tool
from .tools.publish import publish_tool
from .tools.affiliate import affiliate_tool
from .tools.market_screener import market_screener_tool
from .tools.paperclip_kpi import paperclip_kpi
from .tools.remotion_render import remotion_tool
from src.services.optimization.ab_testing_automation import ab_testing_automation

logger = logging.getLogger(__name__)


from src.services.base_agent import BaseEttamettaAgent

class AgentZero(BaseEttamettaAgent):
    """
    The Autonomous Director of ettametta.
    Orchestrates Discovery, Analysis, Production, and Publishing.
    """

    def __init__(self):
        super().__init__(agent_name="AGENT_ZERO")
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
            "screener": market_screener_tool,
            "paperclip": paperclip_kpi,
            "remotion": remotion_tool,
            "ab_testing": ab_testing_automation,
        }

    async def _persist_state(self):
        try:
            from src.api.utils.database import async_session_factory
            from src.api.utils.models import AgentZeroState
            from sqlalchemy import select

            async with async_session_factory() as db:
                state = {
                    "is_running": self.is_running,
                    "last_run_at": self.last_run_at,
                    "next_run_at": self.next_run_at,
                    "current_step": self.current_step
                }
                
                stmt = select(AgentZeroState).where(AgentZeroState.key == "agent_zero_state")
                result = await db.execute(stmt)
                setting = result.scalar_one_or_none()
                
                if setting:
                    setting.value = state
                else:
                    db.add(AgentZeroState(key="agent_zero_state", value=state))
                
                await db.commit()
        except Exception as e:
            logger.error(f"[AgentZero] Persistence failed: {e}")

    async def start(self, auto_resume: bool = False):
        """Starts the autonomous production loop."""
        if self.is_running:
            return
        self.is_running = True
        self.current_step = "IDLE"
        
        if auto_resume:
            await self._log("Autonomous Loop Resuming from persistent state.", "SYSTEM")
        else:
            await self._log("Autonomous Loop Ignition Sequence Initiated.", "SYSTEM")
        
        await self._persist_state()

        # Start A/B testing automation in background
        asyncio.create_task(ab_testing_automation.start())

        while self.is_running:
            try:
                # Check if we need to wait for the next scheduled run
                current_time = time.time()
                if self.next_run_at and current_time < self.next_run_at:
                    wait_seconds = int(self.next_run_at - current_time)
                    await self._log(f"Standby: Next cycle scheduled in {wait_seconds} seconds.", "SYSTEM")
                    # Break wait into small chunks to remain responsive to stop signals
                    for _ in range(wait_seconds):
                        if not self.is_running:
                            break
                        await asyncio.sleep(1)
                    
                    if not self.is_running:
                        break

                # Update run timestamps
                self.last_run_at = time.time()
                self.next_run_at = self.last_run_at + (4 * 3600)
                await self._persist_state()
                
                await self.run_iteration()
                self.current_step = "WAITING"
                await self._log(
                    f"Cycle Complete. Engine entering standby. Next run in 4 hours.",
                    "SUCCESS",
                )
                # The loop will naturally wait at the beginning of the next iteration
            except Exception as e:
                self.current_step = "ERROR"
                await self._log(f"Loop Integrity Failure: {e}", "ERROR")
                await asyncio.sleep(300)  # Wait 5 mins before retry on error

    async def stop(self):
        """Stops the autonomous loop."""
        self.is_running = False
        self.current_step = "IDLE"
        await self._persist_state()
        logger.info("[AgentZero] Autonomous Loop Stopped.")

    async def load_and_resume(self):
        """Loads state from DB and resumes if was running."""
        try:
            from src.api.utils.database import async_session_factory
            from src.api.utils.models import AgentZeroState
            from sqlalchemy import select

            async with async_session_factory() as db:
                stmt = select(AgentZeroState).where(AgentZeroState.key == "agent_zero_state")
                result = await db.execute(stmt)
                setting = result.scalar_one_or_none()

                if setting and setting.value:
                    state = setting.value
                    self.last_run_at = state.get("last_run_at")
                    self.next_run_at = state.get("next_run_at")
                    self.current_step = state.get("current_step", "IDLE")

                    if state.get("is_running"):
                        # Launch in background
                        asyncio.create_task(self.start(auto_resume=True))
        except Exception as e:
            logger.error(f"[AgentZero] Load state failed: {e}")

    async def run_iteration(self):
        """A single iteration of the autonomous cycle."""
        await self._log("Iteration Started: Scouting for market trends...")

        # 1. Fetch monitored niches from DB
        from src.api.utils.database import async_session_factory
        from src.api.utils.models import MonitoredNiche
        from sqlalchemy import select
        import random

        monitored_niches = []
        try:
            async with async_session_factory() as db:
                stmt = select(MonitoredNiche).where(MonitoredNiche.is_active == True)
                result = await db.execute(stmt)
                monitored_niches = [m.niche for m in result.scalars().all()]
        except Exception as e:
            await self._log(f"Failed to fetch monitored niches: {e}", "WARNING")

        target_niche = "Viral Tech Trends"
        if monitored_niches:
            target_niche = random.choice(monitored_niches)
            await self._log(
                f"Syncing scouting vector with monitored niche: {target_niche}",
                "SYSTEM",
            )
        else:
            await self._log(
                "No active monitored niches found. Falling back to default cluster.",
                "INFO",
            )

        # 2. Discover Trends
        self.current_step = "SCOUTING"
        trends = discovery_tool.run(niche=target_niche, limit=5)

        if "error" in trends or not trends.get("valid_candidates"):
            await self._log(
                f"No viable trends detected in '{target_niche}' cluster. Retrying later.",
                "WARNING",
            )
            self.current_step = "WAITING"
            return

        # 2. Screen Trends for Monetization Potential
        self.current_step = "SCREENING"
        await self._log(
            f"Scanned {len(trends['valid_candidates'])} candidates. Analyzing monetization velocity..."
        )
        raw_trends = json.dumps(trends["valid_candidates"])
        analysis = market_screener_tool.run(raw_trends)

        if analysis.get("monetization_potential") == "Low":
            await self._log(
                "Market potential below threshold (Low). Terminating current branch.",
                "NEUTRAL",
            )
            self.current_step = "WAITING"
            return

        top_trend = trends["valid_candidates"][0]
        await self._log(
            f"High-Velocity Signal Detected: {top_trend['title']} (Score: {analysis.get('sentiment_score')})",
            "SUCCESS",
        )

        # 3. Ideate Strategy and Affiliate Links
        self.current_step = "BRAINSTORMING"
        await self._log("Synthesizing cinematic strategy and affiliate alignment...")
        strategy = await self._brainstorm(top_trend, analysis)
        self.latest_insights = strategy

        # Real-First Affiliate Integration: Query User's AffiliateLinkDB first
        from src.api.utils.models import AffiliateLinkDB

        selected_link = "https://ettametta.ai/monetize"
        user_affiliate_found = False

        try:
            async with async_session_factory() as db:
                # Direct match for product alignment
                stmt = (
                    select(AffiliateLinkDB)
                    .where(AffiliateLinkDB.niche == target_niche)
                    .limit(1)
                )
                result = await db.execute(stmt)
                user_link = result.scalar_one_or_none()

                if user_link:
                    selected_link = user_link.link
                    user_affiliate_found = True
                    await self._log(
                        f"Targeting User Affiliate Vector: {user_link.product_name}",
                        "SUCCESS",
                    )
        except Exception as e:
            await self._log(f"Affiliate mapping error: {e}", "WARNING")

        if not user_affiliate_found:
            recommendations = affiliate_tool.recommend_links(
                niche=target_niche,
                script_text=f"{strategy['title']} - {strategy['hook']}",
            )

            if (
                recommendations.get("available_links")
                and len(recommendations["available_links"]) > 0
            ):
                best_link = recommendations["available_links"][0]
                selected_link = best_link.get("link", selected_link)
                await self._log(
                    f"Selected external conversion vector: {best_link.get('product_name')}",
                    "SUCCESS",
                )
            else:
                await self._log(
                    "No existing affiliate links for target niche. Proceeding with generic monetization.",
                    "WARNING",
                )

        # 4. Produce and Render
        self.current_step = "RENDERING"
        await self._log(f"Triggering Neural Render: {strategy['title']}", "SYSTEM")
        render_res = render_tool.run(
            title=strategy["title"], subtitle=strategy["subtitle"]
        )

        if "error" in render_res:
            await self._log(f"Render Pipeline Fault: {render_res['error']}", "ERROR")
            return

        await self._log(f"Render Job Serialized: {render_res.get('job_id')}", "SUCCESS")

        # 4b. Programmatic Overlays (Remotion)
        if "scientific" in top_trend.get(
            "category", ""
        ).lower() or "Technical" in strategy.get("title", ""):
            await self._log(
                "Technical niche detected. Engaging Remotion for high-fidelity data overlays...",
                "SYSTEM",
            )
            remotion_res = remotion_tool.run(
                composition="ScienceOverlay",
                props={"title": strategy["title"], "data_points": [88, 92, 95]},
            )
            await self._log(
                f"Remotion Layer Integrated: {remotion_res.get('job_id')}", "SUCCESS"
            )

        # 5. Publishing (Real Integration)
        self.current_step = "PUBLISHING"
        video_path = render_res.get("output_path", "")
        if video_path:
            await self._log(f"Initiating Broadcast to Platform Mesh...", "SYSTEM")
            publish_res = publish_tool.run(
                video_path=video_path,
                platform="YouTube",  # Optimized for primary node
                title=strategy["title"],
                description=f"{strategy['subtitle']}\n\nGet it here: {selected_link}",
            )

            if "error" in publish_res:
                await self._log(
                    f"Publishing Hub Error: {publish_res['error']}", "ERROR"
                )
            else:
                await self._log(
                    "Content Successfully Deployed to Production.", "SUCCESS"
                )
        else:
            await self._log(
                "No output asset detected. Video rendering in background. Skipping immediate publish.",
                "INFO",
            )

        # 6. Register Activity & Performance (Paperclip)
        await self._log(
            f"Agent Zero Iteration Finalized. JobID: {render_res.get('job_id')}",
            "SUCCESS",
        )

        # Self-Correcting Performance Loop
        await self._log("Auditing previous job performance via Paperclip...", "SYSTEM")
        perf_report = paperclip_kpi.run(
            action="scale", niche=top_trend.get("niche", "General")
        )
        if "Trending" in perf_report:
            await self._log(f"Viral Anchor Detected! {perf_report}", "SUCCESS")

    async def _brainstorm(self, trend: dict, analysis: dict) -> dict:
        """Uses LLM to decide on video title, hooks, and product alignment."""
        prompt = f"""
        Act as a Viral Content Strategist and Elite Affiliate Marketer.
        Trend: {trend["title"]}
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
        response = await self._call_llm(
            prompt=prompt,
            response_format="json_object"
        )
        return json.loads(response)


base_agent_zero_service = AgentZero()
