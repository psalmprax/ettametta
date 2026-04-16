import os
import json
import logging
import asyncio
import random
from typing import Dict, Any, List, Optional
from pathlib import Path
from groq import AsyncGroq
from api.config import settings

logger = logging.getLogger(__name__)

class HermesSkillService:
    """
    Self-Improving Skill Engine inspired by the Hermes Agent pattern.
    Reflects on successful jobs to 'crystallize' winning patterns into a 
    persistent skill library.
    """

    def __init__(self, storage_path: str = "services/hermes/skills.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.skills = self._load_skills()
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"
        
        # Viral Detection Threshold (Views)
        self.viral_threshold = 1000

    def _load_skills(self) -> Dict[str, List[Dict]]:
        """Load crystallized skills from JSON storage."""
        if not self.storage_path.exists():
            return {"global": [], "niches": {}}
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Hermes skills: {e}")
            return {"global": [], "niches": {}}

    def _save_skills(self):
        """Persist crystallized skills to JSON storage."""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.skills, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save Hermes skills: {e}")

    async def _trigger_recursive_spinoff(self, job_data: Dict[str, Any], metrics: Dict[str, Any]):
        """Autonomous Scaling & Transmutation Trigger"""
        logger.info(f"🧬 [Hermes] Spawning recursive variants for job {job_data.get('job_id')}")
        
        # 1. Scaling (Direct)
        print(f"📡 [SIGNAL] RECURSIVE_SPINOFF: {job_data.get('job_id')}")

        # 2. TRANSMUTATION (Strategic)
        # We take the strategy and jump to a new niche
        target_niches = ["Finance", "Health", "Productivity"]
        new_niche = random.choice(target_niches)
        
        print(f"🧪 [Hermes] TRANSMUTATION DETECTED: Copying Pattern '{job_data.get('niche')}' -> '{new_niche}'")
        print(f"📡 [SIGNAL] STRATEGIC_TRANSMUTATION: Source={job_data.get('niche')} Target={new_niche}")

    async def reflect_and_crystallize(self, job_data: Dict[str, Any], metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyzes performance and captures successful patterns.
        Also triggers Recursive Spinoffs for high-performing content.
        """
        views = metrics.get("views", 0)
        retention = metrics.get("retention_p50", 0)
        
        # 1. Crystallization Logic
        is_successful = views > 5000 or retention > 0.6
        
        # 2. VIRAL MILESTONE TRIGGER (10/10 Evolution)
        # If it's a breakout success, we scale it immediately
        if views > 50000 or retention > 0.75:
            logger.info(f"🔥 [Hermes] Breakthrough Success Detected for {job_data.get('job_id')}!")
            await self._trigger_recursive_spinoff(job_data, metrics)

        if not is_successful:
            return None # Not viral enough to be a 'Skill' yet

        job_id = job_data.get("job_id", "unknown")
        niche = job_data.get("niche", "general")
        script = job_data.get("script", {})

        logger.info(f"🚀 [Hermes] Reflecting on Viral Success: Job {job_id} ({views} views)")

        prompt = f"""
        You are the Hermes Reflection Engine. A video in the '{niche}' niche just went viral with {views} views.
        Analyze the following script and extract the 'Winning Pattern' that made it successful.
        
        SCRIPT CONTENT:
        {json.dumps(script, indent=2)}
        
        METRICS:
        {json.dumps(metrics, indent=2)}
        
        TASK:
        1. Identify the 'Hook' pattern (e.g., 'Negative Frame', 'Direct Question', 'Surprising Fact').
        2. Identify the 'Vibe' (e.g., 'Aggressive', 'Calm/Educational', 'Fast-Paced/Hype').
        3. Identify the 'Structure' (e.g., 'Fact -> Explanation -> CTA').
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "skill_name": "Short descriptive name for this pattern",
            "pattern_type": "hook | structure | vibe",
            "niche": "{niche}",
            "abstracted_pattern": "Brief, high-impact instruction for future scripts",
            "confidence_score": 0.95
        }}
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are the Hermes Self-Improvement Engine. You crystallize successes into persistent skills."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            skill = json.loads(response.choices[0].message.content)
            skill["job_id"] = job_id
            skill["timestamp"] = os.path.getmtime(self.storage_path) if self.storage_path.exists() else 0
            
            # Store the skill
            if niche not in self.skills["niches"]:
                self.skills["niches"][niche] = []
            
            # Prevent duplicates by job_id
            if not any(s.get("job_id") == job_id for s in self.skills["niches"][niche]):
                self.skills["niches"][niche].append(skill)
                self._save_skills()
                logger.info(f"💎 [Hermes] Crystallized new skill for {niche}: {skill['skill_name']}")
                return skill

        except Exception as e:
            logger.error(f"Error during Hermes reflection: {e}")
            return None

    def get_winning_context(self, niche: str, limit: int = 3) -> List[Dict]:
        """
        Retrieve crystallized winning patterns for a specific niche to inform
        new generation cycles.
        """
        niche_skills = self.skills["niches"].get(niche, [])
        global_skills = self.skills.get("global", [])
        
        # Return combined skills, prioritized by niche
        return (niche_skills + global_skills)[:limit]

    def get_intelligence_report(self) -> Dict[str, Any]:
        """Provides report for the system dashboard."""
        return {
            "name": "Hermes Skill Engine",
            "status": "operational",
            "total_skills": sum(len(s) for s in self.skills["niches"].values()) + len(self.skills["global"]),
            "top_niches": sorted(self.skills["niches"].keys(), key=lambda k: len(self.skills["niches"][k]), reverse=True)[:5],
            "learning_enabled": True
        }

# Singleton Instance
hermes_service = HermesSkillService()
