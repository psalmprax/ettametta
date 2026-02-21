import json
import logging
from typing import Dict, Any, List, Optional
from groq import AsyncGroq
from api.config import settings
from api.utils.vault import get_secret
from pydantic import BaseModel

class VideoStrategy(BaseModel):
    speed_range: List[float] = [0.98, 1.02]
    jitter_intensity: float = 1.0
    recommended_filters: List[str] = []
    hook_points: List[List[float]] = [] # [ [start, end], [start, end] ]
    b_roll_keywords: List[str] = []
    vibe: str = "Neutral"
    explanation: str = ""

class StoryScene(BaseModel):
    scene_id: int
    visual_prompt: str
    narration_text: str
    duration_hint: float = 5.0
    vibe: str = "Cinematic"

class StoryScript(BaseModel):
    title: str
    scenes: List[StoryScene]
    vibe_summary: str
    target_duration: float

class StrategyService:
    def __init__(self):
        self.api_key = get_secret("groq_api_key")
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"

    async def generate_screenplay(self, prompt: str, style: str = "Cinematic") -> StoryScript:
        """
        Converts a narrative idea into a structured screenplay for multi-scene synthesis.
        """
        system_prompt = f"You are an elite AI Screenwriter for ettametta. Break down narrative prompts into structured scenes. Output JSON."
        user_prompt = f"""
        NARRATIVE IDEA: {prompt}
        STYLE OVERLAY: {style}
        
        TASK:
        1. Create a title for the story.
        2. Break the story into 3-5 logical scenes.
        3. For each scene, provide:
           - A 'visual_prompt' optimized for high-end AI video models (Veo 3/Wan2.2).
           - A 'narration_text' that tells the story (keep it concise).
           - A 'duration_hint' in seconds (usually 4.0-7.0s).
           - A 'vibe' (Cinematic, Hectic, Dramatic, etc.).
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "title": "Story Title",
            "vibe_summary": "Overall aesthetic description",
            "target_duration": total_seconds,
            "scenes": [
                {{
                    "scene_id": 1,
                    "visual_prompt": "...",
                    "narration_text": "...",
                    "duration_hint": 5.0,
                    "vibe": "..."
                }},
                ...
            ]
        }}
        """

        try:
            if not self.api_key:
                # Fallback mock for testing
                return StoryScript(
                    title="Mock Story",
                    vibe_summary="Cinematic Tech",
                    target_duration=15.0,
                    scenes=[
                        StoryScene(scene_id=1, visual_prompt="A glowing AI core", narration_text="The heart of the system pulsed.", duration_hint=5.0),
                        StoryScene(scene_id=2, visual_prompt="A digital city", narration_text="Expanding across the network.", duration_hint=5.0),
                        StoryScene(scene_id=3, visual_prompt="Human hand touching light", narration_text="Connecting with the future.", duration_hint=5.0)
                    ]
                )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            return StoryScript(**data)
        except Exception as e:
            logging.error(f"[StrategyService] Screenplay Error: {e}")
            raise
        """
        Analyzes transcript content, user-selected style, and VLM visual insights to decide on video editing parameters.
        """
        full_text = " ".join([s.get("text", "") for s in transcript])
        
        # Prepare Visual Context if available
        visual_context = ""
        if visual_insights:
            visual_context = f"\nVISUAL INSIGHTS (VLM):\n{json.dumps(visual_insights, indent=2)}\n"

        prompt = f"""
        You are an elite AI Video Editor. Analyze the following video transcript, niche, user-selected STYLE, and VISUAL INSIGHTS to decide the visual strategy.
        
        NICHE: {niche}
        SELECTED STYLE: {style}
        TRANSCRIPT: "{full_text[:2000]}"
        {visual_context}
        
        DECISION CRITERIA:
        1. STYLE OVERRIDE: 
           - 'Cinematic': f7 (Overlays), f9 (Glow), Speed 0.98x.
           - 'ASMR/Calm': No Jitter, Speed 0.95x, f9 (Glow).
           - 'Glitch/High-Art': f8 (High Jitter), f12 (Glitch), Speed 1.05x.
           - 'Noir/Classic': f11 (Grayscale), f10 (Grain), Speed 1.0x.
        2. SPEED: High energy needs 1.02-1.1x speed ramping. Relaxed needs 0.95-1.0x.
        3. JITTER: Intense/Action needs 2.0-3.0 intensity. Calm needs 0.0-0.5.
        4. FILTERS: 'f6' (Speed Ramping), 'f7' (Cinematic), 'f8' (Jitter), 'f9' (Glow), 'f10' (Grain), 'f11' (Grayscale), 'f12' (Glitch).
        5. HOOKS: Identify 1-3 specific segments (start/end in seconds) that are the most viral, emotional, or high-energy parts of the transcript.
        6. B-ROLL: Provide 3-5 search keywords for stock footage.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "speed_range": [min, max],
            "jitter_intensity": float,
            "recommended_filters": ["f6", "f7", "f8"],
            "hook_points": [[start, end], ...],
            "b_roll_keywords": ["keyword1", "keyword2"],
            "vibe": "Energetic" | "Calm" | "Educational" | "Dramatic",
            "explanation": "Why this strategy?"
        }}
        """

        try:
            if not self.api_key or self.api_key == "your_key_here":
                return VideoStrategy()

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a professional social media editor. The user wants a '{style}' aesthetic. Output JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response.choices[0].message.content)
            return VideoStrategy(**data)
        except Exception as e:
            logging.error(f"[StrategyService] Error: {e}")
            return VideoStrategy()

base_strategy_service = StrategyService()
