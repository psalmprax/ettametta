import os
import httpx
import logging
from typing import Optional
from api.config import settings

class VoiceoverService:
    def __init__(self):
        self.elevenlabs_key = settings.ELEVENLABS_API_KEY
        self.fish_endpoint = settings.FISH_SPEECH_ENDPOINT
        self.engine = settings.VOICE_ENGINE
        self.elevenlabs_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = "21m00Tcm4TlvDq8ikWAM" # Rachel

    async def generate_voiceover(self, text: str, voice_id: Optional[str] = None) -> Optional[str]:
        """
        Synthesizes text to speech using the selected engine.
        """
        os.makedirs("outputs/audio", exist_ok=True)
        file_name = f"voiceover_{hash(text) % 1000000}.mp3"
        file_path = os.path.join("outputs/audio", file_name)

        # 1. Check Fish Speech (Local Infrastructure)
        if self.engine == "fish_speech" or not self.elevenlabs_key:
            try:
                logging.info(f"[VoiceoverService] Using Fish Speech via {self.fish_endpoint}")
                async with httpx.AsyncClient() as client:
                    payload = {"text": text, "voice": voice_id or "default"}
                    response = await client.post(f"{self.fish_endpoint}/generate", json=payload, timeout=60.0)
                    if response.status_code == 200:
                        # Assuming the service returns the audio bytes or we need to fetch the audio_url
                        data = response.json()
                        if "audio_url" in data:
                            # If it returns a URL, we might need to download it or it might be served via volumes
                            # For simplicity in this iteration, let's assume it returns bytes or we fetch it
                            audio_resp = await client.get(f"{self.fish_endpoint}{data['audio_url']}")
                            if audio_resp.status_code == 200:
                                with open(file_path, "wb") as f:
                                    f.write(audio_resp.content)
                                return f"audio/{file_name}"
            except Exception as e:
                logging.error(f"[VoiceoverService] Fish Speech failed: {e}")

        # 2. ElevenLabs (Cloud API)
        if self.elevenlabs_key:
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
                    response = await client.post(url, json=data, timeout=30.0)
                    if response.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(response.content)
                        return f"audio/{file_name}"
            except Exception as e:
                logging.error(f"[VoiceoverService] ElevenLabs failed: {e}")

        # 3. Fallback to gTTS (Free)
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang='en')
            tts.save(file_path)
            return f"audio/{file_name}"
        except Exception as e:
            logging.error(f"[VoiceoverService] gTTS Fallback Failed: {e}")
            return None

base_voiceover_service = VoiceoverService()
