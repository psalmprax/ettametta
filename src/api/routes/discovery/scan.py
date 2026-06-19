from fastapi import APIRouter, Depends
from pydantic import BaseModel
import httpx
import os
import logging
import csv
import io

from src.services.discovery.service import base_discovery_service
from src.services.discovery.models import ContentCandidate
from fastapi_cache.decorator import cache
from src.api.utils.api_responses import (
    success_response,
    paginate_list,
    handle_exception,
)

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.database import get_db
from src.services.discovery.service_extended import get_discovery_service_extended
from src.api.utils.subscription import get_subscription_tier_value
from src.shared.enums import SystemJobStatus, ScanStatus

logger = logging.getLogger(__name__)

router = APIRouter()

DISCOVERY_GO_URL = os.getenv("DISCOVERY_GO_URL", "http://discovery-go:8080")


class ScanRequest(BaseModel):
    niches: list[str] | None = None
    niche: str | None = None
    deep: bool = False
    region: str | None = "US"
    depth: int = 1


class RefreshRequest(BaseModel):
    niches: list[str] | None = None
    clear_cache: bool = False


class ExportRequest(BaseModel):
    niche: str | None = None
    format: str = "json"
    limit: int = 100


@router.get("/trends")
@cache(expire=60)
async def get_trends(
    niche: str | None = None,
    horizon: str = "30d",
    page: int = 1,
    limit: int = 20,
    min_viral_score: int = 0,
    exclude_shorts: bool = False,
    region: str | None = "US",
    current_user: UserDB = Depends(get_current_user),
):
    try:
        if niche and niche.strip():
            try:
                trends = await base_discovery_service.find_trending_content(
                    niche,
                    horizon=horizon,
                    tier=get_subscription_tier_value(current_user),
                    min_viral_score=min_viral_score,
                    exclude_shorts=exclude_shorts,
                    region=region,
                )
            except Exception as scan_err:
                logger.exception(f"Scanner error for niche '{niche}': {scan_err}", exc_info=True)
                return success_response(data={"trends": [], "page": page, "page_size": limit, "total": 0, "total_pages": 0})
        else:
            try:
                trends = await base_discovery_service.get_global_trending(
                    limit=limit * page, 
                    min_viral_score=float(min_viral_score),
                    region=region
                )
            except Exception as scan_err:
                logger.exception(f"Global trending scan error: {scan_err}", exc_info=True)
                return success_response(data={"trends": [], "page": page, "page_size": limit, "total": 0, "total_pages": 0})

        paginated = paginate_list(trends, page=page, page_size=limit)
        paginated["trends"] = paginated["items"]
        return success_response(data=paginated)
    except Exception as e:
        logger.exception(f"Discovery trends failed: {e}", exc_info=True)
        return handle_exception(e)


@router.get("/search")
async def search_discovery(
    query: str | None = None,
    platform: list[str] | None = None,
    min_views: int | None = None,
    min_viral_score: float | None = None,
    creator: str | None = None,
    tags: list[str] | None = None,
    date_from: None = None,
    date_to: None = None,
    sort_by: str = "viral_score",
    limit: int = 50,
    offset: int = 0,
    page: int = 1,
    region: str | None = "US",
    current_user: UserDB = Depends(get_current_user),
):
    import datetime as _dt
    try:
        results = await base_discovery_service.search_content(
            query=query,
            platforms=platform,
            min_views=min_views,
            min_viral_score=min_viral_score,
            creator=creator,
            tags=tags,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
            region=region,
            use_live_fallback=False,
        )
        paginated = paginate_list(results, page=page, page_size=limit)
        paginated["results"] = paginated["items"]
        return success_response(data=paginated)
    except Exception as e:
        return handle_exception(e)


@router.post("/scan")
async def trigger_scan(
    request: ScanRequest, current_user: UserDB = Depends(get_current_user)
):
    try:
        if request.deep:
            from src.services.discovery.tasks import deep_scan_task

            task = deep_scan_task.delay(
                niches=request.niches,
                tier=get_subscription_tier_value(current_user),
            )

            return success_response(
                data={
                    "status": SystemJobStatus.QUEUED,
                    "task_id": task.id,
                    "niches": request.niches,
                    "message": "Deep scan started in background. Poll /analyze/{task_id} for results.",
                }
            )
        else:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    scan_niches = request.niches or ([request.niche] if request.niche else ["AI"])
                    
                    resp = await client.post(
                        f"{DISCOVERY_GO_URL}/scan",
                        json={
                            "niches": scan_niches,
                            "region": request.region,
                            "depth": request.depth
                        },
                        timeout=60.0,
                    )
                    resp.raise_for_status()
                    return success_response(data=resp.json())
            except (
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.HTTPStatusError,
            ) as e:
                logger.warning(
                    f"[Discovery] Go engine unavailable: {e}, falling back to Python service"
                )
                all_results = []
                failed_niches = []

                scan_niches = request.niches or ([request.niche] if request.niche else ["AI"])

                for niche in scan_niches:
                    try:
                        results = await base_discovery_service.find_trending_content(
                            niche,
                            horizon="30d",
                            tier=getattr(
                                current_user.subscription,
                                "value",
                                str(current_user.subscription),
                            )
                            if current_user.subscription
                            else "free",
                            region=request.region or "US",
                        )
                        all_results.extend(results)
                    except Exception as inner_e:
                        logger.exception(
                            f"[Discovery] Fallback scan failed for {niche}: {inner_e}"
                        )
                        failed_niches.append(niche)

                if all_results:
                    return success_response(
                        data={
                            "status": ScanStatus.COMPLETED,
                            "niches": request.niches,
                            "candidates": all_results[:50],
                            "count": len(all_results),
                            "source": "fallback_python",
                            "failed_niches": failed_niches,
                        }
                    )

                if failed_niches:
                    logger.warning(
                        f"[Discovery] Primary scanners failed. Deploying Video Lead Scanner for {failed_niches}"
                    )
                    for niche in failed_niches:
                        try:
                            swarm_results = await base_discovery_service.video_lead_scanner.scan_for_video_leads(
                                niche=niche,
                                platforms=["youtube", "tiktok", "rumble"],
                                min_viral_score=0,
                                max_results=10,
                            )
                            all_results.extend(
                                [
                                    ContentCandidate(
                                        id=r.video_id,
                                        platform=r.platform,
                                        source_uri=r.url,
                                        creator_name=r.creator,
                                        title=r.title,
                                        description=r.description,
                                        thumbnail_uri=r.thumbnail_uri,
                                        view_count=r.view_count,
                                        engagement_score=r.engagement_score,
                                        viral_score=int(r.viral_score),
                                        duration_seconds=float(r.duration_seconds),
                                        category=r.content_type,
                                        niche=niche,
                                        metadata={"source": "video_lead_scanner"},
                                    )
                                    for r in swarm_results
                                ]
                            )
                        except Exception as swarm_e:
                            logger.exception(
                                f"[Discovery] Video Lead Scanner failed for {niche}: {swarm_e}"
                            )

                return success_response(
                    data={
                        "status": ScanStatus.COMPLETED,
                        "niches": request.niches,
                        "candidates": all_results[:50],
                        "count": len(all_results),
                        "source": "fallback_python",
                    }
                )
    except Exception as e:
        import traceback
        logger.exception(f"[Discovery] UNHANDLED EXCEPTION in trigger_scan: {e}")
        logger.exception(traceback.format_exc())
        return handle_exception(e)


@router.get("/niche-trends/{niche}")
@cache(expire=300)
async def get_niche_trends(
    niche: str, current_user: UserDB = Depends(get_current_user)
):
    try:
        trend = await base_discovery_service.aggregate_niche_trends(niche)
        if not trend:
            tier_value = get_subscription_tier_value(current_user)
            await base_discovery_service.find_trending_content(niche, tier=tier_value)
            trend = await base_discovery_service.aggregate_niche_trends(niche)
            if not trend:
                return success_response(
                    data={
                        "niche": niche,
                        "top_keywords": [],
                        "avg_engagement_score": 0.0,
                    }
                )
        return success_response(data=trend)
    except Exception as e:
        logger.exception(f"Niche trends failed for {niche}: {e}")
        return handle_exception(e)


@router.get("/niche-trends")
async def get_all_niche_trends(current_user: UserDB = Depends(get_current_user)):
    return success_response(data={"message": "Select a niche to see trends", "top_keywords": []})


@router.get("/summary")
async def get_discovery_summary(
    service=Depends(get_discovery_service_extended),
):
    stats = await service.get_summary_stats()
    return success_response(data=stats)


@router.post("/refresh")
async def refresh_discovery(
    request: RefreshRequest,
    current_user: UserDB = Depends(get_current_user),
):
    from src.api.utils.redis import get_sync_redis

    try:
        r = get_sync_redis()

        refreshed_niches = []

        if request.clear_cache:
            keys = r.keys("discovery:trends:*")
            if keys:
                r.delete(*keys)
                logger.info(f"[Discovery] Cleared {len(keys)} cache keys")

        niches_to_refresh = request.niches if request.niches else [None]

        for niche in niches_to_refresh:
            actual_niche = niche or "global"

            cache_key = f"discovery:trends:{actual_niche}:30d"
            r.delete(cache_key)
            refreshed_niches.append(actual_niche)

            logger.info(f"[Discovery] Triggering refresh scan for: {actual_niche}")

        return success_response(
            data={
                "status": "refresh_queued",
                "niches": refreshed_niches,
                "message": f"Cache cleared and refresh triggered for {len(refreshed_niches)} niche(s)",
            }
        )

    except Exception as e:
        logger.exception(f"Refresh failed: {e}")
        return handle_exception(e)


@router.post("/export")
async def export_discovery(
    request: ExportRequest,
    current_user: UserDB = Depends(get_current_user),
):
    try:
        candidates = []
        if request.niche:
            candidates = await base_discovery_service.find_trending_content(
                request.niche,
                horizon="30d",
                tier="free",
                min_viral_score=0,
            )

        candidates = candidates[: request.limit]

        if request.format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(
                [
                    "id",
                    "title",
                    "platform",
                    "creator",
                    "views",
                    "viral_score",
                    "engagement",
                    "url",
                ]
            )
            for c in candidates:
                writer.writerow(
                    [
                        c.id,
                        c.title,
                        c.platform,
                        c.creator_name,
                        c.view_count,
                        c.viral_score,
                        c.engagement_score,
                        c.source_uri,
                    ]
                )

            csv_content = output.getvalue()
            return success_response(
                data={
                    "format": "csv",
                    "count": len(candidates),
                    "content": csv_content,
                }
            )
        else:
            return success_response(
                data={
                    "format": "json",
                    "count": len(candidates),
                    "candidates": [
                        {
                            "id": c.id,
                            "title": c.title,
                            "platform": c.platform,
                            "creator": c.creator_name,
                            "views": c.view_count,
                            "viral_score": c.viral_score,
                            "engagement": c.engagement_score,
                            "url": c.source_uri,
                        }
                        for c in candidates
                    ],
                }
            )

    except Exception as e:
        logger.exception(f"Export failed: {e}")
        return handle_exception(e)


@router.get("/opencli/search")
async def opencli_search(
    platform: str,
    query: str,
    limit: int = 20,
    current_user: UserDB = Depends(get_current_user),
):
    from src.services.opencli.scanner import OpenCLIScanner
    from src.api.config import settings

    if not settings.ENABLE_OPENCLI:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    scanner = OpenCLIScanner(current_user.id)
    candidates = await scanner.scan_trends(query, platforms=[platform.lower()])

    return success_response(data=candidates[:limit])


@router.get("/opencli/feed/{platform}")
async def opencli_feed(
    platform: str,
    feed_type: str = "trending",
    limit: int = 20,
    current_user: UserDB = Depends(get_current_user),
):
    from src.services.opencli.scanner import OpenCLIScanner
    from src.api.config import settings

    if not settings.ENABLE_OPENCLI:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    scanner = OpenCLIScanner(current_user.id)
    candidates = await scanner.get_platform_feed(platform.lower(), feed_type, limit)

    return success_response(data=candidates)


@router.post("/opencli/scan")
async def opencli_scan(
    niche: str = "general",
    platforms: list[str] | None = None,
    current_user: UserDB = Depends(get_current_user),
):
    from src.services.opencli.scanner import OpenCLIScanner
    from src.api.config import settings

    if not settings.ENABLE_OPENCLI:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="opencli integration is disabled")

    scanner = OpenCLIScanner(current_user.id)
    p = [p.lower() for p in platforms] if platforms else None
    candidates = await scanner.scan_trends(niche, platforms=p)

    return success_response(
        data={
            "candidates": candidates,
            "count": len(candidates),
            "source": "opencli-rs",
            "platforms_scanned": p or "all_connected",
        }
    )


@router.get("/history")
async def get_scan_history(
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 20,
):
    from src.api.utils.models import ScanHistoryDB
    from sqlalchemy import select

    try:
        stmt = (
            select(ScanHistoryDB)
            .where(ScanHistoryDB.user_id == current_user.id)
            .order_by(ScanHistoryDB.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        history = result.scalars().all()

        return success_response(
            data={
                "history": [
                    {
                        "id": h.id,
                        "niche": h.niche,
                        "status": h.status,
                        "results_count": h.results_count,
                        "created_at": h.created_at.isoformat()
                        if h.created_at
                        else None,
                    }
                    for h in history
                ],
                "count": len(history),
            }
        )
    except Exception as e:
        logger.exception(f"Get history failed: {e}")
        return handle_exception(e)
