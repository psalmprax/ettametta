import google.generativeai as genai
import cv2
import os
import logging
import json
import httpx
import base64
from typing import List, Dict, Optional
from api.utils.vault import get_secret
from api.config import settings

class VLMService:
    def __init__(self):
        self.google_key = get_secret("google_api_key")
        self.groq_key = get_secret("groq_api_key")
        self.model_name = settings.DEFAULT_VLM_MODEL
        
        # Initialize Gemini if key exists
        if self.google_key:
            genai.configure(api_key=self.google_key)
            self.gemini_model = genai.GenerativeModel(model_name=self.model_name)
            logging.info(f"[VLMService] Gemini Initialized: {self.model_name}")
        else:
            self.gemini_model = None

        # Initialize Groq client
        if self.groq_key:
            from groq import AsyncGroq
            self.groq_client = AsyncGroq(api_key=self.groq_key)
            logging.info("[VLMService] Groq Vision Initialized")
        else:
            self.groq_client = None

    def _sample_keyframes(self, video_path: str, num_frames: int = 5) -> List[str]:
        """Samples keyframes and returns paths."""
        temp_dir = "temp_frames"
        os.makedirs(temp_dir, exist_ok=True)
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return []

        interval = total_frames // num_frames
        frame_paths = []
        for i in range(num_frames):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i * interval)
            ret, frame = cap.read()
            if ret:
                path = os.path.join(temp_dir, f"frame_{i}.jpg")
                cv2.imwrite(path, frame)
                frame_paths.append(path)
        cap.release()
        return frame_paths

    async def analyze_video_content(self, video_path: str) -> Dict:
        """Orchestrates VLM analysis: Groq -> Local -> Gemini."""
        frame_paths = self._sample_keyframes(video_path)
        if not frame_paths: return {}

        # Tier 1: Groq Vision (Llama 3.2 11B/90B) - FREE/LOW COST
        if self.groq_client:
            logging.info("[VLMService] Tier 1: Attempting Groq Vision...")
            analysis = await self._analyze_groq(frame_paths)
            if analysis: return analysis

        # Tier 2: Local VLM (Moondream2) - ZERO COST (Private GPU)
        logging.info("[VLMService] Tier 2: Attempting Local Moondream...")
        local_analysis = await self._analyze_local(frame_paths)
        if local_analysis: return local_analysis

        # Tier 3: Gemini 1.5 Flash - PAID FALLBACK
        if self.gemini_model:
            logging.info("[VLMService] Tier 3: Falling back to Gemini...")
            analysis = await self._analyze_gemini(frame_paths)
            if analysis: return analysis

        # Cleanup
        for p in frame_paths:
            if os.path.exists(p): os.remove(p)
            
        return {}

    async def _analyze_groq(self, frame_paths: List[str]) -> Optional[Dict]:
        """Analyzes using Groq Vision."""
        try:
            # Groq Vision usually handles 1 image well, for multiple we sample the best one
            # for cost and prompt limits.
            with open(frame_paths[0], "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            completion = await self.groq_client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this video frame. Output JSON with: visual_mood, detected_subjects, lighting_quality, dominant_colors, aesthetic_rating (1-10)."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            logging.warning(f"[VLMService] Groq Vision failed: {e}")
            return None

    async def _analyze_local(self, frame_paths: List[str]) -> Optional[Dict]:
        """Analyzes using Moondream2 on the remote inference node."""
        render_node_url = os.getenv("RENDER_NODE_URL")
        if not render_node_url: return None

        try:
            with open(frame_paths[0], "rb") as f:
                b64_img = base64.b64encode(f.read()).decode('utf-8')
            
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{render_node_url}/vlm/analyze",
                    json={"image_base64": b64_img}
                )
                if resp.status_code == 200:
                    analysis_text = resp.json().get("analysis", "")
                    # Local VLM is usually descriptive, we wrap it in the expected format
                    return {
                        "visual_mood": "Determined from local analysis",
                        "edit_direction": analysis_text,
                        "local_vlm_output": analysis_text
                    }
        except Exception as e:
            logging.warning(f"[VLMService] Local VLM failed: {e}")
        return None

    async def _analyze_gemini(self, frame_paths: List[str]) -> Optional[Dict]:
        """Analyzes using Gemini Multimodal."""
        try:
            from PIL import Image
            images = [Image.open(p) for p in frame_paths]
            prompt = "Analyze these video frames. Output JSON with: visual_mood, detected_subjects, lighting_quality, dominant_colors, edit_direction, aesthetic_rating (1-10)."
            response = self.gemini_model.generate_content([prompt] + images)
            
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            logging.error(f"[VLMService] Gemini failed: {e}")
            return None

vlm_service = VLMService()
