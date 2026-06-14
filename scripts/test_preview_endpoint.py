"""
Test the GET /remotion/compositions/{composition_id}/preview endpoint.
Sends a request and reports the status, content type, and file size.
"""

import asyncio
import sys

import httpx

BASE_URL = "http://localhost:8000/api/v1"
COMPOSITION = sys.argv[1] if len(sys.argv) > 1 else "CinematicPortal"


async def test():
    async with httpx.AsyncClient() as client:
        # 1. Login to get a token
        login = await client.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin"},
        )
        print(f"Login: {login.status_code}")
        if login.status_code != 200:
            print(f"Login body: {login.text[:300]}")
            return False

        token = login.json().get("access_token", "")
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Call the preview endpoint
        print(f"\nRequesting preview for {COMPOSITION}...")
        resp = await client.get(
            f"{BASE_URL}/remotion/compositions/{COMPOSITION}/preview",
            headers=headers,
            timeout=180.0,
        )
        print(f"Preview status: {resp.status_code}")
        if resp.status_code == 200:
            ct = resp.headers.get("content-type", "unknown")
            cd = resp.headers.get("content-disposition", "none")
            size = len(resp.content)
            print(f"Content-Type: {ct}")
            print(f"Content-Length: {size:,} bytes ({size / 1024:.1f} KB)")
            print(f"Content-Disposition: {cd}")
            return True
        else:
            print(f"Error body: {resp.text[:500]}")
            return False


if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
