import asyncio
import pytest

pytest.skip("script-style cinematic verification; run directly, not via pytest", allow_module_level=True)

from src.engines.real_video_fusion_engine import RealVideoFusionEngine
from src.services.audio.rhythm_engine import base_rhythm_service

async def verify_cinematic_intuition():
    print("🎬 STARTING CINEMATIC INTUITION VERIFICATION")
    
    engine = RealVideoFusionEngine()
    
    # Mock Script
    script = {
        "title": "Autonomous Future",
        "segments": [
            {"text": "In a world of silicon and code", "duration": 4.0},
            {"text": "One system rises above all", "duration": 5.0},
            {"text": "The ettametta", "duration": 3.0}
        ]
    }
    
    # Mock NRM Blueprint
    blueprint = {
        "emotional_arc": [
            {"time_start": 0, "time_end": 5, "emotion": "Intrigue", "action": "Setup"},
            {"time_start": 5, "time_end": 15, "emotion": "Shock/Surprise", "action": "Hook"}
        ]
    }
    
    # Mock Assets (paths to avoid real video reading for this test)
    # We'll use a real asset if available, or just mock paths
    mock_assets = [
        {"file_path": "templates/safety/generic_space.mp4", "motion_score": 0.8}
    ]
    
    print("\n🥁 STEP 1: RHYTHM ANALYSIS")
    bg_music = "src/templates/audio/background/cinematic_energetic.mp3"
    rhythm = base_rhythm_service.get_beat_markers(bg_music)
    print(f"BPM: {rhythm['bpm']}, Beats Detected: {len(rhythm['beats'])}")
    
    print("\n🧪 STEP 2: NEURAL PLANNING (CINEMATIC MODE)")
    plan = await engine._create_fusion_plan_neural(mock_assets, script, duration_sec=15, blueprint=blueprint)
    
    print("\n🧐 RESULTS:")
    for i, seg in enumerate(plan["segments"]):
        print(f"Segment {i}: {seg['role']} | Emotion: {seg['emotion']} | Dur: {round(seg['duration'], 3)}s")
        # Verification Logic: Check if duration lands on a beat
        # total_time = sum(s['duration'] for s in plan['segments'][:i+1])
        # nearest_beat = base_rhythm_service.find_nearest_beat(total_time, rhythm['beats'])
        # if abs(total_time - nearest_beat) < 0.1:
        #     print(f"  ✅ Beat-Synced!")

    print("\n✅ Verification Script Complete")

if __name__ == "__main__":
    asyncio.run(verify_cinematic_intuition())
