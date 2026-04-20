import asyncio
import os
import sys
from pathlib import Path

# Add project root and src to path to handle inconsistent imports
root = Path(__file__).parent.parent
sys.path.append(str(root))
sys.path.append(str(root / "src"))

from src.services.openclaw.skills.render_remotion import remotion_skill

async def test_no_gpu_flow():
    print("=" * 60)
    print("🚀 TESTING NO-GPU VIDEO EDITOR FLOW")
    print("=" * 60)

    # Use Case: Render a short "Hormozi Style" clip on the CPU
    composition = "HormoziStyle"
    props = {
        "text": "Ettametta is the future of content automation",
        "highlight_color": "#00ff00"
    }
    output_name = "no_gpu_test.mp4"
    
    print(f"\n🎬 Step 1: Dispatching render for '{composition}'...")
    print(f"   Props: {props}")
    print(f"   Mode: CPU (Software Rendering)")
    
    try:
        # We pass use_gpu=False to ensure --disable-gpu is added
        # We also render just 30 frames (1 second) to keep the test fast
        result = await asyncio.to_thread(
            remotion_skill.execute,
            composition=composition,
            props=props,
            output_name=output_name,
            use_gpu=False,
            frames="0-30"
        )
        
        print(f"\n{result}")
        
        # Verify file existence
        output_path = Path("outputs") / output_name
        if output_path.exists():
            print(f"✅ Success! Video file created at: {output_path}")
            print(f"   File size: {output_path.stat().st_size} bytes")
        else:
            print(f"❌ Error: Video file not found at {output_path}")
            
    except Exception as e:
        print(f"❌ Flow failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_no_gpu_flow())
