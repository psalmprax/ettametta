import logging
import os
import httpx

logger = logging.getLogger("PersonaService")


class PersonaService:
    def __init__(self):
        self.render_node_url = os.getenv("RENDER_NODE_URL")

    async def _generate_tts(self, text: str, voice_id: str | None = None) -> str | None:
        """
        Generate TTS audio for persona animation.
        Tries voiceover service, then remote render node TTS.
        """
        # Try local voiceover service
        try:
            from src.services.voiceover.service import voiceover_service

            audio_path = await voiceover_service.generate_voiceover(text, voice_id=voice_id)
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
                audio_uri = data.get("audio_uri") or data.get("path")
                if audio_uri:
                    logger.info(
                        "[PersonaService] TTS generated via voiceover microservice"
                    )
                    return audio_uri
        except Exception as e:
            logger.debug(f"[PersonaService] Voiceover microservice unavailable: {e}")

        return None

    async def animate_persona(
        self, reference_image_uri: str, niche: str, script: str | None = None, voice_id: str | None = None
    ) -> str:
        """
        Orchestrates the animation of a personalized persona video via external rendering services.
        1. Generates TTS audio via voiceover service.
        2. Sends image + audio to the Render Node for LivePortrait/SadTalker animation.
        """
        logger.info(f"Animating Persona. Image: {reference_image_uri} | Niche: {niche}")

        if not self.render_node_url:
            logger.error("RENDER_NODE_URL missing. Cannot animate persona.")
            raise ValueError(
                "Render node URL not configured. Please set RENDER_NODE_URL in environment."
            )

        script_text = script or f"Hey everyone, let's talk about {niche}."

        # Step 1: Generate TTS audio
        audio_path = await self._generate_tts(script_text, voice_id=voice_id)

        try:
            payload = {
                "image_uri": reference_image_uri,
                "text": script_text,
                "voice_id": voice_id or "default_xtts",
            }

            # If we have audio, send it to the render node
            if audio_path:
                payload["audio_uri"] = audio_path

            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(
                    f"{self.render_node_url}/animate-persona", json=payload
                )

            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                if not job_id:
                    raise RuntimeError("Render node response missing job_id")
                return f"{self.render_node_url}/download/{job_id}"
            else:
                logger.error(f"Render node failed: {response.text}")
                raise RuntimeError(
                    f"Render node returned error: {response.status_code}"
                )

        except Exception as e:
            logger.exception(f"Error connecting to render node for persona: {e}")
            raise RuntimeError(f"Failed to connect to render node: {e}")


base_persona_service = PersonaService()
