"""
Test that DB-stored blueprints persist and include composition_id.

Steps:
1. Login
2. GET /nexus/blueprints — verify composition_id is returned
3. POST /nexus/blueprints — create a custom blueprint
4. GET /nexus/blueprints — verify custom blueprint appears with composition_id
"""

import asyncio
import sys
import uuid

import httpx

BASE_URL = "http://localhost:8000/api/v1"


def _extract_data(resp: httpx.Response) -> dict:
    body = resp.json()
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


async def test():
    async with httpx.AsyncClient() as client:
        # 1. Register + Login
        suffix = uuid.uuid4().hex[:6]
        reg = await client.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": f"bp_test_{suffix}@test.com",
                "password": "TestPass123",
                "username": f"bp_{suffix}",
            },
            timeout=10,
        )
        if reg.status_code not in (200, 201, 409):
            print(f"Register failed: {reg.status_code} {reg.text[:200]}")
            return False

        login = await client.post(
            f"{BASE_URL}/auth/login",
            json={"username": f"bp_{suffix}", "password": "TestPass123"},
            timeout=10,
        )
        if login.status_code != 200:
            # Try with an existing user
            login = await client.post(
                f"{BASE_URL}/auth/login",
                json={"username": "testuser", "password": "TestPass123"},
                timeout=10,
            )
        if login.status_code != 200:
            print(f"Login failed: {login.text[:200]}")
            return False

        token = _extract_data(login).get("access_token", "")
        headers = {"Authorization": f"Bearer {token}"}

        # 2. GET /nexus/blueprints — verify composition_id in all entries
        resp = await client.get(
            f"{BASE_URL}/nexus/blueprints", headers=headers, timeout=10
        )
        print(f"GET /nexus/blueprints: {resp.status_code}")
        if resp.status_code != 200:
            print(f"  Error: {resp.text[:300]}")
            return False

        blueprints = _extract_data(resp)
        print(f"  Total blueprints: {len(blueprints)}")
        missing_cid = [bp for bp in blueprints if "composition_id" not in bp]
        if missing_cid:
            print(f"  ❌ {len(missing_cid)} blueprints missing composition_id:")
            for bp in missing_cid:
                print(f"     - {bp.get('id', 'unknown')}")
            return False
        print(f"  ✅ All {len(blueprints)} blueprints have composition_id")
        for bp in blueprints[:5]:
            print(f"     {bp.get('id','?'):25s} → {bp.get('composition_id','?')}")

        # 3. POST /nexus/blueprints — create a custom test blueprint
        test_bp = {
            "id": f"test-bp-{suffix}",
            "name": "Test Blueprint",
            "description": "Temporary test blueprint for verification",
            "composition_id": "CinematicPortal",
            "nodes": [
                {"type": "ingress", "label": "Test Ingress"},
                {"type": "synthesis", "label": "Test Synthesis"},
                {"type": "egress", "label": "Test Egress"},
            ],
        }
        create = await client.post(
            f"{BASE_URL}/nexus/blueprints",
            headers=headers,
            json=test_bp,
            timeout=10,
        )
        print(f"\nPOST /nexus/blueprints: {create.status_code}")
        if create.status_code == 200 or create.status_code == 201:
            print(f"  ✅ Blueprint '{test_bp['id']}' created")
        elif create.status_code == 400:
            print(f"    (may already exist): {create.text[:200]}")
        else:
            print(f"  ❌ Create failed: {create.text[:300]}")
            return False

        # 4. Verify the custom blueprint appears in the list
        resp2 = await client.get(
            f"{BASE_URL}/nexus/blueprints", headers=headers, timeout=10
        )
        blueprints2 = _extract_data(resp2)
        created = [bp for bp in blueprints2 if bp.get("id") == test_bp["id"]]
        if created:
            bp = created[0]
            cid = bp.get("composition_id")
            print(f"\nCustom blueprint composition_id: {cid}")
            if cid == "CinematicPortal":
                print(f"  ✅ composition_id correctly persisted and returned")
            else:
                print(f"  ❌ Expected CinematicPortal, got {cid}")
                return False
        else:
            print(f"  Custom blueprint not found in list")
            return False

        print(f"\n✅ All blueprint DB tests passed!")
        return True


if __name__ == "__main__":
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
