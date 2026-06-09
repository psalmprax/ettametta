#!/bin/bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:7201/api/v1/auth/login -H "Content-Type: application/json" -d '{"username": "testuser_1780564906", "password": "Test1234."}' | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('access_token',''))")

echo "Token: ${#TOKEN} chars"

# Test trends endpoint
curl -s --max-time 90 "http://localhost:7201/api/v1/discovery/trends?niche=AI&region=US&limit=5" -H "Authorization: Bearer $TOKEN" > /tmp/trends_response.json

echo "Response size: $(wc -c < /tmp/trends_response.json)"
python3 -c "
import json
d = json.load(open('/tmp/trends_response.json'))
print('success:', d.get('success'))
trends = d.get('data',{}).get('trends',[])
print('trends count:', len(trends))
for c in trends[:5]:
    print(f\"  [{c.get('platform')}] {c.get('title','')[:60]}\")
"