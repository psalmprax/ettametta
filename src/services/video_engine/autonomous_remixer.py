"""
Autonomous Video Remix Service
==============================
Complete pipeline: Discovery → Download → Analyze → Fuse → Edit → Voiceover → Captions
Takes a topic/niche and produces a polished video using discovered viral footage.
"""

import logging
import asyncio
import tempfile
from pathlib import Path
from typing import Any
import subprocess

logger = logging.getLogger(__name__)


class AutonomousVideoRemixer:
    """
    Fully autonomous video creation from discovered viral content.
    Chains multiple services to produce finished videos without human intervention.
    """

    def __init__(self):
        self.output_dir = Path("data/storage/outputs/remix")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path("data/storage/temp/remix")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def create_remix_video(
        self,
        topic: str,
        niche: str | None = None,
        style: str = "dynamic",
        duration_seconds: int = 60,
        voice_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Complete autonomous video creation pipeline:
        1. Discover viral videos matching topic/niche
        2. Download selected videos
        3. Analyze and extract best clips
        4. Generate script matching clips
        5. Fuse clips together with transitions
        6. Add AI voiceover synced to clips
        7. Burn in captions
        8. Render final video
        """
        logger.info(f"[Remix] Starting autonomous remix for topic: {topic}, niche: {niche}")

        try:
            # Step 1: Discover viral videos
            logger.info("[Remix] Step 1: Discovering viral videos...")
            discovered_videos = await self._discover_viral_videos(topic, niche)

            if not discovered_videos:
                raise Exception("No suitable videos found for remix")

            # Step 2: Download videos
            logger.info(f"[Remix] Step 2: Downloading {len(discovered_videos)} videos...")
            downloaded_paths = await self._download_videos(discovered_videos[:5])  # Limit to 5

            if not downloaded_paths:
                raise Exception("Failed to download any videos")

            # Step 3: Analyze and extract best segments
            logger.info("[Remix] Step 3: Analyzing and extracting clips...")
            clip_segments = await self._extract_best_clips(downloaded_paths, duration_seconds)

            # Step 4: Generate script matching the clips
            logger.info("[Remix] Step 4: Generating script...")
            script = await self._generate_script_for_clips(clip_segments, niche, style)

            # Step 5: Generate voiceover
            logger.info("[Remix] Step 5: Generating voiceover...")
            voiceover_path = await self._generate_voiceover(script, voice_id)

            # Step 6: Fuse clips with transitions and sync voiceover
            logger.info("[Remix] Step 6: Fusing clips and adding voiceover...")
            fused_video = await self._fuse_clips_with_voiceover(
                clip_segments, voiceover_path, script, style
            )

            # Step 7: Add captions
            logger.info("[Remix] Step 7: Adding captions...")
            final_video = await self._add_captions(fused_video, script)

            logger.info(f"[Remix] ✅ Complete! Output: {final_video}")

            return {
                "status": "completed",
                "output_path": str(final_video),
                "source_videos": len(discovered_videos),
                "clips_used": len(clip_segments),
                "duration": duration_seconds,
                "script_segments": len(script.get("segments", [])),
            }

        except Exception as e:
            logger.error(f"[Remix] Failed: {str(e)}", exc_info=True)
            raise

    async def _discover_viral_videos(self, topic: str, niche: str | None) -> list[dict]:
        """Discover viral videos using the intelligent workflow."""
        from src.engines.intelligent_video_workflow import discover_multi_platform, analyze_content_type, check_eligibility

        # Auto-detect niche if not provided
        if not niche:
            from src.services.script_generator.service import detect_niche_from_topic
            niche = detect_niche_from_topic(topic)

        # Discover videos from multiple platforms
        videos = await discover_multi_platform(
            query=f"{topic} {niche}",
            max_per_platform=3,
            session_id=None,
        )

        if not videos:
            return []

        # Analyze and filter videos
        eligible = []
        for video in videos[:10]:  # Limit analysis to top 10
            try:
                analysis = await analyze_content_type(video)
                video["analysis"] = analysis

                eligibility = await check_eligibility(video)
                video["eligibility"] = eligibility

                if eligibility.get("eligible") and analysis.get("usable"):
                    video["score"] = analysis.get("score", 0)
                    eligible.append(video)
            except Exception as e:
                logger.warning(f"[Remix] Failed to analyze video: {e}")
                continue

        # Sort by viral score
        eligible.sort(key=lambda x: x.get("score", 0), reverse=True)

        logger.info(f"[Remix] Found {len(eligible)} eligible videos")
        return eligible

    async def _download_videos(self, videos: list[dict]) -> list[str]:
        """Download videos using yt-dlp."""
        downloaded = []

        for video in videos:
            url = video.get("url")
            if not url:
                continue

            output_path = self.temp_dir / f"{video.get('id', 'unknown')}.mp4"

            try:
                result = subprocess.run(
                    [
                        "yt-dlp",
                        "-f", "best[ext=mp4]/best",
                        "--merge-output-format", "mp4",
                        "-o", str(output_path),
                        "--no-playlist",
                        "--restrict-filenames",
                        url,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode == 0 and output_path.exists():
                    downloaded.append(str(output_path))
                    logger.info(f"[Remix] Downloaded: {video.get('title', 'unknown')}")
                else:
                    logger.warning(f"[Remix] Failed to download: {url}")

            except Exception as e:
                logger.warning(f"[Remix] Download error: {e}")

        return downloaded

    async def _extract_best_clips(self, video_paths: list[str], target_duration: int) -> list[dict]:
        """Extract best segments from downloaded videos."""
        clips = []
        clip_duration = target_duration // len(video_paths) if video_paths else 10

        for i, video_path in enumerate(video_paths):
            try:
                # Extract first N seconds as clip (simplified - would use scene detection in production)
                clip_path = self.temp_dir / f"clip_{i}.mp4"

                result = subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-i", video_path,
                        "-t", str(clip_duration),
                        "-c", "copy",
                        str(clip_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 and clip_path.exists():
                    clips.append({
                        "path": str(clip_path),
                        "duration": clip_duration,
                        "source_index": i,
                    })

            except Exception as e:
                logger.warning(f"[Remix] Clip extraction failed: {e}")

        return clips

    async def _generate_script_for_clips(self, clips: list[dict], niche: str, style: str) -> dict:
        """Generate script that matches the extracted clips."""
        from src.services.script_generator.service import base_script_service

        # Create a generic topic based on number of clips
        topic = f"viral {niche} content compilation"

        script = await base_script_service.generate_script(
            topic=topic,
            niche=niche,
            duration_sec=sum(c["duration"] for c in clips),
            style=style,
        )

        return script

    async def _generate_voiceover(self, script: dict, voice_id: str | None) -> str:
        """Generate AI voiceover for the script."""
        from src.services.voiceover.service import base_voiceover_service

        # Combine all script segments into one text
        full_text = " ".join(seg.get("text", "") for seg in script.get("segments", []))

        if not full_text:
            raise Exception("Script has no text for voiceover")

        # Generate voiceover
        voiceover_path = await base_voiceover_service.generate_voiceover(
            text=full_text,
            voice_id=voice_id or "alloy",
        )

        return voiceover_path

    async def _fuse_clips_with_voiceover(
        self,
        clips: list[dict],
        voiceover_path: str,
        script: dict,
        style: str,
    ) -> str:
        """Fuse clips together with transitions and sync voiceover."""
        from src.services.video_engine.autonomous_editor import base_autonomous_editor

        # Prepare timeline for autonomous editor
        script_segments = [
            {"text": seg.get("text", ""), "duration": seg.get("duration", 5)}
            for seg in script.get("segments", [])
        ]

        video_clips = [
            {"path": clip["path"]}
            for clip in clips
        ]

        # Use autonomous editor to fuse
        result = await base_autonomous_editor.auto_edit_video(
            script_segments=script_segments,
            video_clips=video_clips,
            audio_track=voiceover_path,
            style=style,
            output_filename=f"remix_{hash(str(clips)) % 10000}.mp4",
        )

        return result["output_path"]

    async def _add_captions(self, video_path: str, script: dict) -> str:
        """Add burned-in captions to the video."""
        # The autonomous editor already adds captions, so this is a no-op
        # In production, you could add additional caption styling here
        return video_path


# Singleton instance
base_autonomous_remixer = AutonomousVideoRemixer()
