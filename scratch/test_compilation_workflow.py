import asyncio
import os
import sys
import uuid
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.discovery.service import base_discovery_service
from src.services.video_engine.processor import VideoProcessor
from src.services.video_engine.downloader import base_downloader_service
from src.api.config import settings

async def run_compilation_test(niche="Motivation"):
    print(f"\n🚀 STARTING MULTI-VIDEO COMPILATION TEST [{niche}]")
    print("-" * 60)
    
    # Initialize Processor
    processor = VideoProcessor()
    
    # 1. Discover
    print("🔍 Discovering candidates...")
    candidates = await base_discovery_service.find_trending_content(niche)
    print(f"✅ Found {len(candidates)} candidates.")
    
    if not candidates:
        print("❌ No candidates found.")
        return

    # Filter for candidates with valid URLs
    valid_candidates = [c for c in candidates if c.source_uri]
    print(f"🎯 Valid candidates: {len(valid_candidates)}")

    # 2. Select top 3
    top_candidates = valid_candidates[:3]
    print(f"🏆 Top {len(top_candidates)} selected for compilation.")

    # 3. Download & Pre-process (Normalization)
    processed_segments = []
    
    for i, candidate in enumerate(top_candidates):
        url = candidate.source_uri
        print(f"\n📦 SEGMENT {i+1}/3: {url}")
        
        try:
            # Download
            raw_path = await base_downloader_service.download_video(url)
            if not raw_path:
                print(f"  ❌ Download failed.")
                continue
            
            print(f"  ✅ Downloaded: {raw_path}")
            
            # Normalize (1080x1920 + Originality)
            # We use the processor's apply_originality which ensures fixed resolution
            norm_path = os.path.join(processor.output_dir, f"norm_{uuid.uuid4().hex[:8]}.mp4")
            print(f"  ⚙️ Normalizing...")
            
            # Using the FFmpeg service directly for more control or the processor method
            from src.services.video_engine.ffmpeg_utils import base_ffmpeg_service
            success = base_ffmpeg_service.apply_originality(
                input_path=raw_path,
                output_path=norm_path,
                mirror=True,
                zoom=1.05
            )
            
            if success:
                processed_segments.append(norm_path)
                print(f"  ✨ Segment ready: {norm_path}")
            else:
                print(f"  ❌ Normalization failed.")
                
        except Exception as e:
            print(f"  ❌ Error processing segment: {e}")

    if len(processed_segments) < 2:
        print(f"\n❌ Not enough valid segments ({len(processed_segments)}) for compilation.")
        return

    # 4. Concatenate with transitions
    print(f"\n🎬 CONCATENATING {len(processed_segments)} segments with xfade...")
    final_output = os.path.join(processor.output_dir, f"compilation_{niche.lower()}_{uuid.uuid4().hex[:8]}.mp4")
    
    from src.services.video_engine.ffmpeg_utils import base_ffmpeg_service
    # Use random transitions for each cut
    success = base_ffmpeg_service.xfade_concatenate(
        video_paths=processed_segments,
        output_path=final_output,
        transition="random",
        trans_duration=0.5
    )
    
    if success:
        print(f"\n✅ COMPILATION SUCCESSFUL!")
        print(f"📍 FINAL VIDEO: {final_output}")
        
        # Link it to the local workspace for preview
        preview_link = os.path.join(os.getcwd(), "multi_preview.mp4")
        if os.path.exists(preview_link):
            os.remove(preview_link)
        os.symlink(final_output, preview_link)
        print(f"🔗 Local Preview Link: {preview_link}")
        
    else:
        print(f"\n❌ Concatenation FAILED.")

if __name__ == "__main__":
    # Ensure storage exists
    os.makedirs(settings.STORAGE_OUTPUT_DIR, exist_ok=True)
    
    asyncio.run(run_compilation_test())
