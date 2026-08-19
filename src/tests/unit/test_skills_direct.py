#!/usr/bin/env python3
"""
Direct test of OpenCLAW skills - runs inside the openclaw container
"""

import pytest
import sys
import os


PROJECT_DIR = "/app" if os.path.exists("/app") else "/root/ettametta"
sys.path.insert(0, PROJECT_DIR)

SKILLS_PARENT = os.path.join(PROJECT_DIR, "src", "services", "openclaw")
if os.path.isdir(SKILLS_PARENT) and SKILLS_PARENT not in sys.path:
    sys.path.insert(0, SKILLS_PARENT)

# Fallback: always check the canonical location
_FALLBACK_SKILLS = "/root/ettametta/src/services/openclaw"
if os.path.isdir(_FALLBACK_SKILLS) and _FALLBACK_SKILLS not in sys.path:
    sys.path.insert(0, _FALLBACK_SKILLS)


_KNOWN_SKILLS_DIRS = [
    os.path.join("/app", "skills"),
    os.path.join("/root/ettametta", "src", "services", "openclaw", "skills"),
    os.path.join("/root/ettametta", "skills"),
]


def _has_skills() -> bool:
    return any(os.path.isdir(p) for p in _KNOWN_SKILLS_DIRS)


async def test_discovery_skill():
    """Test Discovery skill"""
    if not _has_skills():
        pytest.skip("requires skills package in sys.path")
    from skills.discovery import discovery_skill
    result = discovery_skill.search_trends("motivation", limit=3, analyze=False)
    assert result is not None


async def test_content_editor_skill():
    """Test Content Editor skill"""
    if not _has_skills():
        pytest.skip("requires skills package in sys.path")
    from skills.content_editor import content_editor_skill
    result = await content_editor_skill.find_content(
        source="youtube", query="motivation", niche="motivation", limit=3
    )
    assert result is not None


def test_skills_loaded():
    """list available skills"""
    if not _has_skills():
        pytest.skip("requires skills package in sys.path")
    import skills
    skill_names = [
        name for name in dir(skills)
        if not name.startswith("_") and name.endswith("_skill")
    ]
    assert len(skill_names) > 10, f"Expected many skills, got {len(skill_names)}"
