import os
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

# Lazy loading flag
_whisper_available = None

def check_whisper_available():
    global _whisper_available
    if _whisper_available is None:
        try:
            from faster_whisper import WhisperModel  # type: ignore
            _whisper_available = True
        except ImportError:
            _whisper_available = False
            logger.warning("[OS-Worker] faster-whisper not installed. Transcription disabled.")
    return _whisper_available

class AIWorker:
    def __init__(self):
        # Groq API Configuration
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        # Local Whisper Configuration
        self.whisper_model_size = "base"
        self.whisper_model = None 

    def get_dependency_report(self):
        """Returns health of local AI drivers."""
        available = check_whisper_available()
        return {
            "name": "Local AI Core",
            "drivers": [
                {
                    "name": "faster-whisper",
                    "installed": available,
                    "impact": "Local transcription will be unavailable if missing."
                }
            ],
            "healthy": available
        }

    async def transcribe(self, audio_path: str):
        """Transcribes audio using fast-whisper locally."""
        if not check_whisper_available():
            logger.error("[OS-Worker] Transcription requested but dependency is missing.")
            return []

        if not self.whisper_model:
            from faster_whisper import WhisperModel  # type: ignore
            logger.info(f"[OS-Worker] Loading Whisper ({self.whisper_model_size})...")
            try:
                # Add a timeout/safety for model loading on weak CPUs
                self.whisper_model = await asyncio.to_thread(
                    WhisperModel, self.whisper_model_size, device="cpu", compute_type="int8"
                )
            except Exception:
                logger.exception("[OS-Worker] Failed to load Whisper model")
                return []
            
        def _run_transcribe():
            segments, _ = self.whisper_model.transcribe(audio_path, beam_size=5)
            words = []
            for segment in segments:
                words.append({"text": segment.text, "start": segment.start, "end": segment.end})
            return words

        return await asyncio.to_thread(_run_transcribe)

    async def analyze_viral_pattern(self, prompt: str):
        """Analyze content using Groq's high-speed Llama-3."""
        if not self.groq_api_key:
            return "Groq Error: Missing GROQ_API_KEY"

        async with httpx.AsyncClient() as client:
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.5
            }
            try:
                headers = {"Authorization": f"Bearer {self.groq_api_key}"}
                resp = await client.post(self.groq_url, json=payload, headers=headers, timeout=20.0)
                json_data = resp.json()
                return json_data["choices"][0]["message"]["content"]
            except Exception as e:
                return f"Groq API Error: {str(e)}"

ai_worker = AIWorker()
