import os
import logging
import asyncio
import httpx
from typing import Any, List, Dict
from src.api.config import settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    """
    Ettametta Transcription Service
    Uses Faster-Whisper for high-speed local transcription.
    Supports remote offloading via RENDER_NODE_URL.
    """

    def __init__(self):
        self.model_size = os.getenv("WHISPER_MODEL_SIZE", "base")
        self.device = os.getenv("WHISPER_DEVICE", "cpu")  # cpu, cuda
        self.compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        self._model = None
        
        # Remote offloading configuration
        self.remote_url = os.getenv("RENDER_NODE_URL")
        if self.remote_url:
            self.remote_url = self.remote_url.rstrip("/") + "/transcribe"

    def _get_model(self):
        """Lazy loading of the Faster-Whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"🚀 [TranscriptionService] Loading Faster-Whisper model ({self.model_size}) on {self.device}")
                self._model = WhisperModel(
                    self.model_size, 
                    device=self.device, 
                    compute_type=self.compute_type
                )
            except ImportError:
                logger.error("[TranscriptionService] faster-whisper not installed. Local transcription disabled.")
                return None
            except Exception as e:
                logger.error(f"[TranscriptionService] Failed to load model: {e}")
                return None
        return self._model

    async def transcribe(self, audio_path: str, language: str | None = None) -> Dict[str, Any]:
        """
        Transcribes an audio file. Offloads to remote if RENDER_NODE_URL is set, 
        otherwise runs locally.
        """
        if not os.path.exists(audio_path):
            logger.error(f"[TranscriptionService] Audio file not found: {audio_path}")
            return {"error": "File not found"}

        # Step 1: Attempt Remote Offload
        if self.remote_url:
            try:
                return await self._transcribe_remote(audio_path, language)
            except Exception as e:
                logger.warning(f"[TranscriptionService] Remote transcription failed, falling back to local: {e}")

        # Step 2: Local Transcription
        return await self._transcribe_local(audio_path, language)

    async def _transcribe_remote(self, audio_path: str, language: str | None = None) -> Dict[str, Any]:
        """Sends audio to a remote render node for transcription."""
        logger.info(f"🌐 [TranscriptionService] Offloading transcription to {self.remote_url}")
        
        async with httpx.AsyncClient(timeout=300) as client:
            with open(audio_path, "rb") as f:
                files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
                data = {"language": language} if language else {}
                resp = await client.post(self.remote_url, files=files, data=data)
                
                if resp.status_code == 200:
                    return resp.json()
                else:
                    raise RuntimeError(f"Remote transcription error {resp.status_code}: {resp.text}")

    async def _transcribe_local(self, audio_path: str, language: str | None = None) -> Dict[str, Any]:
        """Runs transcription locally using Faster-Whisper."""
        model = self._get_model()
        if not model:
            return {"error": "Transcription model not available"}

        logger.info(f"🎙️ [TranscriptionService] Transcribing locally: {audio_path}")
        
        # Run in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        segments, info = await loop.run_in_executor(
            None, 
            lambda: model.transcribe(
                audio_path, 
                beam_size=5, 
                language=language,
                word_timestamps=True
            )
        )

        full_text = ""
        words_data = []
        
        for segment in segments:
            full_text += segment.text + " "
            if segment.words:
                for word in segment.words:
                    words_data.append({
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": word.probability
                    })

        return {
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "words": words_data
        }

# Singleton accessor
base_transcription_service = TranscriptionService()
