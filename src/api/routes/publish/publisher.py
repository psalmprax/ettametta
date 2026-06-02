"""
Core publishing routes — platforms, package generation, single/multi-platform
post, retry, and auto-broadcast.

Extracted from the original monolithic publish.py.
"""

import uuid
import datetime
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.database import get_db
from src.api.utils.models import PublishedContentDB, ABTestDB, AffiliateLinkDB, VideoJobDB
from src.shared.enums import SystemJobStatus
from src.api.utils.api_responses import success_response
from src.shared.enums import ContentPublishStatus
from src.api.utils.subscription import credits_required
from src.services.payment.credit_service import credit_service
from src.services.optimization.service import base_optimization_service
from src.services.optimization.youtube_publisher import base_youtube_service
from src.services.optimization.tiktok_publisher import base_tiktok_service
from src.services.optimization.auth import token_manager
from src.services.monetization.service import base_monetization_service

from .common import SUPPORTED_PLATFORMS, PLATFORM_NAME_TO_KEY, PublishRequest, MultiPlatformPublishRequest

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Platform Listing ──────────────────────────────────────────────────


@router.get("/platforms")
async def get_supported_platforms():
    """Get list of all supported platforms for publishing"""
    return success_response(
        data={"platforms": SUPPORTED_PLATFORMS, "count": len(SUPPORTED_PLATFORMS)}
    )


# ─── Package Generation ────────────────────────────────────────────────


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
        logger.exception(f"Package generation failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")


# ─── Retry Publishing ──────────────────────────────────────────────────


@router.post("/retry/{content_id}")
async def retry_publish(
    content_id: str,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Retry publishing a video that was pending authentication.
    Called after user has authenticated the platform.
    """
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
            url = await base_tiktok_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "instagram":
            from src.services.optimization.instagram_publisher import base_instagram_service
            url = await base_instagram_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "facebook":
            from src.services.optimization.facebook_publisher import base_facebook_publisher_service
            url = await base_facebook_publisher_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "x":
            from src.services.optimization.x_publisher import base_x_publisher_service
            url = await base_x_publisher_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )
        elif platform_key == "linkedin":
            from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service
            url = await base_linkedin_publisher_service.upload_video(
                video_path, metadata, user_id=current_user.id
            )

        content.status = (
            ContentPublishStatus.PUBLISHED if url else ContentPublishStatus.FAILED
        )
        content.source_uri = url
        content.published_at = datetime.datetime.now(datetime.timezone.utc) if url else None

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
    except Exception as e:
        logger.exception(f"Retry publishing failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")


# ─── Single Platform Publish ───────────────────────────────────────────


@router.post("/post")
async def publish_video(
    request: PublishRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    credits_cost: int = Depends(credits_required("social_publish")),
):
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

        # Affiliate Injection
        if request.inject_monetization:
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
                delete_at = datetime.datetime.now(datetime.timezone.utc) + timedelta(hours=retention_hours)

                new_post = PublishedContentDB(
                    title=metadata.title or "Viral Post",
                    platform=request.platform,
                    status=ContentPublishStatus.PENDING_AUTH,
                    source_uri=request.video_path,
                    account_id=request.account_id,
                    user_id=current_user.id,
                    niche=request.niche,
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

        # Authenticated — proceed with upload
        if platform_key == "youtube":
            url = await base_youtube_service.upload_video(
                request.video_path, metadata, user_id=current_user.id, account_id=request.account_id
            )
        elif platform_key == "tiktok":
            url = await base_tiktok_service.upload_video(
                request.video_path, metadata, user_id=current_user.id, account_id=request.account_id
            )
        elif platform_key == "instagram":
            from src.services.optimization.instagram_publisher import base_instagram_service
            url = await base_instagram_service.upload_video(
                request.video_path, metadata, user_id=current_user.id, account_id=request.account_id
            )
        elif platform_key == "facebook":
            from src.services.optimization.facebook_publisher import base_facebook_publisher_service
            url = await base_facebook_publisher_service.upload_video(
                request.video_path, metadata, user_id=current_user.id, account_id=request.account_id
            )
        elif platform_key == "x":
            from src.services.optimization.x_publisher import base_x_publisher_service
            url = await base_x_publisher_service.upload_video(
                request.video_path, metadata, user_id=current_user.id, account_id=request.account_id
            )
        elif platform_key == "linkedin":
            from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service
            url = await base_linkedin_publisher_service.upload_video(
                request.video_path, metadata, user_id=current_user.id, account_id=request.account_id
            )
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Publisher for platform '{platform_key}' is not yet implemented. "
                "Supported platforms: youtube, tiktok, instagram, facebook, x, linkedin",
            )

        # Record history
        new_post = PublishedContentDB(
            title=metadata.title or "Viral Post",
            platform=request.platform,
            status=ContentPublishStatus.PUBLISHED if url else ContentPublishStatus.FAILED,
            source_uri=url or request.video_path,
            account_id=request.account_id,
            user_id=current_user.id,
            niche=request.niche,
        )
        db.add(new_post)
        await db.commit()
        await db.refresh(new_post)

        # Initialize A/B Test if variant B title provided
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
                status="active",
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
        logger.exception(f"Publishing failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")


# ─── Multi-Platform Publish ────────────────────────────────────────────


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
                            url = await base_tiktok_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "instagram":
                            from src.services.optimization.instagram_publisher import base_instagram_service
                            url = await base_instagram_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "facebook":
                            from src.services.optimization.facebook_publisher import base_facebook_publisher_service
                            url = await base_facebook_publisher_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "x":
                            from src.services.optimization.x_publisher import base_x_publisher_service
                            url = await base_x_publisher_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                        elif platform_key == "linkedin":
                            from src.services.optimization.linkedin_publisher import base_linkedin_publisher_service
                            url = await base_linkedin_publisher_service.upload_video(
                                request.video_path, metadata, user_id=current_user.id
                            )
                    except Exception as e:
                        logging.exception(f"Multi-platform upload failed for {platform_key}: {e}")

                    if url:
                        new_post = PublishedContentDB(
                            title=metadata.title or "Viral Post",
                            platform=platform_name,
                            status=ContentPublishStatus.PUBLISHED,
                            source_uri=url,
                            user_id=current_user.id,
                            niche=request.niche,
                        )
                        db.add(new_post)
                        await db.commit()

                        results["published"].append(
                            {"platform": platform_name, "url": url, "status": "published"}
                        )
                    else:
                        results["failed"].append(
                            {"platform": platform_name, "error": "Upload failed"}
                        )
                else:
                    from datetime import datetime, timedelta
                    delete_at = datetime.datetime.now(datetime.timezone.utc) + timedelta(hours=retention_hours)

                    if request.inject_monetization and not platform_info.get("monetization", False):
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
                        source_uri=request.video_path,
                        user_id=current_user.id,
                        niche=request.niche,
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
        logger.exception(f"Multi-platform publishing failed: {e}")
        raise HTTPException(status_code=503, detail="Publishing service unavailable")


# ─── Pipeline Bridge: Job → Publish ────────────────────────────────────


class PublishFromJobRequest(BaseModel):
    platform: str = "YouTube Shorts"
    niche: str = "General"
    account_id: str | None = None
    inject_monetization: bool = False
    variant_b_title: str | None = None
    variant_b_description: str | None = None


@router.post("/from-job/{job_id}")
async def publish_from_job(
    job_id: str,
    request: PublishFromJobRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    credits_cost: int = Depends(credits_required("social_publish")),
):
    """
    Bridge a completed video generation job directly into the publishing pipeline.

    Closes the loop: Discovery → Analysis → Video Creation → Publish.
    Looks up a completed VideoJobDB or NexusJobDB by ID, extracts the output
    video path, and publishes it to the specified platform.
    """
    from src.api.utils.models import NexusJobDB

    try:
        # 1. Look up the job
        stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

        if not job:
            stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
            result = await db.execute(stmt)
            job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # 2. Verify user ownership
        from src.api.utils.user_models import UserRole
        if job.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized to publish this job")

        # 3. Check job is completed
        status_val = job.status.value if hasattr(job.status, 'value') else job.status
        if status_val != SystemJobStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Job is not completed (status: {status_val}). Only completed jobs can be published.",
            )

        # 4. Get the video output path
        output_path = getattr(job, "output_path", None)
        if not output_path:
            raise HTTPException(
                status_code=400,
                detail="Job has no output path. The video file may have been processed externally.",
            )

        # 5. Construct the publish request and delegate
        publish_req = PublishRequest(
            video_path=output_path,
            niche=request.niche,
            platform=request.platform,
            account_id=request.account_id,
            inject_monetization=request.inject_monetization,
            variant_b_title=request.variant_b_title,
            variant_b_description=request.variant_b_description,
        )

        # Reuse existing publish logic via the inner helper
        return await publish_video(
            request=publish_req,
            current_user=current_user,
            db=db,
            credits_cost=credits_cost,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Publish from job failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to publish from job")


# ─── Auto-Broadcast ────────────────────────────────────────────────────


@router.post("/auto-broadcast")
async def auto_broadcast(
    current_user: UserDB = Depends(get_current_user),
):
    """
    Triggers autonomous broadcast pattern.
    Scans for pending/scheduled content and dispatches to all available platforms.
    """
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
        logger.exception(f"Auto-broadcast failed: {e}")
        raise HTTPException(status_code=503, detail="Broadcast pattern injection failed")
