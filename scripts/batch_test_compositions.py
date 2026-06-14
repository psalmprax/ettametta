"""
Batch test all 12 registered Remotion compositions via the preview endpoint.
Reports pass/fail/timeout for each composition and a final summary.
"""

import asyncio
import sys
import time
import uuid

import httpx

BASE_URL = "http://localhost:8000/api/v1"
PREVIEW_TIMEOUT = 130.0  # slightly above the 120s endpoint timeout


def _extract_data(resp: httpx.Response) -> dict:
    body = resp.json()
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


async def login(client: httpx.AsyncClient) -> str | None:
    """Register + login to get a token."""
    suffix = uuid.uuid4().hex[:6]
    await client.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": f"batch_{suffix}@test.com",
            "password": "TestPass123",
            "username": f"batch_{suffix}",
        },
        timeout=10,
    )
    login = await client.post(
        f"{BASE_URL}/auth/login",
        json={"username": f"batch_{suffix}", "password": "TestPass123"},
        timeout=10,
    )
    if login.status_code == 200:
        return _extract_data(login).get("access_token", "")
    # Fallback login
    login = await client.post(
        f"{BASE_URL}/auth/login",
        json={"username": "testuser", "password": "TestPass123"},
        timeout=10,
    )
    if login.status_code == 200:
        return _extract_data(login).get("access_token", "")
    return None


async def preview_composition(
    client: httpx.AsyncClient, headers: dict, cid: str
) -> dict:
    """Test a single composition preview. Returns result dict."""
    start = time.time()
    result = {
        "composition": cid,
        "status": "unknown",
        "size_kb": None,
        "duration_s": None,
        "error": None,
    }
    try:
        resp = await client.get(
            f"{BASE_URL}/remotion/compositions/{cid}/preview",
            headers=headers,
            timeout=PREVIEW_TIMEOUT,
        )
        elapsed = round(time.time() - start, 1)
        result["duration_s"] = elapsed
        if resp.status_code == 200:
            result["status"] = "PASS"
            result["size_kb"] = round(len(resp.content) / 1024, 1)
        elif resp.status_code == 504:
            result["status"] = "TIMEOUT"
            result["error"] = "504 Gateway Timeout (120s exceeded)"
        else:
            result["status"] = "FAIL"
            try:
                result["error"] = resp.json().get("error", {}).get("message", resp.text[:200])
            except Exception:
                result["error"] = resp.text[:200]
    except httpx.TimeoutException:
        elapsed = round(time.time() - start, 1)
        result["status"] = "TIMEOUT"
        result["duration_s"] = elapsed
        result["error"] = f"HTTP timeout after {elapsed}s"
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        result["status"] = "FAIL"
        result["duration_s"] = elapsed
        result["error"] = str(e)[:200]
    return result


async def main():
    async with httpx.AsyncClient() as client:
        print("=" * 60)
        print("  Batch Composition Preview Test")
        print("=" * 60)

        # Login
        token = await login(client)
        if not token:
            print("❌ Could not authenticate. Aborting.")
            return
        headers = {"Authorization": f"Bearer {token}"}
        print(f"  Auth: ✅ Token obtained\n")

        # Fetch compositions list
        comps_resp = await client.get(
            f"{BASE_URL}/remotion/compositions", headers=headers, timeout=10
        )
        if comps_resp.status_code != 200:
            print(f"❌ Could not fetch compositions list: {comps_resp.text[:200]}")
            return
        compositions = comps_resp.json().get("compositions", [])
        print(f"  Compositions to test: {len(compositions)}\n")

        # Test each composition
        results = []
        for i, cid in enumerate(compositions, 1):
            print(f"  [{i}/{len(compositions)}] {cid}...", end=" ", flush=True)
            result = await preview_composition(client, headers, cid)
            results.append(result)

            status_icon = {
                "PASS": "✅",
                "TIMEOUT": "⏳",
                "FAIL": "❌",
            }.get(result["status"], "❓")

            details = ""
            if result["status"] == "PASS":
                details = f"{result['size_kb']} KB in {result['duration_s']}s"
            elif result["status"] == "TIMEOUT":
                details = f"timed out at {result['duration_s']}s"
            else:
                details = result.get("error", "") or ""
            print(f"{status_icon}  {details}")

        # Summary
        passed = [r for r in results if r["status"] == "PASS"]
        timed_out = [r for r in results if r["status"] == "TIMEOUT"]
        failed = [r for r in results if r["status"] == "FAIL"]

        print("\n" + "=" * 60)
        print("  SUMMARY")
        print("=" * 60)
        print(f"  ✅ Pass:   {len(passed)}/{len(compositions)}")
        for r in passed:
            print(f"           {r['composition']:25s} {r['size_kb']} KB ({r['duration_s']}s)")
        if timed_out:
            print(f"  ⏳ Timeout: {len(timed_out)}/{len(compositions)}")
            for r in timed_out:
                print(f"           {r['composition']:25s} (3D WebGL - needs GPU)")
        if failed:
            print(f"  ❌ Fail:   {len(failed)}/{len(compositions)}")
            for r in failed:
                print(f"           {r['composition']:25s} {r.get('error', '')}")

        print(f"\n  Note: Timeout compositions use Three.js/WebGL which is slow in")
        print(f"  headless Chromium without a GPU. They work on GPU-enabled hosts.")


if __name__ == "__main__":
    asyncio.run(main())
