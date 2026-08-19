import asyncio
import datetime
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from src.api.routes.auth import get_current_user
from src.api.utils.database import get_db
from src.api.utils.models import PublishedContentDB
from src.api.utils.user_models import UserDB, UserRole
from src.api.utils.api_responses import success_response
from src.api.utils.subscription import credits_required
from src.shared.enums import ContentPublishStatus, ABTestStatus
from src.services.optimization.service import base_optimization_service
from src.services.optimization.youtube_publisher import base_youtube_service
from src.services.optimization.tiktok_publisher import base_tiktok_service
from src.services.optimization.auth import token_manager
from src.services.payment.credit_service import credit_service
from src.api.routes.publishing.platforms import SUPPORTED_PLATFORMS, PLATFORM_NAME_TO_KEY

router = APIRouter()

logger = logging.getLogger(__name__)


class PublishRequest(BaseModel):
    video_path: str
    niche: str
    platform: str = "YouTube Shorts"
    account_id: str | None = None
    inject_monetization: bool = False
    variant_b_title: str | None = None
    variant_b_description: str | None = None


class MultiPlatformPublishRequest(BaseModel):
    """Request for publishing to multiple platforms at once"""

    video_path: str
    niche: str
    platforms: list[str]
    account_id: str | None = None
    inject_monetization: bool = False
    variant_b_title: str | None = None
    variant_b_description: str | None = None


@router.post("/package")
async def generate_package(
    niche: str,
    platform: str = "YouTube Shorts",
    current_user: UserDB = Depends(get_current_user),
):
    try:
        content_id = str(current_user.id) + "-" + str(uuid.uuid4())[:8]
        package = await base_optimization_service.generate_viral_package(
            content_id, niche, platform
        )
        return success_response(data=package)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")


@router.get("/comments/{content_id}")
async def get_content_comments(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 10,
):
    """Fetch comments for a published post."""
    try:
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.id == content_id,
            PublishedContentDB.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="Post not found")

        if not content.source_uri:
            raise HTTPException(
                status_code=400, detail="Post has no URL (not published yet)"
            )

        platform_id = None
        platform_key = content.platform.lower()

        if "youtube.com" in content.source_uri or "youtu.be" in content.source_uri:
            if "youtu.be" in content.source_uri:
                platform_id = content.source_uri.split("/")[-1].split("?")[0]
            else:
                url_parts = content.source_uri.split("/")
                for i, part in enumerate(url_parts):
                    if part == "watch" and i + 1 < len(url_parts):
                        platform_id = url_parts[i + 1].split("&")[0].split("?")[0]
                        break
                    elif (
                        part.startswith("UC") or len(part) == 11
                    ):
                        platform_id = part.split("?")[0]
                        break
            platform_key = "youtube"

        elif "tiktok.com" in content.source_uri:
            url_clean = content.source_uri.split("?")[0]
            url_parts = url_clean.split("/")

            for part in reversed(url_parts):
                if part.isdigit() and len(part) >= 15:
                    platform_id = part
                    break
                elif len(part) >= 8 and any(c.isalnum() for c in part):
                    platform_id = part
                    break

            platform_key = "tiktok"

        if not platform_id:
            raise HTTPException(
                status_code=400, detail="Could not extract platform ID from URL"
            )

        comments = []

        if platform_key == "tiktok":
            comments = await base_tiktok_service.get_comments(
                platform_id, user_id=current_user.id, limit=limit
            )
        elif platform_key == "youtube":
            comments = []

        return success_response(
            data={
                "platform": platform_key,
                "video_id": platform_id,
                "comments": comments,
                "total_count": len(comments),
            }
        )

    finally:
        pass


@router.post("/sync/{content_id}")
async def sync_content_metrics(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """Syncs live metrics from the social platform to the database for a specific post."""
    try:
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.id == content_id,
            PublishedContentDB.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="Post not found")

        if not content.source_uri:
            raise HTTPException(
                status_code=400, detail="Post has no URL (not published yet)"
            )

        platform_id = None
        platform_key = content.platform.lower()

        if "youtube.com" in content.source_uri or "youtu.be" in content.source_uri:
            if "youtu.be" in content.source_uri:
                platform_id = content.source_uri.split("/")[-1].split("?")[0]
            else:
                url_parts = content.source_uri.split("/")
                for i, part in enumerate(url_parts):
                    if part == "watch" and i + 1 < len(url_parts):
                        platform_id = url_parts[i + 1].split("&")[0].split("?")[0]
                        break
                    elif (
                        part.startswith("UC") or len(part) == 11
                    ):
                        platform_id = part.split("?")[0]
                        break
            platform_key = "youtube"

        elif "tiktok.com" in content.source_uri:
            url_clean = content.source_uri.split("?")[0]
            url_parts = url_clean.split("/")

            for part in reversed(url_parts):
                if part.isdigit() and len(part) >= 15:
                    platform_id = part
                    break
                elif len(part) >= 8 and any(c.isalnum() for c in part):
                    platform_id = part
                    break

            platform_key = "tiktok"

        if not platform_id:
            raise HTTPException(
                status_code=400, detail="Could not extract platform ID from URL"
            )

        metrics = {"views": 0, "likes": 0, "comments": 0, "shares": 0}

        if platform_key == "youtube":
            metrics = await base_youtube_service.get_metrics(
                platform_id, user_id=current_user.id
            )
        elif platform_key == "tiktok":
            metrics = await base_tiktok_service.get_metrics(
                platform_id, user_id=current_user.id
            )

        old_views = content.view_count or 0
        content.view_count = metrics.get("views", 0)
        content.like_count = metrics.get("likes", 0)
        content.comment_count = metrics.get("comments", 0)
        content.share_count = metrics.get("shares", 0)

        from src.api.utils.models import ABTestDB

        stmt_ab = select(ABTestDB).where(ABTestDB.content_id == str(content.id))
        result_ab = await db.execute(stmt_ab)
        ab_test = result_ab.scalar_one_or_none()
        if ab_test and not ab_test.completed_at:
            new_views = max(0, (content.view_count or 0) - old_views)
            if new_views > 0:
                variant_a_views = new_views // 2
                variant_b_views = new_views - variant_a_views

                ab_test.variant_a_view_count = (
                    ab_test.variant_a_view_count or 0
                ) + variant_a_views
                ab_test.variant_b_view_count = (
                    ab_test.variant_b_view_count or 0
                ) + variant_b_views

                engagement_score = (
                    (content.like_count or 0)
                    + (content.comment_count or 0)
                    + (content.share_count or 0)
                )
                if engagement_score > 0:
                    conversions_a = engagement_score // 2
                    conversions_b = engagement_score - conversions_a
                    ab_test.variant_a_conversion_count = (
                        ab_test.variant_a_conversion_count or 0
                    ) + conversions_a
                    ab_test.variant_b_conversion_count = (
                        ab_test.variant_b_conversion_count or 0
                    ) + conversions_b

        await db.commit()
        return success_response(data={"status": "success", "metrics": metrics})
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Publishing operation failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")
    finally:
        pass


@router.get("/jobs")
async def get_publish_jobs(
    current_user: UserDB = Depends(get_current_user), db=Depends(get_db)
):
    """Returns active publish jobs for the current user."""
    try:
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.user_id == current_user.id,
        )
        stmt = stmt.order_by(PublishedContentDB.published_at.desc())
        result = await db.execute(stmt)
        jobs = result.scalars().all()
        return success_response(
            data=[
                {
                    "id": j.id,
                    "title": j.title,
                    "platform": j.platform,
                    "status": j.status.value if hasattr(j.status, "value") else j.status,
                    "progress": 0,
                    "created_at": j.published_at,
                    "niche": j.niche,
                }
                for j in jobs
            ]
        )
    except Exception as e:
        logger.error(f"Publish jobs failed: {e}")
        return success_response(data=[])
    finally:
        pass


@router.post("/auto-broadcast")
async def auto_broadcast(
    current_user: UserDB = Depends(get_current_user),
):
    """Triggers autonomous broadcast pattern."""
    try:
        from src.services.optimization.scheduler_tasks import check_and_post_scheduled

        check_and_post_scheduled.delay()

        return success_response(
            data={
                "status": "initiated",
                "message": "Autonomous broadcast pattern propagating across distribution nodes.",
            }
        )
    except Exception as e:
        logger.error(f"Auto-broadcast failed: {e}")
        raise HTTPException(
            status_code=503, detail="Broadcast pattern injection failed"
        )


@router.get("/history")
async def get_publish_history(
    current_user: UserDB = Depends(get_current_user), db=Depends(get_db)
):
    try:
        stmt = select(PublishedContentDB)
        if current_user.role != UserRole.ADMIN:
            stmt = stmt.where(PublishedContentDB.user_id == current_user.id)

        stmt = stmt.order_by(PublishedContentDB.published_at.desc())
        result = await db.execute(stmt)
        history = result.scalars().all()
        return success_response(data=history)
    except Exception as e:
        logger.error(f"Publish history failed: {e}")
        return success_response(data=[])
    finally:
        pass


@router.post("/retry/{content_id}")
async def retry_publish(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """Retry publishing a video that was pending authentication."""
    from src.api.utils.models import PublishedContentDB

    try:
        stmt = select(PublishedContentDB).where(
            PublishedContentDB.id == content_id,
            PublishedContentDB.user_id == current_user.id,
        )
        result = await db.execute(stmt)
        content = result.scalar_one_or_none()

        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        if content.status != ContentPublishStatus.PENDING_AUTH:
            raise HTTPException(
                status_code=400,
                detail=f"Content is not in PENDING_AUTH status. Current: {content.status}",
            )

        metadata_dict = content.metadata_json or {}
        video_path = metadata_dict.get("video_path")
        platform_key = metadata_dict.get("platform_key", content.platform.lower())

        if not video_path:
            raise HTTPException(
                status_code=400, detail="Video path not found in content metadata"
            )

        has_auth = (
            await token_manager.get_token(platform_key, user_id=current_user.id)
            is not None
        )

        if not has_auth:
            raise HTTPException(
                status_code=401,
                detail=f"Platform '{platform_key}' still not authenticated. Please authenticate first.",
            )

        metadata = await base_optimization_service.generate_viral_package(
            str(content_id), content.niche, content.platform
        )

        url = None
        if platform_key == "youtube":
            url = await base_youtube_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "tiktok":
            from src.services.optimization.tiktok_publisher import base_tiktok_service

            url = await base_tiktok_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "instagram":
            from src.services.optimization.instagram_publisher import (
                base_instagram_service,
            )

            url = await base_instagram_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "facebook":
            from src.services.optimization.facebook_publisher import (
                base_facebook_service,
            )

            url = await base_facebook_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "x":
            from src.services.optimization.x_publisher import base_x_service

            url = await base_x_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "linkedin":
            from src.services.optimization.linkedin_publisher import (
                base_linkedin_service,
            )

            url = await base_linkedin_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )

        content.status = (
            ContentPublishStatus.PUBLISHED if url else ContentPublishStatus.FAILED
        )
        content.source_uri = url
        content.published_at = datetime.datetime.utcnow() if url else None

        metadata_dict.pop("delete_at", None)
        metadata_dict.pop("retention_hours", None)
        metadata_dict.pop("requires_auth", None)
        content.metadata_json = metadata_dict

        await db.commit()

        return success_response(
            data={
                "status": "success" if url else "failed",
                "source_uri": url,
                "message": "Video published successfully"
                if url
                else "Failed to publish video",
            }
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")
    finally:
        pass


@router.post("/post")
async def publish_video(
    request: PublishRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    credits_cost: int = Depends(credits_required("social_publish")),
):
    from src.api.utils.models import PublishedContentDB, ABTestDB

    try:
        await credit_service.consume_credits(
            user_id=current_user.id,
            amount=credits_cost,
            action="social_publish",
            db=db,
            description=f"Direct post to {request.platform}",
        )

        content_id = str(uuid.uuid4())
        metadata = await base_optimization_service.generate_viral_package(
            content_id, request.niche, request.platform
        )

        if request.inject_monetization:
            from src.api.utils.models import AffiliateLinkDB
            from src.services.monetization.service import base_monetization_service

            try:
                script_text = metadata.description or ""
                recommendations = await base_monetization_service.recommend_products(
                    request.niche, script_text
                )

                if recommendations:
                    top_rec = recommendations[0]
                    injection_text = f"\n\n🔥 {top_rec.get('cta_text', 'Check this out')}: {top_rec.get('link', '')}"
                    metadata.description += injection_text
                    logger.info(
                        f"[Monetization] AI Recommended: {top_rec.get('name', 'Product')}"
                    )
                else:
                    stmt_aff = (
                        select(AffiliateLinkDB)
                        .where(AffiliateLinkDB.niche == request.niche)
                        .order_by(AffiliateLinkDB.created_at.desc())
                        .limit(1)
                    )
                    res_aff = await db.execute(stmt_aff)
                    aff_link = res_aff.scalar_one_or_none()
                    if aff_link:
                        injection_text = f"\n\n🔥 {aff_link.cta_text or 'Check this out'}: {aff_link.link}"
                        metadata.description += injection_text
                        logger.info(
                            f"[Monetization] Injected link: {aff_link.product_name}"
                        )
            except Exception as e:
                logger.warning(f"[Monetization] AI recommendation failed: {e}")
                stmt_aff = (
                    select(AffiliateLinkDB)
                    .where(AffiliateLinkDB.niche == request.niche)
                    .order_by(AffiliateLinkDB.created_at.desc())
                    .limit(1)
                )
                res_aff = await db.execute(stmt_aff)
                aff_link = res_aff.scalar_one_or_none()
                if aff_link:
                    injection_text = f"\n\n🔥 {aff_link.cta_text or 'Check this out'}: {aff_link.link}"
                    metadata.description += injection_text
                    logger.info(
                        f"[Monetization] Injected link: {aff_link.product_name}"
                    )

        url = None

        platform_lower = request.platform.lower()

        platform_key = PLATFORM_NAME_TO_KEY.get(platform_lower, platform_lower)

        if platform_key not in SUPPORTED_PLATFORMS:
            raise HTTPException(
                status_code=400,
                detail=f"Platform '{request.platform}' not supported. Available: {', '.join(SUPPORTED_PLATFORMS.keys())}",
            )

        platform_info = SUPPORTED_PLATFORMS[platform_key]

        if request.inject_monetization and not platform_info.get("monetization", False):
            return {
                "status": "warning",
                "message": f"{platform_info['name']} does not support monetization. Publishing without affiliate links.",
                "url": None,
            }

        has_auth = (
            await token_manager.get_token(
                platform_key, user_id=current_user.id, account_id=request.account_id
            )
            is not None
        )

        retention_hours = 3

        if not has_auth:
            if request.inject_monetization:
                from datetime import datetime, timedelta

                delete_at = datetime.utcnow() + timedelta(hours=retention_hours)

                new_post = PublishedContentDB(
                    title=metadata.title or "Viral Post",
                    platform=request.platform,
                    status=ContentPublishStatus.PENDING_AUTH,
                    url=None,
                    account_id=request.account_id,
                    user_id=current_user.id,
                    niche=request.niche,
                    metadata={
                        "video_path": request.video_path,
                        "delete_at": delete_at.isoformat(),
                        "retention_hours": retention_hours,
                        "requires_auth": True,
                        "platform_key": platform_key,
                    },
                )
                db.add(new_post)
                await db.commit()

                return {
                    "status": "pending_auth",
                    "message": f"Platform '{platform_info['name']}' not authenticated. Video will be deleted in {retention_hours} hours. Please authenticate to publish with monetization.",
                    "video_id": new_post.id,
                    "delete_at": delete_at.isoformat(),
                    "auth_url": f"/publish/auth/{platform_key}",
                    "requires_auth": True,
                }
            else:
                return {
                    "status": "error",
                    "message": f"Platform '{platform_info['name']}' not authenticated. Please authenticate first.",
                    "auth_url": f"/publish/auth/{platform_key}",
                    "requires_auth": True,
                }

        if platform_key == "youtube":
            url = await base_youtube_service.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "tiktok":
            from src.services.optimization.tiktok_publisher import base_tiktok_service

            url = await base_tiktok_service.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "instagram":
            from src.services.optimization.instagram_publisher import (
                base_instagram_service,
            )

            url = await base_instagram_service.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "facebook":
            from src.services.optimization.facebook_publisher import (
                base_facebook_service,
            )

            url = await base_facebook_service.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "x":
            from src.services.optimization.x_publisher import base_x_service

            url = await base_x_service.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        elif platform_key == "linkedin":
            from src.services.optimization.linkedin_publisher import (
                base_linkedin_service,
            )

            url = await base_linkedin_service.upload_video(
                request.video_path,
                metadata,
                user_id=current_user.id,
                account_id=request.account_id,
            )
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Publisher for platform '{platform_key}' is not yet implemented. "
                f"Supported platforms: youtube, tiktok, instagram, facebook, x, linkedin",
            )

        new_post = PublishedContentDB(
            title=metadata.title or "Viral Post",
            platform=request.platform,
            status=ContentPublishStatus.PUBLISHED if url else ContentPublishStatus.FAILED,
            url=url,
            account_id=request.account_id,
            user_id=current_user.id,
            niche=request.niche,
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)

        if request.variant_b_title:
            new_test = ABTestDB(
                content_id=str(new_post.id),
                variant_a_title=metadata.title,
                variant_a_view_count=0,
                variant_b_view_count=0,
                variant_a_click_count=0,
                variant_b_click_count=0,
                variant_a_conversion_count=0,
                variant_b_conversion_count=0,
                status=ABTestStatus.ACTIVE,
            )
            db.add(new_test)
            await db.commit()
            logger.info(f"[A/B Testing] Initialized test for post {new_post.id}")

        return success_response(
            data={"status": "success", "url": url, "metadata": metadata}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")

    finally:
        pass


@router.post("/post-multi")
async def publish_multi_platform(
    request: MultiPlatformPublishRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Publish video to multiple platforms at once.
    - Authenticated platforms will be published immediately
    - Unauthenticated platforms will be stored as PENDING_AUTH (deleted after 3 hours)
    """
    from src.api.utils.models import PublishedContentDB
    from src.services.optimization.service import base_optimization_service
    from src.services.optimization.auth import token_manager

    try:
        results = {"published": [], "pending_auth": [], "failed": []}

        retention_hours = 3

        for platform_name in request.platforms:
            try:
                platform_lower = platform_name.lower()
                platform_key = PLATFORM_NAME_TO_KEY.get(platform_lower, platform_lower)

                if platform_key not in SUPPORTED_PLATFORMS:
                    results["failed"].append(
                        {"platform": platform_name, "error": "Platform not supported"}
                    )
                    continue

                platform_info = SUPPORTED_PLATFORMS[platform_key]

                has_auth = (
                    await token_manager.get_token(platform_key, user_id=current_user.id)
                    is not None
                )

                content_id = str(uuid.uuid4())
                metadata = await base_optimization_service.generate_viral_package(
                    content_id, request.niche, platform_name
                )

                if has_auth:
                    url = None
                    try:
                        if platform_key == "youtube":
                            url = await base_youtube_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "tiktok":
                            from src.services.optimization.tiktok_publisher import (
                                base_tiktok_service,
                            )

                            url = await base_tiktok_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "instagram":
                            from src.services.optimization.instagram_publisher import (
                                base_instagram_service,
                            )

                            url = await base_instagram_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "facebook":
                            from src.services.optimization.facebook_publisher import (
                                base_facebook_service,
                            )

                            url = await base_facebook_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "x":
                            from src.services.optimization.x_publisher import (
                                base_x_service,
                            )

                            url = await base_x_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "linkedin":
                            from src.services.optimization.linkedin_publisher import (
                                base_linkedin_service,
                            )

                            url = await base_linkedin_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                    except Exception as e:
                        logging.error(
                            f"Multi-platform upload failed for {platform_key}: {e}"
                        )

                    if url:
                        new_post = PublishedContentDB(
                            title=metadata.title or "Viral Post",
                            platform=platform_name,
                            status=ContentPublishStatus.PUBLISHED,
                            url=url,
                            user_id=current_user.id,
                            niche=request.niche,
                        )
                        db.add(new_post)
                        await db.commit()

                        results["published"].append(
                            {
                                "platform": platform_name,
                                "url": url,
                                "status": "published",
                            }
                        )
                    else:
                        results["failed"].append(
                            {"platform": platform_name, "error": "Upload failed"}
                        )
                else:
                    from datetime import datetime, timedelta

                    delete_at = datetime.utcnow() + timedelta(hours=retention_hours)

                    if request.inject_monetization and not platform_info.get(
                        "monetization", False
                    ):
                        results["failed"].append(
                            {
                                "platform": platform_name,
                                "error": f"{platform_info['name']} does not support monetization",
                            }
                        )
                        continue

                    new_post = PublishedContentDB(
                        title=metadata.title or "Viral Post",
                        platform=platform_name,
                        status=ContentPublishStatus.PENDING_AUTH,
                        url=None,
                        user_id=current_user.id,
                        niche=request.niche,
                        metadata={
                            "video_path": request.video_path,
                            "delete_at": delete_at.isoformat(),
                            "retention_hours": retention_hours,
                            "requires_auth": True,
                            "platform_key": platform_key,
                            "inject_monetization": request.inject_monetization,
                        },
                    )
                    db.add(new_post)
                    await db.commit()

                    results["pending_auth"].append(
                        {
                            "platform": platform_name,
                            "video_id": new_post.id,
                            "delete_at": delete_at.isoformat(),
                            "auth_url": f"/publish/auth/{platform_key}",
                        }
                    )

            except Exception as e:
                results["failed"].append({"platform": platform_name, "error": str(e)})

        return {
            "status": "completed",
            "total_platforms": len(request.platforms),
            "published_count": len(results["published"]),
            "pending_count": len(results["pending_auth"]),
            "failed_count": len(results["failed"]),
            "results": results,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")
    finally:
        pass


class OpenCLIPostRequest(BaseModel):
    platform: str
    content: str
    media_url: str | None = None


@router.post("/opencli/post")
async def opencli_post(
    request: OpenCLIPostRequest,
    current_user: UserDB = Depends(get_current_user),
):
    """Post content to a platform using the user's Chrome session (via opencli-rs)."""
    from src.api.config import settings
    from src.services.opencli.service import opencli_service

    if not settings.ENABLE_OPENCLI:
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    platform = request.platform.lower()
    result = await opencli_service.post_to_platform(
        current_user.id, platform, request.content, request.media_url
    )

    if result.get("success"):
        from src.api.utils.database import async_session_factory

        async with async_session_factory() as db:
            try:
                post = PublishedContentDB(
                    title=request.content[:100],
                    platform=platform,
                    status=ContentPublishStatus.PUBLISHED,
                    url=result.get("url", ""),
                    account_id=0,
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

    tasks = []
    for platform in platforms:
        tasks.append(
            opencli_service.post_to_platform(
                current_user.id, platform.lower(), content, media_url
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    output = []
    for platform, result in zip(platforms, results, strict=False):
        if isinstance(result, Exception):
            output.append(
                {"platform": platform, "success": False, "error": str(result)}
            )
        else:
            output.append({"platform": platform, **result})

    return {"results": output}
