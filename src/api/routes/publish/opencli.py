"""
opencli-rs routes — Chrome-session-based publishing as an alternative to
platform OAuth APIs.

Extracted from the original monolithic publish.py.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.api_responses import success_response

from .common import OpenCLIPostRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/opencli/post")
async def opencli_post(
    request: OpenCLIPostRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """Post content to a platform using the user's Chrome session (via opencli-rs).

    This is an alternative to OAuth-based publishing. The user must have
    a connected session for the platform via /opencli/sessions/connect.
    """
    from src.api.config import settings
    from src.services.opencli.service import opencli_service
    from src.api.utils.models import PublishedContentDB
    from src.api.utils.database import async_session_factory
    from src.shared.enums import ContentPublishStatus

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    platform = request.platform.lower()
    result = await opencli_service.post_to_platform(
        current_user.id, platform, request.content, request.media_url
    )

    if result.get("success"):
        async with async_session_factory() as db:
            try:
                post = PublishedContentDB(
                    title=request.content[:100],
                    platform=platform,
                    status=ContentPublishStatus.PUBLISHED,
                    source_uri=result.get("url") or request.media_url,
                    account_id=None,
                    user_id=current_user.id,
                )
                db.add(post)
                await db.commit()
            finally:
                pass

    return result


@router.post("/opencli/post-multi")
async def opencli_post_multi(
    platforms: list[str],
    content: str,
    media_url: str | None = None,
    current_user: UserDB = Depends(get_current_user),
):
    """Post to multiple platforms using the user's Chrome sessions."""
    from src.api.config import settings
    from src.services.opencli.service import opencli_service

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    import asyncio

    tasks = []
    for platform in platforms:
        tasks.append(
            opencli_service.post_to_platform(
                current_user.id, platform.lower(), content, media_url
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for platform, result in zip(platforms, results):
        if isinstance(result, Exception):
            output.append(
                {"platform": platform, "success": False, "error": str(result)}
            )
        else:
            output.append({"platform": platform, **result})

    return {"results": output}
