#!/bin/bash
set -e

# Get auth token
echo "=== Getting auth token ==="
TOKEN=$(curl -s -X POST http://localhost:7201/api/v1/auth/login -H "Content-Type: application/json" -d '{"username": "testuser_1780564906", "password": "Test1234."}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('access_token',''))")
echo "Token: ${#TOKEN} chars"

# Test SCAN endpoint (calls discovery-go with X-API-Key auth)
echo ""
echo "=== Testing /discovery/scan (Go service) ==="
curl -s --max-time 60 -X POST "http://localhost:7201/api/v1/discovery/scan" -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"niche": "AI", "deep": false}' > /tmp/scan_resp.json
python3 << 'PYEOF'
import json
d = json.load(open('/tmp/scan_resp.json'))
print("success:", d.get('success'))
results = d.get('data',{}).get('results',[])
print("scan results:", len(results))
for r in results[:5]:
    print(f"  [{r.get('platform')}] {r.get('title','')[:60]}")
PYEOF

# Test TRENDS endpoint (calls Python DiscoveryService -> CloakBrowser)
echo ""
echo "=== Testing /discovery/trends (Python + CloakBrowser) ==="
curl -s --max-time 90 "http://localhost:7201/api/v1/discovery/trends?niche=AI&region=US&limit=5" -H "Authorization: Bearer $TOKEN" > /tmp/trends_resp.json
python3 << 'PYEOF'
import json
d = json.load(open('/tmp/trends_resp.json'))
print("success:", d.get('success'))
trends = d.get('data',{}).get('trends',[])
print("trends count:", len(trends))
for c in trends[:5]:
    print(f"  [{c.get('platform')}] {c.get('title','')[:60]}")
PYEOF