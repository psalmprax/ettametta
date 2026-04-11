import httpx
import time
import os
import sys

# Define constants
API_BASE = "http://localhost:8000"
BLUEPRINT_ID = "test-e2e-remote"

def test_remote_e2e():
    """Trigger E2E remote generation and poll for results."""
    print("🚀 Starting E2E Remote Video Generation Test...")
    print(f"📡 Target API: {API_BASE}")
    print(f"🛠️ Using Blueprint: {BLUEPRINT_ID}")
    
    payload = {
        "niche": "Cyberpunk",
        "topic": "Neon Rain Cityscape",
        "blueprint_id": BLUEPRINT_ID,
        "engine": "ltx-video"  # Specify LTX for faster completion
    }
    
    # We use a long timeout for the initial request just in case
    with httpx.Client(timeout=60) as client:
        # 1. Trigger Composition
        try:
            resp = client.post(f"{API_BASE}/nexus/compose", json=payload)
            if resp.status_code != 200:
                print(f"❌ Failed to trigger composition: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            print(f"❌ Network error contacting API: {e}")
            return False
        
        job_data = resp.json()
        job_id = job_data.get("job_id")
        if not job_id:
            print(f"❌ No job_id returned: {job_data}")
            return False
            
        print(f"✅ Job Created: {job_id}")
        
        # 2. Poll Status
        start_time = time.time()
        timeout = 900 # 15 minutes for remote generation
        last_status = None
        
        print("🕒 Polling status (this may take several minutes)...")
        while time.time() - start_time < timeout:
            try:
                status_resp = client.get(f"{API_BASE}/nexus/status/{job_id}")
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    current_status = status_data.get("status")
                    progress = status_data.get("progress", 0)
                    current_node = status_data.get("current_node", "N/A")
                    
                    if current_status != last_status:
                        print(f"🔄 [{time.strftime('%H:%M:%S')}] Status: {current_status} | Node: {current_node} | Progress: {progress}%")
                        last_status = current_status
                    
                    if current_status == "COMPLETED":
                        print(f"\n🎉 SUCCESS! E2E Remote Generation Test Passed.")
                        print(f"📂 Local Output Path: {status_data.get('output_path')}")
                        return True
                    
                    if current_status == "FAILED":
                        print(f"\n❌ Job Failed: {status_data.get('error')}")
                        return False
                else:
                    print(f"⚠️ Failed to get status: {status_resp.status_code}")
            except Exception as e:
                print(f"⚠️ Polling error: {e}")
                
            time.sleep(10)
        
        print(f"\n❌ Test timed out after {timeout} seconds.")
        return False

if __name__ == "__main__":
    success = test_remote_e2e()
    if not success:
        sys.exit(1)
    sys.exit(0)
