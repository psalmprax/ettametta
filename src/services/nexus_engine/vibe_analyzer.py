"""Vibe analysis — Dify + LangChain provider queries for video vibe data.

Extracted from NexusOrchestrator to reduce god-class size.
"""

from __future__ import annotations

import logging
from typing import Any

from src.api.config import settings

logger = logging.getLogger(__name__)


async def query_dify_vibe(
    job_id: str,
    niche: str,
    style: str,
    blueprint_id: str,
    num_clips: int,
) -> dict[str, Any]:
    """Query Dify provider for video vibe data."""
    if not settings.DIFY_API_KEY:
        return {}

    from src.services.llm.dify_client import base_dify_client
    logger.info(f"[Nexus] Performing Dify Cognitive Analysis for {niche}")
    try:
        dify_resp = await base_dify_client.chat_messages(
            query=f"Analyze the video vibe for niche: {niche}. Context: {num_clips} clips, style: {style}",
            user_id=f"nexus_{job_id}",
            inputs={
                "niche": niche,
                "num_clips": num_clips,
                "blueprint": blueprint_id,
                "style": style,
            },
        )
        if not dify_resp or "answer" not in dify_resp:
            return {}

        answer = dify_resp["answer"]
        if "{" not in answer or "}" not in answer:
            return {}

        try:
            import json as json_lib
            start = answer.find("{")
            end = answer.rfind("}") + 1
            vibe_data = json_lib.loads(answer[start:end])
            logger.info(f"[Nexus] Dify suggested vibe: {vibe_data.get('vibe')}")
            return vibe_data
        except Exception:
            logger.warning("[Nexus] Dify returned non-JSON answer, using as 'explanation'")
            return {"vibe": "Cinematic", "explanation": answer}
    except Exception as e:
        logger.warning(f"[Nexus] Dify analysis failed, falling back: {e}")
        return {}


async def query_langchain_vibe(
    job_id: str,
    niche: str,
    num_clips: int,
    blueprint_id: str,
) -> dict[str, Any]:
    """Query LangChain provider for video vibe data."""
    from src.services.llm.langchain import langchain_service

    if not langchain_service.is_enabled():
        return {}

    logger.info(f"[Nexus] Performing LangChain Vibe Check for {niche}")
    vibe_data = await langchain_service.analyze_video_vibe(
        niche,
        {
            "num_clips": num_clips,
            "blueprint": blueprint_id,
            "job_id": str(job_id),
        },
    )
    if vibe_data:
        logger.info(f"[Nexus] LangChain suggested vibe: {vibe_data.get('vibe')}")
        return vibe_data
    return {}


async def determine_video_vibe(
    job_id: str,
    niche: str,
    style: str,
    blueprint_id: str,
    num_clips: int,
) -> dict[str, Any]:
    """Primary vibe check using Dify, with LangChain fallback."""
    vibe_data = await query_dify_vibe(job_id, niche, style, blueprint_id, num_clips)
    if not vibe_data:
        vibe_data = await query_langchain_vibe(job_id, niche, num_clips, blueprint_id)
    return vibe_data
