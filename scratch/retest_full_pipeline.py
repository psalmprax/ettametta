import asyncio
import os
import uuid
import logging
from src.workflows.elite_production_cycle import run_elite_production_cycle

# Configure logging to see the progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def reality_test():
    print("🚀 [Reality Test] Starting Hardened Production Cycle...")
    
    topic = "Space Exploration"
    session_id = f"test_{uuid.uuid4().hex[:8]}"
    
    print(f"🎬 Topic: {topic}")
    print(f"🆔 Session: {session_id}")
    
    try:
        result_path = await run_elite_production_cycle(
            topic=topic,
            session_id=session_id
        )
        
        if result_path and os.path.exists(result_path):
            print(f"✅ PRODUCTION SUCCESS: {result_path}")
            print(f"📁 Size: {os.path.getsize(result_path)} bytes")
        else:
            print("❌ PRODUCTION FAILED: No output path returned or file missing.")
            
    except Exception as e:
        print(f"💥 FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reality_test())
