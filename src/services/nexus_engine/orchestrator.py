import os
import logging
import json
import asyncio
import time
import random
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
from src.services.video_engine.processor import base_video_processor
from src.services.nexus_engine.audio_mixer import base_audio_mixer
from src.services.nexus_engine.style_library import get_style
from src.shared.observability import get_logger
from src.shared.state_machine import base_state_machine, JobState

logger = get_logger(__name__)
tracer = trace.get_tracer(__name__)

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
        job_metadata: dict[str, Any] | None = None
    ) -> str:
        """
        High-fidelity video assembly using Remotion React engine with node-level tracking.
        Hardened: Includes OTEL spans, JobStateMachine integration, and Asset Validation.
        """
        with tracer.start_as_current_span("Nexus.assemble_video") as span:
            span.set_attribute("job_id", job_id)
            span.set_attribute("niche", niche)
            span.set_attribute("style", style)
        from src.api.routes.ws import notify_nexus_job_update_sync
        from src.services.nexus_engine.blueprints import get_blueprint_by_id

        # Need to use async session here for get_blueprint_by_id
        from src.api.utils.database import async_session_factory

        start_time = time.time()
        self.logger.info(f"[Nexus] Starting assembly for Job {job_id}")

        try:
            async with async_session_factory() as db:
                blueprint = await get_blueprint_by_id(db, blueprint_id)

            self.logger.info(
                f"[Nexus] Using blueprint: {blueprint['name']} for Job {job_id}"
            )

            async def update_node(
                node_type: str, status: str, progress: int, error: str | None = None, extra: dict | None = None
            ):
                # Hardened: State Machine Transition + OTEL Attribute
                state_map = {
                    "ingress": JobState.INGRESSING,
                    "cognition": JobState.COGNITION,
                    "vision_audit": JobState.COGNITION,
                    "synthesis": JobState.SYNTHESIZING,
                    "egress": JobState.PUBLISHING
                }
                
                target_state = state_map.get(node_type, JobState.RENDERING)
                if status == "FAILED":
                    await base_state_machine.transition_to(job_id, None, JobState.FAILED, {"node": node_type, "error": error})
                elif status == "ACTIVE":
                    # For rendering, we have a specific state
                    if node_type == "synthesis":
                        await base_state_machine.transition_to(job_id, JobState.COGNITION, JobState.SYNTHESIZING)
                
                payload = {
                    "id": str(job_id),
                    "status": f"{node_type.upper()}_{status}",
                    "current_node": node_type,
                    "node_status": status,
                    "progress": progress,
                    "niche": niche,
                }
                if error: payload["error"] = error
                if extra: payload.update(extra)
                
                # Still notify legacy WS for now to prevent breaking frontend
                notify_nexus_job_update_sync(payload)

            # 1. Ingress Node - Validate inputs
            with tracer.start_as_current_span("Nexus.Node.Ingress") as node_span:
                await update_node("ingress", "ACTIVE", 20)

                # Validate all inputs exist before proceeding
                validation_errors = []
                for i, path in enumerate(visual_paths):
                    if not path.startswith("http") and not os.path.exists(path):
                        validation_errors.append(f"Visual clip {i} not found: {path}")

                for i, path in enumerate(voiceover_paths):
                    if not path.startswith("http") and not os.path.exists(path):
                        validation_errors.append(f"Voiceover clip {i} not found: {path}")

                if music_path and not music_path.startswith("http") and not os.path.exists(music_path):
                    validation_errors.append(f"Music file not found: {music_path}")

                if validation_errors:
                    error_msg = "; ".join(validation_errors)
                    await update_node("ingress", "FAILED", 20, error_msg)
                    raise RuntimeError(f"Input validation failed: {error_msg}")

                await update_node("ingress", "COMPLETED", 30)

            # 2. Cognition Node - Extract metadata and prepare clips
            with tracer.start_as_current_span("Nexus.Node.Cognition") as node_span:
                await update_node("cognition", "ACTIVE", 40)

                # Cognitive Vibe Check (Dify + LangChain Integration)
                vibe_data = {}
                
                # 1. Try Dify Orchestration (Primary)
                from src.services.llm.dify_client import base_dify_client
                if settings.DIFY_API_KEY:
                    self.logger.info(f"[Nexus] Performing Dify Cognitive Analysis for {niche}")
                    try:
                        dify_resp = await base_dify_client.chat_messages(
                            query=f"Analyze the video vibe for niche: {niche}. Context: {len(visual_paths)} clips, style: {style}",
                            user_id=f"nexus_{job_id}",
                            inputs={
                                "niche": niche,
                                "num_clips": len(visual_paths),
                                "blueprint": blueprint_id,
                                "style": style
                            }
                        )
                        # Expecting Dify to return JSON in 'answer' or structured data
                        if dify_resp and "answer" in dify_resp:
                            answer = dify_resp["answer"]
                            if "{" in answer and "}" in answer:
                                try:
                                    import json as json_lib
                                    start = answer.find("{")
                                    end = answer.rfind("}") + 1
                                    vibe_data = json_lib.loads(answer[start:end])
                                    self.logger.info(f"[Nexus] Dify suggested vibe: {vibe_data.get('vibe')}")
                                except:
                                    self.logger.warning("[Nexus] Dify returned non-JSON answer, using as 'explanation'")
                                    vibe_data = {"vibe": "Cinematic", "explanation": answer}
                    except Exception as e:
                        self.logger.warning(f"[Nexus] Dify analysis failed, falling back: {e}")

                # 2. Fallback to LangChain (Secondary)
                if not vibe_data:
                    from src.services.langchain.service import langchain_service
                    if langchain_service.is_enabled():
                        self.logger.info(f"[Nexus] Performing LangChain Vibe Check for {niche}")
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

                def get_frame_count(path: str) -> int | None:
                    if path.startswith("http"):
                        return 300  # Default for testing
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
                        remotion_clips.append({"url": v_path, "duration_in_frames": count})
                        valid_clip_count += 1
                    else:
                        self.logger.warning(f"Skipping invalid clip: {v_path}")

                if valid_clip_count == 0:
                    await update_node("cognition", "FAILED", 40, "No valid video clips found")
                    raise RuntimeError("No valid video clips available for assembly")

                await update_node("cognition", "COMPLETED", 50)

            # 2.6 Vision Audit Node (Free Tier - Gemini Flash)
            with tracer.start_as_current_span("Nexus.Node.VisionAudit") as node_span:
                await update_node("vision_audit", "ACTIVE", 55)
                self.logger.info(f"[Nexus] Auditing {len(remotion_clips)} clips for relevance...")
                
                from src.services.llm.service import unified_llm_service, LLMProvider
                
                audited_clips = []
                for i, clip in enumerate(remotion_clips):
                    try:
                        # Extract a sample frame for auditing (Middle frame)
                        v_path = clip["url"]
                        if v_path.startswith("http"):
                            # For remote URLs, we skip vision audit or audit metadata
                            self.logger.info(f"[Nexus] Skipping vision audit for remote clip {i}")
                            audited_clips.append(clip)
                            continue

                        # Use CV2 to extract one frame
                        cap = cv2.VideoCapture(v_path)
                        frame_idx = count // 2 if count else 0
                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                        ret, frame_img = cap.read()
                        cap.release()

                        if ret:
                            frame_path = f"temp/audit/frame_{job_id}_{i}.jpg"
                            os.makedirs("temp/audit", exist_ok=True)
                            cv2.imwrite(frame_path, frame_img)
                            
                            # Call Gemini Vision (Free Tier)
                            script_context = script_segments[i].get("text", "") if i < len(script_segments) else niche
                            prompt = f"Does this video frame match the description: '{script_context}'? Answer with YES or NO followed by a 5-word reason."
                            
                            try:
                                audit_result = await unified_llm_service.analyze_image(frame_path, prompt)
                                if "error" in audit_result or not audit_result.get("content"):
                                    raise RuntimeError("Gemini vision audit failed")
                            except Exception as e:
                                self.logger.warning(f"[Nexus] Gemini vision failed, falling back to Ollama: {e}")
                                audit_result = await unified_llm_service.analyze_image(
                                    frame_path, prompt, provider=LLMProvider.OLLAMA, model="llama3.2-vision"
                                )
                            relevance = audit_result.get("content", "YES").upper()
                            
                            if "NO" in relevance:
                                self.logger.warning(f"[Nexus] Clip {i} failed audit: {relevance}")
                                # In v1.0 we just log, but could trigger a re-roll here
                            else:
                                self.logger.info(f"[Nexus] Clip {i} passed audit.")
                        
                        audited_clips.append(clip)
                    except Exception as e:
                        self.logger.warning(f"Vision audit failed for clip {i}: {e}")
                        audited_clips.append(clip)

                await update_node("vision_audit", "COMPLETED", 60)

            # 3. Synthesis Node - Render with Remotion
            with tracer.start_as_current_span("Nexus.Node.Synthesis") as node_span:
                await update_node("synthesis", "ACTIVE", 70)
            
            # Fetch style config once for all downstream usage
            style_config = get_style(style)
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
            if not music_path:
                from src.services.audio.sound_design import sound_design_service
                if sound_design_service.enabled:
                    mood = music_keywords[0] if music_keywords else "cinematic"
                    music_dir = Path(sound_design_service.library_path) / mood
                    if music_dir.exists():
                        tracks = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
                        if tracks:
                            music_path = str(random.choice(tracks))
                            self.logger.info(f"[Nexus] Auto-sourced music: {music_path}")

            # Concatenate all voiceovers into a single master file
            master_voiceover = f"temp/voice/master_{job_id}.mp3"
            os.makedirs("temp/voice", exist_ok=True)
            
            if len(voiceover_paths) > 1:
                self.logger.info(f"[Nexus] Stitching {len(voiceover_paths)} voiceovers...")
                list_path = f"temp/voice/list_{job_id}.txt"
                with open(list_path, "w") as f:
                    for vp in voiceover_paths:
                        f.write(f"file '{os.path.abspath(vp)}'\n")
                
                await asyncio.to_thread(subprocess.run, ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", master_voiceover], capture_output=True)
                audio_uri = master_voiceover
            else:
                audio_uri = voiceover_paths[0] if voiceover_paths else music_path

            # Calculate total duration for Remotion
            total_frames = 0
            try:
                probe_target = audio_uri if audio_uri and os.path.exists(audio_uri) else None
                if probe_target:
                    res = await asyncio.to_thread(subprocess.run, ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", probe_target], capture_output=True, text=True)
                    total_duration_sec = float(res.stdout.strip())
                    # Add 2 seconds buffer for the Outtro to prevent sudden cutoff
                    total_frames = int((total_duration_sec + 2.0) * 30)
                    self.logger.info(f"[Nexus] Master duration detected: {total_duration_sec}s -> Rendering {total_frames} frames")
                else:
                    total_frames = sum(c["duration_in_frames"] for c in remotion_clips)
            except Exception as e:
                self.logger.error(f"[Nexus] Duration probe failed: {e}")
                total_frames = sum(c["duration_in_frames"] for c in remotion_clips)

            # 2.6 Word-level Transcription Node
            word_timestamps = []
            if audio_uri and os.path.exists(audio_uri):
                from src.services.audio.transcription_service import base_transcription_service
                self.logger.info(f"[Nexus] Transcribing master audio for dynamic captions...")
                try:
                    # Transcribe to get word-level timing
                    transcript_data = await base_transcription_service.transcribe(audio_uri)
                    word_timestamps = transcript_data.get("words", [])
                    self.logger.info(f"[Nexus] Generated {len(word_timestamps)} word timestamps.")
                except Exception as e:
                    self.logger.error(f"[Nexus] Transcription failed: {e}")

            # 2.7 Thumbnail Extraction Node
            thumbnail_path = f"temp/thumbnails/{job_id}.jpg"
            os.makedirs("temp/thumbnails", exist_ok=True)
            if visual_paths and os.path.exists(visual_paths[0]):
                try:
                    self.logger.info(f"[Nexus] Extracting thumbnail from first clip...")
                    await asyncio.to_thread(subprocess.run, [
                        "ffmpeg", "-y", "-ss", "00:00:01.500", "-i", visual_paths[0],
                        "-frames:v", "1", "-q:v", "2", thumbnail_path
                    ], capture_output=True)
                except Exception as e:
                    self.logger.error(f"[Nexus] Thumbnail extraction failed: {e}")

            # Final Props Preparation
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

            # Ensure all numeric properties in clips are integers
            for clip in props.get("clips", []):
                if "duration_in_frames" in clip:
                    clip["duration_in_frames"] = int(clip["duration_in_frames"])

            output_filename = f"nexus_{job_id}_{niche.replace(' ', '_')}.mp4"
            rendered_path = await self._retry_remotion_render(
                composition_id=blueprint.get("composition_id", "ViralClip"), 
                props=props, 
                output_name=output_filename
            )

            if not rendered_path:
                await update_node(
                    "synthesis", "FAILED", 60, "Remotion render returned no path"
                )
                raise RuntimeError("Remotion render failed after multiple attempts")

            # Verify rendered file exists and has content
            if (
                not os.path.exists(rendered_path)
                or os.path.getsize(rendered_path) < 1024
            ):
                await update_node(
                    "synthesis", "FAILED", 60, "Rendered file is invalid or empty"
                )
                raise RuntimeError("Rendered file is invalid")

            await update_node("synthesis", "COMPLETED", 90)

            # 4. Egress Node - Automated Publishing & Final Stats
            with tracer.start_as_current_span("Nexus.Node.Egress") as node_span:
                await update_node("egress", "ACTIVE", 95)
                publish_results = []
                
                # Extract final metadata for reporting
                try:
                    cap = cv2.VideoCapture(rendered_path)
                    final_fps = cap.get(cv2.CAP_PROP_FPS)
                    final_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    final_duration = final_frames / final_fps if final_fps > 0 else 0
                    cap.release()
                    self.logger.info(f"[Nexus] Final video stats: {final_duration:.1f}s, {final_fps:.1f} fps")
                except Exception as e:
                    self.logger.warning(f"Failed to extract final video metadata: {e}")
                    final_duration = 0

                # One-Click Publishing
                if job_metadata and job_metadata.get("auto_publish", False):
                    from src.services.publishing.service import base_publishing_service
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
                                    "tags": [niche, "ettametta", vibe_data.get("vibe", "viral")]
                                },
                                use_automation=True
                            )
                            publish_results.append(result)
                        except Exception as e:
                            self.logger.error(f"[Nexus] Publishing to {platform} failed: {e}")
                            publish_results.append({"platform": platform, "status": "failed", "error": str(e)})

                # Temp Cleanup: Remove intermediate files
                try:
                    import shutil
                    for temp_dir in ["temp/voice", "temp/audit", "temp/thumbnails"]:
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as e:
                    self.logger.warning(f"[Nexus] Temp cleanup failed: {e}")

                await update_node("egress", "COMPLETED", 100, extra={
                    "thumbnail": thumbnail_path, 
                    "output": rendered_path,
                    "duration": final_duration,
                    "publish_results": publish_results
                })
                
                total_time = time.time() - start_time
                self.logger.info(f"[Nexus] Pipeline completed for Job {job_id} in {total_time:.1f}s")
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

base_nexus_service = NexusOrchestrator()
