import os
import logging
import json
from typing import Any
from pathlib import Path
import os
import asyncio
import time

# Graceful imports for optional dependencies
try:
    import moviepy

    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    moviepy = None
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from services.video_engine.processor import base_video_processor
from services.nexus_engine.audio_mixer import base_audio_mixer
from typing import Any


class CircuitBreaker:
    """Simple circuit breaker to prevent cascading failures"""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_open(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class NexusOrchestrator:
    def __init__(self, output_dir: str = "outputs/nexus"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.remotion_circuit_breaker = CircuitBreaker()
        self.logger = logging.getLogger("NexusOrchestrator")

        # Check optional dependencies
        self.dependencies_available = {
            "moviepy": MOVIEPY_AVAILABLE,
        }

        if not self.dependencies_available["moviepy"]:
            self.logger.warning(
                "NexusOrchestrator: moviepy not available. Video processing features disabled."
            )

    async def _retry_remotion_render(
        self, composition_id: str, props: dict, output_name: str
    ) -> str | None:
        """Retry wrapper for remotion render with exponential backoff"""
        if self.remotion_circuit_breaker.is_open():
            raise RuntimeError(
                "Remotion service circuit breaker is OPEN - too many failures"
            )

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(
                (TimeoutError, ConnectionError, RuntimeError)
            ),
            reraise=True,
        )
        async def _render():
            from services.video_engine.remotion_service import base_remotion_service

            try:
                result = await asyncio.wait_for(
                    base_remotion_service.render_video(
                        composition_id=composition_id,
                        props=props,
                        output_name=output_name,
                    ),
                    timeout=300,  # 5 minute hard timeout
                )
                self.remotion_circuit_breaker.record_success()
                return result
            except Exception as e:
                self.remotion_circuit_breaker.record_failure()
                raise

        try:
            return await _render()
        except Exception as e:
            self.logger.error(f"Remotion render failed after retries: {e}")
            return None

    async def assemble_video(
        self,
        job_id: str,
        niche: str,
        script_segments: list[Any],
        voiceover_paths: list[str],
        visual_paths: list[str],
        music_path: str | None = None,
        blueprint_id: str = "viral-reskin",
        user_id: str | int | None = None,
    ) -> str:
        """
        High-fidelity video assembly using Remotion React engine with node-level tracking.
        Production-grade with retries, circuit breaking, timeouts, and telemetry.
        
        Args:
            job_id: Unique job identifier
            niche: Target niche for the video
            script_segments: List of script segments with timing
            voiceover_paths: List of voiceover audio file paths
            visual_paths: List of visual/video file paths
            music_path: Optional background music path
            blueprint_id: Blueprint identifier for rendering
            user_id: User ID for brand lookup (optional, for brand identity)
        """
        from api.routes.ws import notify_nexus_job_update_sync
        from services.nexus_engine.blueprints import get_blueprint_by_id

        # Need to use async session here for get_blueprint_by_id
        from api.utils.database import async_session_factory

        start_time = time.time()
        self.logger.info(f"[Nexus] Starting assembly for Job {job_id}")

        # Use a single db session for the entire operation to keep it in scope
        async with async_session_factory() as db:
            blueprint = await get_blueprint_by_id(db, blueprint_id)
            self.logger.info(
                f"[Nexus] Using blueprint: {blueprint['name']} for Job {job_id}"
            )

            def update_node(
                node_type: str, status: str, progress: int, error: str | None = None
            ):
                payload = {
                    "id": str(job_id),
                    "status": f"{node_type.upper()}_{status}",
                    "current_node": node_type,
                    "node_status": status,
                    "progress": progress,
                    "niche": niche,
                    "timestamp": time.time(),
                }
                if error:
                    payload["error"] = error
                notify_nexus_job_update_sync(payload)

            # 1. Ingress Node - Validate inputs
            update_node("ingress", "ACTIVE", 20)

            # Validate all inputs exist before proceeding
            validation_errors = []
            for i, path in enumerate(visual_paths):
                if not os.path.exists(path):
                    validation_errors.append(f"Visual clip {i} not found: {path}")

            for i, path in enumerate(voiceover_paths):
                if not os.path.exists(path):
                    validation_errors.append(f"Voiceover clip {i} not found: {path}")

            if music_path and not os.path.exists(music_path):
                validation_errors.append(f"Music file not found: {music_path}")

            if validation_errors:
                error_msg = "; ".join(validation_errors)
                update_node("ingress", "FAILED", 20, error_msg)
                raise RuntimeError(f"Input validation failed: {error_msg}")

            update_node("ingress", "COMPLETED", 30)

            # 2. Cognition Node - Extract metadata and prepare clips
            update_node("cognition", "ACTIVE", 40)

            # Cognitive Vibe Check (LangChain Integration)
            vibe_data = {}
            from services.langchain.service import langchain_service

            if langchain_service.is_enabled():
                self.logger.info(f"[Nexus] Performing Cognitive Vibe Check for {niche}")
                vibe_data = await langchain_service.analyze_video_vibe(
                    niche,
                    {
                        "num_clips": len(visual_paths),
                        "blueprint": blueprint_id,
                        "job_id": str(job_id),
                    },
                )
                if vibe_data:
                    self.logger.info(
                        f"[Nexus] LangChain suggested vibe: {vibe_data.get('vibe')}"
                    )

            import cv2

            def get_frame_count(path: str) -> int | None:
                if not os.path.exists(path):
                    return None
                try:
                    cap = cv2.VideoCapture(path)
                    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    cap.release()
                    return count if count > 0 else None
                except Exception as e:
                    self.logger.warning(f"Failed to get frame count for {path}: {e}")
                    return None

            # Parallelize metadata extraction via threads to avoid blocking the event loop
            counts = await asyncio.gather(
                *[asyncio.to_thread(get_frame_count, v_path) for v_path in visual_paths]
            )

            remotion_clips = []
            valid_clip_count = 0
            for v_path, count in zip(visual_paths, counts):
                if count is not None:
                    remotion_clips.append({"url": v_path, "durationInFrames": count})
                    valid_clip_count += 1
                else:
                    self.logger.warning(f"Skipping invalid clip: {v_path}")

            if valid_clip_count == 0:
                update_node("cognition", "FAILED", 40, "No valid video clips found")
                raise RuntimeError("No valid video clips available for assembly")

            self.logger.info(
                f"[Nexus] Prepared {valid_clip_count} valid clips for Job {job_id}"
            )
            update_node("cognition", "COMPLETED", 50)

            # 3. Synthesis Node - Render with Remotion
            update_node("synthesis", "ACTIVE", 60)

            # Detect CTAs for visual overlays
            cta_segment = next(
                (s for s in script_segments if s.get("type") in ["engagement", "cta"]),
                None,
            )
            cta_props = {}
            if cta_segment:
                cta_props = {
                    "showCtaOverlay": True,
                    "ctaType": cta_segment.get("type"),
                    "ctaText": cta_segment.get("text", "")[:50],
                }

            # Fetch active Brand Identity (only if user_id provided)
            from services.branding.service import base_branding_service
            brand_identity = None
            brand_props = {}
            if user_id:
                try:
                    brand_identity = await base_branding_service.get_active_brand(user_id, niche, db)
                except Exception as e:
                    self.logger.warning(f"[Nexus] Brand lookup failed: {e}")
            
            if brand_identity:
                brand_props = {
                    "trademarkUrl": brand_identity.logo_url,
                    "brandName": brand_identity.brand_name,
                    "primaryColor": brand_identity.primary_color
                }

            audio_url = voiceover_paths[0] if voiceover_paths else music_path
            props = {
                "title": niche.title(),
                "subtitle": vibe_data.get("explanation", "Analysis & Insights"),
                "vibe": vibe_data.get("vibe", "Neutral"),
                "filter_override": vibe_data.get("filter_override"),
                "clips": remotion_clips,
                "audioUrl": audio_url,
                "jobId": job_id,
                **cta_props,
                **brand_props,
            }

            output_filename = f"nexus_{job_id}_{niche.replace(' ', '_')}.mp4"
            rendered_path = await self._retry_remotion_render(
                composition_id="ViralClip", props=props, output_name=output_filename
            )

            if not rendered_path:
                update_node(
                    "synthesis", "FAILED", 60, "Remotion render returned no path"
                )
                raise RuntimeError("Remotion render failed after multiple attempts")

            # Verify rendered file exists and has content
            if (
                not os.path.exists(rendered_path)
                or os.path.getsize(rendered_path) < 1024
            ):
                update_node(
                    "synthesis", "FAILED", 60, "Rendered file is invalid or empty"
                )
                raise RuntimeError("Rendered file is invalid")

            file_size_mb = os.path.getsize(rendered_path) / (1024 * 1024)
            self.logger.info(
                f"[Nexus] Render completed for Job {job_id}: {file_size_mb:.2f} MB"
            )
            update_node("synthesis", "COMPLETED", 90)

            # 4. Egress Node - Final validation and cleanup
            update_node("egress", "ACTIVE", 95)

            # Any: Post-processing, thumbnail generation, metadata extraction
            try:
                cap = cv2.VideoCapture(rendered_path)
                final_fps = cap.get(cv2.CAP_PROP_FPS)
                final_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                final_duration = final_frames / final_fps if final_fps > 0 else 0
                cap.release()

                self.logger.info(
                    f"[Nexus] Final video stats: {final_frames} frames, {final_duration:.1f}s, {final_fps:.1f} fps"
                )
            except Exception as e:
                self.logger.warning(f"Failed to extract final video metadata: {e}")

            update_node("egress", "COMPLETED", 100)

            total_time = time.time() - start_time
            self.logger.info(
                f"[Nexus] Assembly completed for Job {job_id} in {total_time:.1f}s"
            )

            return rendered_path

        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(
                f"[Nexus] Assembly Failed for Job {job_id} after {total_time:.1f}s: {e}"
            )
            notify_nexus_job_update_sync(
                {
                    "id": str(job_id),
                    "status": "FAILED",
                    "progress": 0,
                    "error": str(e),
                    "timestamp": time.time(),
                }
            )
            raise e


base_nexus_orchestrator = NexusOrchestrator()
