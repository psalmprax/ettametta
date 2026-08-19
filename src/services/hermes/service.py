"""
Hermes Autonomous Operations Engine & Skill-Learning Loop
==========================================================
Self-improving autonomous loop linking:
Trend Discovery -> AEO/GEO Optimization -> Video Synthesis -> Multi-Platform Publishing -> Skill Extraction & Telemetry
"""

import os
import json
import logging
import asyncio
import uuid
import httpx
from typing import Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from src.services.optimization.aeo_service import base_aeo_service, AEOAnalysisResult
from src.services.distribution.postiz_service import base_postiz_service, PostizPostResponse
from src.services.analytics.posthog_service import base_posthog_service

logger = logging.getLogger("HermesService")


class LearnedSkill(BaseModel):
    skill_id: str
    name: str
    niche: str
    pattern_type: str  # e.g., "viral_hook", "aeo_formula", "retention_angle"
    template: str
    success_count: int = 1
    average_aeo_score: float = 85.0
    created_at: str


class HermesCycleConfig(BaseModel):
    niche: str = "ai_technology"
    target_platforms: list[str] = Field(default_factory=lambda: ["youtube", "tiktok"])
    autonomy_mode: str = "AUTOPILOT"  # SIMULATION, AUTOPILOT, APPROVAL_REQUIRED
    min_virality_score: float = 75.0
    auto_publish: bool = True
    notify_channel: Optional[str] = None  # e.g., "telegram", "discord", "webhook"


class HermesCycleResult(BaseModel):
    cycle_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    niche: str
    trend_topic: Optional[str] = None
    aeo_analysis: Optional[AEOAnalysisResult] = None
    learned_skills_extracted: list[str] = Field(default_factory=list)
    rendered_video_path: Optional[str] = None
    publish_result: Optional[PostizPostResponse] = None
    error: Optional[str] = None


class HermesSkillStore:
    """
    Persistent memory store where Hermes Agent records learned skills across cycles.
    """

    def __init__(self, storage_path: str = "data/storage/hermes_learned_skills.json"):
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self.skills: dict[str, LearnedSkill] = {}
        self._load_skills()

    def _load_skills(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.skills[k] = LearnedSkill(**v)
            except Exception as e:
                logger.warning(f"[HermesSkillStore] Error loading skills: {e}")

    def _save_skills(self):
        try:
            with open(self.storage_path, "w") as f:
                json.dump({k: v.model_dump() for k, v in self.skills.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"[HermesSkillStore] Error saving skills: {e}")

    def learn_skill(self, name: str, niche: str, pattern_type: str, template: str, score: float) -> LearnedSkill:
        skill_id = f"skill_{uuid.uuid4().hex[:6]}"
        new_skill = LearnedSkill(
            skill_id=skill_id,
            name=name,
            niche=niche,
            pattern_type=pattern_type,
            template=template,
            average_aeo_score=score,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.skills[skill_id] = new_skill
        self._save_skills()
        return new_skill

    def get_best_skills(self, niche: str, limit: int = 3) -> list[LearnedSkill]:
        matching = [s for s in self.skills.values() if s.niche == niche or s.niche == "general"]
        matching.sort(key=lambda s: s.average_aeo_score, reverse=True)
        return matching[:limit]


class HermesAutonomousService:
    """
    Autonomous engine featuring self-learning skill memory and multi-channel notifications.
    """

    def __init__(self):
        self.active_cycles: dict[str, HermesCycleResult] = {}
        self.skill_store = HermesSkillStore()
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")

    async def _send_notification(self, message: str):
        """Send notification via Telegram or Discord if configured"""
        if self.discord_webhook_url:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(self.discord_webhook_url, json={"content": message})
            except Exception as e:
                logger.warning(f"[Hermes] Discord notification failed: {e}")

        if self.telegram_bot_token and self.telegram_chat_id:
            try:
                url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(url, json={"chat_id": self.telegram_chat_id, "text": message})
            except Exception as e:
                logger.warning(f"[Hermes] Telegram notification failed: {e}")

    async def run_autonomous_cycle(self, config: HermesCycleConfig) -> HermesCycleResult:
        """
        Execute one complete autonomous cycle with self-improving skill extraction.
        """
        cycle_id = f"hermes_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now(timezone.utc).isoformat()

        result = HermesCycleResult(
            cycle_id=cycle_id,
            status="running",
            started_at=start_time,
            niche=config.niche,
        )
        self.active_cycles[cycle_id] = result

        try:
            logger.info(f"🚀 [Hermes] Starting cycle {cycle_id} for niche '{config.niche}' (Mode: {config.autonomy_mode})")

            # Step 1: Recall Best Learned Skills for this Niche
            recalled_skills = self.skill_store.get_best_skills(config.niche)
            logger.info(f"[Hermes] Recalled {len(recalled_skills)} learned skills for niche {config.niche}")

            # Step 2: Trend Discovery
            trend_topic = f"Top 5 AI Tools Disrupting {config.niche.replace('_', ' ').title()} in 2026"
            result.trend_topic = trend_topic
            base_posthog_service.track_video_pipeline_step("system", "discovery", cycle_id, "completed", extra={"topic": trend_topic})

            # Step 3: Script Synthesis & AEO/GEO Optimization
            draft_script = (
                f"Here is how {config.niche} professionals are 10x-ing their output in 2026. "
                f"First, autonomous agent networks handle 80% of repetitive data gathering. "
                f"Second, AI video synthesis tools cut production time by over 90%. "
                f"Why is this critical today? Because early adopters are generating over $50,000 monthly with zero headcount."
            )
            aeo_analysis = base_aeo_service.analyze_and_optimize(
                title=trend_topic,
                script_or_transcript=draft_script,
                niche=config.niche,
                target_platform=config.target_platforms[0] if config.target_platforms else "youtube",
            )
            result.aeo_analysis = aeo_analysis
            base_posthog_service.track_video_pipeline_step("system", "aeo_optimization", cycle_id, "completed", extra={"score": aeo_analysis.scores.overall_aeo_score})

            # Step 4: Extract and Store Learned Skill from High-Performing Script
            if aeo_analysis.scores.overall_aeo_score >= 80.0:
                learned_skill = self.skill_store.learn_skill(
                    name=f"High Retention Hook: {trend_topic[:30]}",
                    niche=config.niche,
                    pattern_type="viral_hook",
                    template=draft_script[:120],
                    score=aeo_analysis.scores.overall_aeo_score,
                )
                result.learned_skills_extracted.append(learned_skill.skill_id)
                logger.info(f"[Hermes] Self-learning: Extracted skill {learned_skill.skill_id}")

            # Step 5: Render Video
            mock_video_path = f"data/storage/outputs/{cycle_id}_final.mp4"
            result.rendered_video_path = mock_video_path
            base_posthog_service.track_video_pipeline_step("system", "rendering", cycle_id, "completed", extra={"path": mock_video_path})

            # Step 6: Multi-Platform Publishing
            if config.auto_publish:
                caption = f"{trend_topic}\n\nKey takeaways:\n" + "\n".join([f"• {rec}" for rec in aeo_analysis.optimization_recommendations[:2]]) + "\n\n#AI #Automation #Trends"
                
                publish_res = await base_postiz_service.publish_video(
                    video_path=mock_video_path,
                    caption=caption,
                    platforms=config.target_platforms,
                    tags=aeo_analysis.extracted_entities[:5],
                )
                result.publish_result = publish_res
                base_posthog_service.track_video_pipeline_step("system", "publishing", cycle_id, publish_res.status)

            result.status = "completed"
            result.completed_at = datetime.now(timezone.utc).isoformat()
            
            # Step 7: Send Channel Notification
            await self._send_notification(
                f"✅ [Hermes Agent] Cycle {cycle_id} completed!\n"
                f"Topic: {trend_topic}\n"
                f"AEO Score: {aeo_analysis.scores.overall_aeo_score}/100\n"
                f"Platforms: {', '.join(config.target_platforms)}"
            )
            logger.info(f"✅ [Hermes] Cycle {cycle_id} finished successfully.")

        except Exception as e:
            logger.exception(f"❌ [Hermes] Cycle {cycle_id} failed: {e}")
            result.status = "failed"
            result.error = str(e)
            result.completed_at = datetime.now(timezone.utc).isoformat()
            await self._send_notification(f"❌ [Hermes Agent] Cycle {cycle_id} failed: {e}")

        return result

    def get_cycle_status(self, cycle_id: str) -> Optional[HermesCycleResult]:
        return self.active_cycles.get(cycle_id)


base_hermes_service = HermesAutonomousService()
