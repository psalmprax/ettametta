import os
import httpx
import logging
import importlib
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.api.utils.vault import get_secret
from src.api.config import settings
from src.api.utils.resilience import CircuitBreaker

logger = logging.getLogger(__name__)

def check_module_available(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

class VoiceoverService:
    @property
    def elevenlabs_key(self):
        return get_secret("elevenlabs_api_key") or settings.ELEVENLABS_API_KEY

    @property
    def fish_endpoint(self):
        # Failover: Check for RENDER_NODE_URL first to support Remote GPU Inference
        remote_url = os.getenv("RENDER_NODE_URL")
        if remote_url:
             return remote_url
        return get_secret("fish_speech_endpoint", settings.FISH_SPEECH_ENDPOINT)

    @property
    def engine(self):
        return get_secret("voice_engine", settings.VOICE_ENGINE)

    def __init__(self):
        self.elevenlabs_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = "21m00Tcm4TlvDq8ikWAM" # Rachel
        self.breakers = {
            "fish": CircuitBreaker(name="FishSpeech"),
            "elevenlabs": CircuitBreaker(name="ElevenLabs")
        }

    @retry(
        stop=stop_after_attempt(settings.DEFAULT_RETRY_COUNT),
        wait=wait_exponential(
            multiplier=settings.RETRY_MULTIPLIER, 
            min=settings.RETRY_MIN_WAIT, 
            max=settings.RETRY_MAX_WAIT
        ),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def generate_voiceover(self, text: str, voice_id: str | None = None) -> str | None:
        """
        Synthesizes text to speech using the selected engine with circuit breakers and retries.
        """
        os.makedirs("outputs/audio", exist_ok=True)
        file_name = f"voiceover_{hash(text) % 1000000}.mp3"
        file_path = os.path.join("outputs/audio", file_name)

        # 1. Check Fish Speech (Local Infrastructure)
        if (self.engine == "fish_speech" or not self.elevenlabs_key) and not self.breakers["fish"].is_open():
            try:
                logger.info(f"[VoiceoverService] Attempting Fish Speech...")
                async with httpx.AsyncClient() as client:
                    payload = {"text": text, "voice": voice_id or "default"}
                    logger.info(f"[VoiceoverService] POST {self.fish_endpoint}/generate")
                    response = await client.post(
                        f"{self.fish_endpoint}/generate", 
                        json=payload, 
                        timeout=settings.VOICEOVER_TIMEOUT
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    uri = data.get("audio_uri")
                    if uri:
                        full_uri = uri if uri.startswith("http") else f"{self.fish_endpoint}{uri}"
                        logger.info(f"[VoiceoverService] GET audio from: {full_uri}")
                        audio_resp = await client.get(full_uri, timeout=settings.VOICEOVER_TIMEOUT * 2)
                        audio_resp.raise_for_status()
                        
                        with open(file_path, "wb") as f:
                            f.write(audio_resp.content)
                        
                        self.breakers["fish"].record_success()
                        logger.info(f"[VoiceoverService] Fish Speech Success: {file_path}")
                        return f"outputs/audio/{file_name}"
            except Exception as e:
                logger.error(f"[VoiceoverService] Fish Speech failure: {e}")
                self.breakers["fish"].record_failure()
                # If Fish fails, we continue to ElevenLabs or gTTS

        # 2. ElevenLabs (Cloud API)
        if self.elevenlabs_key and not self.breakers["elevenlabs"].is_open():
            logger.info(f"[VoiceoverService] Attempting ElevenLabs...")
            voice_id = voice_id or self.default_voice_id
            url = f"{self.elevenlabs_url}/text-to-speech/{voice_id}"
            headers = {"xi-api-key": self.elevenlabs_key, "Content-Type": "application/json"}
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=data, timeout=settings.VOICEOVER_TIMEOUT)
                    response.raise_for_status()
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    
                    self.breakers["elevenlabs"].record_success()
                    logger.info(f"[VoiceoverService] ElevenLabs Success: {file_path}")
                    return f"outputs/audio/{file_name}"
            except Exception as e:
                logger.error(f"[VoiceoverService] ElevenLabs failure: {e}")
                self.breakers["elevenlabs"].record_failure()

        # 3. Fallback to gTTS (Free)
        logger.info(f"[VoiceoverService] Attempting gTTS Fallback...")
        if check_module_available("gtts"):
            try:
                from gtts import gTTS
                tts = gTTS(text=text, lang='en')
                tts.save(file_path)
                logger.info(f"[VoiceoverService] gTTS Success: {file_path}")
                return f"outputs/audio/{file_name}"
            except Exception as e:
                logger.error(f"[VoiceoverService] gTTS Fallback Failed: {e}")
        else:
            logger.warning("[VoiceoverService] gTTS not available, skipping fallback")
        
        return None

base_voiceover_service = VoiceoverService()
