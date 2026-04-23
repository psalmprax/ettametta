#!/usr/bin/env python3
"""
End-to-End Video Lead Generation + Editing Test
================================================

Compares AI-generated video content against professional editing standards.

Workflow:
1. Connect to remote server API container
2. Run video lead discovery for a niche
3. Create scene-based video fusion plan
4. Generate actual video using RealVideoFusionEngine
5. Compare output metrics against professional standards
"""

import asyncio
import sys
import os
from pathlib import Path

# Environment setup
os.environ["DEBUG"] = "false"

# Add project to path
root = Path(__file__).parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src"))

from services.discovery.video_lead_scanner import video_lead_scanner
from services.video_engine.scene_orchestrator import scene_based_orchestrator
from services.video_engine.synthesis_service import base_generative_service
from api.config import settings
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_full_video_workflow(niche: str = "AI productivity tools"):
    """Run complete video lead → editing workflow"""

    print("\n" + "=" * 70)
    print("🎬 END-TO-END VIDEO WORKFLOW TEST")
    print("=" * 70)
    print(f"Niche: {niche}")
    print(f"LLM Provider: {settings.DEFAULT_LLM_PROVIDER}")
    print(f"Ollama Model: {getattr(settings, 'OLLAMA_MODEL', 'N/A')}")

    # ── Phase 1: Video Lead Discovery ────────────────────────────────────
    print("\n" + "─" * 70)
    print("PHASE 1: VIDEO LEAD DISCOVERY")
    print("─" * 70)

    try:
        print(f"🔍 Scanning for high-performing videos in '{niche}'...")

        leads = await video_lead_scanner.scan_for_video_leads(
            niche=niche,
            platforms=["youtube", "tiktok"],
            min_viral_score=7.0,
            max_results=10,
        )

        print(f"✅ Found {len(leads)} video leads")

        if leads:
            print("\nTop 3 Leads:")
            for i, lead in enumerate(leads[:3], 1):
                print(f"  {i}. [{lead.platform}] {lead.title}")
                print(
                    f"     👁️  {lead.view_count:,} views | ⭐ {lead.viral_score:.1f}/10"
                )
                print(f"     🔗 {lead.url}")
        else:
            print("⚠️  No leads found via API — will use local fallback assets")

    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        leads = []

    # ── Phase 2: Scene-Based Production Planning ─────────────────────────
    print("\n" + "─" * 70)
    print("PHASE 2: SCENE-BASED PRODUCTION PLANNING")
    print("─" * 70)

    # Define content strategy
    scenes = [
        {
            "description": "Introduction to AI productivity landscape",
            "visual_prompt": f"Modern workspace with AI tools for {niche}, dynamic lighting, professional setup",
            "duration": 15,
            "key_elements": ["AI tools", "productivity", "workflow"],
        },
        {
            "description": "Practical demonstration of automation",
            "visual_prompt": f"Screen recording showing AI automation for {niche}, split-screen view",
            "duration": 20,
            "key_elements": ["automation", "demo", "tutorial"],
        },
        {
            "description": "Results and ROI analysis",
            "visual_prompt": f"Charts and metrics showing productivity gains from AI in {niche}",
            "duration": 15,
            "key_elements": ["metrics", "results", "ROI"],
        },
    ]

    print(
        f"📝 Planned {len(scenes)} scenes (~{sum(s['duration'] for s in scenes)}s total)"
    )

    # Create production plan using scene orchestrator
    try:
        production_plan = await scene_based_orchestrator.create_scene_based_video(
            scenes=scenes,
            topic=niche,
            style="Cinematic",
            discovered_videos=leads[:3] if leads else [],
        )

        print("✅ Production plan created")
        print(f"   Scenes: {len(production_plan.get('segments', []))}")
        print(f"   Resolution: {production_plan.get('resolution', 'N/A')}")
        print(f"   Frame Rate: {production_plan.get('frame_rate', 'N/A')}fps")

    except Exception as e:
        logger.error(f"Production planning failed: {e}")
        production_plan = {"segments": [], "resolution": "1920x1080", "frame_rate": 30}

    # ── Phase 3: Video Fusion & Rendering ────────────────────────────────
    print("\n" + "─" * 70)
    print("PHASE 3: VIDEO FUSION & RENDERING")
    print("─" * 70)

    # Check if we have available assets
    local_assets = list(Path("/root/ettametta/local_downloads/raw").glob("*.mp4"))
    print(f"📁 Available local assets: {len(local_assets)} videos")

    # Use local assets if no leads discovered
    if not production_plan.get("segments") and local_assets:
        print("🔧 Building fallback production from local assets...")
        production_plan = {
            "segments": [
                {
                    "scene": "Intro & Hook",
                    "video_path": str(local_assets[0]),
                    "duration": 10,
                    "transitions": "none",
                },
                {
                    "scene": "Main Content",
                    "video_path": str(
                        local_assets[1] if len(local_assets) > 1 else local_assets[0]
                    ),
                    "duration": 15,
                    "transitions": "smooth_fade",
                },
                {
                    "scene": "Outro & CTA",
                    "video_path": str(
                        local_assets[2] if len(local_assets) > 2 else local_assets[0]
                    ),
                    "duration": 10,
                    "transitions": "smooth_fade",
                },
            ],
            "resolution": "1920x1080",
            "frame_rate": 30,
        }

    # Execute video fusion
    try:
        print("🎞️  Starting video fusion engine...")

        # Use scene orchestrator for actual video synthesis
        result = await scene_based_orchestrator.produce_scene_based_video(
            segments=production_plan.get("segments", []),
            topic=niche,
            output_dir=settings.OUTPUT_DIR,
        )

        if result and result.get("success"):
            video_path = result.get("video_path", "")
            print(f"\n✅ VIDEO RENDERED SUCCESSFULLY")
            print(f"   📹 Output: {video_path}")
            print(f"   ⏱️  Duration: {result.get('duration', 0):.1f}s")
            print(f"   📊 Quality Score: {result.get('quality_score', 0):.1f}/10")

            # File size check
            if os.path.exists(video_path):
                size_mb = os.path.getsize(video_path) / (1024 * 1024)
                print(f"   💾 File Size: {size_mb:.1f} MB")

            return {
                "success": True,
                "video_path": video_path,
                "duration": result.get("duration", 0),
                "quality_score": result.get("quality_score", 0),
                "scenes_used": len(production_plan.get("segments", [])),
                "discovery_leads": len(leads),
            }
        else:
            print(f"❌ Video generation failed: {result.get('error', 'Unknown')}")
            return {"success": False, "error": result.get("error")}

    except Exception as e:
        logger.error(f"Video fusion error: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def compare_to_professional_standard(result: dict):
    """Compare generated video against professional editing benchmarks"""

    print("\n" + "=" * 70)
    print("📊 PROFESSIONAL STANDARD COMPARISON")
    print("=" * 70)

    if not result.get("success"):
        print("❌ Cannot compare — video generation failed")
        return

    # Professional benchmarks (empirical)
    BENCHMARKS = {
        "min_duration": 30,  # seconds (short-form minimum)
        "min_quality_score": 7.0,  # subjective quality rating
        "max_file_size_ratio": 50,  # MB per minute (efficiency)
        "ideal_fps": 30,
        "ideal_resolution": "1920x1080",
    }

    duration = result.get("duration", 0)
    quality = result.get("quality_score", 0)
    video_path = result.get("video_path", "")
    file_size_mb = (
        os.path.getsize(video_path) / (1024 * 1024) if os.path.exists(video_path) else 0
    )

    print(
        f"\n📏 Duration: {duration}s (benchmark: ≥{BENCHMARKS['min_duration']}s)",
        "✅" if duration >= BENCHMARKS["min_duration"] else "⚠️  Too short",
    )

    print(
        f"⭐ Quality Score: {quality}/10 (benchmark: ≥{BENCHMARKS['min_quality_score']})",
        "✅" if quality >= BENCHMARKS["min_quality_score"] else "❌ Below benchmark",
    )

    size_per_min = file_size_mb / (duration / 60) if duration > 0 else 0
    print(
        f"💾 Size Efficiency: {size_per_min:.1f} MB/min (benchmark: ≤{BENCHMARKS['max_file_size_ratio']} MB/min)",
        "✅" if size_per_min <= BENCHMARKS["max_file_size_ratio"] else "⚠️  Large file",
    )

    # Overall grade
    score = 0
    if duration >= BENCHMARKS["min_duration"]:
        score += 1
    if quality >= BENCHMARKS["min_quality_score"]:
        score += 1
    if size_per_min <= BENCHMARKS["max_file_size_ratio"]:
        score += 1

    print(f"\n🏆 OVERALL GRADE: {score}/3")
    if score == 3:
        print("   ✅ Professional-grade output")
    elif score == 2:
        print("   ⚠️  Near-professional, some optimization needed")
    else:
        print("   ❌ Requires significant improvement")


async def main():
    print("🚀 ettametta Video Lead → Editor Pipeline Test")
    print("Remote server: 149.104.110.122 (Ollama llama3.2:3b primary)")

    # Run workflow
    result = await run_full_video_workflow(niche="AI productivity tools")

    # Compare to professional standards
    await compare_to_professional_standard(result)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    return result


if __name__ == "__main__":
    try:
        outcome = asyncio.run(main())
        sys.exit(0 if outcome.get("success") else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
        sys.exit(130)
