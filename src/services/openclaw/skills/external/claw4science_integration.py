import logging
import requests
from typing import Any
from groq import Groq
from src.api.config import settings

from ..base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)

class Claw4ScienceSkill(OpenClawBaseSkill):
    """
    Skill for transforming technical/academic data into "Science-Pop" viral scripts.
    Integrates with academic repositories and scientific summaries.
    """
    
    def __init__(self):
        super().__init__()
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        # Use LANGCHAIN_MODEL as default or fallback to llama3-8b
        self.model = getattr(settings, "LANGCHAIN_MODEL", "llama-3.1-8b-instant")

    def execute(self, action: str = "convert", topic: str = "", raw_data: str = "", **kwargs) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        if action == "trends":
            return self.fetch_scientific_niche_trends(topic)
            
        return self.convert_technical_to_viral(raw_data, kwargs.get("platform", "TikTok"))
        
    def convert_technical_to_viral(self, raw_data: str, target_platform: str = "TikTok") -> str:
        """
        Uses LLM to rewrite dense scientific data into a viral short-form script.
        """
        prompt = f"""
        TRANSFORM THE FOLLOWING SCIENTIFIC DATA INTO A VIRAL {target_platform} SCRIPT:
        
        DATA: {raw_data}
        
        RULES:
        1. **HOOK**: Start with a "Did you know?" or "This changes everything" hook.
        2. **CONTRAST**: Simplify the complexity (ELIMINATE JARGON).
        3. **PACING**: Fast cuts every 1.5 - 2 seconds.
        4. **MONETIZATION**: Suggest a related niche (e.g., 'Bio-Hacking', 'Quantum Computing', 'Space Tech').
        5. **DURATION**: 15-30 seconds.
        
        Output format:
        [00:00] HOOK: ...
        [00:05] THE PROBLEM: ...
        [00:15] THE SOLUTION: ...
        [00:25] CTA: ...
        """
        
        try:
            completion = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a Viral Science Content Architect."},
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.7,
            )
            return f"🧬 **Science-Pop Transformation Complete**\n\n{completion.choices[0].message.content}"
        except Exception as e:
            return f"⚠️ Transformation failed: {str(e)}"

    def fetch_scientific_niche_trends(self, topic: str) -> str:
        """
        Fetch specialized scientific trends (Placeholder for metadata search).
        """
        return f"🔍 **Claw4Science Trends for {topic}:**\n- Energy Density in SSBs (Trending)\n- Decentralized Bio-Compute (Emerging)"

claw4science_skill = Claw4ScienceSkill()
