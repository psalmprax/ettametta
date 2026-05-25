import logging
import asyncio
from datetime import datetime

from ..base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)

class PaperclipOrganicSkill(OpenClawBaseSkill):
    """
    Skill for Paperclip-style autonomous organic scaling and KPI monitoring.
    Focuses on "Cost-Free" ads through direct social posting and performance loops.
    """
    
    def __init__(self):
        super().__init__()
        self.kpi_data = {}
        self.threshold_viral = 1000 # Minimum views to consider "scaling"

    def execute(self, action: str = "track", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "scale":
            return self.scale_organic_reach(kwargs.get("niche", "General"))
        elif action == "decision":
            return str(self.get_autonomous_decision())
            
        return self.track_organic_performance(
            kwargs.get("job_id", "test_job"),
            kwargs.get("platform", "tiktok"),
            kwargs.get("metrics", {"views": 0, "likes": 0, "shares": 0})
        )
        
    def track_organic_performance(self, job_id: str, platform: str, metrics: dict[str, int]) -> str:
        """
        Record performance of an organic post.
        """
        self.kpi_data[job_id] = {
            "platform": platform,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        views = metrics.get("views", 0)
        likes = metrics.get("likes", 0)
        metrics.get("shares", 0)
        
        logger.info(f"Tracking organic performance for {job_id} on {platform}: {views} views")
        
        status = "Normal"
        if views > self.threshold_viral:
            status = "🔥 VIRAL DETECTED"
            # TRIGGER HERMES REFLECTION
            try:
                from src.services.hermes.service import base_hermes_service
                # In a real system, we'd fetch the job_data from DB here
                # Mocking minimal job_data for reflection
                mock_job_data = {
                    "job_id": job_id,
                    "niche": "organic_trending",
                    "platform": platform,
                    "metrics": metrics
                }
                asyncio.create_task(base_hermes_service.reflect_and_crystallize(mock_job_data, metrics))
                logger.info(f"💎 [Paperclip] Triggered Hermes Reflection for Job {job_id}")
            except Exception as e:
                logger.exception(f"Failed to trigger Hermes reflection: {e}")
        
        return f"📊 **Organic Tracking Update**\nJob: `{job_id}`\nPlatform: `{platform}`\nViews: {views}\nLikes: {likes}\nStatus: {status}"

    def scale_organic_reach(self, niche: str) -> str:
        """
        Analyzes past performance and suggests a scaling strategy (iterations).
        """
        high_performers = [
            jid for jid, data in self.kpi_data.items() 
            if data["metrics"].get("views", 0) > self.threshold_viral
        ]
        
        if not high_performers:
            return "📉 No high-performing organic content found yet. Strategy: Continue broad discovery."
        
        suggestion = f"🚀 **Paperclip Organic Scaling Strategy for {niche}**\n\n"
        suggestion += f"Detected {len(high_performers)} viral anchors. Actions:\n"
        
        for jid in high_performers[:3]:
            suggestion += f"- 🔄 Generate 3 variations of Job `{jid}` (Iterative Scaling).\n"
            suggestion += "- 🔗 Inject 'High-Intent' affiliate links for this specific hook.\n"
            
        return suggestion

    def get_autonomous_decision(self) -> dict:
        """
        Returns a decision for the Master Controller to act upon.
        """
        # Logic to decide if we should trigger a new render automatically
        # based on trending niches and past success
        return {
            "action": "scale",
            "reason": "High engagement on organic TikTok posts in 'AI' niche",
            "recommended_niche": "AI Automation"
        }

paperclip_skill = PaperclipOrganicSkill()
