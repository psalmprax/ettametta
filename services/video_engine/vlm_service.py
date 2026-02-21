import google.generativeai as genai
import cv2
import os
import logging
import json
from typing import List, Dict, Optional
from api.utils.vault import get_secret
from api.config import settings

class VLMService:
    def __init__(self):
        self.api_key = get_secret("google_api_key")
        self.model_name = settings.DEFAULT_VLM_MODEL
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_name=self.model_name)
            logging.info(f"[VLMService] Initialized with model: {self.model_name}")
        else:
            self.model = None
            logging.warning("[VLMService] GOOGLE_API_KEY not found. VLM features will be disabled.")

    def _sample_keyframes(self, video_path: str, num_frames: int = 10) -> List[str]:
        """
        Samples keyframes from the video and saves them as temporary images.
        Returns a list of image paths.
        """
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
            frame_idx = i * interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_path = os.path.join(temp_dir, f"frame_{i}.jpg")
            cv2.imwrite(frame_path, frame)
            frame_paths.append(frame_path)
            
        cap.release()
        return frame_paths

    async def analyze_video_content(self, video_path: str) -> Dict:
        """
        Extracts keyframes, sends them to Gemini 1.5 Flash, and returns visual insights.
        """
        if not self.model:
            return {}

        frame_paths = self._sample_keyframes(video_path)
        if not frame_paths:
            return {}

        try:
            # Prepare the multimodal prompt
            prompt = """
            You are an expert film director and visual analyst. 
            I am providing you with 10 keyframes from a short video. 
            Analyze these frames and provide high-level visual intuition for editing.
            
            OUTPUT THE FOLLOWING AS JSON ONLY:
            {
                "visual_mood": "e.g., 'Dark/Gritty', 'Bright/Commercial', 'Natural/Vlog'",
                "detected_subjects": ["list", "of", "main", "subjects"],
                "lighting_quality": "e.g., 'Low Light', 'Overexposed', 'Cinematic Shadows'",
                "dominant_colors": ["color1", "color2"],
                "edit_direction": "e.g., 'Fast cuts with high energy', 'Slow atmospheric fades'",
                "aesthetic_rating": 1-10,
                "suggested_b_roll_visuals": ["keyword1", "keyword2"]
            }
            """
            
            # Upload frames to Gemini (or pass as parts depending on SDK version/preference)
            # For simplicity with the SDK, we'll convert to PIL or pass bytes
            from PIL import Image
            images = [Image.open(p) for p in frame_paths]
            
            response = self.model.generate_content([prompt] + images)
            
            # Clean up temp frames
            for p in frame_paths:
                if os.path.exists(p):
                    os.remove(p)

            # Extract JSON from response
            text = response.text
            # Basic cleanup if model adds markdown blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            return json.loads(text)
        except Exception as e:
            logging.error(f"[VLMService] Analysis Error: {e}")
            return {}

vlm_service = VLMService()
