import os
import logging
import asyncio
import time
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict

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

COMPOSITION_STYLE_MAP: dict[str, str] = {
    "CINEMATIC_DOC": "CinematicAncient",
    "VOX_EXPLAINER": "CinematicAncient",
    "DEEP_DIVE": "CinematicAncient",
    "STOIC_WISDOM": "CinematicAncient",
    "NOIR_MYSTERY": "CinematicMinimal",
    "INVESTIGATION": "CinematicMinimal",
    "RETRO_ARCHIVE": "CinematicMinimal",
    "HORROR_CREEPY": "CinematicMinimal",
    "FAST_HYPE": "CinematicCyberpunk",
    "ESPORTS_HYPE": "CinematicCyberpunk",
    "GAMING_LORE": "CinematicCyberpunk",
    "FITNESS_MOTIVATION": "CinematicCyberpunk",
    "TOP_LISTICLE": "CinematicCyberpunk",
    "MOTIVATIONAL": "CinematicKinetic",
    "HEARTFELT_NARRATIVE": "CinematicKinetic",
    "RELATIONSHIP_DRAMA": "CinematicIridescent",
    "TRAVEL_VLOG": "CinematicLiquid",
    "PRODUCT_SHOWCASE": "Cinematic3D",
    "CULINARY_MASTERCLASS": "CinematicMinimal",
    "ULTIMATE_TUTORIAL": "CinematicMinimal",
    "REDDIT_STORY": "ViralClip",
    "PERSONA_MONTAGE": "ViralClip",
    "BROADCAST_NEWS": "ViralClip",
    "REACTION_COMMENTARY": "ViralClip",
    "LOFI_CHILL": "ViralClip",
    "PODCAST_SIM": "ViralClip",
}

SHORT_FORM_COMPOSITIONS: set[str] = {
    "CinematicIridescent",
    "CinematicPortal",
    "CinematicCyberpunk",
    "CinematicLiquid",
    "CinematicPrism",
    "CinematicLidar",
    "CinematicKinetic",
}

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
    return subprocess.run(
        args,
        capture_output=capture_output,
        text=text,
        check=check,
        cwd=cwd,
    )


class VibeAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger("VibeAnalyzer")

    async def determine_vibe(
        self, job_id: str, niche: str, style: str, blueprint_id: str, num_clips: int,
    ) -> dict[str, Any]:
        return await determine_video_vibe(job_id, niche, style, blueprint_id, num_clips)

    def _extract_audit_frame(self, clip: dict, v_path: str) -> Any | None:
        clip_frames = clip.get("duration_in_frames", 0)
        frame_idx = clip_frames // 2 if clip_frames else None
        return extract_frame(v_path, frame_idx)

    async def _evaluate_frame_relevance(self, frame_path: str, prompt: str) -> str:
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

    async def run_vision_audit(
        self,
        job_id: str,
        niche: str,
        script_segments: list[dict],
        remotion_clips: list[dict],
        temp_dir: Path,
    ) -> list[dict[str, Any]]:
        audit_dir = temp_dir / "audit"
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

                    frame_img = await asyncio.to_thread(self._extract_audit_frame, clip, v_path)
                    if frame_img is None:
                        audited_clips.append(clip)
                        continue

                    frame_path = str(audit_dir / f"frame_{job_id}_{i}.jpg")
                    await asyncio.to_thread(cv2.imwrite, frame_path, frame_img)

                    script_context = (
                        script_segments[i].get("text", "") if i < len(script_segments) else niche
                    )
                    prompt = (
                        f"Does this video frame match the description: '{script_context}'? "
                        "Answer with YES or NO followed by a 5-word reason."
                    )

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
            shutil.rmtree(str(audit_dir), ignore_errors=True)

        return audited_clips


class AssetManager:
    def __init__(self):
        self.logger = logging.getLogger("AssetManager")

    async def validate_inputs(
        self,
        visual_paths: list[str],
        voiceover_paths: list[str],
        music_path: str | None,
    ) -> list[str]:
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

    def get_frame_count(self, path: str) -> int | None:
        if path.startswith("http"):
            return 300
        if not os.path.exists(path):
            return None
        try:
            info = probe_video(path)
            return info.frame_count if info else None
        except Exception as e:
            self.logger.warning(f"Failed to get frame count for {path}: {e}")
            return None

    async def source_fill_clips(self, niche: str, count: int = 4) -> list[str]:
        from src.services.video_engine.stock_service import base_stock_service

        paths: list[str] = []
        urls = await base_stock_service.fetch_b_roll(niche, count=count)
        for url in urls:
            path = await base_stock_service.download_stock_video(url)
            if path and os.path.exists(path) and os.path.getsize(path) > 1024:
                paths.append(path)
        if not paths:
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

    async def prepare_remotion_clips(self, visual_paths: list[str]) -> list[dict[str, Any]]:
        counts = await asyncio.gather(
            *[asyncio.to_thread(self.get_frame_count, v_path) for v_path in visual_paths]
        )

        remotion_clips = []
        for v_path, count in zip(visual_paths, counts):
            if count is not None:
                remotion_clips.append({"url": v_path, "duration_in_frames": count})
            else:
                self.logger.warning(f"Skipping invalid clip: {v_path}")
        return remotion_clips

    async def stitch_voiceovers(
        self,
        job_id: str,
        voiceover_paths: list[str],
        music_path: str | None,
        temp_dir: Path,
    ) -> str | None:
        voice_dir = temp_dir / "voice"
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

    async def determine_total_frames(
        self,
        audio_uri: str | None,
        remotion_clips: list[dict],
    ) -> int:
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
                return int((total_duration_sec + 2.0) * 30)
        except Exception as e:
            self.logger.error(f"[Nexus] Duration probe failed: {e}")

        return sum(c["duration_in_frames"] for c in remotion_clips)

    async def transcribe_master_audio(self, audio_uri: str | None) -> list[dict[str, Any]]:
        if audio_uri and os.path.exists(audio_uri):
            from src.services.audio.transcription_service import base_transcription_service

            self.logger.info("[Nexus] Transcribing master audio for dynamic captions...")
            try:
                transcript_data = await base_transcription_service.transcribe(audio_uri)
                return transcript_data.get("words", [])
            except Exception as e:
                self.logger.error(f"[Nexus] Transcription failed: {e}")
        return []

    def source_music(self, music_path: str | None, music_keywords: list[str]) -> str | None:
        return source_music(music_path, music_keywords)

    def modulate_video_style(
        self,
        job_id: str,
        style: str,
        style_config: dict[str, Any],
        job_metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return modulate_video_style(job_id, style, style_config, job_metadata)


class RenderPipeline:
    def __init__(self):
        self.logger = logging.getLogger("RenderPipeline")
        self.remotion_breaker = CircuitBreaker(name="NexusRemotion")

    async def retry_remotion_render(
        self, composition_id: str, props: Dict, output_name: str
    ) -> str | None:
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
                render_timeout = settings.LLM_TIMEOUT * 60

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

    def export_srt(
        self, words: list[dict[str, Any]], output_path: str
    ) -> str | None:
        return export_srt(words, output_path)

    async def extract_thumbnail(self, temp_dir: Path, job_id: str, visual_paths: list[str]) -> str:
        return await extract_thumbnail(temp_dir, job_id, visual_paths)


class NexusOrchestrator:
    def __init__(self, output_dir: str = "outputs/nexus"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.logger = logging.getLogger("NexusOrchestrator")
        self.vibe_analyzer = VibeAnalyzer()
        self.asset_manager = AssetManager()
        self.render_pipeline = RenderPipeline()

        self.dependencies_available = {
            "moviepy": MOVIEPY_AVAILABLE,
        }

        if not self.dependencies_available["moviepy"]:
            self.logger.warning(
                "NexusOrchestrator: moviepy not available. Video processing features disabled."
            )

    @property
    def _local_temp_dir(self) -> Path:
        p = Path.cwd() / "tmp" / "ettametta"
        p.mkdir(parents=True, exist_ok=True)
        return p

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
        start_progress, end_progress = progress_range
        await self._update_node_status(job_id, niche, node_type, NodeStatus.ACTIVE, start_progress)
        try:
            yield
            await self._update_node_status(job_id, niche, node_type, NodeStatus.COMPLETED, end_progress)
        except Exception as e:
            await self._update_node_status(job_id, niche, node_type, NodeStatus.FAILED, start_progress, error=str(e))
            raise

    async def _phase_ingress(
        self,
        job_id: str,
        niche: str,
        visual_paths: list[str],
        voiceover_paths: list[str],
        music_path: str | None,
    ) -> None:
        async with self._node_phase(job_id, niche, "ingress", (20, 30)):
            validation_errors = await self.asset_manager.validate_inputs(
                visual_paths, voiceover_paths, music_path
            )
            if validation_errors:
                raise RuntimeError(f"Input validation failed: {'; '.join(validation_errors)}")

    async def _phase_cognition(
        self,
        job_id: str,
        niche: str,
        style: str,
        blueprint_id: str,
        visual_paths: list[str],
        script_segments: list[dict],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        vibe_data = None
        remotion_clips = []

        async with self._node_phase(job_id, niche, "cognition", (40, 50)):
            vibe_data = await self.vibe_analyzer.determine_vibe(
                job_id, niche, style, blueprint_id, len(visual_paths or [])
            )
            remotion_clips = await self.asset_manager.prepare_remotion_clips(visual_paths or [])
            if not remotion_clips:
                raise RuntimeError("No valid video clips available for assembly")

        async with self._node_phase(job_id, niche, "vision_audit", (55, 60)):
            self.logger.info(f"[Nexus] Auditing {len(remotion_clips)} clips for relevance...")
            remotion_clips = await self.vibe_analyzer.run_vision_audit(
                job_id, niche, script_segments, remotion_clips, self._local_temp_dir
            )

        return vibe_data, remotion_clips

    async def _phase_synthesis(
        self,
        job_id: str,
        niche: str,
        style: str,
        vibe_data: dict[str, Any],
        remotion_clips: list[dict[str, Any]],
        script_segments: list[dict],
        voiceover_paths: list[str],
        music_path: str | None,
        job_metadata: dict[str, Any] | None,
        preview_mode: bool,
        blueprint: dict[str, Any],
    ) -> tuple[str, dict[str, Any], int]:
        async with self._node_phase(job_id, niche, "synthesis", (70, 90)):
            style_config = get_style(style)
            style_config = self.asset_manager.modulate_video_style(
                job_id, style, style_config, job_metadata
            )

            music_keywords = style_config.get("music_keywords", [])
            remotion_flags = style_config.get("remotion_flags", {})

            cta_segment = next(
                (s for s in script_segments if s.get("type") in ["engagement", "cta"]),
                None,
            )
            if not cta_segment and script_segments:
                cta_segment = script_segments[-1]
            cta_props = {}
            if cta_segment:
                cta_props = {
                    "show_cta_overlay": True,
                    "cta_type": cta_segment.get("type"),
                    "cta_text": cta_segment.get("text", "")[:50],
                }

            music_path = self.asset_manager.source_music(music_path, music_keywords)

            audio_uri = await self.asset_manager.stitch_voiceovers(
                job_id, voiceover_paths or [], music_path, self._local_temp_dir
            )

            total_frames = await self.asset_manager.determine_total_frames(
                audio_uri, remotion_clips
            )

            max_frames = settings.MAX_RENDER_FRAMES
            if total_frames > max_frames:
                self.logger.warning(
                    f"[Nexus] Capping total_frames from {total_frames} to {max_frames} "
                    f"(MAX_RENDER_FRAMES={max_frames})"
                )
                total_frames = max_frames

            total_clip_frames = sum(
                c["duration_in_frames"] for c in remotion_clips
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
                    3, int(total_frames / 90) - len(remotion_clips)
                )
                extra_paths = await self.asset_manager.source_fill_clips(
                    niche, count=extra_count
                )
                if extra_paths:
                    extra_clips = await self.asset_manager.prepare_remotion_clips(
                        extra_paths
                    )
                    remotion_clips.extend(extra_clips)
                    self.logger.info(
                        "[Nexus] Added %d fill clips (now %d total)",
                        len(extra_clips), len(remotion_clips),
                    )

            if remotion_clips and total_frames > 0:
                per_clip = total_frames / len(remotion_clips)
                for clip in remotion_clips:
                    clip["duration_in_frames"] = int(per_clip)
                self.logger.info(
                    "[Nexus] Even-stretched %d clips to %.0f frames each "
                    "(total=%d)",
                    len(remotion_clips), per_clip, total_frames,
                )

            word_timestamps = await self.asset_manager.transcribe_master_audio(audio_uri)

            srt_path: str | None = None
            if word_timestamps and audio_uri:
                srt_path = (
                    audio_uri.replace(".mp3", ".srt")
                    .replace(".wav", ".srt")
                )
                self.render_pipeline.export_srt(word_timestamps, srt_path)

            thumbnail_path = await self.render_pipeline.extract_thumbnail(
                self._local_temp_dir, job_id, visual_paths or []
            )

            props = {
                "title": niche.title(),
                "subtitle": vibe_data.get("explanation", "Analysis & Insights"),
                "vibe": vibe_data.get("vibe", "Neutral"),
                "filter_override": vibe_data.get("filter_override"),
                "clips": remotion_clips,
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

            if preview_mode:
                preview_frame_cap = 900
                if total_frames > preview_frame_cap:
                    self.logger.info(
                        "[Nexus] Preview mode: capping total_frames "
                        "from %d to %d for fast draft",
                        total_frames, preview_frame_cap,
                    )
                    total_frames = preview_frame_cap
                    props["video_duration_frames"] = preview_frame_cap
                    props["duration_in_frames"] = preview_frame_cap
                    if remotion_clips:
                        per_clip = total_frames / len(remotion_clips)
                        for clip in remotion_clips:
                            clip["duration_in_frames"] = int(per_clip)
                props["preview_mode"] = True
                if "job_metadata" in props and isinstance(
                    props["job_metadata"], dict
                ):
                    props["job_metadata"]["remotion_scale"] = 0.5

            for clip in props.get("clips", []):
                if "duration_in_frames" in clip:
                    clip["duration_in_frames"] = int(clip["duration_in_frames"])

            resolved_composition = COMPOSITION_STYLE_MAP.get(
                style, blueprint.get("composition_id", "ViralClip")
            )

            if resolved_composition in SHORT_FORM_COMPOSITIONS:
                short_max_frames = 120
                if total_frames > short_max_frames:
                    self.logger.info(
                        "[Nexus] Short-form composition %s: capping "
                        "total_frames from %d to %d",
                        resolved_composition, total_frames, short_max_frames,
                    )
                    total_frames = short_max_frames

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
                self.logger.warning(
                    "[Nexus] Unknown composition '%s' for style '%s', "
                    "passing full props (may be ignored by template)",
                    resolved_composition, style,
                )

            output_filename = f"nexus_{job_id}_{niche.replace(' ', '_')}.mp4"
            rendered_path = await self.render_pipeline.retry_remotion_render(
                composition_id=resolved_composition,
                props=props,
                output_name=output_filename,
            )

            if not rendered_path:
                raise RuntimeError("Remotion render failed after multiple attempts")

            if not os.path.exists(rendered_path) or os.path.getsize(rendered_path) < 1024:
                raise RuntimeError("Rendered file is invalid")

            return rendered_path, props, total_frames

    async def _phase_egress(
        self,
        job_id: str,
        niche: str,
        rendered_path: str,
        props: dict,
        job_metadata: dict[str, Any] | None,
        vibe_data: dict,
    ) -> tuple[float, list[dict]]:
        async with self._node_phase(job_id, niche, "egress", (95, 100)):
            publish_results = []

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

            await self._phase_ingress(
                job_id, niche, visual_paths, voiceover_paths, music_path
            )

            vibe_data, remotion_clips = await self._phase_cognition(
                job_id, niche, style, blueprint_id, visual_paths, script_segments
            )

            rendered_path, props, total_frames = await self._phase_synthesis(
                job_id, niche, style, vibe_data, remotion_clips, script_segments,
                voiceover_paths, music_path, job_metadata, preview_mode, blueprint,
            )

            await self._phase_egress(
                job_id, niche, rendered_path, props, job_metadata, vibe_data
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
