#!/usr/bin/env python3
"""
Test All Remotion Templates End-to-End
======================================
Verifies all templates and styles (CinematicMinimal, HormoziStyle, ViralClip with REDDIT_STORY,
BROADCAST_NEWS, CINEMATIC_DOC, TOP_LISTICLE) render successfully for a short frame duration.
"""

import os
import sys
import json
import subprocess

PROJECT_DIR = "/app" if os.path.exists("/app") else "/home/psalmprax/ALL_PROJECTS/ettametta"
sys.path.insert(0, PROJECT_DIR)

STUDIO_PATH = os.path.join(PROJECT_DIR, "apps/remotion-studio")
OUTPUT_DIR = os.path.join(STUDIO_PATH, "out")
os.makedirs(OUTPUT_DIR, exist_ok=True)

PROPS_PATH = "/tmp/remotion_test_props.json"

TEST_CASES = [
    {
        "name": "CinematicMinimal",
        "composition_id": "CinematicMinimal",
        "props": {
            "title": "Minimalist Design in 2026",
            "subtitle": "Simplicity is the ultimate sophistication.",
            "primary_color": "#00F2FE",
            "show_cta_overlay": True,
            "cta_type": "engagement",
            "cta_text": "Follow for more minimalist tips"
        }
    },
    {
        "name": "HormoziStyle",
        "composition_id": "HormoziStyle",
        "props": {
            "text": "discipline equals freedom results money legacy",
            "highlight_color": "#00ff00",
            "show_cta_overlay": True,
            "cta_type": "cta",
            "cta_text": "Click the link in bio"
        }
    },
    {
        "name": "ViralClip_RedditStory",
        "composition_id": "ViralClip",
        "props": {
            "title": "AITEST: Most mind-blowing coding paradigm?",
            "subtitle": "Neural interface compilation",
            "words": [
                {"word": "Mind-blowing", "start": 0.1, "end": 0.8},
                {"word": "Coding", "start": 0.8, "end": 1.4},
                {"word": "Paradigm", "start": 1.4, "end": 2.2}
            ],
            "show_cta_overlay": True,
            "cta_type": "engagement",
            "cta_text": "Join the ettametta community!",
            "brand_name": "ettametta",
            "primary_color": "#8b5cf6",
            "style": "REDDIT_STORY",
            "job_metadata": {
                "reddit_data": {
                    "title": "AITEST: What is the most mind-blowing coding paradigm you know?",
                    "author": "u/antigravity_agent",
                    "score": "12.4k comments",
                    "subreddit": "r/programming"
                }
            }
        }
    },
    {
        "name": "ViralClip_BroadcastNews",
        "composition_id": "ViralClip",
        "props": {
            "title": "AI Video Production Hardened",
            "subtitle": "E2E pipeline testing yields 100% success rate on remote ARM instance",
            "words": [
                {"word": "Breaking", "start": 0.1, "end": 0.5},
                {"word": "News:", "start": 0.5, "end": 1.0},
                {"word": "Production", "start": 1.0, "end": 1.8},
                {"word": "Hardened", "start": 1.8, "end": 2.5}
            ],
            "show_cta_overlay": True,
            "cta_type": "engagement",
            "cta_text": "Subscribe for daily news!",
            "brand_name": "ettametta",
            "primary_color": "#e11d48",
            "style": "BROADCAST_NEWS"
        }
    },
    {
        "name": "ViralClip_CinematicDoc",
        "composition_id": "ViralClip",
        "props": {
            "title": "Stochastic Artistic Nuances",
            "subtitle": "Predictable randomness in video orchestration",
            "words": [
                {"word": "Artistic", "start": 0.1, "end": 0.6},
                {"word": "Stochastic", "start": 0.6, "end": 1.2},
                {"word": "Nuances", "start": 1.2, "end": 2.0}
            ],
            "show_cta_overlay": True,
            "cta_type": "engagement",
            "cta_text": "Follow for more docuseries!",
            "brand_name": "ettametta",
            "primary_color": "#fbbf24",
            "style": "CINEMATIC_DOC"
        }
    },
    {
        "name": "ViralClip_TopListicle",
        "composition_id": "ViralClip",
        "props": {
            "title": "Top 5 AI Coding Agents",
            "subtitle": "Which ones actually build production software?",
            "words": [
                {"word": "Top", "start": 0.1, "end": 0.5},
                {"word": "Coding", "start": 0.5, "end": 1.0},
                {"word": "Agents", "start": 1.0, "end": 1.8}
            ],
            "show_cta_overlay": True,
            "cta_type": "engagement",
            "cta_text": "Save this video!",
            "brand_name": "ettametta",
            "primary_color": "#10b981",
            "style": "TOP_LISTICLE"
        }
    }
]


def test_render_all():
    print("=== STARTING ALL TEMPLATES RENDER VERIFICATION ===")
    
    success_count = 0
    
    for case in TEST_CASES:
        name = case["name"]
        comp_id = case["composition_id"]
        props = case["props"]
        
        print(f"\n🎬 [TestCase] Rendering {name} ({comp_id})...")
        
        # Write props to temp file
        with open(PROPS_PATH, "w") as f:
            json.dump(props, f)
            
        output_file = f"verify_{name}.mp4"
        output_path = os.path.join(OUTPUT_DIR, output_file)
        
        cmd = [
            "npx",
            "remotion",
            "render",
            "src/index.ts",
            comp_id,
            output_path,
            "--props", PROPS_PATH,
            "--quality", "1",
            "--frames", "0-40",
            "--chromium-flags", "--no-sandbox --disable-setuid-sandbox",
            "--force"
        ]
        
        print(f"  Command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd, cwd=STUDIO_PATH, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120
            )
            if result.returncode == 0 and os.path.exists(output_path):
                size = os.path.getsize(output_path) / 1024
                print(f"  ✅ SUCCESS: {output_file} ({size:.1f} KB)")
                success_count += 1
            else:
                print(f"  ❌ FAILED (Exit Code: {result.returncode})")
                print(f"  Stderr: {result.stderr[-500:]}")
        except subprocess.TimeoutExpired:
            print("  ❌ TIMEOUT")
            
    print(f"\n=== SUMMARY: {success_count}/{len(TEST_CASES)} CASES PASSED ===")
    return success_count == len(TEST_CASES)


if __name__ == "__main__":
    all_passed = test_render_all()
    sys.exit(0 if all_passed else 1)
