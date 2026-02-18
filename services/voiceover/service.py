import os
import httpx
import logging
from typing import Optional
from api.config import settings

class VoiceoverService:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = "21m00Tcm4TlvDq8ikWAM" # Rachel

    async def generate_voiceover(self, text: str, voice_id: Optional[str] = None) -> Optional[str]:
        """
        Synthesizes text to speech. Attempts ElevenLabs first, fallbacks to gTTS.
        """
        # Save to outputs directory
        os.makedirs("outputs/audio", exist_ok=True)
        file_name = f"voiceover_{hash(text) % 1000000}.mp3"
        file_path = os.path.join("outputs/audio", file_name)

        if self.api_key:
            voice_id = voice_id or self.default_voice_id
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            headers = {"xi-api-key": self.api_key, "Content-Type": "application/json"}
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
            }

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json=data, timeout=30.0)
                    if response.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        return f"audio/{file_name}"
                    else:
                        logging.warning(f"[VoiceoverService] ElevenLabs API Error: {response.status_code}. Falling back to gTTS.")
            except Exception as e:
                logging.error(f"[VoiceoverService] ElevenLabs Exception: {e}. Falling back to gTTS.")

        # Fallback to gTTS (Free)
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en')
            tts.save(file_path)
            return f"audio/{file_name}"
        except Exception as e:
            logging.error(f"[VoiceoverService] gTTS Fallback Failed: {e}")
            return None

base_voiceover_service = VoiceoverService()
