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
from src.services.video_engine.ffmpeg_utils import base_ffmpeg_service

async def run_full_pipeline(niche="AI Technology"):
    print(f"\n⚡ INITIATING FULL PIPELINE: LEAD GENERATION -> AUTO-EDITING [{niche}]")
    print("-" * 70)
    
    # 1. LEAD GENERATION (Discovery)
    print(f"🔍 STEP 1: Generating Leads for '{niche}'...")
    leads = await base_discovery_service.discover_video_leads(
        niche=niche,
        platforms=["youtube"],
        min_viral_score=5.0,
        max_results=5
    )
    
    if not leads:
        print("❌ No leads found for this niche.")
        return
        
    print(f"✅ Generated {len(leads)} qualified leads.")
    for i, lead in enumerate(leads):
        print(f"   [{i+1}] {lead.title[:50]}... (Score: {lead.viral_score})")

    # 2. SELECTION
    # We'll take the top 3 for the auto-edit
    top_leads = leads[:3]
    print(f"\n🎯 STEP 2: Selected top {len(top_leads)} leads for production.")

    # 3. DOWNLOAD & NORMALIZATION
    print("\n📦 STEP 3: Downloading and Normalizing Assets...")
    processed_paths = []
    processor = VideoProcessor()
    
    for i, lead in enumerate(top_leads):
        print(f"   ▶️ Processing Lead {i+1}: {lead.url}")
        try:
            # Download
            raw_path = await base_downloader_service.download_video(lead.url)
            if not raw_path:
                print("     ❌ Download failed.")
                continue
                
            # Normalize + Originality
            norm_path = os.path.join(processor.output_dir, f"lead_norm_{uuid.uuid4().hex[:8]}.mp4")
            success = base_ffmpeg_service.apply_originality(
                input_path=raw_path,
                output_path=norm_path,
                mirror=True,
                zoom=1.03
            )
            
            if success:
                processed_paths.append(norm_path)
                print(f"     ✅ Normalized: {norm_path}")
            else:
                print("     ❌ Normalization failed.")
        except Exception as e:
            print(f"     ❌ Error: {e}")

    if len(processed_paths) < 2:
        print(f"\n❌ Pipeline aborted: Not enough processed segments ({len(processed_paths)}).")
        return

    # 4. AUTO-VIDEO EDITING (Compilation)
    print("\n🎬 STEP 4: Auto-Editing Compilation...")
    final_video = os.path.join(processor.output_dir, f"pipeline_final_{niche.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}.mp4")
    
    # Use cinematic transitions
    success = base_ffmpeg_service.xfade_concatenate(
        video_paths=processed_paths,
        output_path=final_video,
        transition="radial", # Using a specific transition
        trans_duration=0.6
    )
    
    if success:
        print("\n✨ PIPELINE COMPLETE!")
        print(f"🏆 FINAL PRODUCTION: {final_video}")
        
        # Link for local preview
        preview_path = os.path.join(os.getcwd(), "pipeline_preview.mp4")
        if os.path.exists(preview_path):
            os.remove(preview_path)
        os.symlink(final_video, preview_path)
        print(f"🔗 Preview ready: {preview_path}")
    else:
        print("\n❌ Final editing failed.")

if __name__ == "__main__":
    os.makedirs(settings.STORAGE_OUTPUT_DIR, exist_ok=True)
    asyncio.run(run_full_pipeline())
