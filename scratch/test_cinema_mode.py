#!/usr/bin/env python3
"""Test cinema mode pipeline end-to-end: dispatch compose and poll for result."""

import json
import time
import sys
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000/api/v1"

def api_post(path, data, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"HTTP Error {e.code} for {path}: {body}")
        return json.loads(body) if body else {}

def api_get(path, token):
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {token}"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def main():
    import random
    import string
    suffix = int(time.time())
    uid = "".join(random.choices(string.ascii_lowercase, k=6))
    email = f"render_{suffix}_{uid}@example.com"
    username = f"render_{uid}"
    
    print("=== Registering new user ===")
    reg = api_post("/auth/register", {
        "email": email,
        "password": "TestPassword123!",
        "username": username
    })
    print(f"Register response keys: {list(reg.keys())}")

    # Login
    print("\n=== Logging in ===")
    login = api_post("/auth/login", {
        "email": email,
        "password": "TestPassword123!"
    })
    token = login.get("data", {}).get("access_token", "")
    if not token:
        print(f"Failed to get token. Response: {json.dumps(login, indent=2)[:500]}")
        sys.exit(1)
    print(f"Got token: {token[:30]}...")

    # Dispatch compose
    print("\n=== Dispatching cinema mode compose ===")
    compose = api_post("/nexus/compose", {
        "niche": "Wildlife",
        "cinema_mode": True
    }, token)
    print(f"Compose response: {json.dumps(compose, indent=2)[:500]}")
    
    job_id = compose.get("data", {}).get("job_id", "")
    if not job_id:
        print("No job_id returned!")
        sys.exit(1)
    print(f"Job ID: {job_id}")

    # Poll for up to 15 minutes
    print("\n=== Polling job status ===")
    max_polls = 30  # 30 * 30s = 15 minutes
    for i in range(1, max_polls + 1):
        time.sleep(30)
        result = api_get(f"/nexus/job/{job_id}", token)
        data = result.get("data", result)
        status = data.get("status", "unknown")
        progress = data.get("progress", 0)
        node = data.get("current_node", "")
        output = data.get("output_path", "")
        error = data.get("error_log", "")
        
        print(f"[{i:2d}] Status: {status:10s} | Progress: {progress:3d} | Node: {node:15s} | Output: {output or 'none'}")

        if error:
            print(f"  ERROR: {error[:300]}")

        if status == "COMPLETED":
            print(f"\n✅ RENDER COMPLETE! Output: {output}")
            # Verify file exists
            import os
            if output and os.path.exists(output):
                size = os.path.getsize(output)
                print(f"   File size: {size} bytes ({size/1024/1024:.1f} MB)")
            break
        elif status == "FAILED":
            print("\n❌ RENDER FAILED")
            print(f"   Full data: {json.dumps(data, indent=2)[:1000]}")
            break

    print("\nDone.")

if __name__ == "__main__":
    main()
