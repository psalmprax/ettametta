#!/usr/bin/env python3
"""
Video Lead + Fusion Test - Complete Pipeline
Tests: discovery → planning → fusion → output comparison
"""

import asyncio
import sys
import os
from pathlib import Path
import json

# Environment
os.environ["DEBUG"] = "false"

# Add source to path
root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "src"))

from services.discovery.video_lead_scanner import video_lead_scanner
from services.video_engine.scene_orchestrator import base_scene_based_orchestrator
from api.config import settings


async def run_full_workflow():
    print("\n" + "=" * 70)
    print("🎬 END-TO-END VIDEO WORKFLOW TEST")
    print("=" * 70)
    print(
        f"LLM: {settings.DEFAULT_LLM_PROVIDER} | Model: {getattr(settings, 'OLLAMA_MODEL', 'N/A')}"
    )

    # ── Phase 1: Discovery ────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("PHASE 1: VIDEO LEAD DISCOVERY")
    print("─" * 70)

    niche = "AI productivity tools"
    print(f"🔍 Scanning: {niche}")

    leads = []
    try:
        leads = await video_lead_scanner.scan_for_video_leads(
            niche=niche,
            platforms=["youtube", "tiktok"],
            min_viral_score=7.0,
            max_results=10,
        )
        print(f"✅ Found {len(leads)} leads")
        if leads:
            for i, l in enumerate(leads[:3], 1):
                print(f"  {i}. [{l.platform}] {l.title[:60]}")
                print(f"     👁️ {l.view_count:,} | ⭐ {l.viral_score:.1f}")
    except Exception as e:
        print(f"❌ Discovery error: {e}")

    # ── Phase 2: Scene Planning ──────────────────────────────────────────
    print("\n" + "─" * 70)
    print("PHASE 2: SCENE-BASED PRODUCTION PLAN")
    print("─" * 70)

    scenes = [
        {
            "description": "AI tools landscape overview",
            "visual_prompt": f"Modern workspace showing AI productivity tools for {niche}",
            "duration": 12,
        },
        {
            "description": "Workflow automation demo",
            "visual_prompt": f"Screen capture of AI automating {niche} tasks",
            "duration": 15,
        },
        {
            "description": "Results and ROI metrics",
            "visual_prompt": f"Charts showing productivity gains with AI in {niche}",
            "duration": 10,
        },
    ]

    total_duration = sum(s["duration"] for s in scenes)
    print(f"📝 {len(scenes)} scenes → {total_duration}s total")

    # ── Phase 3: Video Fusion ────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("PHASE 3: VIDEO FUSION & RENDERING")
    print("─" * 70)

    audio_script = (
        f"Discover how AI productivity tools can transform your {niche} workflow. "
        f"We'll explore three key areas: understanding the landscape, practical automation, "
        f"and measuring real results."
    )

    try:
        print("🎞️  Calling orchestrator.produce_scene_based_video()...")

        result = await base_scene_based_orchestrator.produce_scene_based_video(
            scenes=scenes,
            niche=niche,
            target_duration=total_duration,
            audio_script=audio_script,
            output_filename="workflow_test_output",
        )

        if result and result.get("success"):
            print(f"\n✅ VIDEO RENDERED")
            print(f"   📹 {result.get('video_path')}")
            print(f"   ⏱️  {result.get('duration', 0):.1f}s")
            print(f"   ⭐ {result.get('quality_score', 0):.1f}/10")
            print(f"   🎬 {result.get('scenes_used', 0)} scenes")

            # Save report
            report = {
                "niche": niche,
                "leads_discovered": len(leads),
                "video_result": result,
                "llm_provider": settings.DEFAULT_LLM_PROVIDER,
                "ollama_model": getattr(settings, "OLLAMA_MODEL", None),
            }
            report_path = settings.OUTPUT_DIR / "workflow_test_report.json"
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n📋 Report: {report_path}")

            return result
        else:
            err = result.get("error") if isinstance(result, dict) else "Unknown"
            print(f"❌ Failed: {err}")
            return {"success": False, "error": err}

    except Exception as e:
        print(f"❌ Fusion error: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def quality_comparison(result: dict):
    """Benchmark against professional standards"""

    print("\n" + "=" * 70)
    print("📊 PROFESSIONAL VIDEO EDITOR COMPARISON")
    print("=" * 70)

    if not result.get("success"):
        print("❌ Cannot compare — generation failed")
        return

    BENCHMARKS = {
        "min_duration": 30,  # Short-form minimum
        "min_quality": 7.0,  # Subjective quality
        "max_size_mb_per_min": 60,  # Efficiency
    }

    duration = result.get("duration", 0)
    quality = result.get("quality_score", 0)
    path = result.get("video_path", "")
    size_mb = os.path.getsize(path) / (1024 * 1024) if os.path.exists(path) else 0
    size_per_min = size_mb / (duration / 60) if duration else 0

    print(
        f"📏 Duration: {duration}s (need ≥{BENCHMARKS['min_duration']}s) {'✅' if duration >= 30 else '❌'}"
    )
    print(
        f"⭐ Quality: {quality:.1f}/10 (need ≥{BENCHMARKS['min_quality']}) {'✅' if quality >= 7 else '❌'}"
    )
    print(
        f"💾 Efficiency: {size_per_min:.1f} MB/min (need ≤{BENCHMARKS['max_size_mb_per_min']}) {'✅' if size_per_min <= 60 else '⚠️'}"
    )

    score = sum(
        [
            duration >= BENCHMARKS["min_duration"],
            quality >= BENCHMARKS["min_quality"],
            size_per_min <= BENCHMARKS["max_size_mb_per_min"],
        ]
    )

    grade = {
        3: "✅ Professional-grade",
        2: "⚠️ Near-professional",
        1: "⚠️ Needs work",
        0: "❌ Failing",
    }[score]
    print(f"\n🏆 OVERALL: {grade} ({score}/3)")


async def main():
    print("🚀 ettametta Video Pipeline Test")
    print("Remote: 149.104.110.122 | Ollama: llama3.2:3b")

    result = await run_full_workflow()
    await quality_comparison(result)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    return result


if __name__ == "__main__":
    try:
        outcome = asyncio.run(main())
        sys.exit(0 if outcome.get("success") else 1)
    except Exception as e:
        print(f"Fatal: {e}")
        sys.exit(1)
