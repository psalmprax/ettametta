import requests
import json

BASE_URL = "http://149.104.110.122.sslip.io:7200/api/v1"
AUTH_URL = f"{BASE_URL}/auth/login"
TRADEMARK_URL = f"{BASE_URL}/agent/generate-trademark"

# 1. Login
print("Logging in...")
login_data = {"username": "test@example.com", "password": "password123"}
resp = requests.post(AUTH_URL, data=login_data)
if resp.status_code != 200:
    print(f"Login failed: {resp.text}")
    exit(1)

token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. Generate Trademark
print("Generating Trademark for niche: 'Stoic Wisdom'...")
payload = {"niche": "Stoic Wisdom"}
resp = requests.post(TRADEMARK_URL, json=payload, headers=headers)

if resp.status_code == 200:
    print("✅ Trademark Generated Successfully!")
    print(json.dumps(resp.json(), indent=2))
else:
    print(f"❌ Trademark Generation Failed: {resp.status_code}")
    print(resp.text)
