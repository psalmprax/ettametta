import os
import httpx
from faster_whisper import WhisperModel
import asyncio

class AIWorker:
    def __init__(self):
        # Groq API Configuration
        self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        # Local Whisper Configuration
        self.whisper_model_size = "base"
        self.whisper_model = None 

    async def transcribe(self, audio_path: str):
        """Transcribes audio using fast-whisper locally."""
        if not self.whisper_model:
            print(f"[OS-Worker] Loading Whisper ({self.whisper_model_size})...")
            self.whisper_model = WhisperModel(self.whisper_model_size, device="cpu", compute_type="int8")
            
        segments, info = self.whisper_model.transcribe(audio_path, beam_size=5)
        
        words = []
        for segment in segments:
            words.append({"text": segment.text, "start": segment.start, "end": segment.end})
        return words

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
