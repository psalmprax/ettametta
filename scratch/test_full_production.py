import asyncio
import os
import sys
import uuid
import shutil
from datetime import datetime
from sqlalchemy import select

# Override environment variables before importing settings
os.environ["ENV"] = "development"
os.environ["OLLAMA_URL"] = "http://localhost:11434"
os.environ["ELEVENLABS_API_KEY"] = ""
# Require DATABASE_URL to be set by the caller (never hardcode credentials)
_database_url = os.environ.get("DATABASE_URL")
if not _database_url:
    print("ERROR: DATABASE_URL is required. Set it before running this script.")
    print("  export DATABASE_URL=sqlite:///./test_local.db")
    sys.exit(1)
os.environ["DATABASE_URL"] = _database_url
_redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
os.environ["REDIS_URL"] = _redis_url
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_purposes_123"

# Add project root to sys.path
sys.path.insert(0, os.getcwd())

from src.api.config import settings
from src.api.utils.database import async_session_factory
from src.api.utils.user_models import UserDB
from src.api.utils.models import NexusJobDB
from src.shared.enums import SystemJobStatus
from src.services.video_engine.automation import AutomationMode
from src.services.nexus_engine.auto_creator import base_creator_service


def reset_all_circuit_breakers():
    """Reset circuit breakers so each scenario starts fresh."""
    from src.services.nexus_engine.orchestrator import base_nexus_service
    from src.services.video_engine.remotion_service import base_remotion_service
    for attr_name in dir(base_creator_service):
        obj = getattr(base_creator_service, attr_name, None)
        if hasattr(obj, 'reset'):
            obj.reset()
    if hasattr(base_creator_service, 'breaker'):
        base_creator_service.breaker.reset()
    if hasattr(base_remotion_service, '_breaker'):
        base_remotion_service._breaker.reset()
    if hasattr(base_nexus_service, 'breaker'):
        base_nexus_service.breaker.reset()
    print("  🔄 All circuit breakers reset.")


async def run_single_production(
    topic: str,
    niche: str,
    intro_style: str,
    outro_style: str,
    script_segments: list[dict],
    brand_name: str = "Antigravity",
    primary_color: str = "#ff007f"
):
    reset_all_circuit_breakers()

    print(f"\n🎬 Seeding job for Topic: '{topic}' | Intro: '{intro_style}' | Outro: '{outro_style}'...")
    
    async with async_session_factory() as db:
        user_stmt = select(UserDB).limit(1)
        res = await db.execute(user_stmt)
        user = res.scalar_one_or_none()
        if not user:
            user = UserDB(
                id=str(uuid.uuid4()),
                username="test_user",
                email="test_user@example.com",
                hashed_password="mock_password",
                role="user",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user)
            await db.commit()
            print(f"  Created test user: {user.id}")
        else:
            print(f"  Using existing user: {user.id}")
            
        job_id = str(uuid.uuid4())
        job = NexusJobDB(
            id=job_id,
            status=SystemJobStatus.QUEUED,
            niche=niche,
            user_id=user.id,
            job_metadata={
                "topic": topic,
                "niche": niche,
                "duration_seconds": 10,
                "intro_style": intro_style,
                "outro_style": outro_style,
                "scene_layout": "split-horizontal",
                "vfx": "default",
                "brand_name": brand_name,
                "primary_color": primary_color
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(job)
        await db.commit()
        print(f"  Created job: {job_id}")

    try:
        output_path = await base_creator_service.create_cinema_video(
            job_id=job_id,
            topic=topic,
            niche=niche,
            blueprint_id="topic-fusion",
            engine="cloud",
            script=script_segments,
            duration_seconds=10,
            style="CINEMATIC_DOC",
            use_dag=False,
            automation_mode=AutomationMode.MANUAL
        )
        
        print(f"  ✨ SUCCESS! Rendered video path: {output_path}")
        if output_path and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024*1024)
            print(f"  File size: {size_mb:.2f} MB")
            
            # Copy to scratch for easy access
            dest = f"scratch/output_{intro_style}_{outro_style}.mp4"
            shutil.copy2(output_path, dest)
            print(f"  📁 Copied to: {dest}")
            return output_path
        else:
            print("  ❌ Render output file is missing or path is empty!")
            return None
            
    except Exception as e:
        print(f"  ❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    print("🚀 Full Story Production E2E Test")
    print("=" * 60)

    # Pick the scenario to test via CLI arg, or default to 0
    scenario_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    
    scenarios = [
        {
            "topic": "Mars Colonization and Space Exploration",
            "niche": "Tech",
            "intro_style": "round",
            "outro_style": "cyber-grid",
            "brand_name": "MarsOne",
            "primary_color": "#ff3b30",
            "script_segments": [
                {
                    "text": "Humanity has always looked at the stars, dreaming of a new horizon beyond Earth.",
                    "visual_prompt": "space exploration mars colony rocket launch",
                    "mood": "inspirational",
                    "type": "clip"
                },
                {
                    "text": "Now, the red planet beckons us to step into the cosmic unknown.",
                    "visual_prompt": "mars surface rover red desert mountains sunset",
                    "mood": "cinematic",
                    "type": "clip"
                }
            ]
        },
        {
            "topic": "AI Consciousness and Future Tech",
            "niche": "Tech",
            "intro_style": "glitch",
            "outro_style": "neon-minimal",
            "brand_name": "Synthetix",
            "primary_color": "#00f0ff",
            "script_segments": [
                {
                    "text": "Artificial intelligence is no longer just a tool. It is becoming a mirror of our minds.",
                    "visual_prompt": "artificial intelligence neural networks server room glowing",
                    "mood": "futuristic",
                    "type": "clip"
                },
                {
                    "text": "As machines learn to think, we must ask ourselves what it truly means to be conscious.",
                    "visual_prompt": "futuristic city neon lights cyberpunk robot",
                    "mood": "intense",
                    "type": "clip"
                }
            ]
        },
        {
            "topic": "Mysteries of the Deep Ocean",
            "niche": "Nature",
            "intro_style": "elevator",
            "outro_style": "glass",
            "brand_name": "DeepBlue",
            "primary_color": "#34c759",
            "script_segments": [
                {
                    "text": "Deep beneath the ocean waves lies a world alien to our own, full of wonder.",
                    "visual_prompt": "deep ocean dark water bioluminescent creatures jellyfish",
                    "mood": "mysterious",
                    "type": "clip"
                },
                {
                    "text": "These unexplored depths hold secrets older than humanity itself.",
                    "visual_prompt": "underwater trench exploration submarine deep sea coral reef",
                    "mood": "epic",
                    "type": "clip"
                }
            ]
        }
    ]
    
    if scenario_idx >= len(scenarios):
        print(f"Invalid scenario index {scenario_idx}. Use 0-{len(scenarios)-1}")
        return

    sc = scenarios[scenario_idx]
    print(f"\n--- Scenario {scenario_idx + 1}: {sc['topic']} ---")
    print(f"    Intro: {sc['intro_style']} | Outro: {sc['outro_style']}")
    
    path = await run_single_production(
        topic=sc["topic"],
        niche=sc["niche"],
        intro_style=sc["intro_style"],
        outro_style=sc["outro_style"],
        script_segments=sc["script_segments"],
        brand_name=sc["brand_name"],
        primary_color=sc["primary_color"]
    )
    
    if path:
        print(f"\n🎉 Video rendered successfully: {path}")
    else:
        print(f"\n💀 Video render failed for scenario {scenario_idx + 1}")

if __name__ == "__main__":
    asyncio.run(main())
