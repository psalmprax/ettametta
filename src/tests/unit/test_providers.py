#!/usr/bin/env python3
"""
E2E Test Script for Video Generation Providers
Tests all working and non-working providers
"""

import asyncio
import os
import requests
import sys

API_BASE = os.getenv("API_BASE", "http://localhost:7201/api/v1")
TOKEN = None


def login():
    """Login and get token"""
    global TOKEN
    response = requests.post(
        f"{API_BASE}/auth/login",
        data={"username": "samuelolle", "password": "Single123."},
    )
    if response.status_code == 200:
        TOKEN = response.json()["access_token"]
        print("✓ Login successful")
        return True
    print(f"✗ Login failed: {response.text}")
    return False


def test_api_provider(name, endpoint, payload):
    """Test an API-based provider (no browser needed)"""
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

    try:
        response = requests.post(
            f"{API_BASE}{endpoint}", json=payload, headers=headers, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ {name}: {data}")
            return True
        elif response.status_code == 401:
            print(f"⚠ {name}: Auth required")
            return False
        elif response.status_code == 403:
            print(f"⚠ {name}: Subscription required")
            return False
        else:
            print(f"✗ {name}: {response.status_code} - {response.text[:100]}")
            return False
    except Exception as e:
        print(f"✗ {name}: {e}")
        return False


def test_pollinations():
    """Test Pollinations (free, no login)"""
    try:
        url = "https://image.pollinations.ai/prompt/a%20cyberpunk%20city?width=1024&height=1024&nologo=1"
        response = requests.get(url, timeout=30)

        if response.status_code == 200 and len(response.content) > 1000:
            print(f"✓ Pollinations: Image generated ({len(response.content)} bytes)")
            return True
        else:
            print(f"✗ Pollinations: Failed ({len(response.content)} bytes)")
            return False
    except Exception as e:
        print(f"✗ Pollinations: {e}")
        return False


def test_discovery():
    """Test Discovery API"""
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

    try:
        response = requests.get(
            f"{API_BASE}/discovery/trends?niche=Motivation", headers=headers, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Discovery: {len(data)} trends")
            return True
        else:
            print(f"✗ Discovery: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Discovery: {e}")
        return False


def test_agent():
    """Test Agent chat"""
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

    try:
        response = requests.post(
            f"{API_BASE}/agent/chat",
            json={"message": "hello"},
            headers=headers,
            timeout=30,
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✓ Agent: {data.get('response', '')[:50]}...")
            return True
        else:
            print(f"✗ Agent: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Agent: {e}")
        return False


def test_content_editor():
    """Test Content Editor providers"""
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

    try:
        response = requests.get(
            f"{API_BASE}/content-editor/providers", headers=headers, timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            providers = data.get("providers", {})
            gen_count = len(providers.get("generation", []))
            print(f"✓ Content Editor: {gen_count} providers")
            return True
        else:
            print(f"✗ Content Editor: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Content Editor: {e}")
        return False


def main():
    print("=" * 60)
    print("E2E Video Generation Providers Test")
    print("=" * 60)

    # Login first
    print("\n[1] Testing Authentication...")
    if not login():
        print("Cannot proceed without authentication")
        return

    # Test Discovery API
    print("\n[2] Testing Discovery API...")
    test_discovery()

    # Test Agent
    print("\n[3] Testing Agent Chat...")
    test_agent()

    # Test Content Editor
    print("\n[4] Testing Content Editor...")
    test_content_editor()

    # Test Pollinations (no auth needed)
    print("\n[5] Testing Pollinations (no login required)...")
    test_pollinations()

    print("\n" + "=" * 60)
    print("Tests Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
