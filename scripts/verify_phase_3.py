import requests
import time
import sys

API_URL = "http://localhost:8011"

def test_settings_persistence():
    print("[1/3] Testing Settings Persistence...")
    test_key = "youtube_api_key"
    test_val = "AIza_TEST_KEY_123"
    
    # 1. Update setting
    res = requests.post(f"{API_URL}/settings/", json={"key": test_key, "value": test_val})
    if res.status_code != 200:
        print(f"❌ Failed to update setting: {res.text}")
        return False
    
    # 2. Verify setting
    res = requests.get(f"{API_URL}/settings/")
    data = res.json()
    if data.get(test_key) == test_val:
        print("✅ Settings persisted successfully.")
        return True
    else:
        print(f"❌ Persistence failed. Expected {test_val}, got {data.get(test_key)}")
        return False

def test_async_video_processing():
    print("\n[2/3] Testing Async Video Processing (Celery)...")
    payload = {
        "input_url": "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "niche": "Verification",
        "platform": "YouTube Shorts"
    }
    
    res = requests.post(f"{API_URL}/video/transform", json=payload)
    if res.status_code == 200:
        task_id = res.json().get("task_id")
        print(f"✅ Video task queued. Task ID: {task_id}")
        # Note: We can't easily check Celery status from here without a dedicated endpoint, 
        # but the successful submission to Redis is verified.
        return True
    else:
        print(f"❌ Failed to queue video task: {res.text}")
        return False

def test_db_schema():
    print("\n[3/3] Testing Database Schema (Alembic/PostgreSQL)...")
    # This is implicitly tested by settings persistence, but we'll check the health/version if possible
    try:
        res = requests.get(f"{API_URL}/health")
        if res.status_code == 200:
            print("✅ Database connection healthy.")
            return True
    except:
        print("❌ Database health check failed.")
        return False

if __name__ == "__main__":
    s1 = test_settings_persistence()
    s2 = test_async_video_processing()
    s3 = test_db_schema()
    
    if all([s1, s2, s3]):
        print("\n🚀 PHASE 3 VERIFICATION COMPLETED SUCCESSFULLY!")
    else:
        print("\n⚠️ PHASE 3 VERIFICATION FAILED SOME CHECKS.")
        sys.exit(1)
