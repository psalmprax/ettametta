import sys
import os
import asyncio
import json

# Add src to path
sys.path.append(os.path.abspath("src"))

async def demonstrate():
    try:
        from services.openclaw.agent import OpenClawAgent
        
        agent = OpenClawAgent()
        print("🤖 **OpenClaw Agent Online**")
        
        # Phase 1: Research & Scripting (System Skill)
        print("\n--- 📝 Phase 1: Scripting & Concept ---")
        mission_1 = "Generate a viral TikTok script about 'Deep Work' for a productivity niche. Include 5 scenes with visual descriptions."
        resp_1 = await agent.execute_mission(mission_1)
        print(resp_1)
        
        # Phase 2: Video Production Assistance (VIDEO_ASSISTANT)
        print("\n--- 🎬 Phase 2: Production Instructions ---")
        mission_2 = "Generate detailed editing instructions and an FFmpeg command sequence for a 60-second productivity video based on a deep work theme."
        # We'll call the skill directly for the demo to show its specific output
        resp_2 = await agent.skill_registry["VIDEO_ASSISTANT"].execute(
            action="generate_instructions",
            niche="productivity",
            scenes=[
                {"title": "The Distraction", "duration": 5},
                {"title": "Entering the Flow", "duration": 15},
                {"title": "The Focused Work", "duration": 25},
                {"title": "The Breakthrough", "duration": 10},
                {"title": "Results", "duration": 5}
            ]
        )
        print(resp_2)
        
        # Phase 3: Content Editing (CONTENT_EDITOR - Mocked result for demo)
        print("\n--- ✂️ Phase 3: AI Video Editing ---")
        print("Plan: [CONTENT_EDITOR] - Sourcing clips, trimming emotional peaks, and syncing audio.")
        # Simulating the polymorphic execute call
        print("✅ **Content Editor (remix)**")
        print("Result: {'status': 'success', 'output_path': '/home/psalmprax/ALL_PROJECTS/ettametta/exports/deep_work_viral.mp4', 'clips_used': 5, 'duration': '58s'}")
        
        print("\n🚀 **Final Product Ready: exports/deep_work_viral.mp4**")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demonstrate())
