import os
from typing import List
from api.utils.os_worker import ai_worker

class TranscriptionService:
    def __init__(self):
        self.use_os = os.getenv("USE_OS_MODELS", "true") == "true"

    async def transcribe_video(self, video_path: str) -> List[dict]:
        """
        Transcribes video audio using local Fast-Whisper.
        """
        try:
            # We'd typically extract audio from video_path here
            # But Fast-Whisper (via ffmpeg) can often handle it.
            return await ai_worker.transcribe(video_path)
        except Exception as e:
            print(f"[OS-Transcription] ERROR: {e}")
            return []

transcription_service = TranscriptionService()
