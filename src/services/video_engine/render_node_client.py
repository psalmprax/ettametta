"""
Render Node Dispatch Client
============================

Centralized HTTP client for offloading video generation to a remote GPU node
configured via the ``RENDER_NODE_URL`` env var. This client was missing from
the orchestrator's surface area — individual inference services (wan, ltx,
hunyuan, etc.) each rolled their own ad-hoc POST + poll loops, and the
orchestrator had no way to dispatch blueprint execution to a remote node
at all.

Design
------
1. **Single source of truth** for the RENDER_NODE_URL contract. Other
   services should import ``base_render_node_client`` rather than building
   their own httpx calls.
2. **Circuit breaker** so a flapping render node doesn't take down the
   orchestrator. After ``failure_threshold`` consecutive failures the
   breaker opens for ``recovery_timeout`` seconds.
3. **Async polling** with a configurable max wait so blueprint execution
   can block on remote generation without hanging forever.
4. **Graceful local fallback** — if no ``RENDER_NODE_URL`` is set, every
   call returns ``None`` and the caller can decide to run locally. The
   client never crashes on missing config.

Usage
-----
    from src.services.video_engine.render_node_client import (
        base_render_node_client,
        RenderNodeRequest,
    )

    req = RenderNodeRequest(
        model="ltx-video",
        prompt="A cinematic cityscape at sunset",
        duration_seconds=5,
        aspect_ratio="16:9",
    )
    result = await base_render_node_client.dispatch_and_await(req)
    if result is None:
        # No remote node configured, or it failed — fall back to local
        ...

Env
---
    RENDER_NODE_URL              Required. The remote node base URL.
    RENDER_NODE_TIMEOUT          Optional. Per-request timeout (default 60s).
    RENDER_NODE_FAILURE_THRESH   Optional. Failures before breaker opens (default 3).
    RENDER_NODE_RECOVERY_SECONDS Optional. Breaker recovery window (default 300s).
    RENDER_NODE_POLL_INTERVAL    Optional. Seconds between status polls (default 5s).
    RENDER_NODE_MAX_WAIT         Optional. Hard cap on total wait (default 1800s).
    RENDER_NODE_AUTH_TOKEN       Optional. Bearer token sent to the remote node.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from src.api.utils.resilience import CircuitBreaker

logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        logger.warning(
            "[RenderNodeClient] %s=%r is not an int; falling back to %d",
            name, raw, default,
        )
        return default


@dataclass
class RenderNodeRequest:
    """What to ask the remote node to generate."""
    model: str
    prompt: str
    duration_seconds: int = 5
    aspect_ratio: str = "16:9"
    image_url: str | None = None  # for image2video
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class RenderNodeResult:
    """What the remote node returned when generation finished."""
    job_id: str
    video_url: str
    model: str
    duration_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class RenderNodeClient:
    """
    Centralized RENDER_NODE_URL dispatch + poll client.

    All other services that need to offload generation to a remote GPU
    should use this client instead of building their own HTTP calls.
    """

    def __init__(self) -> None:
        self.base_url = (os.getenv("RENDER_NODE_URL") or "").rstrip("/")
        self.request_timeout = _env_int("RENDER_NODE_TIMEOUT", 60)
        self.failure_threshold = _env_int("RENDER_NODE_FAILURE_THRESH", 3)
        self.recovery_timeout = _env_int("RENDER_NODE_RECOVERY_SECONDS", 300)
        self.poll_interval = _env_int("RENDER_NODE_POLL_INTERVAL", 5)
        self.max_wait = _env_int("RENDER_NODE_MAX_WAIT", 1800)
        self.auth_token = os.getenv("RENDER_NODE_AUTH_TOKEN", "")

        self.breaker = CircuitBreaker(
            name="RenderNode",
            failure_threshold=self.failure_threshold,
            recovery_timeout=self.recovery_timeout,
        )

        if not self.base_url:
            logger.info(
                "[RenderNodeClient] RENDER_NODE_URL not set; remote dispatch "
                "disabled. Callers should fall back to local generation."
            )

    @property
    def is_configured(self) -> bool:
        """True if a remote node URL is configured. False means callers
        MUST run locally."""
        return bool(self.base_url)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def health_check(self) -> bool:
        """Returns True if the remote node is reachable. Does not consult
        the circuit breaker — useful for periodic liveness probes."""
        if not self.is_configured:
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.base_url}/health", headers=self._headers()
                )
                return resp.status_code == 200
        except Exception as e:
            logger.debug("[RenderNodeClient] health check failed: %s", e)
            return False

    async def dispatch(self, request: RenderNodeRequest) -> str | None:
        """
        POST a generation job to the remote node. Returns the job_id
        (string) on success, or None if the node is not configured, the
        circuit breaker is open, or the POST fails. Does NOT poll — the
        caller can either call ``poll()`` separately, or use the
        convenience ``dispatch_and_await()`` below.
        """
        if not self.is_configured:
            return None
        if self.breaker.is_open():
            logger.warning(
                "[RenderNodeClient] circuit breaker OPEN; refusing to dispatch"
            )
            return None

        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "duration": request.duration_seconds,
            "aspect_ratio": request.aspect_ratio,
        }
        if request.image_url:
            payload["image_url"] = request.image_url
        payload.update(request.extra)

        try:
            async with httpx.AsyncClient(timeout=self.request_timeout) as client:
                resp = await client.post(
                    f"{self.base_url}/generate",
                    json=payload,
                    headers=self._headers(),
                )
                if resp.status_code not in (200, 201):
                    logger.error(
                        "[RenderNodeClient] dispatch %s: %d %s",
                        request.model, resp.status_code, resp.text[:200],
                    )
                    self.breaker.record_failure()
                    return None
                data = resp.json()
        except Exception as e:
            logger.exception(
                "[RenderNodeClient] dispatch failed for model=%s: %s",
                request.model, e,
            )
            self.breaker.record_failure()
            return None

        self.breaker.record_success()
        job_id = data.get("id") or data.get("job_id")
        if not job_id:
            logger.error(
                "[RenderNodeClient] dispatch returned no job id: %s", data,
            )
            return None
        return str(job_id)

    async def poll(self, job_id: str) -> dict[str, Any] | None:
        """
        GET the current status of a remote generation job. Returns the raw
        JSON body on success, or None on transport failure. The caller is
        responsible for interpreting the ``state`` field.
        """
        if not self.is_configured:
            return None
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{self.base_url}/jobs/{job_id}",
                    headers=self._headers(),
                )
                if resp.status_code != 200:
                    return None
                return resp.json()
        except Exception as e:
            logger.warning(
                "[RenderNodeClient] poll failed for %s: %s", job_id, e
            )
            return None

    async def dispatch_and_await(
        self, request: RenderNodeRequest
    ) -> RenderNodeResult | None:
        """
        Convenience wrapper: dispatch the job, then poll until it reaches a
        terminal state (completed/failed) or the ``max_wait`` ceiling is
        hit. Returns a ``RenderNodeResult`` on success, ``None`` otherwise
        (caller should fall back to local generation).
        """
        job_id = await self.dispatch(request)
        if not job_id:
            return None

        terminal_states = {"completed", "failed", "complete", "error"}
        deadline = time.monotonic() + self.max_wait
        last_state: str = "queued"

        while time.monotonic() < deadline:
            data = await self.poll(job_id)
            if data is not None:
                last_state = (data.get("state") or "").lower()
                if last_state in ("completed", "complete"):
                    assets = data.get("assets") or {}
                    video_url = (
                        assets.get("video") if isinstance(assets, dict) else None
                    ) or data.get("video_url")
                    if not video_url:
                        logger.error(
                            "[RenderNodeClient] job %s completed but no video URL",
                            job_id,
                        )
                        return None
                    return RenderNodeResult(
                        job_id=job_id,
                        video_url=video_url,
                        model=data.get("model") or request.model,
                        duration_seconds=float(data.get("duration") or 0.0),
                        metadata=data,
                    )
                if last_state in ("failed", "error"):
                    logger.error(
                        "[RenderNodeClient] job %s failed: %s",
                        job_id, data.get("failure_reason") or "unknown",
                    )
                    return None
            await asyncio.sleep(self.poll_interval)

        logger.error(
            "[RenderNodeClient] job %s did not complete within %ds (last state: %s)",
            job_id, self.max_wait, last_state,
        )
        return None


base_render_node_client = RenderNodeClient()
