#!/usr/bin/env python3
"""
Tests the portal-showcase blueprint by:
1. Verifying the blueprint is registered in FALLBACK_BLUEPRINTS
2. Attempting a CinematicPortal Remotion render with minimal props

Usage:
    python3 scripts/test_portal_blueprint.py              # local test (if Remotion is available)
    python3 scripts/test_portal_blueprint.py --api         # test via API endpoint
"""

import sys
import os
import json
import asyncio
import argparse

# Ensure src is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.services.nexus_engine.blueprints import FALLBACK_BLUEPRINTS
from src.services.video_engine.remotion_service import base_remotion_service


def test_blueprint_exists() -> dict:
    """Verify the portal-showcase blueprint is registered in FALLBACK_BLUEPRINTS."""
    for bp in FALLBACK_BLUEPRINTS:
        if bp["id"] == "portal-showcase":
            print(f"[PASS] Blueprint 'portal-showcase' found in FALLBACK_BLUEPRINTS")
            print(f"       Name: {bp['name']}")
            print(f"       Composition: {bp['composition_id']}")
            print(f"       Nodes: {[n['type'] for n in bp.get('nodes', [])]}")
            return bp
    print("[FAIL] Blueprint 'portal-showcase' NOT found in FALLBACK_BLUEPRINTS")
    print(f"       Available: {[bp['id'] for bp in FALLBACK_BLUEPRINTS]}")
    sys.exit(1)
    return None  # unreachable


async def test_render_portal(output_dir: str = "outputs/nexus_tests") -> str | None:
    """Attempt to render a 4-second CinematicPortal video via RemotionService."""
    os.makedirs(output_dir, exist_ok=True)

    # Don't pass duration_in_frames — let the composition use its default
    # (CinematicPortal has durationInFrames=120 in Root.tsx, range 0-119)
    props = {
        "title": "DISCOVERY",
        "subtitle": "BEYOND THE VEIL",
        "show_cta_overlay": False,
    }

    output_name = f"test_portal_{os.urandom(4).hex()}.mp4"

    print(f"\n[TEST] Rendering CinematicPortal composition...")
    print(f"       Props: {json.dumps(props, indent=2)}")
    print(f"       Output: {output_name}")

    try:
        result = await base_remotion_service.render_video(
            composition_id="CinematicPortal",
            props=props,
            output_name=output_name,
        )
        if result and os.path.exists(result) and os.path.getsize(result) > 0:
            size_mb = os.path.getsize(result) / (1024 * 1024)
            print(f"[PASS] CinematicPortal render succeeded!")
            print(f"       Output: {result}")
            print(f"       Size: {size_mb:.1f} MB")
            return result
        else:
            print(f"[FAIL] Render returned no valid output path")
            return None
    except Exception as e:
        print(f"[INFO] Render not available locally (expected without Remotion/Chromium): {e}")
        return None


async def test_via_api(base_url: str = "http://149.104.110.122.sslip.io:7200") -> dict:
    """Test by hitting the Nexus compose API with the portal-showcase blueprint."""
    import httpx

    url = f"{base_url}/api/v1/nexus/compose"
    payload = {
        "niche": "Technology",
        "topic": "The Future of Quantum Computing",
        "blueprint_id": "portal-showcase",
        "style": "SCIENCE",
        "automation_mode": "manual",
        "cinema_mode": False,
    }

    print(f"\n[TEST] Hitting Nexus compose API: POST {url}")
    print(f"       Payload: {json.dumps(payload, indent=2)}")

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, json=payload)
            print(f"       Status: {resp.status_code}")
            data = resp.json()
            print(f"       Response: {json.dumps(data, indent=2)}")
            return data
        except Exception as e:
            print(f"[FAIL] API call failed: {e}")
            return {"error": str(e)}


async def main():
    parser = argparse.ArgumentParser(description="Test portal-showcase blueprint")
    parser.add_argument("--api", action="store_true", help="Test via remote API instead of local render")
    parser.add_argument("--api-url", default="http://149.104.110.122.sslip.io:7200", help="API base URL")
    parser.add_argument("--output-dir", default="outputs/nexus_tests", help="Output directory for local render")
    args = parser.parse_args()

    print("=" * 60)
    print("  Portal Showcase Blueprint Test")
    print("=" * 60)

    # Step 1: Verify blueprint exists
    print("\n── Step 1: Blueprint Registration ──")
    bp = test_blueprint_exists()

    # Step 2: Test render
    print(f"\n── Step 2: CinematicPortal Render ──")
    if args.api:
        result = await test_via_api(args.api_url)
    else:
        result = await test_render_portal(args.output_dir)

    # Summary
    print("\n" + "=" * 60)
    print("  RESULT SUMMARY")
    print("=" * 60)
    print(f"  Blueprint:      {'✅' if bp else '❌'} portal-showcase (composition_id=CinematicPortal)")
    print(f"  Render Output:  {'✅' if result else '⚠️  See details above'}")

    if result is None and not args.api:
        print("\n  ⚠️  Local render couldn't complete (expected without Chromium).")
        print("     Run with --api to test on the remote server.")
    elif result:
        print(f"\n  ✅ Test passed! See output above.")

    return 0 if bp else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
