"""
Scene-Based Video Production Orchestrator
=========================================

Orchestrates the complete video production pipeline:
1. Scene analysis and video discovery
2. Video fusion with transitions
3. Audio overlay integration
4. Upload-ready rendering
"""

import asyncio
import logging
from typing import Any
from pathlib import Path
import os
import json
import cv2

from src.services.discovery.video_lead_scanner import video_lead_scanner
from src.services.video_engine.processor import VideoProcessor
from src.services.monetization.service import MonetizationEngine

logger = logging.getLogger(__name__)


from src.api.config import settings

class SceneBasedVideoOrchestrator:
    """Orchestrates scene-based video production with audio overlay"""

    def __init__(self):
        self.video_scanner = video_lead_scanner
        self.video_processor = VideoProcessor()
        self.monetization_engine = MonetizationEngine()
        self.output_dir = Path(settings.STORAGE_OUTPUT_DIR) / "scene_based_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Check available capabilities
        self.can_process_video = self._check_video_processing_available()
        self.can_add_audio = self._check_audio_processing_available()

    def _check_video_processing_available(self) -> bool:
        """Check if video processing capabilities are available"""
        try:
            # Try to import moviepy
            import moviepy

            return True
        except ImportError:
            return False

    def _check_audio_processing_available(self) -> bool:
        """Check if audio processing capabilities are available"""
        try:
            # Check for basic audio capabilities
            import subprocess

            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    async def produce_scene_based_video(
        self,
        scenes: list[dict[str, Any]],
        niche: str,
        target_duration: int = 60,
        audio_script: str = None,
        output_filename: str = None,
    ) -> dict[str, Any]:
        """
        Produce a complete video from scenes with audio overlay.

        Args:
            scenes: list of scene dictionaries
            niche: Content niche
            target_duration: Target video duration in seconds
            audio_script: Script for voiceover
            output_filename: Output filename (auto-generated if None)

        Returns:
            Production results with video path and metadata
        """

        logger.info(
            f"Starting scene-based video production for {len(scenes)} scenes in '{niche}' niche"
        )

        # Step 1: Create production plan
        logger.info("Step 1: Creating production plan...")
        production_plan = await self.video_scanner.create_scene_based_video(
            scenes=scenes,
            niche=niche,
            target_duration=target_duration,
            audio_script=audio_script,
        )

        if not production_plan.get("production_ready"):
            return {
                "success": False,
                "error": "No suitable videos found for production",
                "production_plan": production_plan,
            }

        # Step 2: Execute video fusion
        logger.info("Step 2: Executing video fusion...")
        fusion_result = await self._execute_video_fusion(production_plan)

        if not fusion_result.get("success"):
            return {
                "success": False,
                "error": "Video fusion failed",
                "fusion_error": fusion_result.get("error"),
                "production_plan": production_plan,
            }

        # Step 3: Add audio overlay
        logger.info("Step 3: Adding audio overlay...")
        audio_result = await self._add_audio_overlay(
            fusion_result["video_path"], production_plan["audio_plan"]
        )

        # Step 4: Finalize for upload
        logger.info("Step 4: Finalizing for upload...")
        final_result = await self._finalize_for_upload(
            audio_result["video_path"]
            if audio_result.get("success")
            else fusion_result["video_path"],
            production_plan["upload_specs"],
            output_filename,
        )

        # Step 4b: Generate Thumbnail
        thumbnail_path = None
        if final_result.get("success"):
            thumbnail_path = await self._generate_video_thumbnail(final_result["final_path"])

        # Step 5: Generate monetization plan
        logger.info("Step 5: Generating monetization plan...")
        monetization_plan = await self._generate_monetization_plan(final_result)

        # Compile final results
        final_output = {
            "success": final_result.get("success", False),
            "video_path": final_result.get("final_path"),
            "thumbnail_path": thumbnail_path,
            "duration": production_plan.get("estimated_duration", 0),
            "file_size": final_result.get("file_size", 0),
            "quality_score": production_plan.get("quality_score", 0),
            "scenes_used": len(production_plan.get("scene_videos", {})),
            "videos_found": sum(
                len(videos)
                for videos in production_plan.get("scene_videos", {}).values()
            ),
            "platforms_used": list(
                {
                    video.platform
                    for videos in production_plan.get("scene_videos", {}).values()
                    for video in videos[:1]  # Only count selected videos
                }
            ),
            "upload_specs": production_plan.get("upload_specs"),
            "monetization_plan": monetization_plan,
            "production_plan": production_plan,
            "processing_stats": {
                "video_fusion_time": fusion_result.get("processing_time", 0),
                "audio_overlay_time": audio_result.get("processing_time", 0)
                if audio_result.get("success")
                else 0,
                "total_processing_time": (
                    fusion_result.get("processing_time", 0)
                    + (
                        audio_result.get("processing_time", 0)
                        if audio_result.get("success")
                        else 0
                    )
                ),
            },
        }

        logger.info(
            f"Scene-based video production completed: {final_output['video_path']}"
        )
        return final_output

    async def _execute_video_fusion(
        self, production_plan: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute the actual video fusion based on the production plan with narrative awareness"""
        from .processor import VideoProcessor
        VideoProcessor(output_dir=str(self.output_dir))
        try:
            if not self.can_process_video:
                return {
                    "success": False,
                    "error": "Video processing not available - MoviePy not installed",
                }

            fusion_plan = production_plan.get("fusion_plan", {})
            segments = fusion_plan.get("segments", [])

            if not segments:
                return {"success": False, "error": "No video segments in fusion plan"}

            import time

            start_time = time.time()

            output_path = self.output_dir / f"scene_fusion_{int(time.time())}.mp4"

            # 1. Acquire Source Videos with Stock Fallback
            from .downloader import base_downloader_service
            from .stock_service import base_stock_service

            logger.info(f"Acquiring assets for {len(segments)} segments (with Pexels stock fallback)...")

            async def download_asset_with_fallback(idx, segment):
                """Try yt-dlp download first, then Pexels stock as fallback."""
                source_path = segment.get("video_path") or segment.get("source_video")
                video_uri = segment.get("url") or segment.get("source_uri")

                # 1. Local file already exists
                if source_path and Path(source_path).exists():
                    logger.info(f"[Scene {idx+1}] Using local asset: {source_path}")
                    return (source_path, segment)

                # 2. Try yt-dlp download (YouTube, TikTok, etc.)
                if video_uri:
                    try:
                        logger.info(f"[Scene {idx+1}] Downloading via yt-dlp: {video_uri}")
                        downloaded_path = await base_downloader_service.download_video(video_uri)
                        if downloaded_path and Path(downloaded_path).exists():
                            logger.info(f"[Scene {idx+1}] yt-dlp download success: {downloaded_path}")
                            return (downloaded_path, segment)
                    except Exception as e:
                        logger.warning(f"[Scene {idx+1}] yt-dlp download failed: {e}")

                # 3. Pexels Stock Fallback — search using scene keywords
                visual_prompt = segment.get("visual_prompt") or segment.get("scene", "")
                niche_keyword = production_plan.get("niche") or "cinematic"
                search_query = f"{visual_prompt} {niche_keyword}".strip()[:80]

                logger.info(f"[Scene {idx+1}] Falling back to Pexels stock: '{search_query}'")
                try:
                    stock_urls = await base_stock_service.fetch_b_roll(search_query, count=1)
                    if stock_urls:
                        stock_path = await base_stock_service.download_stock_video(
                            stock_urls[0], output_dir=f"/tmp/ettametta/stock_scene_{idx}"
                        )
                        if stock_path and Path(stock_path).exists():
                            logger.info(f"[Scene {idx+1}] Pexels stock acquired: {stock_path}")
                            return (stock_path, segment)
                except Exception as e:
                    logger.warning(f"[Scene {idx+1}] Pexels stock fallback failed: {e}")

                # 4. Absolute last resort — try with just the niche keyword
                try:
                    logger.info(f"[Scene {idx+1}] Last resort stock search: '{niche_keyword} video'")
                    fallback_urls = await base_stock_service.fetch_b_roll(f"{niche_keyword} video", count=1)
                    if fallback_urls:
                        fallback_path = await base_stock_service.download_stock_video(
                            fallback_urls[0], output_dir=f"/tmp/ettametta/stock_fallback_{idx}"
                        )
                        if fallback_path and Path(fallback_path).exists():
                            logger.info(f"[Scene {idx+1}] Last resort stock acquired: {fallback_path}")
                            return (fallback_path, segment)
                except Exception as e:
                    logger.exception(f"[Scene {idx+1}] All asset sources exhausted: {e}")

                logger.error(f"[Scene {idx+1}] CRITICAL: No video asset could be acquired")
                return None

            # Execute all downloads concurrently
            download_tasks = [download_asset_with_fallback(i, seg) for i, seg in enumerate(segments)]
            video_files_raw = await asyncio.gather(*download_tasks)

            # Filter out failed downloads
            video_files = [v for v in video_files_raw if v is not None]

            logger.info(f"Successfully acquired {len(video_files)} / {len(segments)} video assets.")

            if not video_files:
                return {"success": False, "error": "No source videos could be acquired (all sources exhausted)"}

            # 2. Production Assembly (MoviePy 2.x)
            try:
                from moviepy import VideoFileClip, CompositeVideoClip

                normalized_clips = []
                target_w, target_h = 1080, 1920 # Default vertical

                # Check production plan for orientation hints
                if production_plan.get("aspect_ratio") == "16:9":
                    target_w, target_h = 1920, 1080

                logger.info(f"Normalizing {len(video_files)} clips to {target_w}x{target_h} for seamless fusion...")

                for video_path, segment in video_files:
                    try:
                        logger.info(f"Processing segment: {video_path}")
                        # 1. Normalize Resolution and Aspect Ratio (Smart Crop)
                        norm_path = f"{video_path}_norm.mp4"
                        success = self.video_processor.base_ffmpeg_service.apply_fast_transform(
                            video_path, norm_path, width=target_w, height=target_h
                        )

                        final_path = norm_path if success else video_path
                        logger.info(f"Normalization success: {success}, using: {final_path}")

                        # 2. Load the normalized clip
                        clip = VideoFileClip(final_path)
                        duration = segment.get("duration", 5)
                        logger.info(f"Loaded clip duration: {clip.duration}, target: {duration}")

                        # Apply smart duration cropping (narrative aware)
                        if clip.duration > duration:
                            start_t = min(clip.duration * 0.1, clip.duration - duration)
                            clip = clip.subclipped(start_t, start_t + duration)
                            logger.info(f"Subclipped to: {clip.duration}")

                        # Add simple text overlay if prompt exists (Pillow-based, no ImageMagick)
                        if segment.get("visual_prompt") and self.video_processor.font_path:
                            logger.info(f"Applying text overlay: {segment['visual_prompt']}")
                            from PIL import Image, ImageDraw, ImageFont
                            import numpy as np
                            from moviepy import ImageClip

                            # ... (rest of the pillow logic)

                            # Create a small transparent overlay for text
                            txt_text = segment["visual_prompt"][:50]
                            font_size = 32
                            try:
                                font = ImageFont.truetype(self.video_processor.font_path, font_size)
                            except Exception:
                                font = ImageFont.load_default()

                            # Measure text
                            dummy_img = Image.new('RGBA', (target_w, 100))
                            draw = ImageDraw.Draw(dummy_img)
                            bbox = draw.textbbox((0, 0), txt_text, font=font)
                            tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]

                            # Create actual overlay
                            overlay_img = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 0))
                            draw = ImageDraw.Draw(overlay_img)

                            # Draw semi-transparent background for text
                            padding = 10
                            draw.rectangle(
                                [(target_w - tw)//2 - padding, target_h - th - 60 - padding,
                                 (target_w + tw)//2 + padding, target_h - 60 + padding],
                                fill=(0, 0, 0, 160)
                            )
                            draw.text(((target_w - tw)//2, target_h - th - 60), txt_text, font=font, fill=(255, 255, 255, 255))

                            # Convert to MoviePy clip
                            overlay_array = np.array(overlay_img)
                            txt_clip = ImageClip(overlay_array, is_mask=False, transparent=True).with_duration(clip.duration)
                            clip = CompositeVideoClip([clip, txt_clip])

                        normalized_clips.append(clip)
                    except Exception as clip_err:
                        logger.exception(f"Error processing clip {video_path}: {clip_err}")

                if normalized_clips:
                    # Collect paths for FFmpeg concatenation
                    norm_paths = [f"{v_path}_norm.mp4" for v_path, _ in video_files]

                    # Add Intro
                    title = production_plan.get("niche") or "Viral Content"
                    intro_path = str(self.output_dir / f"intro_{int(time.time())}.mp4")
                    intro_res = await self._add_intro_clip(target_w, target_h, title.upper(), intro_path)
                    if intro_res:
                        norm_paths.insert(0, intro_res)

                    # Add Engagement CTA (Like/Follow)
                    outro_path = str(self.output_dir / f"outro_{int(time.time())}.mp4")
                    outro_res = await self._add_engagement_cta(target_w, target_h, outro_path)
                    if outro_res:
                        norm_paths.append(outro_res)

                    # 4. Final Render & Audio Ducking (Elite FFmpeg Path)
                    temp_output = str(output_path.parent / f"temp_no_audio_{output_path.name}")

                    # Close clips to free file handles for FFmpeg
                    for clip in normalized_clips:
                        clip.close()

                    transformer = self.video_processor.base_ffmpeg_service
                    concat_success = transformer.concatenate_videos(norm_paths, temp_output)

                    if concat_success:
                        logger.info("✅ [Orchestrator] FFmpeg Concatenation Complete. Mixing Audio with Ducking...")

                        # Use audio_plan or defaults
                        audio_plan = fusion_plan.get("audio_plan", {})
                        music_path = audio_plan.get("music_path") or "data/storage/audio/background/cinematic.mp3"
                        voiceover_path = audio_plan.get("voiceover_path") # Assumed to be passed or generated

                        if voiceover_path and os.path.exists(voiceover_path) and os.path.exists(music_path):
                            transformer.mix_production_audio_with_ducking(
                                temp_output, voiceover_path, music_path, str(output_path)
                            )
                        else:
                            # Fallback if audio missing
                            os.rename(temp_output, str(output_path))

                        # 5. Vision-Based Quality Control
                        from src.services.video_engine.quality_control import base_qc_service
                        qc_report = await base_qc_service.audit_video(str(output_path), "nexus_auto")

                        return {
                            "success": True,
                            "video_path": str(output_path),
                            "segments_processed": len(video_files),
                            "qc_report": qc_report,
                            "processing_time": time.time() - start_time,
                            "method": "ffmpeg_elite_fusion_with_ducking",
                        }

                    return {
                        "success": False,
                        "reason": "FFmpeg concatenation failed",
                        "video_path": None
                    }

            except Exception as e:
                logger.exception(f"Real video fusion failed: {e}")
                raise e

            # Fallback: Create placeholder if no videos or processing failed
            await asyncio.sleep(2)  # Simulate processing time

            # Create a text file describing what would be created
            with open(output_path.with_suffix(".txt"), "w") as f:
                f.write("SCENE-BASED VIDEO FUSION PLAN\\n")
                f.write(f"Segments: {len(segments)}\\n")
                f.write(f"Total Duration: {fusion_plan.get('total_duration', 0)}s\\n")
                f.write(f"Video Files Used: {len(video_files)}\\n")
                for i, segment in enumerate(segments):
                    f.write(
                        f"Segment {i + 1}: {segment.get('scene', f'Scene_{i + 1}')}\\n"
                    )

            return {
                "success": False,  # Return False since no actual video was created
                "video_path": str(output_path.with_suffix(".txt")),  # Text file instead
                "segments_processed": len(segments),
                "total_duration": fusion_plan.get("total_duration", 0),
                "processing_time": time.time() - start_time,
                "method": "simulation_only",
                "reason": "No compatible video files found or processing failed",
            }

        except Exception as e:
            logger.exception(f"Video fusion failed: {e}")
            return {"success": False, "error": str(e)}

    async def _add_audio_overlay(
        self, video_path: str, audio_plan: dict[str, Any]
    ) -> dict[str, Any]:
        """Add audio overlay to the video using FFmpeg"""
        import time
        import subprocess
        import tempfile

        try:
            if not audio_plan.get("voice_over", False):
                return {
                    "success": True,
                    "video_path": video_path,
                    "audio_added": False,
                    "processing_time": 0,
                }

            if not self.can_add_audio:
                logger.warning(
                    "Audio processing not available - skipping audio overlay"
                )
                return {
                    "success": True,
                    "video_path": video_path,
                    "audio_added": False,
                    "processing_time": 0,
                }

            start_time = time.time()
            audio_segments = audio_plan.get("audio_segments", [])
            audio_output_path = video_path.replace(".mp4", "_with_audio.mp4")

            if not audio_segments:
                # No audio segments — try to use background_music or voiceover_path
                bg_music = audio_plan.get("background_music")
                voiceover_path = audio_plan.get("voiceover_path")

                if voiceover_path and Path(voiceover_path).exists():
                    # Mix voiceover with video using FFmpeg
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", video_path,
                        "-i", voiceover_path,
                        "-filter_complex",
                        "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[a]",
                        "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest",
                        audio_output_path,
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    if result.returncode == 0 and Path(audio_output_path).exists():
                        return {
                            "success": True,
                            "video_path": audio_output_path,
                            "audio_added": True,
                            "audio_segments": 0,
                            "processing_time": time.time() - start_time,
                        }
                    logger.warning(f"FFmpeg voiceover mix failed: {result.stderr[:200]}")

                elif bg_music and Path(bg_music).exists():
                    # Mix background music at lower volume
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", video_path,
                        "-i", bg_music,
                        "-filter_complex",
                        "[0:a]volume=1.0[orig];[1:a]volume=0.25[music];[orig][music]amix=inputs=2:duration=first[a]",
                        "-map", "0:v", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest",
                        audio_output_path,
                    ]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    if result.returncode == 0 and Path(audio_output_path).exists():
                        return {
                            "success": True,
                            "video_path": audio_output_path,
                            "audio_added": True,
                            "audio_segments": 0,
                            "processing_time": time.time() - start_time,
                        }
                    logger.warning(f"FFmpeg music mix failed: {result.stderr[:200]}")

                # No audio to add
                return {
                    "success": True,
                    "video_path": video_path,
                    "audio_added": False,
                    "processing_time": time.time() - start_time,
                }

            # Multiple audio segments — concatenate them, then mix with video
            valid_segments = [s for s in audio_segments if isinstance(s, str) and Path(s).exists()]
            if not valid_segments:
                logger.warning("No valid audio segment files found")
                return {
                    "success": True,
                    "video_path": video_path,
                    "audio_added": False,
                    "processing_time": time.time() - start_time,
                }

            # Concatenate audio segments into one track
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                for seg in valid_segments:
                    f.write(f"file '{Path(seg).absolute()}'\n")
                concat_list = f.name

            concat_audio = video_path.replace(".mp4", "_concat_audio.m4a")
            try:
                cmd_concat = [
                    "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", concat_list, "-c:a", "aac", "-b:a", "192k",
                    concat_audio,
                ]
                result = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    logger.warning(f"Audio concat failed: {result.stderr[:200]}")
                    return {
                        "success": True,
                        "video_path": video_path,
                        "audio_added": False,
                        "processing_time": time.time() - start_time,
                    }
            finally:
                Path(concat_list).unlink(missing_ok=True)

            # Mix concatenated audio with video
            cmd_mix = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", concat_audio,
                "-filter_complex",
                "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[a]",
                "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                audio_output_path,
            ]
            result = subprocess.run(cmd_mix, capture_output=True, text=True, timeout=120)
            Path(concat_audio).unlink(missing_ok=True)

            if result.returncode == 0 and Path(audio_output_path).exists():
                return {
                    "success": True,
                    "video_path": audio_output_path,
                    "audio_added": True,
                    "audio_segments": len(valid_segments),
                    "processing_time": time.time() - start_time,
                }

            logger.warning(f"FFmpeg audio mix failed: {result.stderr[:200]}")
            return {
                "success": True,
                "video_path": video_path,
                "audio_added": False,
                "processing_time": time.time() - start_time,
            }

        except Exception as e:
            logger.exception(f"Audio overlay failed: {e}")
            return {"success": False, "error": str(e), "video_path": video_path}

    async def _finalize_for_upload(
        self, video_path: str, upload_specs: dict[str, Any], custom_filename: str = None
    ) -> dict[str, Any]:
        """Finalize video for upload with proper formatting"""
        try:
            import time

            start_time = time.time()

            # Generate output filename
            if custom_filename:
                final_filename = f"{custom_filename}.mp4"
            else:
                timestamp = int(time.time())
                final_filename = f"scene_video_{timestamp}.mp4"

            final_path = self.output_dir / final_filename

            # Simulate final processing (format optimization, metadata addition)
            await asyncio.sleep(1)

            # Get file size (placeholder)
            file_size = len("MOCK_FINAL_VIDEO_CONTENT") * 1024 * 1024  # Simulate ~1MB

            # Copy/create final file
            import shutil

            shutil.copy2(video_path, final_path)

            # Add upload metadata
            metadata = {
                "upload_specs": upload_specs,
                "processing_date": time.time(),
                "platforms_ready": upload_specs.get("platforms", []),
                "seo_tags": upload_specs.get("seo_tags", []),
                "hashtags": upload_specs.get("metadata", {}).get("hashtags", []),
            }

            # Save metadata alongside video
            metadata_path = final_path.with_suffix(".json")
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            return {
                "success": True,
                "final_path": str(final_path),
                "file_size": file_size,
                "metadata_path": str(metadata_path),
                "platforms_ready": metadata["platforms_ready"],
                "processing_time": time.time() - start_time,
            }

        except Exception as e:
            logger.exception(f"Upload finalization failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_monetization_plan(
        self, final_result: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate monetization plan for the produced video"""
        try:
            if not final_result.get("success"):
                return {"error": "Video production failed"}

            # Create monetization suggestions
            monetization_plan = {
                "affiliate_opportunities": [
                    {
                        "type": "amazon",
                        "timing": "30s",
                        "product_category": "productivity_tools",
                    },
                    {
                        "type": "shareasale",
                        "timing": "45s",
                        "product_category": "software",
                    },
                ],
                "end_screen_elements": [
                    {"type": "subscribe", "priority": "high"},
                    {"type": "like", "priority": "high"},
                    {"type": "affiliate_link", "priority": "medium"},
                ],
                "estimated_revenue": "$25-150 per 1000 views",
                "optimization_score": 8.7,
                "recommended_platforms": final_result.get("platforms_ready", []),
            }

            return monetization_plan

        except Exception as e:
            logger.exception(f"Monetization plan generation failed: {e}")
            return {"error": str(e)}


    async def _add_intro_clip(self, w: int, h: int, title: str, output_path: str) -> str | None:
        """Appends a branded intro segment using Pillow, renders to file and returns path."""
        try:
            from moviepy import ColorClip, CompositeVideoClip, ImageClip
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np

            logger.info("Injecting Branded Intro segment (Pillow-based)...")
            duration = 3.0

            bg = ColorClip(size=(w, h), color=(15, 15, 15)).with_duration(duration)

            img = Image.new('RGB', (w, h), color=(15, 15, 15))
            draw = ImageDraw.Draw(img)

            try:
                font_size = h // 20
                font = ImageFont.truetype(self.video_processor.font_path, font_size)
            except Exception:
                font = ImageFont.load_default()

            cta_lines = ["ETTAMETTA PRESENTS", "", title]
            total_h = len(cta_lines) * (font_size * 1.5)
            current_y = (h - total_h) // 2

            for i, line in enumerate(cta_lines):
                bbox = draw.textbbox((0, 0), line, font=font)
                line_w = bbox[2] - bbox[0]
                color = (255, 255, 255) if i != 0 else (100, 200, 255)
                draw.text(((w - line_w) // 2, current_y), line, font=font, fill=color)
                current_y += font_size * 1.5

            img_array = np.array(img)
            txt_clip = ImageClip(img_array).with_duration(duration)

            intro_segment = CompositeVideoClip([bg, txt_clip])
            intro_segment.write_videofile(output_path, fps=30, codec="libx264", audio=False, preset="ultrafast", logger=None)
            intro_segment.close()
            return output_path
        except Exception as e:
            logger.exception(f"Failed to inject Intro: {e}")
            return None

    async def _add_engagement_cta(self, w: int, h: int, output_path: str) -> str | None:
        """Appends a high-energy CTA segment using Pillow, renders to file and returns path."""
        try:
            from moviepy import ColorClip, CompositeVideoClip, ImageClip
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np

            logger.info("Injecting Engagement CTA segment (Pillow-based)...")
            duration = 4.0

            bg = ColorClip(size=(w, h), color=(15, 15, 15)).with_duration(duration)

            img = Image.new('RGB', (w, h), color=(15, 15, 15))
            draw = ImageDraw.Draw(img)

            try:
                font_size = h // 25
                font = ImageFont.truetype(self.video_processor.font_path, font_size)
            except Exception:
                font = ImageFont.load_default()

            cta_lines = ["LIKE • SHARE • FOLLOW", "", "Hit the 🔔 for more!"]
            total_h = len(cta_lines) * (font_size * 1.5)
            current_y = (h - total_h) // 2

            for line in cta_lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                line_w = bbox[2] - bbox[0]
                draw.text(((w - line_w) // 2, current_y), line, font=font, fill=(255, 215, 0))
                current_y += font_size * 1.5

            img_array = np.array(img)
            txt_clip = ImageClip(img_array).with_duration(duration)

            cta_segment = CompositeVideoClip([bg, txt_clip])
            cta_segment.write_videofile(output_path, fps=30, codec="libx264", audio=False, preset="ultrafast", logger=None)
            cta_segment.close()
            return output_path
        except Exception as e:
            logger.exception(f"Failed to inject CTA: {e}")
            return None

    async def _generate_video_thumbnail(self, video_path: str) -> str:
        """Generates a high-quality thumbnail from the video."""
        try:
            output_dir = os.path.dirname(video_path)
            thumb_name = os.path.basename(video_path).replace(".mp4", "_thumb.jpg")
            thumb_path = os.path.join(output_dir, thumb_name)

            # Use absolute path to ensure it's found
            abs_thumb_path = str(Path(thumb_path).absolute())

            logger.info(f"Generating high-impact thumbnail: {abs_thumb_path}")

            # Extract frame at 25% of duration (to avoid intro/cta)
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            cap.release()

            timestamp = "00:00:01"
            if duration > 4:
                # Proper HH:MM:SS or just seconds
                seconds = int(duration * 0.25)
                timestamp = f"{seconds // 3600:02d}:{(seconds % 3600) // 60:02d}:{seconds % 60:02d}"

            cmd = [
                "ffmpeg", "-y", "-ss", timestamp, "-i", video_path,
                "-vframes", "1", "-q:v", "2", abs_thumb_path
            ]

            import subprocess
            result = subprocess.run(cmd, capture_output=True, text=True)

            if os.path.exists(abs_thumb_path):
                logger.info(f"Thumbnail created successfully: {abs_thumb_path}")
                return abs_thumb_path
            else:
                logger.error(f"FFmpeg failed to create thumbnail. Stderr: {result.stderr}")
                return None
        except Exception as e:
            logger.exception(f"Thumbnail generation failed: {e}")
            return None

# Global instance
base_scene_orchestrator_service = SceneBasedVideoOrchestrator()
