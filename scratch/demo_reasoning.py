import asyncio
import os
import sys
import json
from pathlib import Path

# 1. Environment & Path Setup
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "src"))

from src.engines.intelligent_video_discovery_edit import VideoContentAnalyzer

async def demo_reasoning():
    print("🕵️  EXTRACTING NEURAL VISION REASONING...")
    analyzer = VideoContentAnalyzer()
    
    # Analyze the top lead from our previous test
    url = "https://youtube.com/watch?v=yTX8L6WLfnc"
    print(f"Target: {url}")
    
    # This triggers the LLM Vision Audit
    result = await analyzer.analyze_video_content(video_url=url)
    
    print("\n" + "=" * 50)
    print("🔍 AI VISION AUDIT REPORT")
    print("=" * 50)
    print(json.dumps(result, indent=4))
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(demo_reasoning())
