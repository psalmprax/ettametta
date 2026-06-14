"""
Test the GET /remotion/compositions/{composition_id}/preview endpoint.
Registers a user, logs in, calls the preview, and reports the result.
"""

import asyncio
import sys
import uuid

import httpx

BASE_URL = "http://localhost:8000/api/v1"
COMPOSITION = sys.argv[1] if len(sys.argv) > 1 else "CinematicPortal"
TIMEOUT = 180.0


def _extract_data(resp: httpx.Response) -> dict:
    """Extract the inner `data` field from a success_response wrapper."""
    body = resp.json()
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


async def test():
    async with httpx.AsyncClient() as client:
        # 1. Register a fresh test user
        suffix = uuid.uuid4().hex[:6]
        reg = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": f"preview_test_{suffix}@test.com",
                "password": "TestPass123",
                "username": f"preview_{suffix}",
            },
            timeout=10,
        )
        print(f"Register: {reg.status_code}")
        if reg.status_code not in (200, 201, 409):
            print(f"  Body: {reg.text[:300]}")
        else:
            print(f"  User created: preview_{suffix}")

        # 2. Login to get a token
        login = await client.post(
            f"{BASE_URL}/auth/login",
            json={"username": f"preview_{suffix}", "password": "TestPass123"},
            timeout=10,
        )
        print(f"Login: {login.status_code}")

        # If login failed, try registering via a different user
        if login.status_code != 200:
            login = await client.post(
                f"{BASE_URL}/auth/login",
                json={"username": "preview_test", "password": "TestPass123"},
                timeout=10,
            )
            print(f"Login (alt): {login.status_code}")

        if login.status_code != 200:
            print(f"  Body: {login.text[:300]}")
            return False

        data = _extract_data(login)
        token = data.get("access_token", "")
        if not token:
            print(f"  No access_token in response: {login.text[:300]}")
            return False
        print(f"  Token obtained: {token[:20]}...")

        headers = {"Authorization": f"Bearer {token}"}

        # 3. Verify compositions list works
        comps = await client.get(
            f"{BASE_URL}/remotion/compositions", headers=headers, timeout=10
        )
        print(f"Compositions: {comps.status_code}")
        if comps.status_code == 200:
            data = comps.json()
            ids = data.get("compositions", [])
            print(f"  Available: {len(ids)} compositions")
            for cid in ids[:5]:
                print(f"    - {cid}")
        else:
            print(f"  Body: {comps.text[:300]}")

        # 4. Call the preview endpoint
        print(f"\nRequesting preview for {COMPOSITION}...")
        resp = await client.get(
            f"{BASE_URL}/remotion/compositions/{COMPOSITION}/preview",
            headers=headers,
            timeout=TIMEOUT,
        )
        print(f"Preview status: {resp.status_code}")
        if resp.status_code == 200:
            ct = resp.headers.get("content-type", "unknown")
            cd = resp.headers.get("content-disposition", "none")
            size = len(resp.content)
            print(f"Content-Type: {ct}")
            print(f"Content-Length: {size:,} bytes ({size / 1024:.1f} KB)")
            print(f"Content-Disposition: {cd}")
            print(f"\n✅ Preview render SUCCEEDED for {COMPOSITION}")
            return True
        else:
            print(f"Error body: {resp.text[:600]}")
            print(f"\n❌ Preview render FAILED for {COMPOSITION}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
