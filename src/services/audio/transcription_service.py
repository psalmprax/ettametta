import os
import logging
import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Any, Dict
from src.api.config import settings

logger = logging.getLogger(__name__)

class TranscriptionService:
    """
    Ettametta Transcription Service
    Uses Faster-Whisper for high-speed local transcription.
    Supports remote offloading via RENDER_NODE_URL.
    """

    def __init__(self):
        self.model_size = settings.WHISPER_MODEL_SIZE
        self.device = settings.WHISPER_DEVICE
        self.compute_type = settings.WHISPER_COMPUTE_TYPE
        self.timeout = settings.TRANSCRIPTION_TIMEOUT
        self._model = None
        
        # Remote offloading configuration
        self.remote_url = os.getenv("RENDER_NODE_URL")
        if self.remote_url:
            self.remote_url = self.remote_url.rstrip("/") + "/transcribe"

    def _get_model(self, force_size: str | None = None):
        """Lazy loading of the Faster-Whisper model with fallback support."""
        size = force_size or self.model_size
        
        # If we already have a model and it's the right size, return it
        if self._model is not None and getattr(self, "_current_size", None) == size:
            return self._model

        try:
            from faster_whisper import WhisperModel
            logger.info(f"🚀 [TranscriptionService] Loading Faster-Whisper model ({size}) on {self.device}")
            self._model = WhisperModel(
                size, 
                device=self.device, 
                compute_type=self.compute_type
            )
            self._current_size = size
            return self._model
        except ImportError:
            logger.exception("[TranscriptionService] faster-whisper not installed. Local transcription disabled.")
            return None
        except Exception as e:
            logger.exception(f"[TranscriptionService] Failed to load model {size}: {e}")
            if size != "tiny":
                logger.warning("[TranscriptionService] Attempting fallback to 'tiny' model...")
                return self._get_model(force_size="tiny")
            return None

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

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=2, min=4, max=10),
        retry=retry_if_exception_type((asyncio.TimeoutError, RuntimeError, Exception)),
        reraise=True
    )
    async def _transcribe_local(self, audio_path: str, language: str | None = None) -> Dict[str, Any]:
        """Runs transcription locally with timeout and retry protection."""
        model = self._get_model()
        if not model:
            return {"error": "Transcription model not available"}

        logger.info(f"🎙️ [TranscriptionService] Transcribing locally: {audio_path} (Timeout: {self.timeout}s)")
        
        try:
            # Run in a thread with a hard timeout to prevent job stalls
            loop = asyncio.get_running_loop()
            
            async def _do_transcribe():
                return await loop.run_in_executor(
                    None, 
                    lambda: list(model.transcribe(
                        audio_path, 
                        beam_size=5, 
                        language=language,
                        word_timestamps=True
                    ))
                )

            # model.transcribe returns a generator (segments) and info
            # We need to exhaust the generator inside the executor or it will block here
            result = await asyncio.wait_for(_do_transcribe(), timeout=self.timeout)
            segments, info = result[0], result[1]

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
        except asyncio.TimeoutError:
            logger.exception(f"⏱️ [TranscriptionService] Transcription timed out for {audio_path}")
            raise
        except Exception as e:
            logger.exception(f"❌ [TranscriptionService] Local transcription failed: {e}")
            raise

# Singleton accessor
base_transcription_service = TranscriptionService()
