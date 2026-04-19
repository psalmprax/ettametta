import os
import json
import logging
import asyncio
import random
from typing import Any
from pathlib import Path
from groq import AsyncGroq
from api.config import settings

logger = logging.getLogger(__name__)

from services.base_agent import BaseEttamettaAgent
from datetime import datetime

class HermesSkillService(BaseEttamettaAgent):
    """
    Elite Self-Improving Skill Engine.
    Reflects on successful jobs to 'crystallize' winning patterns and 
    triggers autonomous recursive spinoffs via Celery.
    """

    def __init__(self, storage_path: str = "services/hermes/skills.json"):
        super().__init__(agent_name="HERMES")
        # Normalize path to ensure it's relative to the app root or absolute
        self.storage_path = Path(os.getenv("HERMES_SKILLS_PATH", storage_path))
        if not self.storage_path.is_absolute():
            # Use project root if relative
            self.storage_path = settings.BASE_DIR / "src" / storage_path
            
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.skills = self._load_skills()
        
        # Viral Detection Thresholds
        self.success_views = 5000
        self.breakout_views = 50000

    def _load_skills(self) -> dict[str, list[dict]]:
        """Load crystallized skills from JSON storage."""
        if not self.storage_path.exists():
            return {"global": [], "niches": {}}
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[Hermes] Failed to load skills: {e}")
            return {"global": [], "niches": {}}

    def _save_skills(self):
        """Persist crystallized skills to JSON storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.skills, f, indent=4)
        except Exception as e:
            logger.error(f"[Hermes] Failed to save skills: {e}")

    async def _trigger_recursive_spinoff(self, job_data: dict[str, Any], metrics: dict[str, Any], pattern_summary: str):
        """
        Autonomous Scaling & Transmutation via Celery.
        Spawns a new 'Elite' Narrative Fusion task based on the winning pattern.
        """
        job_id = job_data.get("job_id", "unknown")
        source_niche = job_data.get("niche", "general")
        
        await self._log(f"🧬 Spawning recursive variant for breakout success: {job_id}")
        
        # Determine target niche (Scaling vs Transmutation)
        # 70% chance to double down on success, 30% to jump niche
        if random.random() < 0.7:
            target_niche = source_niche
            mode = "SCALING"
        else:
            niches = ["Finance", "Technology", "Health", "Lifestyle", "Gaming"]
            target_niche = random.choice([n for n in niches if n != source_niche])
            mode = "TRANSMUTATION"

        await self._log(f"🧪 {mode} Triggered: '{source_niche}' -> '{target_niche}'")

        try:
            from api.utils.celery import celery_app
            # Trigger recursive narrative fusion with the winning seed
            celery_app.send_task(
                "video.narrative_fusion",
                kwargs={
                    "niche": target_niche,
                    "duration_sec": 60,
                    "user_id": job_data.get("user_id"),
                    # Injecting the winning pattern as a 'Hint'
                    "analysis_data": {
                        "hermes_seed": pattern_summary,
                        "source_job": job_id,
                        "evolution_mode": mode
                    }
                }
            )
            await self._log(f"📡 Spinoff task enqueued for {target_niche}")
        except Exception as e:
            await self._log(f"Failed to enqueue spinoff: {e}", "ERROR")

    async def reflect_and_crystallize(self, job_data: dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any] | None:
        """
        Analyzes performance and captures successful patterns.
        Triggers recursive spinoffs for breakout successes.
        """
        views = metrics.get("views", 0)
        retention = metrics.get("retention_p50", 0)
        
        # 1. Breakthrough Detection
        is_breakout = views >= self.breakout_views or retention > 0.75
        is_successful = views >= self.success_views or retention > 0.6
        
        if not is_successful:
            return None

        job_id = job_data.get("job_id", "unknown")
        niche = job_data.get("niche", "general")
        script = job_data.get("script", {})

        await self._log(f"🚀 Reflecting on success: {job_id} ({views} views)")

        prompt = f"""
        You are the Hermes Reflection Engine. A video in the '{niche}' niche was successful.
        Extract the core 'Winning Pattern' for future replication.
        
        SCRIPT: {json.dumps(script)[:1000]}...
        METRICS: {json.dumps(metrics)}
        
        OUTPUT FORMAT (JSON):
        {{
            "skill_name": "...",
            "pattern_type": "hook | structure | vibe",
            "abstracted_pattern": "A 1-sentence instruction for future AI generation",
            "confidence_score": 0.95
        }}
        """

        try:
            response_content = await self._call_llm(
                prompt=prompt,
                system_prompt="You are the Hermes Self-Improvement Engine.",
                response_format="json_object"
            )
            
            skill = json.loads(response_content)
            skill.update({
                "job_id": job_id,
                "niche": niche,
                "timestamp": datetime.utcnow().isoformat(),
                "performance": metrics
            })
            
            # Store Skill
            if niche not in self.skills["niches"]:
                self.skills["niches"][niche] = []
            
            # Avoid dupes
            if not any(s.get("job_id") == job_id for s in self.skills["niches"][niche]):
                self.skills["niches"][niche].append(skill)
                self._save_skills()
                await self._log(f"💎 Crystallized pattern: {skill['skill_name']}")

                # 2. Trigger Spinoff if Breakout
                if is_breakout:
                    await self._trigger_recursive_spinoff(job_data, metrics, skill["abstracted_pattern"])
                
                return skill

        except Exception as e:
            await self._log(f"Reflection failed: {e}", "ERROR")
            return None

    def get_winning_context(self, niche: str, limit: int = 3) -> list[str]:
        """
        Retrieve winning pattern strings to inject into new generator prompts.
        Used by Decision Engine to boost success probability.
        """
        niche_skills = self.skills["niches"].get(niche, [])
        global_skills = self.skills.get("global", [])
        
        # Order by performance (views)
        all_skills = sorted(
            niche_skills + global_skills, 
            key=lambda x: x.get("performance", {}).get("views", 0), 
            reverse=True
        )
        
        return [s["abstracted_pattern"] for s in all_skills[:limit]]

    def get_intelligence_report(self) -> dict[str, Any]:
        return {
            "name": "Hermes Elite Evolution",
            "status": "operational",
            "total_skills": sum(len(s) for s in self.skills["niches"].values()),
            "learning_enabled": True,
            "storage": str(self.storage_path)
        }

# Singleton
base_hermes_service = HermesSkillService()
