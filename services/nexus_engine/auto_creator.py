import json
import logging
import uuid
import os
from typing import List, Dict, Any
from groq import AsyncGroq
from api.config import settings
from services.nexus_engine.orchestrator import base_nexus_orchestrator

class AutoCreator:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = "llama-3.3-70b-versatile"

    async def generate_viral_script(self, topic: str, niche: str) -> List[Dict]:
        """
        Generates a segmented high-retention script for Auto-Creation.
        """
        prompt = f"""
        Generate a 60-second viral video script for a {niche} video about "{topic}".
        Segment the script into 5-7 parts, each with:
        1. 'text': The narration text.
        2. 'visual_prompt': A description for what should be on screen.
        3. 'mood': The emotional vibe of this segment.
        
        OUTPUT FORMAT (JSON ONLY):
        [
            {{ "text": "...", "visual_prompt": "...", "mood": "..." }},
            ...
        ]
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional scriptwriter. Output JSON array."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} # Some Llama models might need specific instructions for arrays but usually json_object works if wrapped.
            )
            # Handle potential wrapping in a key if needed, or just list
            content = json.loads(response.choices[0].message.content)
            if isinstance(content, dict) and "segments" in content:
                return content["segments"]
            return content if isinstance(content, list) else []
        except Exception as e:
            logging.error(f"[AutoCreator] Script Error: {e}")
            return [{"text": f"Discussing {topic} in the {niche} niche.", "visual_prompt": "Generic cinematic shot", "mood": "Neutral"}]

    async def create_cinema_video(self, job_id: int, topic: str, niche: str) -> str:
        """
        Autonomous Script-to-Video Workflow.
        """
        logging.info(f"[AutoCreator] Launching Cinema Mode for Topic: {topic}")
        
        # 1. Generate Script
        segments = await self.generate_viral_script(topic, niche)
        
        # 2. Source Assets (Autonomous)
        # In a real system, we'd call Stock Media APIs or AI Image Generators here.
        # For this version, we'll use high-quality placeholders or existing stock libraries.
        visual_paths = []
        for seg in segments:
            # Placeholder: In a real deploy, this would call stock_media_service.search(seg['visual_prompt'])
            visual_paths.append("temp/stock/placeholder_visual.mp4") 
            
        # 3. Generate Voiceover (Autonomous)
        # Using placeholder paths for now (Real integration would call voiceover_service)
        voice_paths = [f"temp/voice/segment_{i}.mp3" for i in range(len(segments))]
        
        # 4. Final Assembly via Nexus
        # We'll need to mock the existence of these assets for the orchestrator test
        output_path = await base_nexus_orchestrator.assemble_video(
            job_id=job_id,
            niche=niche,
            script_segments=segments,
            voiceover_paths=voice_paths,
            visual_paths=visual_paths,
            music_path=None # Auto-select music later
        )
        
        return output_path

base_auto_creator = AutoCreator()
