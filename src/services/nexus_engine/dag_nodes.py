"""
Nexus Engine DAG Nodes
======================

Reusable DAG nodes for the NEXUS video production pipeline.

Each node is a self-contained processing step that:
1. Receives a context dict with results from upstream nodes
2. Executes its logic (possibly spawning sub-tasks in parallel)
3. Returns a result for downstream nodes to consume

Asset sourcing nodes follow a parallel-execution pattern:
- StockSearchNode      → search Pexels/Coverr/Mixkit by keyword
- PlatformSearchNode   → search YouTube/TikTok/etc. by query
- VideoDownloadNode    → download from URL (stock or platform)
- ParallelAssetSource  → run all sources concurrently, pick best
- VisionAuditNode      → validate clip relevance via LLM vision
- ColorGradeNode       → apply LUT-based color grading
- AudioMixNode         → mix voiceover + music with ducking
- SceneRenderNode      → render final composition
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from src.services.video_engine.dag_executor import BaseNode

# WebSocket notification helper for DAG progress reporting
from src.api.routes.ws import notify_nexus_job_update_sync
from src.shared.enums import NodeStatus


def _dag_notify(
    job_id: str,
    node_type: str,
    status: NodeStatus,
    progress: int,
    niche: str = "",
    error: str | None = None,
) -> None:
    """Publish a progress update for a DAG node via WebSocket.

    Non-blocking: failures (e.g., Redis being down) are logged as
    debug messages and silently swallowed. A WS notification failure
    should never derail video production.
    """
    try:
        payload = {
            "id": job_id,
            "status": f"DAG_{node_type.upper()}_{status.value}",
            "current_node": node_type,
            "node_status": status.value,
            "progress": progress,
            "niche": niche,
        }
        if error:
            payload["error"] = error
        notify_nexus_job_update_sync(payload)
    except Exception as _exc:
        logger.debug("[DAG:WS] WS notification failed (non-blocking): %s", _exc)
from src.services.video_engine.media_ir import MediaIR

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════
# Asset Sourcing Nodes
# ═══════════════════════════════════════════

class StockSearchNode(BaseNode):
    """Search stock video services (Pexels → Coverr → fallback) for a keyword.

    When ``semantic_rank=True`` (default in PARTIAL/FULL modes), results are
    further ranked by CLIP embedding similarity to the ``keyword`` text.

    Reports progress via WebSocket notifications.

    Params:
        keyword:       Search query (e.g., "sunset beach", "city traffic")
        count:         Number of results to return (default 3)
        niche:         Fallback niche if keyword returns nothing
        semantic_rank: Whether to apply CLIP-based semantic ranking (default True)
        job_id:        Job identifier for WS notifications

    Returns:
        list[str] of video download URLs
    """

    async def execute(self, ctx: dict[str, Any]) -> list[str]:
        job_id = str(self.params.get("job_id", f"dag_{self.id}"))
        niche = str(self.params.get("niche", ""))
        _dag_notify(job_id, self.__class__.__name__, NodeStatus.ACTIVE, 10, niche=niche)
        from src.services.video_engine.stock_service import base_stock_service

        keyword = str(self.params.get("keyword", ""))
        count = int(self.params.get("count", 3))
        niche = str(self.params.get("niche", keyword))
        semantic_rank = bool(self.params.get("semantic_rank", True))

        if semantic_rank:
            # Use semantic ranking: keyword search → download → CLIP rank
            from src.services.video_engine.semantic_stock import base_semantic_stock_matcher
            results = await base_semantic_stock_matcher.search(
                query=keyword,
                niche=niche if niche != keyword else None,
                count=count,
            )
            len(results)
            _dag_notify(job_id, self.__class__.__name__, NodeStatus.COMPLETED, 50, niche=niche)
            # Store both URLs and local paths so downstream nodes can reuse
            urls = [r["url"] for r in results]
            paths = [r["path"] for r in results if r.get("path")]
            ctx[f"{self.id}_paths"] = paths
            return urls

        # Legacy keyword path (no semantic ranking)
        urls = await base_stock_service.fetch_b_roll(keyword, count=count)
        if not urls:
            logger.info(
                "[DAG:StockSearch] No results for '%s', falling back to niche '%s'",
                keyword,
                niche,
            )
            urls = await base_stock_service.fetch_b_roll(niche, count=count)
        _dag_notify(job_id, self.__class__.__name__, NodeStatus.COMPLETED, 50, niche=niche)
        return urls or []


class SemanticSearchNode(BaseNode):
    """DAG node: Search and rank stock footage by CLIP semantic similarity.

    This is the "Stock Video Intelligence Layer" — instead of returning any
    keyword match, it downloads candidates, CLIP-embeds their frames, and
    returns only the clips that semantically match the query text.

    The ranking scores are stored in the context for downstream nodes
    (e.g., to skip low-quality matches or log scores).

    Reports progress via WebSocket notifications.

    Params:
        query:         Semantic query text (e.g., "cinematic sunset beach")
        count:         Number of top results to return (default 3)
        max_candidates: How many candidates to download for ranking (default 6)
        niche:         Fallback niche if query returns no candidates
        job_id:        Job identifier for WS notifications

    Returns:
        list[dict] with keys ``url``, ``path``, ``score``, ``frame_count``,
        sorted by ``score`` descending.
    """

    async def execute(self, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        job_id = str(self.params.get("job_id", f"dag_{self.id}"))
        niche = str(self.params.get("niche", ""))
        _dag_notify(job_id, self.__class__.__name__, NodeStatus.ACTIVE, 20, niche=niche)
        from src.services.video_engine.semantic_stock import base_semantic_stock_matcher

        query = str(self.params.get("query", ""))
        count = int(self.params.get("count", 3))
        max_candidates = int(self.params.get("max_candidates", 6))
        niche = str(self.params.get("niche", query))

        # Temporarily increase candidate pool for better ranking
        original_max = base_semantic_stock_matcher.max_candidates
        base_semantic_stock_matcher.max_candidates = max_candidates

        try:
            results = await base_semantic_stock_matcher.search(
                query=query,
                niche=niche if niche != query else None,
                count=count,
            )
            
            _dag_notify(job_id, self.__class__.__name__, NodeStatus.COMPLETED, 50, niche=niche)
            
            # Store scores in context for downstream introspection
            scores = {os.path.basename(r["path"]): r["score"] for r in results}
            ctx[f"{self.id}_scores"] = scores
            
            return results
        finally:
            base_semantic_stock_matcher.max_candidates = original_max


class VideoDownloadNode(BaseNode):
    """Download a video from a URL.

    Supports two source types:
    - "stock":    Uses StockService.download_stock_video (Pexels/Coverr)
    - "platform": Uses VideoDownloader.download_video (yt-dlp, 1000+ sites)

    Expects the URL to be in ``ctx[self.inputs[0]]`` (a string URL from
    an upstream search node) OR in ``self.params["url"]``.

    Reports progress via WebSocket notifications.

    Params:
        url:         Direct URL to download (optional, overrides input)
        source_type: "stock" or "platform" (default "stock")
        output_dir:  Where to save the file (default "temp")
        job_id:      Job identifier for WS notifications

    Returns:
        str | None — path to the downloaded file, or None on failure
    """

    async def execute(self, ctx: dict[str, Any]) -> str | None:
        job_id = str(self.params.get("job_id", f"dag_{self.id}"))
        niche = str(self.params.get("niche", ""))
        from src.services.video_engine.stock_service import base_stock_service
        from src.services.video_engine.downloader import base_downloader_service

        # Resolve URL: explicit param > upstream node result > fallback
        url = self.params.get("url")
        if not url and self.inputs:
            upstream_id = self.inputs[0]
            upstream = ctx.get(upstream_id)
            if isinstance(upstream, list) and upstream:
                url = upstream[0]
            elif isinstance(upstream, str):
                url = upstream

        if not url:
            logger.warning("[DAG:VideoDownload] No URL provided for node '%s'", self.id)
            return None

        # If an upstream node already downloaded this URL, reuse the local path
        if self.inputs:
            upstream_id = self.inputs[0]
            upstream_paths_key = f"{upstream_id}_paths"
            cached_paths = ctx.get(upstream_paths_key, [])
            if isinstance(cached_paths, list) and len(cached_paths) > 0:
                path_idx = 0
                if isinstance(upstream, list) and upstream:
                    # Match index of URL in upstream list
                    try:
                        path_idx = upstream.index(url) if url in upstream else 0
                    except ValueError:
                        path_idx = 0
                if path_idx < len(cached_paths):
                    cached = cached_paths[path_idx]
                    if cached and os.path.exists(cached) and os.path.getsize(cached) > 1024:
                        logger.info("[DAG:VideoDownload] Reusing cached path: %s", cached)
                        return cached

        source_type = str(self.params.get("source_type", "stock"))
        _dag_notify(job_id, self.__class__.__name__, NodeStatus.ACTIVE, 40, niche=niche)

        result = None
        if source_type == "platform":
            result = await base_downloader_service.download_video(url)
        else:
            result = await base_stock_service.download_stock_video(url)

        if result:
            _dag_notify(job_id, self.__class__.__name__, NodeStatus.COMPLETED, 60, niche=niche)
        else:
            _dag_notify(job_id, self.__class__.__name__, NodeStatus.FAILED, 60, niche=niche, error="Download failed")
        return result


class ParallelAssetSourceNode(BaseNode):
    """Run multiple asset sourcing strategies in parallel and return the first success.

    This is the core of the parallel asset sourcing upgrade. Instead of
    trying stock → platform → fallback sequentially, it runs ALL strategies
    concurrently and returns whichever succeeds first.

    Reports progress via WebSocket notifications.

    Params:
        keyword:       Search keyword for stock video
        niche:         Fallback niche
        platform_urls: List of platform URLs to try via yt-dlp
        output_dir:    Download directory
        job_id:        Job identifier for WS notifications

    Returns:
        MediaIR | None — the first successfully downloaded asset, or None
    """

    async def execute(self, ctx: dict[str, Any]) -> MediaIR | None:
        job_id = str(self.params.get("job_id", f"dag_{self.id}"))
        niche = str(self.params.get("niche", ""))
        _dag_notify(job_id, self.__class__.__name__, NodeStatus.ACTIVE, 10, niche=niche)
        from src.services.video_engine.stock_service import base_stock_service
        from src.services.video_engine.downloader import base_downloader_service

        keyword = str(self.params.get("keyword", ""))
        niche = str(self.params.get("niche", keyword))
        platform_urls: list[str] = list(self.params.get("platform_urls", []))
        stock_urls: list[str] = list(self.params.get("stock_urls", []))

        async def _try_stock() -> str | None:
            """Search Pexels + download, with up to 3 attempts."""
            urls = stock_urls or await base_stock_service.fetch_b_roll(keyword, count=3)
            for url in urls[:3]:
                path = await base_stock_service.download_stock_video(url)
                if path and os.path.exists(path):
                    return path
            return None

        async def _try_platform() -> str | None:
            """Try downloading from platform URLs (yt-dlp)."""
            for url in platform_urls[:3]:
                path = await base_downloader_service.download_video(url)
                if path and os.path.exists(path):
                    return path
            return None

        async def _try_semantic() -> str | None:
            """CLIP-ranked semantic search (preferred)."""
            try:
                from src.services.video_engine.semantic_stock import base_semantic_stock_matcher
                results = await base_semantic_stock_matcher.search(query=keyword, niche=niche, count=1)
                if results:
                    path = results[0].get("path")
                    if path and os.path.exists(path):
                        logger.info("[DAG:ParallelAsset] Semantic match: %.3f — %s", results[0]["score"], os.path.basename(path))
                        return path
            except Exception as e:
                logger.warning("[DAG:ParallelAsset] Semantic search failed: %s", e)
            return None

        async def _try_niche_fallback() -> str | None:
            """Last resort: search by niche keyword only."""
            urls = await base_stock_service.fetch_b_roll(f"{niche} video", count=1)
            if urls:
                return await base_stock_service.download_stock_video(urls[0])
            return None

        # Fire all strategies concurrently — semantic preferred, then stock, platform, niche fallback
        results = await asyncio.gather(
            _try_semantic(),
            _try_stock(),
            _try_platform(),
            _try_niche_fallback(),
            return_exceptions=True,
        )

        for r in results:
            if isinstance(r, Exception):
                logger.warning("[DAG:ParallelAsset] Strategy failed: %s", r)
                continue
            if r and os.path.exists(r):
                _dag_notify(job_id, self.__class__.__name__, NodeStatus.COMPLETED, 80, niche=niche)
                logger.info("[DAG:ParallelAsset] Acquired asset: %s", r)
                return await MediaIR.from_video_path(r)

        _dag_notify(
            job_id, self.__class__.__name__, NodeStatus.FAILED, 80,
            niche=niche, error="All sourcing strategies exhausted",
        )
        logger.warning(
            "[DAG:ParallelAsset] All sourcing strategies exhausted for '%s'",
            keyword,
        )
        return None


# ═══════════════════════════════════════════
# Vision & Quality Audit Nodes
# ═══════════════════════════════════════════

class VisionAuditNode(BaseNode):
    """Audit a video against a text description using Gemini/Ollama vision.

    Extracts the middle frame from the video and sends it to a vision LLM
    to verify relevance. This runs AFTER downloading (not before), making
    it a quality gate rather than a search filter.

    Params:
        video_path_key: Key in ctx or param for the video path
        prompt:         Text description to match against
        job_id:         For temp file naming

    Returns:
        dict with keys:
        - "passed": bool
        - "reason": str
        - "video_path": str  (unchanged, for chaining)
    """

    async def execute(self, ctx: dict[str, Any]) -> dict:
        from src.services.llm.service import unified_llm_service

        # Resolve video path from input
        path_key = str(self.params.get("video_path_key", "video_path"))
        video_path = self.params.get(path_key)
        if not video_path and self.inputs:
            upstream = ctx.get(self.inputs[0])
            if isinstance(upstream, dict):
                video_path = upstream.get("uri") or upstream.get(path_key)
            elif isinstance(upstream, str):
                video_path = upstream

        if not video_path or not os.path.exists(video_path):
            return {"passed": True, "reason": "no_video", "video_path": video_path}

        prompt = str(self.params.get("prompt", ""))
        job_id = str(self.params.get("job_id", "unknown"))

        # Extract middle frame
        import cv2
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_idx = total_frames // 2 if total_frames > 0 else 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {"passed": True, "reason": "frame_extraction_failed", "video_path": video_path}

        frame_dir = "/tmp/ettametta/dag_audit"
        os.makedirs(frame_dir, exist_ok=True)
        frame_path = os.path.join(frame_dir, f"audit_{job_id}_{self.id}.jpg")
        cv2.imwrite(frame_path, frame)

        audit_prompt = (
            f"Rate how well this video frame matches the description: "
            f"'{prompt}'. Return a score from 0 (not at all) to 100 "
            f"(perfect match), followed by a brief reason. "
            f"Example: '85 - good match, similar colors and composition'"
        )

        try:
            audit_result = await unified_llm_service.analyze_image(frame_path, audit_prompt)
            content = audit_result.get("content", "50") if audit_result else "50"
            # Parse numeric score from LLM response (first 1-3 digit number)
            import re
            score_match = re.search(r"(\d{1,3})", str(content))
            score = int(score_match.group(1)) if score_match else 50
            score = max(0, min(100, score))
            passed = score >= 40  # Minimum relevance threshold: 40/100
            return {
                "passed": passed,
                "score": score,
                "reason": str(content)[:80],
                "video_path": video_path,
            }
        except Exception as e:
            logger.warning("[DAG:VisionAudit] Vision audit failed: %s", e)
            return {
                "passed": True,
                "score": 50,
                "reason": f"audit_error: {e}",
                "video_path": video_path,
            }
        finally:
            if os.path.exists(frame_path):
                os.remove(frame_path)


# ═══════════════════════════════════════════
# Production Nodes
# ═══════════════════════════════════════════

class ColorGradeNode(BaseNode):
    """Apply color grading to a video based on style profile.

    Params:
        input_path:  Video file path (overrides context lookup)
        output_path: Output file path (auto-generated if empty)
        style:       Style name matching style_library.py (e.g., "CINEMATIC_DOC")
        quality_mode:"ELITE" or "FAST"
    """

    async def execute(self, ctx: dict[str, Any]) -> str:
        from src.services.video_engine.ffmpeg_utils import base_ffmpeg_service

        # Resolve input
        input_path = self.params.get("input_path")
        if not input_path and self.inputs:
            upstream = ctx.get(self.inputs[0])
            if isinstance(upstream, dict):
                input_path = upstream.get("uri") or upstream.get("video_path")
            elif isinstance(upstream, str):
                input_path = upstream

        if not input_path or not os.path.exists(input_path):
            logger.warning("[DAG:ColorGrade] No valid input for '%s'", self.id)
            return input_path or ""

        # Determine output path
        output_path = self.params.get("output_path", "")
        if not output_path:
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_graded{ext}"

        style = str(self.params.get("style", "CINEMATIC_DOC"))
        quality = str(self.params.get("quality_mode", "ELITE"))

        # Lookup style config for grading parameters
        try:
            from src.services.nexus_engine.style_library import get_style
            style_config = get_style(style)
            color_profile = style_config.get("color_profile", {})
        except Exception:
            color_profile = {}

        success = base_ffmpeg_service.apply_color_grading(
            input_path,
            output_path,
            lut_path=color_profile.get("lut_path"),
            contrast_boost=color_profile.get("contrast", 1.2),
            saturation=color_profile.get("saturation", 1.1),
            grain_opacity=color_profile.get("grain", 0.05),
            color_temp=color_profile.get("color_temp", 5500),
            quality_mode=quality,
        )
        return output_path if success else input_path


class AudioMixNode(BaseNode):
    """Mix voiceover and/or background music into a video.

    For production-level audio, uses sidechain compression (ducking)
    to automatically lower music volume when voiceover is active.

    Params:
        video_path:     Input video path
        voiceover_path: Voiceover audio path (optional)
        music_path:     Background music path (optional)
        output_path:    Output file path
        music_volume:   Background music volume (default 0.25)
    """

    async def execute(self, ctx: dict[str, Any]) -> str:
        from src.services.video_engine.ffmpeg_utils import base_ffmpeg_service

        # Resolve paths from params or upstream context
        video_path = self.params.get("video_path")
        if not video_path and self.inputs:
            upstream = ctx.get(self.inputs[0])
            if isinstance(upstream, dict):
                video_path = upstream.get("uri") or upstream.get("video_path")
            elif isinstance(upstream, str):
                video_path = upstream

        if not video_path or not os.path.exists(video_path):
            logger.warning("[DAG:AudioMix] No valid video input for '%s'", self.id)
            return video_path or ""

        voiceover_path = self.params.get("voiceover_path")
        music_path = self.params.get("music_path")
        output_path = self.params.get("output_path", "")
        music_volume = float(self.params.get("music_volume", 0.25))

        if not output_path:
            base, ext = os.path.splitext(video_path)
            output_path = f"{base}_mixed{ext}"

        if voiceover_path and os.path.exists(voiceover_path) and music_path and os.path.exists(music_path):
            success = base_ffmpeg_service.mix_production_audio_with_ducking(
                video_path, voiceover_path, music_path, output_path,
                music_volume=music_volume,
            )
        elif music_path and os.path.exists(music_path):
            success = base_ffmpeg_service.add_background_music(
                video_path, music_path, output_path, music_volume=music_volume,
            )
        else:
            logger.info("[DAG:AudioMix] No audio assets for '%s', skipping", self.id)
            return video_path

        return output_path if success else video_path


class SceneRenderNode(BaseNode):
    """Render the final composition using either Remotion (primary) or FFmpeg (fallback).

    This is the terminal node of the asset DAG — it takes all processed
    assets and produces the final output video.

    Reports progress via WebSocket notifications at render start and completion.

    Params:
        audio_uri:        Master audio path
        job_id:           Job identifier
        niche:            Content niche
        style:            Style name
        blueprint:        Blueprint dict
        job_metadata:     Additional metadata for render
        composition_id:   Remotion composition ID (default "ViralClip")
    """

    async def execute(self, ctx: dict[str, Any]) -> dict:
        from src.services.video_engine.ffmpeg_utils import base_ffmpeg_service

        job_id = str(self.params.get("job_id", "unknown"))
        niche = str(self.params.get("niche", ""))
        str(self.params.get("style", "CINEMATIC_DOC"))
        _dag_notify(job_id, self.__class__.__name__, NodeStatus.ACTIVE, 70, niche=niche)
        dict(self.params.get("blueprint", {}))
        dict(self.params.get("job_metadata", {}))
        composition_id = str(self.params.get("composition_id", "ViralClip"))

        # Collect audited clips from upstream context
        audited_clips: list[dict] = self.params.get("audited_clips", [])
        if not audited_clips and self.inputs:
            for input_id in self.inputs:
                upstream = ctx.get(input_id)
                if isinstance(upstream, list):
                    audited_clips.extend(upstream)
                elif isinstance(upstream, dict) and "clips" in upstream:
                    audited_clips.extend(upstream["clips"])

        # Extract clip paths (support MediaIR, dict, and string)
        visual_paths: list[str] = []
        for clip in audited_clips:
            if isinstance(clip, dict):
                path = clip.get("uri") or clip.get("url") or clip.get("video_path", "")
                if path:
                    visual_paths.append(path)
            elif isinstance(clip, str):
                visual_paths.append(clip)

        if not visual_paths:
            _dag_notify(
                job_id, self.__class__.__name__, NodeStatus.FAILED, 70,
                niche=niche, error="No visual assets",
            )
            logger.error("[DAG:SceneRender] No visual paths available for '%s'", self.id)
            return {"success": False, "error": "no_visual_assets", "output_path": None}

        render_dir = "outputs/nexus"
        os.makedirs(render_dir, exist_ok=True)
        output_filename = f"nexus_{job_id}_{niche.replace(' ', '_')}.mp4"
        fallback_output = os.path.join(render_dir, f"ffmpeg_{job_id}.mp4")

        # Try Remotion first (primary render engine)
        rendered = None
        try:
            from src.services.nexus_engine.orchestrator import base_nexus_service
            rendered = await base_nexus_service._retry_remotion_render(
                composition_id=composition_id,
                props=self.params.get("props", {}),
                output_name=output_filename,
            )
        except Exception as e:
            _dag_notify(
                job_id, self.__class__.__name__, NodeStatus.FAILED, 75,
                niche=niche, error=f"Remotion failed: {e}",
            )
            logger.warning("[DAG:SceneRender] Remotion failed, falling back to FFmpeg: %s", e)

        # FFmpeg fallback
        if not rendered or not os.path.exists(rendered) or os.path.getsize(rendered or "") < 1024:
            logger.info("[DAG:SceneRender] Using FFmpeg fallback render")
            local_paths = [p for p in visual_paths if os.path.exists(p)]

            if len(local_paths) >= 1:
                if len(local_paths) == 1:
                    import shutil
                    shutil.copy2(local_paths[0], fallback_output)
                    rendered = fallback_output
                else:
                    success = base_ffmpeg_service.xfade_concatenate(
                        local_paths, fallback_output, transition="fade", trans_duration=0.3,
                    )
                    if success and os.path.exists(fallback_output):
                        rendered = fallback_output
                    else:
                        success = base_ffmpeg_service.concatenate_videos(local_paths, fallback_output)
                        if success:
                            rendered = fallback_output

            if not rendered or not os.path.exists(rendered):
                _dag_notify(
                    job_id, self.__class__.__name__, NodeStatus.FAILED, 90,
                    niche=niche, error="All render methods failed",
                )
                return {"success": False, "error": "all_render_methods_failed", "output_path": None}

        # Add audio if available
        audio_uri = self.params.get("audio_uri") or (ctx.get("audio") if "audio" in ctx else None)
        if audio_uri and os.path.exists(audio_uri) and rendered:
            audio_mixed = rendered.replace(".mp4", "_audio.mp4")
            has_audio = base_ffmpeg_service._has_audio(rendered)
            if not has_audio:
                success = base_ffmpeg_service.add_background_music(
                    rendered, audio_uri, audio_mixed, music_volume=1.0,
                )
                if success:
                    os.replace(audio_mixed, rendered)

        _dag_notify(job_id, self.__class__.__name__, NodeStatus.COMPLETED, 100, niche=niche)
        return {
            "success": True,
            "output_path": rendered,
            "visual_paths": visual_paths,
        }
