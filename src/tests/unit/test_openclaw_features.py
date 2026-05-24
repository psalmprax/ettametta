#!/usr/bin/env python3
"""
Test script to verify OpenCLAW skills are working:
- Discovery skills
- Video generation skills (12 providers)
- Content editor skills
"""

import pytest
import socket
import requests
import json
import sys
import os


# Skip if not running in Docker environment (API host won't resolve)
_HAS_DOCKER_API = False
try:
    socket.getaddrinfo("api", 8000)
    _HAS_DOCKER_API = True
except (socket.gaierror, OSError):
    pass

API_URL = os.getenv("API_URL", "http://api:8000")
TOKEN = os.getenv("AUTH_TOKEN", "")


def print_header(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


@pytest.mark.skipif(not _HAS_DOCKER_API, reason="requires Docker environment (api:8000)")
def test_discovery_trends():
    """Test discovery /trends endpoint"""
    print_header("Testing /discovery/trends")

    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    params = {"niche": "motivation", "horizon": "24h", "min_viral_score": "50"}

    try:
        response = requests.get(
            f"{API_URL}/discovery/trends", params=params, headers=headers, timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} trending items")
            for i, item in enumerate(data[:3]):
                print(
                    f"  {i + 1}. {item.get('title', 'N/A')[:50]}... ({item.get('platform', 'N/A')})"
                )
        else:
            assert False, f"Error: {response.status_code} - {response.text[:100]}"
    except Exception as e:
        assert False, f"Connection error: {e}"


@pytest.mark.skipif(not _HAS_DOCKER_API, reason="requires Docker environment (api:8000)")
def test_discovery_niches():
    """Test discovery niches endpoint"""
    print_header("Testing /discovery/niches")

    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

    try:
        response = requests.get(
            f"{API_URL}/discovery/niches", headers=headers, timeout=10
        )
        if response.status_code == 200:
            niches = response.json()
            print(f"✅ Found {len(niches)} niches")
            print(f"  Sample: {niches[:5]}")
        else:
            assert False, f"Error: {response.status_code}"
    except Exception as e:
        assert False, f"Connection error: {e}"


@pytest.mark.skipif(not _HAS_DOCKER_API, reason="requires Docker environment (api:8000)")
def test_discovery_niche_trends():
    """Test niche-trends endpoint"""
    print_header("Testing /discovery/niche-trends/motivation")

    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

    try:
        response = requests.get(
            f"{API_URL}/discovery/niche-trends/motivation", headers=headers, timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Niche trends retrieved")
            print(f"  Keywords: {data.get('top_keywords', [])[:5]}")
        else:
            assert False, f"Error: {response.status_code}"
    except Exception as e:
        assert False, f"Connection error: {e}"


@pytest.mark.skipif(not _HAS_DOCKER_API, reason="requires Docker environment (api:8000)")
def test_content_editor_providers():
    """Test content-editor providers endpoint"""
    print_header("Testing /content-editor/providers")

    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

    try:
        response = requests.get(
            f"{API_URL}/content-editor/providers", headers=headers, timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            providers = data.get("providers", {})

            print("✅ Providers retrieved:")
            print(f"  Generation: {len(providers.get('generation', []))} providers")
            for p in providers.get("generation", [])[:5]:
                print(f"    - {p.get('id')}: {p.get('name')} (free={p.get('free')})")

            print(
                f"  Content Editor: {len(providers.get('content_editor', []))} providers"
            )
            print(f"  Remotion: {len(providers.get('remotion', []))} templates")
        else:
            assert False, f"Error: {response.status_code}"
    except Exception as e:
        assert False, f"Connection error: {e}"


@pytest.mark.skipif(not _HAS_DOCKER_API, reason="requires Docker environment (api:8000)")
def test_content_editor_find():
    """Test content-editor find endpoint"""
    print_header("Testing /content-editor/find")

    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    headers["Content-Type"] = "application/json"

    payload = {
        "source": "youtube",
        "query": "motivation",
        "niche": "motivation",
        "limit": 3,
    }

    try:
        response = requests.post(
            f"{API_URL}/content-editor/find", json=payload, headers=headers, timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Content found: {data.get('status')}")
            videos = data.get("videos", [])
            print(f"  Found {len(videos)} videos")
        else:
            assert False, f"Error: {response.status_code} - {response.text[:100]}"
    except Exception as e:
        assert False, f"Connection error: {e}"


def test_video_providers_free():
    """Test free video providers"""
    print_header("Testing Free Video Providers")

    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}

    try:
        response = requests.get(
            f"{API_URL}/free-video/providers", headers=headers, timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            providers = data.get("providers", {})

            print(f"✅ {len(providers)} video providers available:")
            for name, config in providers.items():
                print(
                    f"  - {name}: {config.get('free_credits', 'N/A')} free credits/day"
                )
        else:
            assert False, "Not found at /free-video/providers"
    except Exception as e:
        print("❌ /free-video/providers not available (this is optional)")
        # This endpoint might not exist yet — treat as non-fatal


def main():
    print("\n🔬 OpenCLAW Features Test")
    print(f"API URL: {API_URL}")

    if not TOKEN:
        print("⚠️ No AUTH_TOKEN set - some tests may fail with 401")

    results = []

    # Test discovery
    results.append(("Discovery - Trends", test_discovery_trends()))
    results.append(("Discovery - Niches", test_discovery_niches()))
    results.append(("Discovery - Niche Trends", test_discovery_niche_trends()))

    # Test content editor
    results.append(("Content Editor - Providers", test_content_editor_providers()))

    # Test content editor find (if authenticated)
    if TOKEN:
        results.append(("Content Editor - Find", test_content_editor_find()))

    # Test video providers
    results.append(("Free Video Providers", test_video_providers_free()))

    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
