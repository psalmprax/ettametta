"""
Automation Mode Configuration
==============================

Three-tier automation model for the DAG video compiler:

MANUAL  (0)  - Hand-crafted DAG: user writes nodes, the DAG executes them.
               No AI involvement in structure. Asset sourcing is parallel
               and efficient, but the user decides the graph.

PARTIAL (1)  - AI generates the DAG from a prompt, but user approves before
               execution. Asset sourcing, script generation, and style
               selection are automated. User can review/edit nodes.

FULL    (2)  - End-to-end: prompt → AI generates DAG → auto-executes with
               no manual intervention. Includes semantic caching and
               similarity-based reuse of previous DAG subgraphs.

The mode is configurable per-job (passed as a parameter) and at the
system level (settings.AUTOMATION_MODE).

Usage:
    from src.services.video_engine.automation import AutomationMode, resolve_mode

    # Use the enum directly when calling pipeline functions
    await auto_creator.create_cinema_video(
        ...,
        automation_mode=AutomationMode.PARTIAL,
    )

    # Or resolve from config with per-job override
    mode = resolve_mode(settings, job_override="FULL")
"""

from __future__ import annotations

import enum
import logging
from typing import Any

logger = logging.getLogger(__name__)


class AutomationMode(str, enum.Enum):
    """Three-tier automation model for the DAG video compiler."""

    MANUAL = "MANUAL"
    """User constructs DAG nodes by hand. No AI involvement in graph structure.
    This is the existing `use_dag=True` behavior — parallel asset sourcing
    via inline nodes, but the user defines the full pipeline."""

    PARTIAL = "PARTIAL"
    """AI generates the DAG structure from a prompt, but execution pauses
    for user approval before rendering. The user can review generated nodes,
    edit params, and approve or reject. Best for iterative editing."""

    FULL = "FULL"
    """End-to-end automation: prompt → AI generates DAG → auto-executes.
    No manual intervention. Uses semantic caching to detect similar prompts
    and reuse previous DAG subgraphs for efficiency."""

    @classmethod
    def from_str(cls, value: str) -> "AutomationMode":
        """Parse a string value to AutomationMode, case-insensitive.

        Accepts 'MANUAL', 'PARTIAL', 'FULL' (or any case variant).
        Falls back to MANUAL on unknown values.
        """
        try:
            return cls(value.upper())
        except ValueError:
            logger.warning(
                "[AutomationMode] Unknown mode '%s', falling back to MANUAL",
                value,
            )
            return cls.MANUAL

    @classmethod
    def is_valid(cls, value: str) -> bool:
        try:
            cls(value.upper())
            return True
        except ValueError:
            return False


def resolve_mode(
    settings_obj: Any | None = None,
    job_override: str | None = None,
) -> AutomationMode:
    """Resolve the effective automation mode.

    Priority:
    1. ``job_override`` (per-job parameter) — if provided and valid
    2. ``settings.AUTOMATION_MODE`` — system-level default
    3. ``Settings.AUTOMATION_MODE`` env var fallback
    4. ``AutomationMode.MANUAL`` — final fallback

    Args:
        settings_obj: A settings object with an ``AUTOMATION_MODE`` attribute.
                      If None, reads from ``src.api.config.settings``.
        job_override: Per-job override string (e.g., ``"FULL"``, ``"partial"``).

    Returns:
        The resolved AutomationMode.
    """
    # 1. Per-job override takes priority
    if job_override:
        mode = AutomationMode.from_str(job_override)
        return mode

    # 2. System-level setting
    if settings_obj is not None:
        sys_mode = getattr(settings_obj, "AUTOMATION_MODE", None)
        if sys_mode:
            return AutomationMode.from_str(sys_mode)

    # 3. Try loading from config directly
    try:
        from src.api.config import settings as app_settings
        sys_mode = getattr(app_settings, "AUTOMATION_MODE", None)
        if sys_mode:
            return AutomationMode.from_str(sys_mode)
    except (ImportError, AttributeError):
        pass

    # 4. Fallback
    return AutomationMode.MANUAL


# Constants for tier thresholds
MODE_TO_INT = {
    AutomationMode.MANUAL: 0,
    AutomationMode.PARTIAL: 1,
    AutomationMode.FULL: 2,
}

MODE_TO_LABEL = {
    AutomationMode.MANUAL: "🛠️ Manual — User defines the DAG",
    AutomationMode.PARTIAL: "⚡ Partial — AI generates, user approves",
    AutomationMode.FULL: "🤖 Full — Autonomous end-to-end",
}


def mode_to_int(mode: AutomationMode) -> int:
    """Get integer tier for threshold comparisons."""
    return MODE_TO_INT.get(mode, 0)


def is_at_least(mode: AutomationMode, threshold: AutomationMode) -> bool:
    """Check if ``mode`` is at or above ``threshold`` in automation level."""
    return mode_to_int(mode) >= mode_to_int(threshold)
