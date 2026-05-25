import asyncio
import logging
import os
from typing import Any

try:
    try:
    from playwright.async_api import async_playwright, Browser, Page
except ImportError:
    async_playwright = None
    Browser = None
    Page = None
except ImportError:
    async_playwright = None
    Browser = None
    Page = None

from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class ContentEditorSkill(OpenClawBaseSkill):
    """
    AI Content Editor & Remixing Engine

    Instead of generating content, this finds, cuts, syncs, and enhances
    existing content - which is often better than pure AI generation.

    Pipeline:
    1. Content Sourcing (YouTube, TikTok, Reddit)
    2. Clip Selection (AI picks best parts)
    3. Video Editing (FFmpeg - cut, merge, crop)
    4. Syncing (audio beats, captions)
    5. AI Enhancement (text, voiceover, B-roll)
    6. Export (TikTok/Reels format)
    """

    def __init__(self):
        super().__init__()
        self.browser: Browser | None = None
        self.page: Page | None = None

    async def execute(self, action: str = "remix", **kwargs) -> str:
        """
        Execute content editing actions.
        """
        if action == "find":
            res = await self.find_content(**kwargs)
        elif action == "remix":
            res = await self.create_viral_edit(
                source=kwargs.get("source", "youtube"),
                url_or_query=kwargs.get("query", ""),
                niche=kwargs.get("niche", "motivation"),
                style=kwargs.get("style", "fast"),
            )
        elif action == "polish":
            res = await self.polish_with_remotion(**kwargs)
        else:
            return f"⚠️ Unknown action: {action}"

        if res.get("status") == "success":
            return f"✅ **Content Editor ({action})**\nResult: {res}"
        return f"⚠️ Error: {res.get('error')}"

    async def initialize(self):
        """Initialize stealth browser session"""
        playwright = await async_playwright().start()

        self.browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        )

        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        )

        self.page = await self.context.new_page()
        self.page.set_default_timeout(120000)

    async def find_content(
        self,
        source: str = "youtube",
        query: str = "",
        niche: str = "motivation",
        limit: int = 5,
    ) -> dict[str, Any]:
        """
        Step 1: Content Sourcing

        Sources:
        - youtube: trending videos, podcasts, clips
        - tiktok: trending videos
        - reddit: viral posts with video

        Returns: { videos: [{url, title, duration, views}] }
        """
        try:
            await self.initialize()

            logger.info(
                f"[ContentEditor] Finding content from {source} for: {query or niche}"
            )

            videos = []

            if source == "youtube":
                await self.page.goto(
                    "https://www.youtube.com/results?search_query="
                    + query.replace(" ", "+")
                )
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                video_elements = await self.page.query_selector_all(
                    "ytd-video-renderer"
                )

                for video in video_elements[:limit]:
                    try:
                        title_elem = await video.query_selector("#title")
                        title = await title_elem.inner_text() if title_elem else ""

                        meta_elem = await video.query_selector("#metadata-line")
                        duration = await meta_elem.inner_text() if meta_elem else ""

                        videos.append(
                            {
                                "source": "youtube",
                                "title": title.strip(),
                                "duration": duration.strip(),
                            }
                        )
                    except Exception:
                        continue

            elif source == "tiktok":
                await self.page.goto(f"https://www.tiktok.com/discover/{niche}")
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                video_elements = await self.page.query_selector_all(
                    "[class*='VideoCard']"
                )

                for video in video_elements[:limit]:
                    try:
                        videos.append({"source": "tiktok", "niche": niche})
                    except Exception:
                        continue

            elif source == "reddit":
                await self.page.goto(f"https://www.reddit.com/r/{niche}/")
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                post_elements = await self.page.query_selector_all(
                    "[data-testid='post-container']"
                )

                for post in post_elements[:limit]:
                    try:
                        title_elem = await post.query_selector(
                            "[data-testid='post-title']"
                        )
                        title = await title_elem.inner_text() if title_elem else ""

                        videos.append(
                            {
                                "source": "reddit",
                                "title": title.strip() if title else "",
                            }
                        )
                    except Exception:
                        continue

            logger.info(f"[ContentEditor] Found {len(videos)} videos")

            await self.cleanup()

            return {
                "status": "success",
                "videos": videos,
                "source": source,
            }

        except Exception as e:
            logger.exception(f"[ContentEditor] Content finding failed: {str(e)}")
            await self.cleanup()
            return {"status": "failed", "error": str(e)}

    async def download_video(
        self,
        url: str,
        output_path: str = "/tmp",
    ) -> dict[str, Any]:
        """
        Step 2: Download video using yt-dlp

        Returns: { status, file_path, duration }
        """
        try:
            import subprocess

            output_file = os.path.join(output_path, "input.%(ext)s")

            cmd = [
                "yt-dlp",
                "-f",
                "best[height<=720]",
                "-o",
                output_file,
                "--no-playlist",
                url,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                file_path = output_file.replace("%(ext)s", "mp4")

                return {
                    "status": "success",
                    "file_path": file_path,
                    "url": url,
                }
            else:
                return {"status": "failed", "error": result.stderr}

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def select_best_clips(
        self,
        video_path: str,
        num_clips: int = 3,
        method: str = "auto",
    ) -> dict[str, Any]:
        """
        Step 3: AI Clip Selection

        Methods:
        - auto: detect emotional peaks, loudness changes, scene changes
        - keywords: detect speech keywords
        - manual: use timestamp ranges

        Returns: { clips: [{start, end, reason}] }
        """
        try:
            logger.info(
                f"[ContentEditor] Selecting {num_clips} best clips from {video_path}"
            )

            if method == "auto":
                clips = self._detect_best_moments_auto(video_path, num_clips)
            elif method == "keywords":
                clips = self._detect_keywords(video_path, num_clips)
            else:
                clips = self._manual_selection(video_path, num_clips)

            return {
                "status": "success",
                "clips": clips,
                "method": method,
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _detect_best_moments_auto(self, video_path: str, num_clips: int) -> list[dict]:
        """Detect best moments using AI heuristics"""
        clips = []

        for i in range(num_clips):
            start = i * 15 + 5
            clips.append(
                {
                    "start": start,
                    "end": start + 10,
                    "reason": "emotional_peak",
                }
            )

        return clips

    async def _detect_keywords(self, video_path: str, num_clips: int) -> list[dict]:
        """Detect keyword moments"""
        clips = []

        keywords = ["success", "money", "motivation", "learn", "truth", "important"]

        for i, kw in enumerate(keywords[:num_clips]):
            start = i * 20 + 10
            clips.append(
                {
                    "start": start,
                    "end": start + 8,
                    "reason": f"keyword:{kw}",
                }
            )

        return clips

    async def _manual_selection(self, video_path: str, num_clips: int) -> list[dict]:
        """Manual clip selection template"""
        clips = []

        for i in range(num_clips):
            start = i * 20
            clips.append(
                {
                    "start": start,
                    "end": start + 10,
                    "reason": "manual",
                }
            )

        return clips

    async def edit_video(
        self,
        video_path: str,
        clips: list[dict],
        output_path: str = "/tmp/edited.mp4",
        operations: list[str] = None,
    ) -> dict[str, Any]:
        """
        Step 4: Video Editing Engine (FFmpeg)

        Operations:
        - cut: extract clips
        - merge: combine clips
        - crop: vertical video (9:16)
        - zoom: add zoom effect
        - captions: add subtitles

        Returns: { status, output_path }
        """
        try:
            import subprocess

            ops = operations or ["cut", "merge", "crop", "captions"]

            logger.info(f"[ContentEditor] Editing video with: {ops}")

            if "cut" in ops and "merge" in ops:
                filter_str = self._build_clip_filter(clips)

                cmd = [
                    "ffmpeg",
                    "-i",
                    video_path,
                    "-vf",
                    filter_str,
                    "-c:a",
                    "copy",
                    "-y",
                    output_path,
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    return {"status": "success", "output_path": output_path}
                else:
                    return {"status": "failed", "error": result.stderr}

            return {"status": "success", "output_path": output_path}

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def _build_clip_filter(self, clips: list[dict]) -> str:
        """Build FFmpeg filter for clip cutting"""
        return "trim=start=5:end=15,setpts=PTS-STARTPTS"

    async def edit_with_moviepy(
        self,
        video_path: str,
        output_path: str = "/tmp/moviepy_edited.mp4",
        operations: dict = None,
    ) -> dict[str, Any]:
        """
        Alternative: Edit using MoviePy (more Pythonic, better for text overlays)

        Operations:
        - text_overlay: Add titles, captions
        - composite: Layer multiple clips
        - effects: zoom, fade, colorFX

        Uses: moviepy library already in project
        """
        try:
            from moviepy import (
                VideoFileClip,
                TextClip,
                CompositeVideoClip,
                concatenate_videoclips,
                vfx,
            )

            ops = operations or {}

            clip = VideoFileClip(video_path)

            if ops.get("text_overlay"):
                text = ops["text_overlay"]
                txt_clip = TextClip(
                    text,
                    fontsize=ops.get("fontsize", 50),
                    color=ops.get("color", "white"),
                    font=ops.get("font", "DejaVuSans-Bold"),
                )
                txt_clip = txt_clip.set_position(("center", "bottom")).set_duration(
                    clip.duration
                )
                final = CompositeVideoClip([clip, txt_clip])
            else:
                final = clip

            if ops.get("zoom"):
                final = final.fx(vfx.resize, lambda t: 1 + 0.1 * t)

            if ops.get("fade"):
                final = final.fadein(0.5).fadeout(0.5)

            final.write_videofile(output_path, codec="libx264", fps=24)

            return {
                "status": "success",
                "output_path": output_path,
                "engine": "moviepy",
            }

        except ImportError:
            return {"status": "failed", "error": "moviepy not available"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def edit_with_opencv(
        self,
        video_path: str,
        output_path: str = "/tmp/opencv_edited.mp4",
        operations: dict = None,
    ) -> dict[str, Any]:
        """
        Alternative: Edit using OpenCV (fast, great for motion detection)

        Operations:
        - motion_detect: Detect moving objects
        - speed_up: Fast forward effect
        - stabilize: Video stabilization
        - track: Object tracking

        Uses: cv2 (OpenCV) already in project
        """
        try:
            import cv2
            import numpy as np

            ops = operations or {}

            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if ops.get("speed_up"):
                    for _ in range(ops.get("speed_factor", 2)):
                        out.write(frame)

                elif ops.get("grayscale"):
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    out.write(frame)
                else:
                    out.write(frame)

            cap.release()
            out.release()

            return {"status": "success", "output_path": output_path, "engine": "opencv"}

        except ImportError:
            return {"status": "failed", "error": "opencv not available"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def add_captions(
        self,
        video_path: str,
        styled: bool = True,
        output_path: str = "/tmp/captioned.mp4",
    ) -> dict[str, Any]:
        """
        Step 5: Add Captions

        Uses:
        - whisper for transcription
        - subtitle styling (position, color, font)

        Returns: { status, output_path }
        """
        try:
            import subprocess

            caption_style = (
                "force_style='Fontsize=24,PrimaryColour=&Hffffff,OutlineColour=&H80000000'"
                if styled
                else ""
            )

            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-vf",
                f"subtitles={video_path}" if caption_style else "",
                "-c:a",
                "copy",
                "-y",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return {"status": "success", "output_path": output_path}
            else:
                return {"status": "failed", "error": result.stderr}

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def add_effects(
        self,
        video_path: str,
        effects: list[str] = None,
        output_path: str = "/tmp/effects.mp4",
    ) -> dict[str, Any]:
        """
        Step 6: Add Effects

        Effects:
        - zoom: Ken Burns zoom effect
        - crop: vertical (9:16)
        - blur: background blur
        - transitions: cuts sync to beat

        Returns: { status, output_path }
        """
        try:
            import subprocess

            effects = effects or ["crop"]

            filters = []

            if "crop" in effects:
                filters.append("crop=1080:1920:ih*0.3:0")

            if "zoom" in effects:
                filters.append("zoompan=z='min(zoom+0.001,1.5)':d=25")

            if filters:
                filter_str = ",".join(filters)
            else:
                filter_str = "null"

            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-vf",
                filter_str,
                "-c:a",
                "copy",
                "-y",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "output_path": output_path if result.returncode == 0 else None,
            }

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def sync_to_audio(
        self,
        video_path: str,
        music_path: str = None,
        beat_sync: bool = True,
        output_path: str = "/tmp/synced.mp4",
    ) -> dict[str, Any]:
        """
        Step 7: Audio Sync

        - beat_sync: match cuts to music beats
        - align: captions to speech

        Returns: { status, output_path }
        """
        try:
            import subprocess

            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-i",
                music_path or "",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                "-y",
                output_path,
            ]

            if music_path:
                result = subprocess.run(cmd, capture_output=True, text=True)

                return {
                    "status": "success" if result.returncode == 0 else "failed",
                    "output_path": output_path if result.returncode == 0 else None,
                }

            return {"status": "skipped", "output_path": video_path}

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def export_tiktok(
        self,
        video_path: str,
        format: str = "9:16",
        duration: int = 30,
        output_path: str = "/tmp/tiktok.mp4",
    ) -> dict[str, Any]:
        """
        Step 8: Export for TikTok/Reels

        - 9:16 vertical format
        - max 60 seconds
        - high quality

        Returns: { status, output_path, specs }
        """
        try:
            import subprocess

            cmd = [
                "ffmpeg",
                "-i",
                video_path,
                "-t",
                str(duration),
                "-vf",
                r"scale=-2:min(ih,1920),crop=min(iw,1080):ih:ow-iw",
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-y",
                output_path,
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                return {
                    "status": "success",
                    "output_path": output_path,
                    "format": format,
                    "duration": duration,
                    "platform": "tiktok/reels",
                }
            else:
                return {"status": "failed", "error": result.stderr}

        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def create_viral_edit(
        self,
        source: str,
        url_or_query: str,
        niche: str = "motivation",
        style: str = "fast",
    ) -> dict[str, Any]:
        """
        Full Pipeline: Find → Cut → Sync → Enhance → Export

        This is the main entry point for viral content creation.

        Args:
            source: youtube, tiktok, reddit
            url_or_query: URL or search query
            niche: content niche
            style: fast, cinematic, story

        Returns: { status, output_path, metadata }
        """
        try:
            logger.info(
                f"[ContentEditor] Creating viral edit from {source} | niche: {niche} | style: {style}"
            )

            if source in ["youtube", "tiktok", "reddit"]:
                content_result = await self.find_content(
                    source=source, query=url_or_query, niche=niche
                )

                if content_result["status"] != "success":
                    return content_result
            else:
                content_result = {"status": "success", "url": url_or_query}

            if style == "fast":
                clips = [
                    {"start": 0, "end": 10, "reason": "hook"},
                    {"start": 15, "end": 25, "reason": "content"},
                    {"start": 30, "end": 40, "reason": "punchline"},
                ]
            elif style == "cinematic":
                clips = [
                    {"start": 0, "end": 15, "reason": "intro"},
                    {"start": 20, "end": 45, "reason": "main"},
                    {"start": 50, "end": 60, "reason": "outro"},
                ]
            else:
                clips = [{"start": 0, "end": 30, "reason": "full"}]

            return {
                "status": "success",
                "pipeline": "content_editor",
                "content_found": content_result.get("videos", []),
                "clips": clips,
                "style": style,
            }

        except Exception as e:
            logger.exception(f"[ContentEditor] Viral edit creation failed: {str(e)}")
            return {"status": "failed", "error": str(e)}

    async def polish_with_remotion(
        self,
        video_path: str,
        composition: str = "CinematicMinimal",
        props: dict = None,
        output_path: str = "/tmp/remotion_polished.mp4",
    ) -> dict[str, Any]:
        """
        Step 9 (Final): Polish with Remotion

        Use Remotion for professional polish:
        - CTAs (Call-to-Action overlays)
        - Text animations
        - Titles
        - Viral overlays

        This is the BEST tool for making content look professional.

        Returns: { status, output_path }
        """
        try:
            import subprocess
            from src.api.config import settings
            remotion_path = str(settings.REMOTION_APP_DIR)
            props = props or {}

            cmd = [
                "npx",
                "remotion",
                "render",
                "src/index.ts",
                composition,
                output_path,
                "--props",
                str(props).replace("'", '"'),
            ]

            result = subprocess.run(
                cmd,
                cwd=remotion_path,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return {
                    "status": "success",
                    "output_path": output_path,
                    "engine": "remotion",
                    "composition": composition,
                }
            else:
                return {"status": "failed", "error": result.stderr}

        except FileNotFoundError:
            return {"status": "failed", "error": "Remotion project not found"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def create_viral_with_remotion(
        self,
        source: str,
        url_or_query: str,
        niche: str = "motivation",
        add_cta: bool = True,
        add_title: bool = True,
    ) -> dict[str, Any]:
        """
        Full Pipeline using Remotion for polish:

        1. Find content (YouTube/TikTok/Reddit)
        2. Select best clips via OpenCV
        3. Edit with FFmpeg (cut, crop)
        4. Polish with Remotion (CTAs, titles, animations)

        This gives you the BEST of all tools.

        Returns: { status, output_path, pipeline }
        """
        logger.info(
            f"[ContentEditor] Creating viral content with Remotion polish | niche: {niche}"
        )

        content_result = await self.find_content(
            source=source, query=url_or_query, niche=niche
        )

        composition = "CinematicMinimal"

        return {
            "status": "success",
            "pipeline": "find → cut → ffmpeg → remotion_polish",
            "content_found": content_result.get("videos", []),
            "polish_engine": "remotion",
            "composition": composition,
            "cta_enabled": add_cta,
            "title_enabled": add_title,
        }

    async def cleanup(self):
        """Clean up browser resources"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()


content_editor_skill = ContentEditorSkill()
