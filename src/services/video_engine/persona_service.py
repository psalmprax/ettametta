import logging
import os
import httpx

logger = logging.getLogger("PersonaService")


class PersonaService:
    def __init__(self):
        self.render_node_url = os.getenv("RENDER_NODE_URL")

    async def _generate_tts(self, text: str) -> str | None:
        """
        Generate TTS audio for persona animation.
        Tries voiceover service, then remote render node TTS.
        """
        # Try local voiceover service
        try:
            from services.voiceover.service import voiceover_service

            audio_path = await voiceover_service.generate_voiceover(text)
            if audio_path:
                logger.info(
                    f"[PersonaService] TTS generated via voiceover service: {audio_path}"
                )
                return audio_path
        except (ImportError, Exception) as e:
            logger.debug(f"[PersonaService] Local voiceover service unavailable: {e}")

        # Try remote voiceover microservice
        voiceover_url = os.getenv("VOICEOVER_URL", "http://voiceover:8080")
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{voiceover_url}/generate", json={"text": text}
                )
            if response.status_code == 200:
                data = response.json()
                audio_url = data.get("audio_url") or data.get("path")
                if audio_url:
                    logger.info(
                        f"[PersonaService] TTS generated via voiceover microservice"
                    )
                    return audio_url
        except Exception as e:
            logger.debug(f"[PersonaService] Voiceover microservice unavailable: {e}")

        return None

    async def animate_persona(
        self, reference_image_url: str, topic: str, script: str | None = None
    ) -> str:
        """
        Orchestrates the creation of a personalized deepfake video.
        1. Generates TTS audio via voiceover service.
        2. Sends image + audio to the Render Node for LivePortrait/SadTalker animation.
        """
        logger.info(f"Animating Persona. Image: {reference_image_url} | Topic: {topic}")

        if not self.render_node_url:
            logger.error("RENDER_NODE_URL missing. Cannot animate persona.")
            raise ValueError(
                "Render node URL not configured. Please set RENDER_NODE_URL in environment."
            )

        script_text = script or f"Hey everyone, let's talk about {topic}."

        # Step 1: Generate TTS audio
        audio_path = await self._generate_tts(script_text)

        try:
            payload = {
                "image_url": reference_image_url,
                "text": script_text,
                "voice_id": "default_xtts",
            }

            # If we have audio, send it to the render node
            if audio_path:
                payload["audio_url"] = audio_path

            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(
                    f"{self.render_node_url}/animate-persona", json=payload
                )

            if response.status_code == 200:
                data = response.json()
                return f"{self.render_node_url}/download/{data.get('job_id')}"
            else:
                logger.error(f"Render node failed: {response.text}")
                raise RuntimeError(
                    f"Render node returned error: {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Error connecting to render node for persona: {e}")
            raise RuntimeError(f"Failed to connect to render node: {e}")


base_persona_service = PersonaService()
