import logging
import os
import httpx
from typing import Optional

logger = logging.getLogger("PersonaService")

class PersonaService:
    def __init__(self):
        self.render_node_url = os.getenv("RENDER_NODE_URL")

    async def animate_persona(self, reference_image_url: str, topic: str, script: Optional[str] = None) -> str:
        """
        Orchestrates the creation of a personalized deepfake video.
        1. Generates script/audio (mocked here for MVP).
        2. Sends image + audio to the Render Node for LivePortrait/SadTalker animation.
        """
        logger.info(f"Animating Persona. Image: {reference_image_url} | Topic: {topic}")
        
        if not self.render_node_url:
            logger.warning("RENDER_NODE_URL missing. Using fallback mock persona.")
            return "https://storage.googleapis.com/viral-forge-assets/mocks/persona_fallback.mp4"
            
        try:
            # We would typically call XTTS or ElevenLabs here to generate the speech first.
            # For this MVP, we pass the text down to the node which may have its own TTS integration.
            payload = {
                "image_url": reference_image_url,
                "text": script or f"Hey everyone, let's talk about {topic}.",
                "voice_id": "default_xtts" 
            }
            
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(f"{self.render_node_url}/animate-persona", json=payload)
                
            if response.status_code == 200:
                data = response.json()
                return f"{self.render_node_url}/download/{data.get('job_id')}"
            else:
                logger.error(f"Render node failed: {response.text}")
                return "https://storage.googleapis.com/viral-forge-assets/mocks/persona_fallback_error.mp4"
                
        except Exception as e:
            logger.error(f"Error connecting to render node for persona: {e}")
            return "https://storage.googleapis.com/viral-forge-assets/mocks/persona_fallback.mp4"

persona_service = PersonaService()
