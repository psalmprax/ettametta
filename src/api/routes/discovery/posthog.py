"""
PostHog Event Tracking for Ettametta

Integrates ettametta discovery/scanning events with PostHog for product analytics.
Accepts PostHog-compatible event data and forwards to PostHog API.
"""

import httpx
import asyncio
import json
import os
from typing import Any, Optional

from fastapi import APIRouter, Request, HTTPException, status

router = APIRouter(prefix="/posthog", tags=["PostHog Integration"])

# PostHog configuration
POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "")
POSTHOG_SERVER_URL = os.getenv("POSTHOG_SERVER_URL", "https://app.posthog.com")
DEFAULT_PROJECT = os.getenv("POSTHOG_PROJECT_ID", "$default")

# Rate limiting for PostHog events
_posthog_client: Optional[httpx.AsyncClient] = None


def _get_posthog_client() -> httpx.AsyncClient:
    """Get or create the PostHog HTTP client."""
    global _posthog_client
    if _posthog_client is None:
        _posthog_client = httpx.AsyncClient(
            base_url=POSTHOG_SERVER_URL,
            timeout=10.0,
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
    return _posthog_client


async def _send_to_posthog(
    event_name: str,
    distinct_id: str,
    properties: dict[str, Any],
    ip: str | None = None,
    ip_country: str | None = None,
    referrer: str | None = None,
    user_agent: str | None = None,
) -> bool:
    """
    Send an event to PostHog.

    PostHog API format:
    POST /api/projects/{project_id}/events/
    {
        "event": event_name,
        "properties": properties,
        "timestamp": optional ISO timestamp,
        "api_version": "2.0"
    }
    """
    if not POSTHOG_API_KEY:
        logger = logging.getLogger(__name__)
        logger.warning("POSTHOG_API_KEY not configured - skipping event")
        return False

    client = _get_posthog_client()

    # Prepare the event payload
    payload = {
        "event": event_name,
        "properties": properties,
        "api_version": "2.0",
    }

    # Add optional fields if provided
    if ip:
        payload["ip"] = ip
    if ip_country:
        payload["ip_country"] = ip_country
    if referrer:
        payload["referrer"] = referrer
    if user_agent:
        payload["user_agent"] = user_agent

    try:
        response = await client.post(
            f"/api/projects/{DEFAULT_PROJECT}/events/",
            json=payload,
            headers={
                "Authorization": f"Key {POSTHOG_API_KEY}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code not in (200, 201, 202, 204):
            logger = logging.getLogger(__name__)
            logger.error(
                f"PostHog API error {response.status_code}: {response.text}"
            )
            return False

        return True

    except httpx.RequestError as e:
        logger = logging.getLogger(__name__)
        logger.error(f"PostHog request failed: {e}")
        return False
    except Exception:
        logger = logging.getLogger(__name__)
        logger.exception("Unexpected error sending to PostHog")
        return False


@router.post("/events", tags=["PostHog Integration"], summary="Send event to PostHog")
async def posthog_events(
    request: Request,
    event: str,
    distinct_id: str,
    properties: dict[str, Any],
    ip: str | None = None,
    ip_country: str | None = None,
    referrer: str | None = None,
    user_agent: str | None = None,
):
    """
    Send a single event to PostHog.

    This endpoint accepts PostHog-compatible event data and forwards it
    to the PostHog API for product analytics.

    - **event**: The event name (e.g., "video_discovered", "video_rendered")
    - **distinct_id**: The user's distinct ID (user ID, session ID, etc.)
    - **properties**: Event properties dict with relevant data
    - **ip**: Optional client IP address
    - **ip_country**: Optional IP country code
    - **referrer**: Optional referrer URL
    - **user_agent**: Optional user agent string
    """
    success = await _send_to_posthog(
        event_name=event,
        distinct_id=distinct_id,
        properties=properties,
        ip=ip,
        ip_country=ip_country,
        referrer=referrer,
        user_agent=user_agent,
    )

    if success:
        return {"status": "ok", "sent": True}
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to send event to PostHog",
        )


@router.post("/batch", tags=["PostHog Integration"], summary="Send batch events to PostHog")
async def posthog_batch_events(
    request: Request,
    events: list[dict[str, Any]],
):
    """
    Send a batch of events to PostHog.

    Each event in the list should have:
    - event: event name
    - distinct_id: user distinct ID
    - properties: event properties
    """
    if not POSTHOG_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostHog not configured",
        )

    client = _get_posthog_client()

    # PostHog batch format
    payload = {
        "events": events,
        "api_version": "2.0",
    }

    try:
        response = await client.post(
            f"/api/projects/{DEFAULT_PROJECT}/events/batch/",
            json=payload,
            headers={
                "Authorization": f"Key {POSTHOG_API_KEY}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code not in (200, 201, 202, 204):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"PostHog API error: {response.text}",
            )

        return {"status": "ok", "sent": len(events)}
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PostHog request failed: {e}",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected error sending batch to PostHog",
        )
