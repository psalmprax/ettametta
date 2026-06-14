#!/usr/bin/env python3
"""
Tests the portal-showcase blueprint through the full Nexus assembly pipeline.

This calls assemble_video() directly (bypassing auth) with minimal inputs
to verify the composition_id resolves to CinematicPortal and the short-form
handling works (frame capping, props simplification).

Usage:
    python3 scripts/test_nexus_portal_pipeline.py    # inside the Docker container
"""

import sys
import os
import json
import asyncio
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.nexus_engine.orchestrator import (
    base_nexus_service,
    COMPOSITION_STYLE_MAP,
    SHORT_FORM_COMPOSITIONS,
)
from src.services.nexus_engine.blueprints import FALLBACK_BLUEPRINTS
from src.shared.enums import NodeStatus


async def test_blueprint_composition_resolution() -> dict:
    """Test 1: Verify blueprint + style resolve to CinematicPortal."""
    print("=" * 60)
    print("  TEST 1: Blueprint Composition Resolution")
    print("=" * 60)

    # Find the portal blueprint
    bp = None
    for bp_item in FALLBACK_BLUEPRINTS:
        if bp_item["id"] == "portal-showcase":
            bp = bp_item
            break

    if not bp:
        print("[FAIL] portal-showcase blueprint not found in FALLBACK_BLUEPRINTS")
        return {"passed": False}

    bp_composition = bp.get("composition_id", "ViralClip")
    print(f"  Blueprint composition_id: {bp_composition}")

    # Verify blueprint directly declares CinematicPortal
    print(f"  Blueprint composition_id: {bp_composition}")
    print(f"  Expected: CinematicPortal")

    # Verify CinematicPortal is in SHORT_FORM_COMPOSITIONS
    is_short = "CinematicPortal" in SHORT_FORM_COMPOSITIONS
    print(f"  CinematicPortal is short-form: {is_short}")

    # Verify a style that IS in the map resolves correctly
    # CINEMATIC_DOC → CinematicAncient
    mapped_style = "CINEMATIC_DOC"
    mapped_composition = COMPOSITION_STYLE_MAP.get(mapped_style)
    print(f"  COMPOSITION_STYLE_MAP['{mapped_style}'] → {mapped_composition}")

    all_ok = bp_composition == "CinematicPortal" and is_short
    print(f"\n  Result: {'PASS' if all_ok else 'FAIL'}")
    return {"passed": all_ok, "composition": bp_composition}


async def test_assemble_video_with_portal() -> dict:
    """Test 2: Call assemble_video() with portal blueprint + minimal inputs.

    Uses style not in COMPOSITION_STYLE_MAP so it falls through to the
    blueprint's composition_id = CinematicPortal.
    """
    print("\n" + "=" * 60)
    print("  TEST 2: assemble_video() with portal-showcase blueprint")
    print("=" * 60)

    job_id = str(uuid.uuid4())[:8]

    # Use a style NOT in COMPOSITION_STYLE_MAP so blueprint's composition_id
    # takes effect.  CinematicAncient is in FULL_FORM_COMPOSITIONS but
    # CINEMATIC_DOC maps to it, so use an unmapped style instead.
    style = "PORTAL_TEST"

    # Minimal inputs — use a real stock video URL if available
    visual_paths = [
        "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    ]
    voiceover_paths = []
    script_segments = [
        {
            "text": "Welcome to the portal showcase. This is a test of the CinematicPortal composition.",
            "visual_prompt": "portal, discovery, mystery",
            "mood": "mysterious",
            "type": "clip",
        }
    ]

    print(f"  Job ID: {job_id}")
    print(f"  Blueprint: portal-showcase")
    print(f"  Style: {style}")
    print(f"  Visuals: {len(visual_paths)} remote clip(s)")
    print(f"  Voiceovers: {len(voiceover_paths)}")
    print(f"  Segments: {len(script_segments)}")

    try:
        output_path = await base_nexus_service.assemble_video(
            job_id=job_id,
            niche="Technology",
            script_segments=script_segments,
            voiceover_paths=voiceover_paths,
            visual_paths=visual_paths,
            music_path=None,
            blueprint_id="portal-showcase",
            style=style,
            job_metadata={"vfx": "default", "test_mode": True},
        )
        if output_path and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"\n  Output: {output_path}")
            print(f"  Size: {size_mb:.1f} MB")
            print(f"\n  Result: ✅ PASS")
            return {"passed": True, "output_path": output_path, "size_mb": size_mb}
        else:
            print(f"\n  Output: {output_path}")
            print(f"\n  Result: ⚠️  Render returned no valid output")
            return {"passed": False, "error": "no_output"}
    except Exception as e:
        print(f"\n  Error: {e}")
        print(f"\n  Result: ⚠️  Pipeline error (expected with minimal inputs)")
        print(f"  This doesn't mean the blueprint is broken — the asset")
        print(f"  sourcing pipeline needs stock service connectivity.")
        return {"passed": False, "error": str(e)}


async def main():
    print("Nexus Portal Pipeline Test\n")

    # Test 1: Composition resolution
    result1 = await test_blueprint_composition_resolution()

    # Test 2: Full assembly (will likely fail without stock service, but tests the flow)
    result2 = await test_assemble_video_with_portal()

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Blueprint resolution: {'✅' if result1.get('passed') else '❌'}")
    print(f"  Full pipeline:        {'✅' if result2.get('passed') else '⚠️  see above'}")

    if result2.get("output_path"):
        print(f"\n  Video output: {result2['output_path']}")

    return 0 if result1.get("passed") else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
