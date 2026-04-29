import requests
import json
import os
import sys
from datetime import datetime

# API Configuration
API_BASE = "http://localhost:8000/api/v1"
TOKEN = os.getenv("ETTAMETTA_TEST_TOKEN")

if not TOKEN:
    print("WARNING: ETTAMETTA_TEST_TOKEN not set. Audit may fail on protected routes.")

ENDPOINTS = [
    ("/discovery/trends", "GET", {"niche": "Motivation"}),
    ("/discovery/alerts", "GET", {}),
    ("/analytics/stats/summary", "GET", {}),
    ("/analytics/report", "GET", {}),
    ("/video/jobs", "GET", {}),
    ("/publish/accounts", "GET", {}),
    ("/publish/platforms", "GET", {}),
    ("/nexus/personas", "GET", {}),
    ("/nexus/blueprints", "GET", {}),
]

def audit_endpoint(path, method, params=None):
    url = f"{API_BASE}{path}"
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=5)
        else:
            response = requests.post(url, headers=headers, json=params, timeout=5)
            
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}", response.text[:100]
            
        data = response.json()
        if "data" not in data:
            return False, "Missing 'data' key", data
            
        return True, "OK", None
    except Exception as e:
        return False, "Exception", str(e)

def run_audit():
    print(f"--- Ettametta Semantic Parity Audit ({datetime.now().isoformat()}) ---")
    results = []
    failed = 0
    
    for path, method, params in ENDPOINTS:
        success, status, detail = audit_endpoint(path, method, params)
        print(f"[{'PASS' if success else 'FAIL'}] {method} {path} - {status}")
        if not success:
            print(f"      Detail: {detail}")
            failed += 1
        results.append({"path": path, "success": success, "status": status})
        
    print("-" * 50)
    print(f"Summary: {len(ENDPOINTS) - failed}/{len(ENDPOINTS)} passed.")
    
    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run_audit()
