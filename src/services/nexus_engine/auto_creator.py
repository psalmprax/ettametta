# Databricks notebook source
import json
import logging
import os
import asyncio
import cv2
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.api.utils.resilience import CircuitBreaker
from src.services.llm.service import LLMProvider
from src.services.nexus_engine.cta_templates import get_cta_template
from src.services.video_engine.automation import AutomationMode, is_at_least
from src.shared.enums import NodeStatus

logger = logging.getLogger(__name__)

# Redis pub/sub channel prefix for DAG approvals across workers
APPROVAL_CHANNEL_PREFIX = "nexus:approval"

STYLE_ALIASES = {
    "cinematic": "CINEMATIC_DOC",
    "documentary": "CINEMATIC_DOC",
    "story": "HEARTFELT_NARRATIVE",
    "educational": "ULTIMATE_TUTORIAL",
    "tutorial": "ULTIMATE_TUTORIAL",
    "aggressive": "FAST_HYPE",
    "fast": "FAST_HYPE",
    "hype": "FAST_HYPE",
    "motivation": "MOTIVATIONAL",
    "motivational": "MOTIVATIONAL",
    "reddit": "REDDIT_STORY",
    "noir": "NOIR_MYSTERY",
    "news": "BROADCAST_NEWS",
    "listicle": "TOP_LISTICLE",
    "fitness": "FITNESS_MOTIVATION",
    "gaming": "GAMING_LORE",
    "esports": "ESPORTS_HYPE",
}

# Vision audit pass threshold (0-100). Raise to be conservative in automated selection.
VISION_AUDIT_THRESHOLD = 60


def normalize_nexus_style(style: str | None) -> str:
    """Accept user-facing style names while keeping Nexus style IDs canonical."""
    from .style_library import STYLE_DEFINITIONS

    if not style:
        return "CINEMATIC_DOC"

    normalized = str(style).strip()
    if normalized in STYLE_DEFINITIONS:
        return normalized

    upper = normalized.upper().replace("-", "_").replace(" ", "_")
    if upper in STYLE_DEFINITIONS:
        return upper

    return STYLE_ALIASES.get(normalized.lower(), "CINEMATIC_DOC")


class AutoCreator:
    """
    Autonomous Video Creation Engine.
    Hardened with Circuit Breakers and retries for production-grade reliability.
    Orchestrates LLM, Video, and Voiceover services.

    Supports three automation modes:
    - MANUAL: Sequential legacy path or manually constructed DAG
    - PARTIAL: AI generates DAG + scripts, user approves before execution
    - FULL: End-to-end AI-driven video compilation

    Cross-worker approval signaling
    --------------------------------
    In PARTIAL mode, the Celery worker that called ``_wait_for_dag_approval``
    may be a *different process* from the API worker that receives the user's
    PUT to ``/api/v1/nexus/jobs/{job_id}/dag-approval``. Three layers make this
    safe — there is **no worker-pinning requirement**:

    1. **Database is the source of truth.** The pending DAG preview and the
       final approval state are written to ``NexusJobDB.job_metadata`` so
       any process can read or write the current state.
    2. **Redis pub/sub is the cross-worker signal.** ``_publish_approval``
       publishes to the ``nexus:approval:{job_id}`` channel, and the waiter
       worker's listener (``_listen_for_approval``) wakes its local
       ``asyncio.Event`` on receipt.
    3. **The four ``_pending_*`` / ``_approval_*`` instance dicts are local
       subscription cleanup handles only.** They are *not* the source of
       truth. If the API request lands on a worker whose
       ``_pending_approvals`` does not contain the job, ``approve_dag``
       loads the preview from the DB before publishing.

    Implication: running multiple Celery workers and a separate API
    server is fully supported. The instance state on any one worker
    only governs the lifetime of that worker's pubsub listener and
    local ``asyncio.Event`` — it is not load-bearing for correctness.
    """

    def __init__(self):
        self.breaker = CircuitBreaker(name="AutoCreator-Pipeline", failure_threshold=3, recovery_timeout=300)
        # Pending DAG approvals: {job_id: dag_data}
        self._pending_approvals: dict[str, dict] = {}
        # Approval events: {job_id: asyncio.Event}
        self._approval_events: dict[str, asyncio.Event] = {}
        # Redis pub/sub subscriptions: {job_id: pubsub_obj}
        self._approval_subscriptions: dict[str, any] = {}
        # Background listener tasks: {job_id: asyncio.Task}
        self._approval_listeners: dict[str, asyncio.Task] = {}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def generate_viral_script(self, topic: str, niche: str, duration_seconds: int = 60, style: str = "CINEMATIC_DOC") -> List[Dict[str, Any]]:
        """
        Generates a multi-part viral script with resilience.
        """
        from .style_library import get_style
        style = normalize_nexus_style(style)
        style_config = get_style(style)

        num_chapters = max(1, duration_seconds // 60)
        all_segments = []

        logger.info(f"[AutoCreator] Generating {num_chapters} chapters for style: {style}")

        for i in range(num_chapters):
            context = f"Topic: {topic}. Niche: {niche}. Style: {style_config['name']}. {style_config['prompt_modifier']}"
            if all_segments:
                last_segment = all_segments[-1].get("text", "")
                context += f" Previous context: {last_segment[-200:]}"

            part_segments = await self._generate_script_part(
                topic, niche, duration_seconds, f"Chapter {i+1}", context=context, style=style
            )

            if part_segments:
                all_segments.extend(part_segments)

        if not all_segments:
            raise RuntimeError("Script generation returned no segments after multiple attempts.")

        return all_segments

    async def _generate_script_part(
        self, topic: str, niche: str, duration: int, chapter_info: str, context: str = "", style: str = "CINEMATIC_DOC"
    ) -> list[dict]:
        from src.services.llm.intelligence_hub import base_intelligence_service
        from .style_library import get_style
        style = normalize_nexus_style(style)
        style_config = get_style(style)

        system_prompt = f"You are a professional video scriptwriter for the {niche} niche. Your style is: {style_config['name']}."
        prompt = f"""
        Topic: {topic}
        Style: {style_config['name']} ({style_config['description']})
        Tone: {style_config['prompt_modifier']}
        Target Duration: {duration} seconds
        Part Info: {chapter_info}
        {context}

        Generate a JSON object with a 'segments' key. This key MUST contain a list of 6 to 8 segments.
        Each segment MUST have: 'text', 'visual_prompt', 'mood', 'type'.

        OUTPUT FORMAT (JSON ONLY):
        {{ "segments": [ ... ] }}
        """

        try:
            response = await base_intelligence_service.chat(
                prompt=prompt,
                system_prompt=system_prompt,
                json_mode=True,
                complexity="high"
            )

            content = json.loads(response["response"])
            segments = []
            if isinstance(content, list):
                segments = content
            elif isinstance(content, dict):
                segments = content.get("segments", content.get("script", [content]))

            return segments
        except Exception:
            logger.exception("[AutoCreator] _generate_script_part error")
            raise

    async def create_cinema_video(
        self,
        job_id: str,
        topic: str,
        niche: str,
        blueprint_id: str = "story-factory",
        engine: str = "cloud",
        script: list[dict] | None = None,
        use_gpu: bool = False,
        batch_count: int = 1,
        duration_seconds: int = 60,
        style: str = "CINEMATIC_DOC",
        use_dag: bool = False,
        automation_mode: AutomationMode = AutomationMode.MANUAL,
    ) -> str:
        """
        Main creation loop protected by CircuitBreaker.

        Args:
            automation_mode: Controls DAG usage and AI involvement.
                - MANUAL: Respects ``use_dag`` flag (legacy behavior).
                - PARTIAL: Forces ``use_dag=True`` + AI generates script +
                  approval gate before execution.
                - FULL: Forces ``use_dag=True`` + AI generates script +
                  auto-executes with no manual approval.
        """
        if self.breaker.is_open():
            logger.error("[AutoCreator] Circuit OPEN. Creation denied.")
            raise RuntimeError("AutoCreator is temporarily unavailable.")

        style = normalize_nexus_style(style)
        _ = use_gpu
        _ = batch_count

        # Resolve effective DAG and automation settings
        effective_dag = use_dag or is_at_least(automation_mode, AutomationMode.PARTIAL)
        if automation_mode == AutomationMode.MANUAL:
            effective_dag = use_dag  # Respect the flag as-is

        try:
            result = await self._create_cinema_video_inner(
                job_id, topic, niche, blueprint_id, engine, script,
                duration_seconds, style, use_dag=effective_dag,
                automation_mode=automation_mode,
            )
            self.breaker.record_success()
            return result
        except Exception:
            self.breaker.record_failure()
            logger.exception("[AutoCreator] Creation Pipeline Failed")
            raise

    async def _create_cinema_video_inner(
        self, job_id, topic, niche, blueprint_id, engine, script,
        duration_seconds, style, use_dag: bool = False,
        automation_mode: AutomationMode = AutomationMode.MANUAL,
    ) -> str:
        from src.api.routes.ws import notify_nexus_job_update_sync
        from src.api.utils.database import async_session_factory
        from src.api.utils.models import NexusJobDB
        from sqlalchemy import select

        async def notify(node: str, status: NodeStatus, progress: int):
            try:
                async with async_session_factory() as db:
                    stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
                    result = await db.execute(stmt)
                    job = result.scalar_one_or_none()
                    if job:
                        job.current_node = node
                        current_status = dict(job.node_status or {})
                        current_status[node] = status.value
                        job.node_status = current_status
                        job.progress = progress
                        await db.commit()
            except Exception:
                logger.exception("[AutoCreator] DB notify error")

            notify_nexus_job_update_sync({
                "id": str(job_id),
                "status": f"{node.upper()}_{status}",
                "current_node": node,
                "node_status": status.value,
                "progress": progress
            })

        # 1. Ingress — Generate script
        await notify("ingress", NodeStatus.ACTIVE, 10)
        if script:
            segments = script
        else:
            # In PARTIAL/FULL modes, use Prompt→DAG Generator for richer structure
            if is_at_least(automation_mode, AutomationMode.PARTIAL):
                segments = await self._generate_dag_guided_script(
                    topic, niche, duration_seconds, style, job_id,
                )
            else:
                segments = await self.generate_viral_script(
                    topic, niche, duration_seconds=duration_seconds, style=style,
                )
        await notify("ingress", NodeStatus.COMPLETED, 20)

        # 2. Cognition — Source assets
        await notify("cognition", NodeStatus.ACTIVE, 30)

        # For PARTIAL mode: wait for approval before executing
        # Only when AI actually generated a DAG (not when script was provided)
        ai_generated_script = script is None and is_at_least(automation_mode, AutomationMode.PARTIAL)
        if ai_generated_script and automation_mode == AutomationMode.PARTIAL and use_dag:
            dag_preview = await self._build_dag_preview(segments, job_id, niche)
            approved = await self._wait_for_dag_approval(job_id, dag_preview)
            if not approved:
                raise RuntimeError(
                    f"DAG execution rejected by user for job {job_id}"
                )

        visual_paths = await self._source_visual_assets(
            segments, job_id, niche, engine=engine, style=style, use_dag=use_dag,
        )
        voice_paths = await self._generate_voiceovers(segments, job_id)

        if not visual_paths or not voice_paths:
            raise ValueError("Asset sourcing failed.")
        await notify("cognition", NodeStatus.COMPLETED, 50)

        # 3. Synthesis
        await notify("synthesis", NodeStatus.ACTIVE, 60)
        from src.services.nexus_engine.orchestrator import base_nexus_service

        from .style_library import get_style
        style_config = get_style(style)
        vfx_type = style_config.get("remotion_flags", {}).get("vfx", "default")

        output_path = await base_nexus_service.assemble_video(
            job_id=job_id,
            niche=niche,
            script_segments=segments,
            voiceover_paths=voice_paths,
            visual_paths=visual_paths,
            music_path=None,
            blueprint_id=blueprint_id,
            style=style,
            job_metadata={"vfx": vfx_type}
        )

        if not output_path:
            raise RuntimeError("Assembly failed.")

        await notify("synthesis", NodeStatus.COMPLETED, 90)

        # 4. Egress
        await notify("egress", NodeStatus.ACTIVE, 95)
        # Final output path persistence
        async with async_session_factory() as db:
            stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()
            if job:
                metadata = dict(job.job_metadata or {})
                metadata["output_path"] = output_path
                job.job_metadata = metadata
                await db.commit()

        await notify("egress", NodeStatus.COMPLETED, 100)
        return output_path

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def publish_job(self, job_id: str, platforms: list[str] = None) -> dict:
        """Publishes a completed job with resilience."""
        from src.services.distribution.publishing import base_publishing_service
        from src.api.utils.database import async_session_factory
        from src.api.utils.models import NexusJobDB
        from sqlalchemy import select

        if platforms is None:
            platforms = ["youtube"]
        async with async_session_factory() as db:
            stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()

            if not job or "output_path" not in job.job_metadata:
                raise ValueError("Job not ready for publishing.")

            output_path = job.job_metadata["output_path"]
            publish_results = {}

            for platform in platforms:
                try:
                    res = await base_publishing_service.publish_to_platform(
                        user_id=job.user_id,
                        platform=platform,
                        video_path=output_path,
                        metadata={"title": job.job_metadata.get("topic", "EttaMetta Viral Video")}
                    )
                    publish_results[platform] = res
                except Exception as e:
                    publish_results[platform] = {"status": "error", "message": str(e)}

            metadata = dict(job.job_metadata or {})
            metadata["publish_results"] = publish_results
            job.job_metadata = metadata
            await db.commit()
        return publish_results

    async def launch_automated_video(
        self,
        user_id: str,
        topic: str,
        niche: str | None,
        style: str = "CINEMATIC_DOC",
        duration: int = 60,
        engine: str = "cloud",
        script: list[dict] | None = None,
        use_gpu: bool = False,
        batch_count: int = 1,
        cta_text: str | None = None,
        cta_type: str = "cta",
        cta_template: str | None = None,
    ) -> str:
        """
        Create a persisted Nexus job and launch the cinema pipeline.

        Supports both legacy CTA overrides and CTA templates.
        If cta_template is provided, it takes precedence over cta_text/cta_type.
        """
        from src.api.utils.database import async_session_factory
        from src.api.utils.models import NexusJobDB
        from src.shared.enums import SystemJobStatus

        resolved_niche = niche or "General"
        resolved_style = normalize_nexus_style(style)

        effective_cta_text = cta_text
        effective_cta_type = cta_type
        cta_duration: int | None = None

        if cta_template:
            template = get_cta_template(cta_template)
            if template:
                effective_cta_text = template.get_default_text()
                effective_cta_type = "cta"
                cta_duration = template.duration_seconds
                logger.info(
                    f"[AutoCreator] Applying CTA template {cta_template} "
                    f"with duration {cta_duration}s"
                )
            else:
                logger.warning(
                    f"[AutoCreator] Unknown CTA template '{cta_template}' - falling back to legacy CTA override"
                )

        prepared_script = self._apply_cta_override(
            script,
            effective_cta_text,
            effective_cta_type,
            cta_duration=cta_duration,
        )

        async with async_session_factory() as db:
            job = NexusJobDB(
                niche=resolved_niche,
                user_id=user_id,
                status=SystemJobStatus.QUEUED,
                progress=0,
                job_metadata={
                    "topic": topic,
                    "style": resolved_style,
                    "engine": engine,
                    "cinema_mode": True,
                    "cta_text": cta_text,
                    "cta_type": cta_type,
                    "cta_template": cta_template,
                },
            )
            db.add(job)
            await db.commit()
            await db.refresh(job)
            job_id = str(job.id)

        await self.create_cinema_video(
            job_id=job_id,
            topic=topic,
            niche=resolved_niche,
            engine=engine,
            script=prepared_script,
            use_gpu=use_gpu,
            batch_count=batch_count,
            duration_seconds=duration,
            style=resolved_style,
        )
        return job_id

    @staticmethod
    def _apply_cta_override(
        script: list[dict] | None,
        cta_text: str | None,
        cta_type: str = "cta",
        cta_duration: int | None = None,
    ) -> list[dict] | None:
        if not script or not cta_text:
            return script

        updated = [dict(segment) for segment in script]
        for segment in reversed(updated):
            if segment.get("type") in {"cta", "engagement"}:
                segment["text"] = cta_text
                segment["type"] = cta_type if cta_type in {"cta", "engagement"} else "cta"
                if cta_duration is not None:
                    segment["duration"] = cta_duration
                return updated

        updated.append({
            "type": cta_type if cta_type in {"cta", "engagement"} else "cta",
            "text": cta_text,
            "visual_prompt": "clear call to action social media end screen",
            "mood": "decisive",
            "duration": cta_duration if cta_duration is not None else 5,
        })
        return updated

    # ─── Prompt → DAG Generator ────────────────────────────────────────

    async def _generate_dag_guided_script(
        self, topic: str, niche: str, duration_seconds: int,
        style: str, job_id: str,
    ) -> list[dict]:
        """
        Prompt → DAG Generator (Runway-style).

        Uses an LLM to output a structured DAG node graph instead of flat
        script segments. Each node declares:
        - id: Unique node identifier
        - type: clip | effect | audio | composite | export
        - inputs: List of upstream node IDs
        - params: Execution parameters (query, effect, preset, etc.)

        The output is parsed into script segments for backward compatibility
        with the existing pipeline, while preserving the DAG structure for
        the scheduler.

        Returns:
            list[dict] of script segments with DAG metadata preserved
        """
        from src.services.llm.intelligence_hub import base_intelligence_service
        from .style_library import get_style
        style_config = get_style(style)

        segments_prompt = f"""You are a professional video DAG architect.
        Given a topic, niche, and style, design a structured video DAG (directed acyclic graph)
        of processing nodes. Each node represents a processing step.

        Topic: {topic}
        Niche: {niche}
        Style: {style_config['name']} ({style_config['description']})
        Tone: {style_config['prompt_modifier']}
        Target Duration: {duration_seconds} seconds

        Return a JSON object with a 'nodes' key containing 6-8 segments, each with:
        - 'id': str (e.g., "intro_clip", "scene_establish", "transition_fx")
        - 'type': "clip" | "effect" | "audio" | "composite" | "export"
        - 'inputs': list[str] of upstream node IDs this depends on (empty for root nodes)
        - 'params': dict with:
            - 'text': spoken text or narration for this segment
            - 'visual_prompt': keyword for stock footage search
            - 'mood': emotional tone
            - 'effect': optional effect name
            - 'preset': optional style preset
            - 'duration_sec': approximate duration in seconds

        OUTPUT FORMAT (JSON ONLY):
        {{ "nodes": [
            {{ "id": "intro", "type": "clip", "inputs": [], "params": {{ "text": "...", "visual_prompt": "...", "mood": "...", "duration_sec": 8 }} }},
            {{ "id": "scene_1", "type": "clip", "inputs": ["intro"], "params": {{ "text": "...", "visual_prompt": "...", "mood": "...", "duration_sec": 10 }} }},
            {{ "id": "transition_1", "type": "effect", "inputs": ["scene_1"], "params": {{ "effect": "crossfade", "duration_sec": 1 }} }}
        ]}}
        """

        try:
            response = await base_intelligence_service.chat(
                prompt=segments_prompt,
                system_prompt="You are a professional video DAG architect. Output valid JSON only.",
                json_mode=True,
                complexity="high",
            )

            content = json.loads(response["response"])
            nodes = []
            if isinstance(content, dict):
                nodes = content.get("nodes", content.get("segments", []))
            elif isinstance(content, list):
                nodes = content

            # Convert DAG nodes to script segments with preserved dag_metadata
            segments = []
            for n in nodes:
                params = n.get("params", {})
                seg = {
                    "text": params.get("text", ""),
                    "visual_prompt": params.get("visual_prompt", niche),
                    "mood": params.get("mood", "neutral"),
                    "type": params.get("type", n.get("type", "clip")),
                    "dag_metadata": {
                        "node_id": n.get("id"),
                        "dag_type": n.get("type", "clip"),
                        "inputs": n.get("inputs", []),
                        "effect": params.get("effect"),
                        "preset": params.get("preset"),
                        "duration_sec": params.get("duration_sec", 10),
                    },
                }
                if seg["text"] or seg["visual_prompt"]:
                    segments.append(seg)

            if not segments:
                logger.warning("[DAG-GuidedScript] LLM returned empty, falling back to standard generation")
                return await self.generate_viral_script(
                    topic, niche, duration_seconds=duration_seconds, style=style,
                )

            logger.info("[DAG-GuidedScript] Generated %d DAG nodes for %s", len(segments), topic)
            return segments

        except Exception as e:
            logger.warning("[DAG-GuidedScript] Failed: %s, falling back to standard generation", e)
            return await self.generate_viral_script(
                topic, niche, duration_seconds=duration_seconds, style=style,
            )

    async def _build_dag_preview(self, segments: list[dict], job_id: str, niche: str) -> dict:
        """Build a preview structure for user approval in PARTIAL mode."""
        total_duration = sum(
            s.get("dag_metadata", {}).get("duration_sec", 10) or 10
            for s in segments
        )
        return {
            "job_id": job_id,
            "niche": niche,
            "segments_count": len(segments),
            "estimated_duration_sec": total_duration,
            "segments": [
                {
                    "index": i,
                    "text": s.get("text", "")[:80],
                    "visual_prompt": s.get("visual_prompt", "")[:60],
                    "mood": s.get("mood", "neutral"),
                    "type": s.get("type", "clip"),
                    "dag_type": s.get("dag_metadata", {}).get("dag_type", "clip"),
                    "inputs": s.get("dag_metadata", {}).get("inputs", []),
                    "effect": s.get("dag_metadata", {}).get("effect"),
                }
                for i, s in enumerate(segments)
            ],
        }

    async def _wait_for_dag_approval(self, job_id: str, dag_preview: dict) -> bool:
        """
        Wait for user approval before executing a DAG in PARTIAL mode.

        Stores the preview for polling via API and waits up to 5 minutes
        for the user to approve or reject.
        """
        # Keep in-memory copy for the current process to signal waiting callers
        self._pending_approvals[job_id] = dag_preview
        event = asyncio.Event()
        self._approval_events[job_id] = event

        # Persist preview to DB so approval survives restarts and multi-worker setups
        try:
            from src.api.utils.database import async_session_factory
            from src.api.utils.models import NexusJobDB
            from sqlalchemy import select

            async with async_session_factory() as db:
                stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()
                if job:
                    metadata = dict(job.job_metadata or {})
                    metadata["dag_preview"] = dag_preview
                    metadata["dag_approval_state"] = {"awaiting": True}
                    job.job_metadata = metadata
                    await db.commit()
        except Exception:
            logger.exception("[AutoCreator] Failed to persist DAG preview to DB")

        # Subscribe to Redis pub/sub BEFORE notifying the user. If we notified
        # first, a fast user approval could be published to Redis before we
        # had subscribed, and the message would be silently lost (Redis
        # pub/sub is fire-and-forget). The DB-persisted state is the recovery
        # path: the timeout branch below re-reads ``dag_approval_state`` from
        # the DB to detect approvals that landed in the subscribe window.
        await self._subscribe_to_approval_channel(job_id)

        # Notify via WebSocket so frontend can prompt the user
        try:
            from src.api.routes.ws import notify_nexus_job_update_sync
            notify_nexus_job_update_sync({
                "id": str(job_id),
                "status": "AWAITING_APPROVAL",
                "current_node": "dag_approval",
                "progress": 25,
                "dag_preview": dag_preview,
                "message": "DAG generated. Approve or reject via API: PUT /api/v1/nexus/jobs/{job_id}/dag-approval",
            })
        except Exception:
            logger.warning("[AutoCreator] WS notification failed for approval gate")

        logger.info(
            "[AutoCreator] Awaiting DAG approval for job %s "
            "(timeout=300s). Preview: %d segments, ~%ds",
            job_id,
            dag_preview.get("segments_count", 0),
            dag_preview.get("estimated_duration_sec", 0),
        )

        # Subscribe to Redis pub/sub channel for cross-worker approval signaling
        await self._subscribe_to_approval_channel(job_id)

        try:
            await asyncio.wait_for(event.wait(), timeout=300.0)
        except asyncio.TimeoutError:
            # Timeout reached. This can mean one of two things:
            #   (a) the user genuinely never approved, OR
            #   (b) the user approved during the race window between WS
            #       notification and our Redis subscription, and the Redis
            #       message was lost (pub/sub is fire-and-forget).
            # ``approve_dag`` persists the approval to the DB in the same
            # transaction as the publish, so case (b) is detectable: re-read
            # the DB and honour any approval that was recorded while we
            # were waiting.
            logger.warning(
                "[AutoCreator] DAG approval timed out for job %s, "
                "checking DB for late approval before rejecting",
                job_id,
            )
            self._pending_approvals.pop(job_id, None)
            self._approval_events.pop(job_id, None)
            await self._cleanup_approval_subscription(job_id)
            # Track which branch we were in when/if a DB error fires, so
            # the except handler can log a useful message.
            state_was_approved = False
            # Note: the read-then-write below is not row-locked. On a busy
            # PostgreSQL deployment, ``approve_dag`` could commit
            # ``approved=True`` in the small window between our SELECT and
            # UPDATE. With SQLite (test) this is impossible (single-writer).
            # In production this is acceptable because the worst case is
            # that a single approval is downgraded to "rejected by timeout"
            # in the DB; the user's next retry will succeed. The DB row
            # lock is deliberately omitted to avoid coupling the timeout
            # path to the API request path.
            try:
                from src.api.utils.database import async_session_factory
                from src.api.utils.models import NexusJobDB
                from sqlalchemy import select

                async with async_session_factory() as db:
                    stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
                    result = await db.execute(stmt)
                    job = result.scalar_one_or_none()
                    if job:
                        metadata = dict(job.job_metadata or {})
                        state = metadata.get("dag_approval_state") or {}
                        if state.get("approved") is True:
                            # Late approval: the API side already wrote
                            # approved=True; honour it and return True.
                            logger.info(
                                "[AutoCreator] Recovered late approval for "
                                "job %s from DB after Redis message lost",
                                job_id,
                            )
                            state_was_approved = True
                            metadata.pop("dag_preview", None)
                            metadata["dag_approval_state"] = {
                                "awaiting": False,
                                "approved": True,
                                "reason": "recovered_after_redis_lost",
                            }
                            job.job_metadata = metadata
                            await db.commit()
                            return True
                        # Genuine timeout: no approval recorded.
                        metadata.pop("dag_preview", None)
                        metadata["dag_approval_state"] = {"awaiting": False, "approved": False, "reason": "timeout"}
                        job.job_metadata = metadata
                        await db.commit()
            except Exception:
                # The recovery path's commit failure and the timeout
                # persistence failure share this handler. We log a distinct
                # warning depending on which case we were in: a recoverable
                # approval being lost is a worse outcome than a timeout
                # persistence blip, so flag it loudly for the operator to
                # manually flip the DB state.
                logger.exception(
                    "[AutoCreator] DB error while resolving approval timeout "
                    "for job %s (recovery_state=%s) - check DB and flip "
                    "dag_approval_state manually if a recoverable approval "
                    "was lost",
                    job_id,
                    "approved" if state_was_approved else "timeout",
                )
            return False

        # Check result: was it approved or rejected?
        approved = dag_preview.get("_approved", False)
        # Persist approval state
        try:
            from datetime import datetime
            from src.api.utils.database import async_session_factory
            from src.api.utils.models import NexusJobDB
            from sqlalchemy import select

            async with async_session_factory() as db:
                stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()
                if job:
                    metadata = dict(job.job_metadata or {})
                    metadata.pop("dag_preview", None)
                    metadata["dag_approval_state"] = {
                        "awaiting": False,
                        "approved": bool(approved),
                        "approved_at": datetime.utcnow().isoformat(),
                    }
                    job.job_metadata = metadata
                    await db.commit()
        except Exception:
            logger.exception("[AutoCreator] Failed to persist DAG approval state to DB")

        # Clean up in-memory structures and Redis subscription
        self._pending_approvals.pop(job_id, None)
        self._approval_events.pop(job_id, None)
        await self._cleanup_approval_subscription(job_id)
        return bool(approved)

    # ─── Approval API (for external callers like REST routes) ────────────

    async def approve_dag(self, job_id: str, approved: bool) -> bool:
        """Approve or reject a pending DAG for PARTIAL mode.

        Called by REST routes to resolve the approval gate.
        """
        # Ensure pending preview exists in-memory; if not, try loading from DB
        if job_id not in self._pending_approvals:
            try:
                from src.api.utils.database import async_session_factory
                from src.api.utils.models import NexusJobDB
                from sqlalchemy import select

                async with async_session_factory() as db:
                    stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
                    result = await db.execute(stmt)
                    job = result.scalar_one_or_none()
                    if job:
                        metadata = dict(job.job_metadata or {})
                        preview = metadata.get("dag_preview")
                        if preview:
                            self._pending_approvals[job_id] = preview
            except Exception:
                logger.exception("[AutoCreator] Failed to load pending DAG from DB for approval")

        if job_id not in self._pending_approvals:
            logger.warning("[AutoCreator] No pending DAG for job %s", job_id)
            return False

        pending = self._pending_approvals.get(job_id, {})
        pending["_approved"] = approved
        self._pending_approvals[job_id] = pending

        # Update persisted job metadata with approval
        try:
            from datetime import datetime
            from src.api.utils.database import async_session_factory
            from src.api.utils.models import NexusJobDB
            from sqlalchemy import select

            async with async_session_factory() as db:
                stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()
                if job:
                    metadata = dict(job.job_metadata or {})
                    metadata.pop("dag_preview", None)
                    metadata["dag_approval_state"] = {
                        "awaiting": False,
                        "approved": bool(approved),
                        "approved_at": datetime.utcnow().isoformat(),
                    }
                    job.job_metadata = metadata
                    await db.commit()
        except Exception:
            logger.exception("[AutoCreator] Failed to persist approval via API")

        # Publish approval to Redis pub/sub channel for cross-worker signaling.
        # This is the **only** mechanism that wakes a waiter on a different
        # worker (the API request may be on a process whose
        # ``_approval_events`` does not contain this job).
        await self._publish_approval(job_id, approved)

        # Same-process fast path: if the API request happened to land on the
        # same worker that's awaiting, set the local event immediately and
        # skip the round-trip through Redis. In cross-worker setups this
        # branch is a no-op and the wakeup arrives via the Redis listener.
        event = self._approval_events.get(job_id)
        if event:
            event.set()
            logger.info("[AutoCreator] DAG %s for job %s (same-process fast path)", "APPROVED" if approved else "REJECTED", job_id)
            return True

        # If no local waiter, the Redis listener on the waiter worker will
        # pick up the message we just published. Return True because we
        # persisted the approval.
        logger.info("[AutoCreator] DAG approval persisted for job %s (cross-worker; awaiting Redis pickup)", job_id)
        return True

    async def get_pending_approval(self, job_id: str) -> dict | None:
        """Get the pending DAG preview for a job (for API polling)."""
        pending = self._pending_approvals.get(job_id)
        if pending:
            # Strip internal metadata
            return {k: v for k, v in pending.items() if not k.startswith("_")}

        # If not in memory, try loading persisted preview from DB
        try:
            from src.api.utils.database import async_session_factory
            from src.api.utils.models import NexusJobDB
            from sqlalchemy import select

            async with async_session_factory() as db:
                stmt = select(NexusJobDB).where(NexusJobDB.id == str(job_id))
                result = await db.execute(stmt)
                job = result.scalar_one_or_none()
                if job:
                    metadata = dict(job.job_metadata or {})
                    preview = metadata.get("dag_preview")
                    if preview:
                        # Do not include internal fields
                        return {k: v for k, v in preview.items() if not k.startswith("_")}
        except Exception:
            logger.exception("[AutoCreator] Failed to load pending DAG preview from DB")

        return None


    # ─── Redis Pub/Sub for Cross-Worker Approval Signaling ────────────

    async def _publish_approval(self, job_id: str, approved: bool) -> None:
        """
        Publish an approval decision to Redis pub/sub so other workers
        listening on this job can wake up.
        """
        try:
            from src.api.utils.redis import get_async_redis
        except ImportError:
            logger.debug("[AutoCreator] Redis not available, skipping pub/sub publish")
            return

        channel = f"{APPROVAL_CHANNEL_PREFIX}:{job_id}"
        try:
            redis = await get_async_redis()
            message = "approved" if approved else "rejected"
            await redis.publish(channel, message)
            logger.info(f"[AutoCreator] Published {message} to channel {channel}")
        except Exception as e:
            logger.warning(f"[AutoCreator] Failed to publish approval to {channel}: {e}")

    async def _subscribe_to_approval_channel(self, job_id: str) -> None:
        """
        Subscribe to the approval channel for a job using Redis pub/sub.
        When approval is published on another worker, this listener will
        set the local asyncio.Event to wake up the waiter.
        """
        try:
            from src.api.utils.redis import get_async_redis
        except ImportError:
            logger.warning("[AutoCreator] Redis not available, skipping pub/sub subscription")
            return

        channel = f"{APPROVAL_CHANNEL_PREFIX}:{job_id}"
        try:
            redis = await get_async_redis()
            pubsub = redis.pubsub()
            await pubsub.subscribe(channel)
            self._approval_subscriptions[job_id] = pubsub
            logger.info(f"[AutoCreator] Subscribed to approval channel: {channel}")

            # Start background listener task
            task = asyncio.create_task(self._listen_for_approval(job_id, channel))
            self._approval_listeners[job_id] = task
        except Exception as e:
            logger.warning(f"[AutoCreator] Failed to subscribe to approval channel {channel}: {e}")

    async def _listen_for_approval(self, job_id: str, channel: str) -> None:
        """
        Background task that listens for approval messages on Redis pub/sub.
        When a message arrives, set the local asyncio.Event to wake the waiter.
        """
        pubsub = self._approval_subscriptions.get(job_id)
        if not pubsub:
            return

        try:
            while True:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=300.0)
                    if message and message.get("type") == "message":
                        data = message.get("data", "")
                        logger.info(f"[AutoCreator] Received approval message on {channel}: {data}")

                        # Mark approval in the pending dict
                        if job_id in self._pending_approvals:
                            self._pending_approvals[job_id]["_approved"] = (data == "approved")

                        # Signal the local waiter
                        event = self._approval_events.get(job_id)
                        if event:
                            event.set()
                            logger.info(f"[AutoCreator] Woke up local waiter for job {job_id}")

                        # Approval is one-shot per job. Exit the listener;
                        # _wait_for_dag_approval will call
                        # _cleanup_approval_subscription to release the
                        # pubsub handle and cancel this task.
                        break

                    # Timeout waiting for approval; exit listener
                    if message is None:
                        logger.info(f"[AutoCreator] Approval listener timeout for {job_id}, exiting")
                        break

                except asyncio.TimeoutError:
                    logger.debug(f"[AutoCreator] Listener timeout for {job_id} (expected)")
                    break
        except Exception as e:
            logger.exception(f"[AutoCreator] Error in approval listener for {job_id}: {e}")
        finally:
            # Clean up subscription
            await self._cleanup_approval_subscription(job_id)

    async def _cleanup_approval_subscription(self, job_id: str) -> None:
        """Clean up Redis pub/sub subscription for a job."""
        pubsub = self._approval_subscriptions.pop(job_id, None)
        if pubsub:
            try:
                await pubsub.unsubscribe(f"{APPROVAL_CHANNEL_PREFIX}:{job_id}")
                await pubsub.close()
                logger.info(f"[AutoCreator] Cleaned up approval subscription for {job_id}")
            except Exception as e:
                logger.warning(f"[AutoCreator] Error cleaning up subscription: {e}")

        # Cancel listener task
        task = self._approval_listeners.pop(job_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _source_visual_assets(self, segments, job_id, niche, engine, style, use_dag: bool = False):
        if use_dag:
            return await self._source_visual_assets_via_dag(segments, job_id, niche)
        visual_paths = []
        for i, seg in enumerate(segments):
            best_path = await self._source_single_visual_asset(seg, i, job_id, niche)
            if best_path:
                visual_paths.append(best_path)
        return visual_paths

    async def _source_visual_assets_via_dag(self, segments, job_id, niche):
        """
        Parallel asset sourcing using the DAG video compiler.
        Each segment gets its own stock search, download, and audit nodes,
        all executing in parallel batches via the DAG scheduler.
        """
        from src.services.video_engine.dag_executor import BaseNode, DAGCompiler, Scheduler, Cache

        cache = Cache()
        compiler = DAGCompiler()
        scheduler = Scheduler(cache=cache)

        # Pre-import services for use in node closures
        from src.services.video_engine.stock_service import base_stock_service
        from src.services.video_engine.downloader import base_downloader_service
        from src.services.nexus_engine.platform_composer import base_composer_service

        # ─── Inline DAG nodes ────────────────────────────────────────────
        # Each class captures its dependencies via closure.

        class _ComposerSearchNode(BaseNode):
            """Search all sources (stock + CloakBrowser + discovery) for visual assets."""

            async def execute(self, ctx: dict) -> dict:
                prompt = str(self.params.get("prompt", niche))
                logger.info(f"[DAG] Composer search for: {prompt}")
                platform_urls, stock_urls = await base_composer_service.compose_for_dag(
                    prompt, niche, count=3,
                )
                all_urls = stock_urls + platform_urls
                logger.info(
                    "[DAG] Composer found %d stock + %d platform URLs for: %s",
                    len(stock_urls), len(platform_urls), prompt,
                )
                return {"urls": all_urls, "platform_urls": platform_urls, "prompt": prompt}

        class _VideoDownloadNode(BaseNode):
            """Download video URLs from upstream search results."""

            async def execute(self, ctx: dict) -> dict:
                search_id = self.inputs[0] if self.inputs else None
                search_result = ctx.get(search_id, {}) if search_id else {}
                urls = search_result.get("urls", [])
                platform_urls = set(search_result.get("platform_urls", []))
                seg_idx = self.params.get("seg_idx", 0)

                paths = []
                for url in urls:
                    if url in platform_urls:
                        path = await base_downloader_service.download_video(url)
                    else:
                        path = await base_stock_service.download_stock_video(url)
                    if path:
                        paths.append(path)
                return {"paths": paths, "seg_idx": seg_idx}

        class _VisionAuditNode(BaseNode):
            """Audit downloaded video against visual prompt using vision LLM."""

            async def execute(self, ctx: dict) -> dict:
                # Get download results from upstream
                download_id = self.inputs[0] if self.inputs else None
                download_result = ctx.get(download_id, {}) if download_id else {}
                paths = download_result.get("paths", [])
                prompt = str(self.params.get("prompt", ""))
                seg_idx = self.params.get("seg_idx", 0)
                job_id_str = str(self.params.get("job_id", ""))

                best: dict | None = None  # {path, score}
                for path in paths:
                    result = await self._run_vision_audit(path, prompt, job_id_str, seg_idx)
                    score = result.get("score", 50)
                    if result.get("passed"):
                        logger.info(
                            f"[DAG] Segment {seg_idx} passed audit: "
                            f"{path} (score={score})"
                        )
                        if best is None or score > best["score"]:
                            if best is not None and os.path.exists(best["path"]):
                                os.remove(best["path"])
                            best = {"path": path, "score": score}
                    else:
                        logger.warning(
                            f"[DAG] Segment {seg_idx} failed audit "
                            f"(score={score}), cleaning up: {path}"
                        )
                        if os.path.exists(path):
                            os.remove(path)

                if best:
                    return {"path": best["path"], "seg_idx": seg_idx, "score": best["score"]}

                if paths:
                    best_path = paths[0]
                    logger.warning(f"[DAG] Segment {seg_idx} using unaudited fallback: {best_path}")
                    return {"path": best_path, "seg_idx": seg_idx}

                return {"path": None, "seg_idx": seg_idx}

            async def _run_vision_audit(self, video_path: str, visual_prompt: str,
                                        job_id_str: str, seg_idx: int) -> dict:
                """Wrapper that calls the parent AutoCreator's _vision_audit.

                Returns dict with ``passed``, ``score``, ``reason``.
                """
                try:
                    return await self._parent_audit(video_path, visual_prompt, job_id_str, seg_idx)
                except Exception:
                    logger.exception("[DAG] Vision audit error — marking as failed")
                    return {"passed": False, "score": 0, "reason": "wrapper_error"}

        # ─── Build DAG nodes ─────────────────────────────────────────────
        all_nodes = []
        for i in range(len(segments)):
            prompt = segments[i].get("visual_prompt", niche)
            seg_id = f"seg_{i}"

            # Composer search (no dependencies — runs in batch 1)
            search_node = _ComposerSearchNode(
                node_id=f"{seg_id}_search",
                params={"prompt": prompt, "niche": niche, "seg_idx": i},
            )
            all_nodes.append(search_node)

            # Video download (depends on search result — runs after search completes)
            download_node = _VideoDownloadNode(
                node_id=f"{seg_id}_download",
                params={"seg_idx": i, "job_id": str(job_id)},
                inputs=[f"{seg_id}_search"],
            )
            all_nodes.append(download_node)

            # Vision audit (depends on download — runs after download)
            audit_node = _VisionAuditNode(
                node_id=f"{seg_id}_audit",
                params={"prompt": prompt, "seg_idx": i, "job_id": str(job_id)},
                inputs=[f"{seg_id}_download"],
            )
            # Inject parent audit method into the node instance
            audit_node._parent_audit = self._vision_audit
            all_nodes.append(audit_node)

        # ─── Compile & Execute ───────────────────────────────────────────
        logger.info(
            "[DAG] Compiling %d asset sourcing nodes for %d segments",
            len(all_nodes), len(segments),
        )
        plan = compiler.compile(all_nodes)
        logger.info(
            "[DAG] Executing %d nodes in %d parallel batches",
            plan.total_nodes(), plan.total_batches(),
        )

        context = await scheduler.run(plan)

        # ─── Collect results in order ────────────────────────────────────
        visual_paths = []
        for i in range(len(segments)):
            audit_result = context.get(f"seg_{i}_audit", {})
            path = audit_result.get("path") if isinstance(audit_result, dict) else None
            if path:
                visual_paths.append(path)
            else:
                logger.warning(f"[DAG] Segment {i} produced no visual asset")

        logger.info(
            "[DAG] Asset sourcing complete: %d/%d segments acquired",
            len(visual_paths), len(segments),
        )
        return visual_paths

    async def _source_single_visual_asset(self, seg, i, job_id, niche):
        from src.services.video_engine.stock_service import base_stock_service

        prompt = seg.get("visual_prompt", niche)
        logger.info(f"[AutoCreator] Sourcing visual for segment {i}: {prompt}")

        # Fetch up to 3 candidates for re-roll
        urls = await base_stock_service.fetch_b_roll(prompt, count=3)
        if not urls:
            logger.warning(f"[AutoCreator] No stock found for: {prompt}. Using fallback.")
            urls = await base_stock_service.fetch_b_roll(niche, count=1)

        best_path = await self._download_and_audit_visual_asset(urls, seg, i, job_id, niche)
        if best_path:
            return best_path

        # If all 3 fail, try one last time with generic niche prompt and skip audit
        logger.error(f"[AutoCreator] Segment {i} exhausted re-rolls. Falling back to generic.")
        fallback_urls = await base_stock_service.fetch_b_roll(niche, count=1)
        if fallback_urls:
            f_path = await base_stock_service.download_stock_video(fallback_urls[0])
            if f_path:
                return f_path

        return None

    async def _download_and_audit_visual_asset(self, urls, seg, i, job_id, niche):
        from src.services.video_engine.stock_service import base_stock_service

        best: dict | None = None  # {path, score}
        for attempt, url in enumerate(urls):
            path = await base_stock_service.download_stock_video(url)
            if not path:
                continue

            # Perform Scored Vision Audit (Phase 10-05)
            result = await self._vision_audit(path, seg.get("visual_prompt", niche), job_id, i)
            score = result.get("score", 50)
            if result.get("passed"):
                logger.info(
                    f"[AutoCreator] Segment {i} passed audit on attempt "
                    f"{attempt+1} (score={score})"
                )
                if best is None or score > best["score"]:
                    # Clean up previous best if we're replacing it
                    if best is not None and os.path.exists(best["path"]):
                        os.remove(best["path"])
                    best = {"path": path, "score": score}
            else:
                logger.warning(
                    f"[AutoCreator] Segment {i} failed audit on attempt "
                    f"{attempt+1} (score={score}). Re-rolling..."
                )
                if os.path.exists(path):
                    os.remove(path)

        if best:
            logger.info(
                f"[AutoCreator] Segment {i} selected best clip (score={best['score']})"
            )
            return best["path"]
        return None

    async def _vision_audit(self, video_path: str, visual_prompt: str, job_id: str, segment_idx: int) -> dict:
        """
        Extracts a frame and audits it against the visual prompt using configured vision LLMs.

        Returns dict with keys: ``passed`` (bool), ``score`` (int 0-100), ``reason`` (str).
        Uses a conservative default: failures in extraction or LLM providers return a failed audit
        so callers can re-roll or escalate.
        """
        from src.services.llm.service import unified_llm_service

        audit_frame_dir = "/tmp/ettametta/audit_source"
        os.makedirs(audit_frame_dir, exist_ok=True)
        frame_path = f"{audit_frame_dir}/audit_{job_id}_{segment_idx}.jpg"

        try:
            # Extract middle frame
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames // 2))
            ret, frame = cap.read()
            cap.release()

            if not ret or frame is None:
                logger.warning("[AutoCreator] Frame extraction failed for %s (seg=%s)", video_path, segment_idx)
                return {"passed": False, "score": 0, "reason": "frame_extraction_failed"}

            cv2.imwrite(frame_path, frame)

            # Try providers: primary Gemini, fallback Ollama (if configured)
            audit_result = None
            try:
                audit_result = await unified_llm_service.analyze_image(frame_path, visual_prompt, provider=LLMProvider.GEMINI)
                if not audit_result or not audit_result.get("content") or audit_result.get("error"):
                    raise RuntimeError("Gemini returned no content or error flag")
            except Exception as e:
                logger.warning("[AutoCreator] Gemini vision audit failed: %s", e)
                try:
                    from src.api.config import settings as app_settings
                    audit_result = await unified_llm_service.analyze_image(
                        frame_path, visual_prompt, provider=LLMProvider.OLLAMA, model=app_settings.OLLAMA_MODEL,
                    )
                    if not audit_result or not audit_result.get("content") or audit_result.get("error"):
                        raise RuntimeError("Ollama returned no content or error flag")
                except Exception as e2:
                    logger.exception("[AutoCreator] All vision audit providers failed: %s", e2)
                    if os.path.exists(frame_path):
                        os.remove(frame_path)
                    return {"passed": False, "score": 0, "reason": "llm_providers_failed"}

            content = audit_result.get("content", "0") if audit_result else "0"

            # Parse numeric score from LLM response (first 1-3 digit number)
            import re
            score_match = re.search(r"(\d{1,3})", str(content))
            score = int(score_match.group(1)) if score_match else 0
            score = max(0, min(100, score))

            # Clean up frame
            if os.path.exists(frame_path):
                os.remove(frame_path)

            passed = score >= VISION_AUDIT_THRESHOLD
            return {"passed": passed, "score": score, "reason": str(content)[:200]}
        except Exception:
            logger.exception("[AutoCreator] Vision audit unexpected error — failing conservative")
            try:
                if os.path.exists(frame_path):
                    os.remove(frame_path)
            except Exception:
                pass
            return {"passed": False, "score": 0, "reason": "audit_error"}

    async def _generate_voiceovers(self, segments, job_id):
        from src.services.audio.voiceover import base_voiceover_service
        voice_paths = []
        for _i, seg in enumerate(segments):
            text = seg.get("text", "")
            if text:
                path = await base_voiceover_service.generate_voiceover(text)
                if path:
                    voice_paths.append(path)
        return voice_paths

base_creator_service = AutoCreator()
