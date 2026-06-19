import os
import logging
import asyncio
import time
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

# Graceful imports for optional dependencies
try:
    import moviepy
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    moviepy = None

import cv2
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from opentelemetry import trace
from src.api.config import settings
from src.api.utils.resilience import CircuitBreaker
from src.services.nexus_engine.style_library import get_style
from src.shared.observability import get_logger
from src.shared.state_machine import base_state_machine, JobState
from src.shared.enums import NodeStatus
from src.services.video_engine.video_utils import probe_video, extract_frame, probe_duration_ffprobe
from src.services.nexus_engine.vibe_analyzer import determine_video_vibe
from src.services.nexus_engine.render_pipeline import (
    modulate_video_style, source_music, extract_thumbnail, export_srt,
)
from contextlib import asynccontextmanager

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)


# ── Style-to-Composition Mapping ────────────────────────────────────────
# Maps each Nexus video style to the most visually appropriate Remotion
# composition.  Long-form compositions (18000 frames) accept full props
# (clips, words, audio).  Short-form compositions (120 frames) are capped
# and receive simplified props (title, subtitle, video_url, audio_url).

COMPOSITION_STYLE_MAP: dict[str, str] = {
    # Documentary / Narrative (→ CinematicAncient — astrolabe, celestial, timeless)
    "CINEMATIC_DOC": "CinematicAncient",
    "VOX_EXPLAINER": "CinematicAncient",
    "DEEP_DIVE": "CinematicAncient",
    "STOIC_WISDOM": "CinematicAncient",

    # Mystery / Noir / Investigation (→ CinematicMinimal — clean, moody, understated)
    "NOIR_MYSTERY": "CinematicMinimal",
    "INVESTIGATION": "CinematicMinimal",
    "RETRO_ARCHIVE": "CinematicMinimal",
    "HORROR_CREEPY": "CinematicMinimal",

    # Fast / Hype / Gaming (→ CinematicCyberpunk — HUD, scanlines, neon)
    "FAST_HYPE": "CinematicCyberpunk",
    "ESPORTS_HYPE": "CinematicCyberpunk",
    "GAMING_LORE": "CinematicCyberpunk",
    "FITNESS_MOTIVATION": "CinematicCyberpunk",
    "TOP_LISTICLE": "CinematicCyberpunk",

    # Motivational / Heartfelt (→ CinematicKinetic — kinetic typography)
    "MOTIVATIONAL": "CinematicKinetic",
    "HEARTFELT_NARRATIVE": "CinematicKinetic",

    # Relationship / Emotional (→ CinematicIridescent — glass, beauty, fragility)
    "RELATIONSHIP_DRAMA": "CinematicIridescent",

    # Travel / Vlog (→ CinematicLiquid — liquid metal, fluid, dynamic)
    "TRAVEL_VLOG": "CinematicLiquid",

    # Product / Showcase (→ Cinematic3D — 3D extruded text, premium)
    "PRODUCT_SHOWCASE": "Cinematic3D",

    # Culinary / Tutorial (→ CinematicMinimal — clean instructional aesthetic)
    "CULINARY_MASTERCLASS": "CinematicMinimal",
    "ULTIMATE_TUTORIAL": "CinematicMinimal",

    # Reddit / Persona / Podcast / Lofi (→ ViralClip — full production engine)
    "REDDIT_STORY": "ViralClip",
    "PERSONA_MONTAGE": "ViralClip",
    "BROADCAST_NEWS": "ViralClip",
    "REACTION_COMMENTARY": "ViralClip",
    "LOFI_CHILL": "ViralClip",
    "PODCAST_SIM": "ViralClip",
}

# Compositions registered with only 120 frames (4 seconds at 30fps) in Root.tsx
SHORT_FORM_COMPOSITIONS: set[str] = {
    "CinematicIridescent",
    "CinematicPortal",
    "CinematicCyberpunk",
    "CinematicLiquid",
    "CinematicPrism",
    "CinematicLidar",
    "CinematicKinetic",
}

# Compositions that accept the full ViralClip-style props (clips, words, timeline, etc.)
FULL_FORM_COMPOSITIONS: set[str] = {
    "ViralClip",
    "CinematicMinimal",
    "CinematicAncient",
    "Cinematic3D",
    "HormoziStyle",
}


def _run_subprocess(
    args: list[str],
    *,
    capture_output: bool = True,
    text: bool = False,
    check: bool = True,
    cwd: str | None = None,
) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    """Run a subprocess command. Raises subprocess.CalledProcessError on non-zero exit."""
    return subprocess.run(
        args,
        capture_output=capture_output,
        text=text,
        check=check,
        cwd=cwd,
    )


class NexusOrchestrator:
    """
    High-fidelity video assembly using Remotion React engine.
    Orchestrates the end-to-end pipeline from ingress to egress.
    """
    def __init__(self, output_dir: str = "outputs/nexus"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.remotion_breaker = CircuitBreaker(name="NexusRemotion")
        self.logger = logging.getLogger("NexusOrchestrator")

        # Check optional dependencies
        self.dependencies_available = {
            "moviepy": MOVIEPY_AVAILABLE,
        }

        if not self.dependencies_available["moviepy"]:
            self.logger.warning(
                "NexusOrchestrator: moviepy not available. Video processing features disabled."
            )

    @property
    def _local_temp_dir(self) -> Path:
        """Get a project-local temporary directory path and ensure it exists."""
        p = Path.cwd() / "tmp" / "ettametta"
        p.mkdir(parents=True, exist_ok=True)
        return p

    async def _retry_remotion_render(
        self, composition_id: str, props: Dict, output_name: str
    ) -> str | None:
        """Retry wrapper for remotion render with exponential backoff and circuit breaking"""
        if self.remotion_breaker.is_open():
            raise RuntimeError(
                "Remotion service circuit breaker is OPEN - too many failures"
            )

        @retry(
            stop=stop_after_attempt(settings.DEFAULT_RETRY_COUNT),
            wait=wait_exponential(
                multiplier=settings.RETRY_MULTIPLIER, 
                min=settings.RETRY_MIN_WAIT, 
                max=settings.RETRY_MAX_WAIT
            ),
            retry=retry_if_exception_type(
                (TimeoutError, ConnectionError, RuntimeError, asyncio.TimeoutError)
            ),
            reraise=True,
        )
        async def _render():
            from src.services.video_engine.remotion_service import base_remotion_service

            try:
                # Use a very long timeout for rendering, but still respect settings
                render_timeout = settings.LLM_TIMEOUT * 60 # Default 60s * 60 = 3600s
                
                result = await asyncio.wait_for(
                    base_remotion_service.render_video(
                        composition_id=composition_id,
                        props=props,
                        output_name=output_name,
                    ),
                    timeout=render_timeout,
                )
                self.remotion_breaker.record_success()
                return result
            except Exception as e:
                self.logger.error(f"Render attempt failed: {e}")
                self.remotion_breaker.record_failure()
                raise

        try:
            return await _render()
        except Exception as e:
            self.logger.error(f"Remotion render exhausted all retries: {e}")
            return None

    async def _update_node_status(
        self,
        job_id: str,
        niche: str,
        node_type: str,
        status: NodeStatus,
        progress: int,
        error: str | None = None,
        extra: dict | None = None,
    ) -> None:
        """Helper to transition states, build payloads, and notify websockets."""
        from src.api.routes.ws import notify_nexus_job_update_sync

        if status == NodeStatus.FAILED:
            await base_state_machine.transition_to(
                job_id, None, JobState.FAILED, {"node": node_type, "error": error}
            )
        elif status == NodeStatus.ACTIVE and node_type == "synthesis":
            await base_state_machine.transition_to(
                job_id, JobState.COGNITION, JobState.SYNTHESIZING
            )

        payload = {
            "id": str(job_id),
            "status": f"{node_type.upper()}_{status.value}",
            "current_node": node_type,
            "node_status": status.value,
            "progress": progress,
            "niche": niche,
        }
        if error:
            payload["error"] = error
        if extra:
            payload.update(extra)

        notify_nexus_job_update_sync(payload)

    @asynccontextmanager
    async def _node_phase(self, job_id: str, niche: str, node_type: str, progress_range: tuple[int, int] = (0, 100)):
        """Context manager for pipeline node phases — automatically sends ACTIVE/COMPLETED/FAILED."""
        start_progress, end_progress = progress_range
        await self._update_node_status(job_id, niche, node_type, NodeStatus.ACTIVE, start_progress)
        try:
            yield
            await self._update_node_status(job_id, niche, node_type, NodeStatus.COMPLETED, end_progress)
        except Exception as e:
            await self._update_node_status(job_id, niche, node_type, NodeStatus.FAILED, start_progress, error=str(e))
            raise

    async def _validate_inputs(
        self,
        visual_paths: list[str],
        voiceover_paths: list[str],
        music_path: str | None,
    ) -> list[str]:
        """Validate input paths for existence (except remote HTTP URIs)."""
        def check_existence() -> list[str]:
            validation_errors = []
            for i, path in enumerate(visual_paths or []):
                if not path.startswith("http") and not os.path.exists(path):
                    validation_errors.append(f"Visual clip {i} not found: {path}")

            for i, path in enumerate(voiceover_paths or []):
                if not path.startswith("http") and not os.path.exists(path):
                    validation_errors.append(f"Voiceover clip {i} not found: {path}")

            if music_path and not music_path.startswith("http") and not os.path.exists(music_path):
                validation_errors.append(f"Music file not found: {music_path}")
            return validation_errors

        return await asyncio.to_thread(check_existence)


    async def _determine_video_vibe(
        self,
        job_id: str,
        niche: str,
        style: str,
        blueprint_id: str,
        num_clips: int,
    ) -> dict[str, Any]:
        """Primary vibe check using Dify, with LangChain fallback."""
        return await determine_video_vibe(job_id, niche, style, blueprint_id, num_clips)

    def _get_frame_count(self, path: str) -> int | None:
        """Get the number of frames in a video clip."""
        if path.startswith("http"):
            return 300  # Default for testing
        if not os.path.exists(path):
            return None
        try:
            info = probe_video(path)
            return info.frame_count if info else None
        except Exception as e:
            self.logger.warning(f"Failed to get frame count for {path}: {e}")
            return None

    async def _source_fill_clips(
        self, niche: str, count: int = 4
    ) -> list[str]:
        """Source additional clips to fill duration gaps between sourced
        footage and probed audio length (Phase 10-05 quick-win).

        Uses stock service with niche fallback.  Returns local file paths.
        """
        from src.services.video_engine.stock_service import base_stock_service

        paths: list[str] = []
        urls = await base_stock_service.fetch_b_roll(niche, count=count)
        for url in urls:
            path = await base_stock_service.download_stock_video(url)
            if path and os.path.exists(path) and os.path.getsize(path) > 1024:
                paths.append(path)
        if not paths:
            # Last-resort fallback with generic niche prompt
            fallback_urls = await base_stock_service.fetch_b_roll(
                f"{niche} video", count=count
            )
            for url in fallback_urls:
                path = await base_stock_service.download_stock_video(url)
                if path and os.path.exists(path) and os.path.getsize(path) > 1024:
                    paths.append(path)
        self.logger.info(
            "[Nexus] Fill-clip sourcing: acquired %d/%d paths for niche '%s'",
            len(paths), count, niche,
        )
        return paths

    async def _prepare_remotion_clips(self, visual_paths: list[str]) -> list[dict[str, Any]]:
        """Parallelize metadata extraction via threads to avoid blocking the event loop."""
        counts = await asyncio.gather(
            *[asyncio.to_thread(self._get_frame_count, v_path) for v_path in visual_paths]
        )

        remotion_clips = []
        for v_path, count in zip(visual_paths, counts):
            if count is not None:
                remotion_clips.append({"url": v_path, "duration_in_frames": count})
            else:
                self.logger.warning(f"Skipping invalid clip: {v_path}")
        return remotion_clips

    def _extract_audit_frame(self, clip: dict, v_path: str) -> Any | None:
        """Extract a middle frame from the video clip for audit."""
        clip_frames = clip.get("duration_in_frames", 0)
        frame_idx = clip_frames // 2 if clip_frames else None
        return extract_frame(v_path, frame_idx)

    async def _evaluate_frame_relevance(self, frame_path: str, prompt: str) -> str:
        """Use LLM to evaluate the relevance of the frame image."""
        from src.services.llm.service import unified_llm_service, LLMProvider

        try:
            audit_result = await unified_llm_service.analyze_image(frame_path, prompt)
            if "error" in audit_result or not audit_result.get("content"):
                raise RuntimeError("Gemini vision audit failed")
        except Exception as e:
            self.logger.warning(
                f"[Nexus] Gemini vision failed, falling back to Ollama: {e}"
            )
            from src.api.config import settings as app_settings
            audit_result = await unified_llm_service.analyze_image(
                frame_path,
                prompt,
                provider=LLMProvider.OLLAMA,
                model=app_settings.OLLAMA_MODEL,
            )
        return audit_result.get("content", "YES").upper()

    async def _run_vision_audit(
        self,
        job_id: str,
        niche: str,
        script_segments: list[dict],
        remotion_clips: list[dict],
    ) -> list[dict[str, Any]]:
        """Perform vision audit to verify clip relevance."""
        import shutil

        # Use a process-local secure temporary directory for audit frames
        audit_dir = self._local_temp_dir / "audit"
        audit_dir.mkdir(parents=True, exist_ok=True)
        audited_clips = []

        try:
            for i, clip in enumerate(remotion_clips):
                try:
                    v_path = clip["url"]
                    if v_path.startswith("http"):
                        self.logger.info(f"[Nexus] Skipping vision audit for remote clip {i}")
                        audited_clips.append(clip)
                        continue

                    # Extract frame
                    frame_img = await asyncio.to_thread(self._extract_audit_frame, clip, v_path)
                    if frame_img is None:
                        audited_clips.append(clip)
                        continue

                    # Securely write the frame file inside our private directory
                    frame_path = str(audit_dir / f"frame_{job_id}_{i}.jpg")
                    await asyncio.to_thread(cv2.imwrite, frame_path, frame_img)

                    # Build prompt
                    script_context = (
                        script_segments[i].get("text", "") if i < len(script_segments) else niche
                    )
                    prompt = (
                        f"Does this video frame match the description: '{script_context}'? "
                        "Answer with YES or NO followed by a 5-word reason."
                    )

                    # Evaluate relevance
                    relevance = await self._evaluate_frame_relevance(frame_path, prompt)

                    if "NO" in relevance:
                        self.logger.warning(f"[Nexus] Clip {i} failed audit: {relevance}")
                    else:
                        self.logger.info(f"[Nexus] Clip {i} passed audit.")

                    audited_clips.append(clip)
                except Exception as e:
                    self.logger.warning(f"Vision audit failed for clip {i}: {e}")
                    audited_clips.append(clip)
        finally:
            # Safely cleanup the temp directory and its contents
            shutil.rmtree(str(audit_dir), ignore_errors=True)

        return audited_clips

    def _modulate_video_style(
        self,
        job_id: str,
        style: str,
        style_config: dict[str, Any],
        job_metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Apply stochastic style modulation."""
        return modulate_video_style(job_id, style, style_config, job_metadata)

    def _source_music(self, music_path: str | None, music_keywords: list[str]) -> str | None:
        """Auto-sources background music from library if not provided."""
        return source_music(music_path, music_keywords)

    async def _stitch_voiceovers(
        self,
        job_id: str,
        voiceover_paths: list[str],
        music_path: str | None,
    ) -> str | None:
        """Concatenate voiceover clips into a single master file."""
        voice_dir = self._local_temp_dir / "voice"
        voice_dir.mkdir(parents=True, exist_ok=True)
        master_voiceover = str(voice_dir / f"master_{job_id}.mp3")

        if len(voiceover_paths or []) > 1:
            self.logger.info(f"[Nexus] Stitching {len(voiceover_paths)} voiceovers...")
            list_path = str(voice_dir / f"list_{job_id}.txt")

            def write_voiceover_list():
                with open(list_path, "w") as f:
                    for vp in voiceover_paths:
                        f.write(f"file '{os.path.abspath(vp)}'\n")

            await asyncio.to_thread(write_voiceover_list)
            await asyncio.to_thread(
                _run_subprocess,
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_path,
                    "-c",
                    "copy",
                    master_voiceover,
                ],
            )
            return master_voiceover
        else:
            return voiceover_paths[0] if voiceover_paths else music_path

    async def _determine_total_frames(
        self,
        audio_uri: str | None,
        remotion_clips: list[dict],
    ) -> int:
        """Determine duration in frames by probing the master audio."""
        try:
            probe_target = audio_uri if audio_uri and os.path.exists(audio_uri) else None
            if probe_target:
                res = await asyncio.to_thread(
                    _run_subprocess,
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        probe_target,
                    ],
                    text=True,
                )
                total_duration_sec = float(res.stdout.strip())
                # Add 2 seconds buffer for the Outtro to prevent sudden cutoff
                return int((total_duration_sec + 2.0) * 30)
        except Exception as e:
            self.logger.error(f"[Nexus] Duration probe failed: {e}")

        return sum(c["duration_in_frames"] for c in remotion_clips)

    async def _transcribe_master_audio(self, audio_uri: str | None) -> list[dict[str, Any]]:
        """Get word-level transcription for dynamic captions."""
        if audio_uri and os.path.exists(audio_uri):
            from src.services.audio.transcription_service import base_transcription_service

            self.logger.info("[Nexus] Transcribing master audio for dynamic captions...")
            try:
                transcript_data = await base_transcription_service.transcribe(audio_uri)
                return transcript_data.get("words", [])
            except Exception as e:
                self.logger.error(f"[Nexus] Transcription failed: {e}")
        return []

    def _export_srt(
        self, words: list[dict[str, Any]], output_path: str
    ) -> str | None:
        """Export word-level timestamps as an SRT subtitle sidecar file."""
        return export_srt(words, output_path)

    async def _extract_thumbnail(self, job_id: str, visual_paths: list[str]) -> str:
        """Extract a thumbnail from the first clip."""
        return await extract_thumbnail(self._local_temp_dir, job_id, visual_paths)

    async def _publish_and_cleanup(
        self,
        niche: str,
        rendered_path: str,
        props: dict,
        job_metadata: dict[str, Any] | None,
        vibe_data: dict,
    ) -> tuple[float, list[dict]]:
        """Log stats, publish to selected platforms, and clean up temporary paths."""
        publish_results = []

        # Extract final metadata for reporting
        try:
            info = probe_video(rendered_path)
            if info:
                final_duration = info.duration
                self.logger.info(
                    f"[Nexus] Final video stats: {final_duration:.1f}s, {info.fps:.1f} fps"
                )
            else:
                final_duration = 0
        except Exception as e:
            self.logger.warning(f"Failed to extract final video metadata: {e}")
            final_duration = 0

        # One-Click Publishing
        if job_metadata and job_metadata.get("auto_publish", False):
            from src.services.distribution.publishing import base_publishing_service

            platforms = job_metadata.get("platforms", ["youtube"])

            for platform in platforms:
                try:
                    self.logger.info(f"[Nexus] One-Click Publishing to {platform}...")
                    result = await base_publishing_service.publish_to_platform(
                        user_id=job_metadata.get("user_id", "system"),
                        platform=platform,
                        video_path=rendered_path,
                        metadata={
                            "title": props["title"],
                            "description": props.get("subtitle", ""),
                            "tags": [niche, "ettametta", vibe_data.get("vibe", "viral")],
                        },
                        use_automation=True,
                    )
                    publish_results.append(result)
                except Exception as e:
                    self.logger.error(f"[Nexus] Publishing to {platform} failed: {e}")
                    publish_results.append(
                        {"platform": platform, "status": "failed", "error": str(e)}
                    )

        # Temp Cleanup: Remove intermediate files
        try:
            for rel_dir in ["voice", "audit", "thumbnails"]:
                temp_dir = self._local_temp_dir / rel_dir
                if temp_dir.exists():
                    shutil.rmtree(str(temp_dir), ignore_errors=True)
        except Exception as e:
            self.logger.warning(f"[Nexus] Temp cleanup failed: {e}")

        return final_duration, publish_results

    async def assemble_video(
        self,
        job_id: str,
        niche: str,
        script_segments: list[dict],
        voiceover_paths: list[str],
        visual_paths: list[str],
        music_path: str | None = None,
        blueprint_id: str = "story-factory",
        style: str = "CINEMATIC_DOC",
        job_metadata: dict[str, Any] | None = None,
        preview_mode: bool = False,
    ) -> str:
        """
        High-fidelity video assembly using Remotion React engine with node-level tracking.
        Hardened: Includes OTEL spans, JobStateMachine integration, and Asset Validation.
        """
        with tracer.start_as_current_span("Nexus.assemble_video") as span:
            span.set_attribute("job_id", job_id)
            span.set_attribute("niche", niche)
            span.set_attribute("style", style)

        from src.services.nexus_engine.blueprints import get_blueprint_by_id
        from src.api.utils.database import async_session_factory

        start_time = time.time()
        self.logger.info(f"[Nexus] Starting assembly for Job {job_id}")

        try:
            async with async_session_factory() as db:
                blueprint = await get_blueprint_by_id(db, blueprint_id)

            self.logger.info(
                f"[Nexus] Using blueprint: {blueprint['name']} for Job {job_id}"
            )

            # 1. Ingress Node - Validate inputs
            async with self._node_phase(job_id, niche, "ingress", (20, 30)):
                validation_errors = await self._validate_inputs(
                    visual_paths, voiceover_paths, music_path
                )
                if validation_errors:
                    raise RuntimeError(f"Input validation failed: {'; '.join(validation_errors)}")

            # 2. Cognition Node - Extract metadata and prepare clips
            vibe_data = None
            remotion_clips = []
            async with self._node_phase(job_id, niche, "cognition", (40, 50)):
                vibe_data = await self._determine_video_vibe(
                    job_id, niche, style, blueprint_id, len(visual_paths or [])
                )
                remotion_clips = await self._prepare_remotion_clips(visual_paths or [])
                if not remotion_clips:
                    raise RuntimeError("No valid video clips available for assembly")

            # 2.6 Vision Audit Node (Free Tier - Gemini Flash)
            async with self._node_phase(job_id, niche, "vision_audit", (55, 60)):
                self.logger.info(f"[Nexus] Auditing {len(remotion_clips)} clips for relevance...")
                audited_clips = await self._run_vision_audit(
                    job_id, niche, script_segments, remotion_clips
                )

            # 3. Synthesis Node - Render with Remotion
            await self._update_node_status(job_id, niche, "synthesis", NodeStatus.ACTIVE, 70)

            # Fetch style config once for all downstream usage
            style_config = get_style(style)
            style_config = self._modulate_video_style(job_id, style, style_config, job_metadata)

            music_keywords = style_config.get("music_keywords", [])
            remotion_flags = style_config.get("remotion_flags", {})

            # Detect CTAs for visual overlays
            cta_segment = next(
                (s for s in script_segments if s.get("type") in ["engagement", "cta"]),
                None,
            )

            # Fallback: if no explicit CTA segment, use the last segment as CTA
            if not cta_segment and script_segments:
                cta_segment = script_segments[-1]
            cta_props = {}
            if cta_segment:
                cta_props = {
                    "show_cta_overlay": True,
                    "cta_type": cta_segment.get("type"),
                    "cta_text": cta_segment.get("text", "")[:50],  # Keep it short for overlay
                }

            # 2.5 Music Sourcing Node
            music_path = self._source_music(music_path, music_keywords)

            # Concatenate all voiceovers into a single master file
            audio_uri = await self._stitch_voiceovers(job_id, voiceover_paths or [], music_path)

            # Calculate total duration for Remotion
            total_frames = await self._determine_total_frames(audio_uri, audited_clips)

            # Cap frame count to prevent excessively long renders (max ~100s at 30fps)
            max_frames = settings.MAX_RENDER_FRAMES
            if total_frames > max_frames:
                self.logger.warning(
                    f"[Nexus] Capping total_frames from {total_frames} to {max_frames} "
                    f"(MAX_RENDER_FRAMES={max_frames})"
                )
                total_frames = max_frames

            # ── Phase 10-05: Duration-aware clip sourcing & even-stretching ──
            # If sourced clips don't cover the probed audio duration, source
            # extra fill clips and evenly distribute the total frame budget
            # across all clips.  This eliminates the naive looping in the
            # Remotion composition.
            total_clip_frames = sum(
                c["duration_in_frames"] for c in audited_clips
            )
            if (
                total_clip_frames > 0
                and total_clip_frames < total_frames * 0.7
            ):
                gap_pct = (1 - total_clip_frames / max(total_frames, 1)) * 100
                self.logger.info(
                    "[Nexus] Clip coverage gap: %.0f%% (%d/%d frames). "
                    "Sourcing fill clips...",
                    gap_pct, total_clip_frames, total_frames,
                )
                extra_count = max(
                    3, int(total_frames / 90) - len(audited_clips)
                )
                extra_paths = await self._source_fill_clips(
                    niche, count=extra_count
                )
                if extra_paths:
                    extra_clips = await self._prepare_remotion_clips(
                        extra_paths
                    )
                    audited_clips.extend(extra_clips)
                    self.logger.info(
                        "[Nexus] Added %d fill clips (now %d total)",
                        len(extra_clips), len(audited_clips),
                    )

            # Even-distribute clip durations to exactly fill the audio
            if audited_clips and total_frames > 0:
                per_clip = total_frames / len(audited_clips)
                for clip in audited_clips:
                    clip["duration_in_frames"] = int(per_clip)
                self.logger.info(
                    "[Nexus] Even-stretched %d clips to %.0f frames each "
                    "(total=%d)",
                    len(audited_clips), per_clip, total_frames,
                )

            # 2.6 Word-level Transcription Node
            word_timestamps = await self._transcribe_master_audio(audio_uri)

            # ── Phase 10-05: Export SRT captions ──
            srt_path: str | None = None
            if word_timestamps and audio_uri:
                srt_path = (
                    audio_uri.replace(".mp3", ".srt")
                    .replace(".wav", ".srt")
                )
                self._export_srt(word_timestamps, srt_path)

            # 2.7 Thumbnail Extraction Node
            thumbnail_path = await self._extract_thumbnail(job_id, visual_paths or [])

            # Final Props Preparation
            props = {
                "title": niche.title(),
                "subtitle": vibe_data.get("explanation", "Analysis & Insights"),
                "vibe": vibe_data.get("vibe", "Neutral"),
                "filter_override": vibe_data.get("filter_override"),
                "clips": audited_clips,
                "audio_url": audio_uri,
                "job_id": job_id,
                "trademark_url": (job_metadata or {}).get("trademark_url", "assets/logo.png"),
                "brand_name": "EttaMetta",
                "primary_color": vibe_data.get("primary_color", "#00D4FF"),
                "vignette_intensity": 0.6,
                "grain_opacity": 0.08,
                "video_duration_frames": int(total_frames),
                "duration_in_frames": int(total_frames),
                "style": style,
                "words": word_timestamps,
                "timeline": script_segments,
                "job_metadata": {**(job_metadata or {}), **remotion_flags},
                **cta_props,
            }

            # ── Phase 10-05: Preview mode (fast draft render) ──
            if preview_mode:
                preview_frame_cap = 900  # 30 seconds at 30fps
                if total_frames > preview_frame_cap:
                    self.logger.info(
                        "[Nexus] Preview mode: capping total_frames "
                        "from %d to %d for fast draft",
                        total_frames, preview_frame_cap,
                    )
                    total_frames = preview_frame_cap
                    props["video_duration_frames"] = preview_frame_cap
                    props["duration_in_frames"] = preview_frame_cap
                    # Re-stretch clips to match the capped frame budget
                    if audited_clips:
                        per_clip = total_frames / len(audited_clips)
                        for clip in audited_clips:
                            clip["duration_in_frames"] = int(per_clip)
                props["preview_mode"] = True
                if "job_metadata" in props and isinstance(
                    props["job_metadata"], dict
                ):
                    props["job_metadata"]["remotion_scale"] = 0.5

            # Ensure all numeric properties in clips are integers
            for clip in props.get("clips", []):
                if "duration_in_frames" in clip:
                    clip["duration_in_frames"] = int(clip["duration_in_frames"])

            # Resolve composition_id: style map > blueprint > default ViralClip
            resolved_composition = COMPOSITION_STYLE_MAP.get(
                style, blueprint.get("composition_id", "ViralClip")
            )

            # ── Short-form composition handling ──────────────────────
            # Compositions with 120-frame defaults (CinematicPortal,
            # CinematicCyberpunk, etc.) only accept minimal props and
            # have a fixed short duration.  Simplify the props and cap
            # total_frames accordingly.
            if resolved_composition in SHORT_FORM_COMPOSITIONS:
                short_max_frames = 120
                if total_frames > short_max_frames:
                    self.logger.info(
                        "[Nexus] Short-form composition %s: capping "
                        "total_frames from %d to %d",
                        resolved_composition, total_frames, short_max_frames,
                    )
                    total_frames = short_max_frames

                # Rebuild props for short-form composition
                # (only title, subtitle, video_url, audio_url, cta)
                # Don't pass duration_in_frames — short-form compositions
                # have their defaults in Root.tsx (e.g. 120 frames for
                # CinematicPortal). Passing --frames 0-120 would request
                # frame 120 which is out of range (0-119).
                props = {
                    "title": niche.title(),
                    "subtitle": vibe_data.get("explanation", "Analysis & Insights"),
                    "video_url": props.get("video_url") or (
                        props.get("clips", [{}])[0].get("url")
                        if props.get("clips") else None
                    ),
                    "audio_url": audio_uri,
                    "primary_color": vibe_data.get("primary_color", "#00D4FF"),
                    "style": style,
                    "job_metadata": {**(job_metadata or {}), **remotion_flags},
                    **cta_props,
                }
            elif resolved_composition not in FULL_FORM_COMPOSITIONS:
                # Unknown composition — keep ViralClip-style props but
                # log a warning so we catch mismatches early
                self.logger.warning(
                    "[Nexus] Unknown composition '%s' for style '%s', "
                    "passing full props (may be ignored by template)",
                    resolved_composition, style,
                )

            output_filename = f"nexus_{job_id}_{niche.replace(' ', '_')}.mp4"
            rendered_path = await self._retry_remotion_render(
                composition_id=resolved_composition,
                props=props,
                output_name=output_filename,
            )

            if not rendered_path:
                await self._update_node_status(
                    job_id,
                    niche,
                    "synthesis",
                    NodeStatus.FAILED,
                    60,
                    "Remotion render returned no path",
                )
                raise RuntimeError("Remotion render failed after multiple attempts")

            # Verify rendered file exists and has content
            if not os.path.exists(rendered_path) or os.path.getsize(rendered_path) < 1024:
                await self._update_node_status(
                    job_id,
                    niche,
                    "synthesis",
                    NodeStatus.FAILED,
                    60,
                    "Rendered file is invalid or empty",
                )
                raise RuntimeError("Rendered file is invalid")

            await self._update_node_status(job_id, niche, "synthesis", NodeStatus.COMPLETED, 90)

            # 4. Egress Node - Automated Publishing & Final Stats
            async with self._node_phase(job_id, niche, "egress", (95, 100)):
                final_duration, publish_results = await self._publish_and_cleanup(
                    niche,
                    rendered_path,
                    props,
                    job_metadata,
                    vibe_data,
                )

                total_time = time.time() - start_time
                self.logger.info(
                    f"[Nexus] Pipeline completed for Job {job_id} in {total_time:.1f}s"
                )
                return rendered_path

        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(
                f"[Nexus] Assembly Failed for Job {job_id} after {total_time:.1f}s: {e}"
            )
            from src.api.routes.ws import notify_nexus_job_update_sync

            notify_nexus_job_update_sync(
                {
                    "id": str(job_id),
                    "status": NodeStatus.FAILED.value,
                    "progress": 0,
                    "error": str(e),
                    "timestamp": time.time(),
                }
            )
            raise e

base_nexus_service = NexusOrchestrator()
