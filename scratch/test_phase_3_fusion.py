
import asyncio
import os
import sys
import logging
from unittest.mock import MagicMock, patch, AsyncMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from src.engines.real_video_fusion_engine import RealVideoFusionEngine
from src.services.video_engine.synthesis_service import base_generative_service

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestPhase3")

async def test_fusion():
    print("\n🚀 Testing Phase 3: Neural Fusion (RealVideoFusionEngine)")
    
    # Initialize Engine
    engine = RealVideoFusionEngine(synthesis_service=base_generative_service)
    
    topic = "The Future of AI in Video Production"
    niche = "AI Technology"
    
    # Mocking external heavy services to use our dummy asset
    dummy_path = os.path.abspath("scratch/dummy.mp4")
    
    with patch("src.services.media.discovery_service.base_discovery_service.batch_download_videos", new_callable=AsyncMock) as mock_download:
        mock_download.return_value = [
            {"id": "v1", "file_path": dummy_path, "platform": "YouTube"},
            {"id": "v2", "file_path": dummy_path, "platform": "TikTok"}
        ]
        
        with patch("src.services.video_engine.synthesis_service.base_generative_service.pull_stock_for_niche", new_callable=AsyncMock) as mock_stock:
            mock_stock.return_value = [
                {"id": "s1", "file_path": dummy_path, "url": "http://example.com/s1.mp4"}
            ]
            
            print(f"🎬 Creating content for topic: {topic}")
            
            # Run the fusion engine (very short duration to speed up)
            result = await engine.create_real_video_content(
                topic=topic,
                niche=niche,
                duration_sec=5, # Tiny duration for test
                session_id="test_session_fusion"
            )
            
            if result and result.get("video_path"):
                print(f"✅ Fusion Successful!")
                print(f"📁 Video Path: {result['video_path']}")
                print(f"📝 Script: {result.get('script', 'No script found')[:100]}...")
                
                # Check if file actually exists
                if os.path.exists(result["video_path"]):
                    print(f"🚀 Physical file verified: {result['video_path']}")
                else:
                    print(f"❌ File not found at {result['video_path']}")
            else:
                print(f"❌ Fusion Failed or returned no result.")
                print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_fusion())
