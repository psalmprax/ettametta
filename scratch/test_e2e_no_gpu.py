import asyncio
import os
import sys
import json
from pathlib import Path

# Add project root to path
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "src"))

# Mock environment for OpenClaw
os.environ["DEBUG"] = "false"
os.environ["TELEGRAM_ADMIN_ID"] = "12345678"

from src.services.openclaw.agent import OpenClawAgent
from api.config import settings

async def test_e2e_no_gpu_flow():
    print("=" * 60)
    print("🚀 E2E NO-GPU VIDEO PRODUCTION TEST")
    print("=" * 60)

    # 1. Initialize Agent
    # We use 'standard' mode which uses Groq/OpenAI directly
    agent = OpenClawAgent()
    
    # User identifier (matches TELEGRAM_ADMIN_ID fallback for testing)
    user_id = "12345678"
    
    # 2. Define Request
    # We want the agent to:
    # a) Generate a script/props
    # b) Use the REMOTION tool to render
    request = "Create a 5-second Hormozi-style video clip about why Ettametta is the best for AI automation. Use high impact typography."
    
    print(f"\n💬 User Request: {request}")
    print("\n🧠 Agent is thinking...")
    
    # 3. Process Message
    # This will trigger the LLM to decide on a plan and call the tool
    response = await agent.process_message(user_id, request)
    
    print("\n" + "=" * 40)
    print("🤖 AGENT RESPONSE:")
    print("=" * 40)
    print(response)
    print("=" * 40)
    
    # 4. Verify output
    # The agent should have called the REMOTION tool which saves to outputs/
    # We can't know the exact filename if it was random, but we can check if any new file appeared
    # In my previous test I used 'remotion_output.mp4' or similar.
    
    # Let's check for 'remotion_output.mp4' which is the default in the skill if not specified
    output_dir = Path("outputs")
    recent_videos = list(output_dir.glob("*.mp4"))
    
    if any(v.exists() for v in recent_videos):
        print(f"\n✅ E2E Flow Complete! Found {len(recent_videos)} video(s) in outputs/")
        for v in recent_videos:
            if (asyncio.get_event_loop().time() - v.stat().st_mtime) < 300: # Created in last 5 mins
                print(f"   🎬 New video: {v.name} ({v.stat().st_size} bytes)")
    else:
        print("\n❌ E2E Flow Failed: No video found in outputs/")

if __name__ == "__main__":
    asyncio.run(test_e2e_no_gpu_flow())
