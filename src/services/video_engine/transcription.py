import os
import asyncio
from src.api.utils.os_worker import ai_worker
from .ffmpeg_utils import base_ffmpeg_service


class TranscriptionService:
    def __init__(self, temp_dir: str = "temp/audio"):
        self.use_os = os.getenv("USE_OS_MODELS", "true") == "true"
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    async def transcribe_video(self, video_path: str) -> list[dict]:
        """
        Transcribes video audio using local Fast-Whisper with explicit audio extraction.
        Returns empty list if transcription fails.
        """
        import uuid

        audio_path = os.path.join(self.temp_dir, f"transcribe_{uuid.uuid4().hex}.mp3")
        try:
            # 1. Explicit Audio Extraction (Hardening)
            success = await asyncio.to_thread(
                base_ffmpeg_service.extract_audio, video_path, audio_path
            )
            if not success:
                print(f"[OS-Transcription] Audio extraction failed for {video_path}")
                return []

            # 2. Transcribe the extracted audio
            result = await ai_worker.transcribe(audio_path)

            # 3. Cleanup
            if os.path.exists(audio_path):
                os.remove(audio_path)

            return result
        except Exception as e:
            print(f"[OS-Transcription] ERROR: {e}. No transcript available.")
            if os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
            return []


base_transcription_service = TranscriptionService()
