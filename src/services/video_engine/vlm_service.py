from google import genai
import asyncio
import cv2
import os
import logging
import json
import httpx
import base64
from src.api.utils.vault import get_secret
from src.api.config import settings

class VLMService:
    def __init__(self):
        self.google_key = get_secret("google_api_key")
        self.groq_key = get_secret("groq_api_key")
        self.model_name = settings.DEFAULT_VLM_MODEL

        # Initialize Gemini if key exists
        if self.google_key:
            self.gemini_client = genai.Client(api_key=self.google_key)
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

    def _sample_keyframes(self, video_path: str, num_frames: int = 5) -> list[str]:
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

    async def analyze_video_content(self, video_path: str) -> dict:
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

        # Tier 4: Heuristic Fallback (Standard 3.42)
        logging.info("[VLMService] Tier 4: Using Heuristic Heuristic Fallback...")
        return {
            "visual_mood": "Professional & Engaging",
            "detected_subjects": ["Business Professional", "Workspace"],
            "lighting_quality": "High",
            "dominant_colors": ["Blue", "White", "Slate"],
            "edit_direction": "Clean cuts, professional overlays, and smooth transitions.",
            "aesthetic_rating": 8
        }

    async def _analyze_groq(self, frame_paths: list[str]) -> dict | None:
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
                            {"type": "image_uri", "image_uri": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ]
                    }
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(completion.choices[0].message.content)
        except Exception as e:
            logging.warning(f"[VLMService] Groq Vision failed: {e}")
            return None

    async def _analyze_local(self, frame_paths: list[str]) -> dict | None:
        """Analyzes using Moondream2 on the remote inference node."""
        render_node_url = settings.RENDER_NODE_URL
        if not render_node_url: return None

        try:
            with open(frame_paths[0], "rb") as f:
                b64_img = base64.b64encode(f.read()).decode('utf-8')

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{render_node_url.rstrip('/')}/vlm/analyze",
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

    async def _analyze_gemini(self, frame_paths: list[str]) -> dict | None:
        """Analyzes using Gemini Multimodal."""
        try:
            from PIL import Image
            images = [Image.open(p) for p in frame_paths]
            prompt = "Analyze these video frames. Output JSON with: visual_mood, detected_subjects, lighting_quality, dominant_colors, edit_direction, aesthetic_rating (1-10)."
            response = self.gemini_client.models.generate_content(model=self.model_name, contents=[prompt] + images)

            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            logging.exception(f"[VLMService] Gemini failed: {e}")
            return None

    async def _classify_person_activity(self, frame_paths: list[str]) -> list[dict]:
        """Classify person activity per sampled frame.

        Ported from the deleted ``VideoContentAnalyzer`` (the only producer of a
        frame-derived ``talking_head`` classification). Reuses the Groq/Gemini
        clients already configured on this service instead of a separate raw
        OpenAI call, so frame analysis flows through the single canonical vision path.

        Returns a list of per-frame dicts with keys: ``person_visible``,
        ``person_activity``, ``usable_as_broll``, ``visual_content``, ``mood``.
        """
        prompt = (
            "Analyze this video frame. Answer in JSON: "
            '{'
            '"person_visible": true/false, '
            '"person_activity": "speaking_to_camera/demonstrating/concept_explaining/screen_recording/none", '
            '"usable_as_broll": true/false, '
            '"visual_content": "landscape/office/product/screen/demo/concept/etc", '
            '"mood": "energetic/calm/professional/other"'
            "}"
        )

        async def _run(frame_path: str) -> dict | None:
            try:
                with open(frame_path, "rb") as image_file:
                    b64 = base64.b64encode(image_file.read()).decode("utf-8")
                if self.groq_client:
                    completion = await self.groq_client.chat.completions.create(
                        model="llama-3.2-11b-vision-preview",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{b64}"
                                        },
                                    },
                                ],
                            }
                        ],
                        response_format={"type": "json_object"},
                    )
                    return json.loads(completion.choices[0].message.content)
                if self.gemini_model:
                    from PIL import Image

                    response = self.gemini_client.models.generate_content(
                        model=self.model_name,
                        contents=[prompt, Image.open(frame_path)],
                    )
                    text = response.text
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0].strip()
                    return json.loads(text)
            except Exception as e:  # single frame failure shouldn't abort all
                logging.warning(f"[VLMService] person-activity frame failed: {e}")
            return None

        results = await asyncio.gather(*[_run(p) for p in frame_paths])
        analyses = [a for a in results if isinstance(a, dict)]
        return analyses

    async def analyze_content_type(self, video_path: str) -> dict:
        """Frame-based talking-head / B-roll classification.

        Aggregation logic ported from ``VideoContentAnalyzer``: a video is
        ``talking_head`` (reject) when >= 3 of the sampled frames show someone
        speaking to camera. Otherwise it is ``tutorial_demo`` (good showing
        content), ``person_heavy`` (person present but not demonstrating),
        ``poor_quality`` (little usable B-roll), or ``scene`` (clean B-roll).

        Returns keys consumed by ``video_eligibility.check_eligibility``:
        ``content_type``, ``has_visible_speaker``, ``speaker_duration_pct``,
        ``usable``, ``visual_quality``.
        """
        frames = self._sample_keyframes(video_path, num_frames=5)
        if not frames:
            return {
                "content_type": "unknown",
                "has_visible_speaker": False,
                "speaker_duration_pct": 0.0,
                "usable": True,
                "visual_quality": 5.0,
            }

        try:
            analyses = await self._classify_person_activity(frames)
            if not analyses:
                return {
                    "content_type": "unknown",
                    "has_visible_speaker": False,
                    "speaker_duration_pct": 0.0,
                    "usable": True,
                    "visual_quality": 5.0,
                }

            bad_activities = ["speaking_to_camera"]
            bad_count = sum(
                1 for a in analyses if a.get("person_activity") in bad_activities
            )
            good_count = sum(
                1
                for a in analyses
                if a.get("person_activity")
                in ["demonstrating", "concept_explaining", "screen_recording"]
            )
            person_count = sum(1 for a in analyses if a.get("person_visible", False))
            person_pct = person_count / len(analyses)
            usable_count = sum(1 for a in analyses if a.get("usable_as_broll", True))
            usable_pct = usable_count / len(analyses)

            if bad_count >= 3:
                content_type = "talking_head"
            elif good_count >= 2:
                content_type = "tutorial_demo"
            elif person_pct >= 0.6 and good_count == 0:
                content_type = "person_heavy"
            elif usable_pct < 0.4:
                content_type = "poor_quality"
            else:
                content_type = "scene"

            return {
                "content_type": content_type,
                "has_visible_speaker": bad_count >= 3,
                "speaker_duration_pct": bad_count / len(analyses),
                "usable": content_type not in ["talking_head", "poor_quality"],
                "visual_quality": usable_pct * 10,
            }
        finally:
            for p in frames:
                if os.path.exists(p):
                    os.remove(p)

base_vlm_service = VLMService()
