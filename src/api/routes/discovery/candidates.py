from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import hashlib
import logging
import datetime

from src.api.utils.api_responses import (
    success_response,
    handle_exception,
)

from src.api.utils.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.database import get_db
from src.services.discovery.service_extended import get_discovery_service_extended
from src.api.utils.models import ContentCandidateDB
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()


class NicheAlertRequest(BaseModel):
    niche: str
    threshold: int = 7
    enabled: bool = True


class InteractionRequest(BaseModel):
    candidate_id: str | None = None
    niche: str | None = None
    platform: str | None = None
    action: str = "handshake"
    content_url: str | None = None


class BulkFavoriteRequest(BaseModel):
    candidate_ids: list[str]
    action: str = "add"


@router.get("/niches")
async def list_monitored_niches(
    current_user: UserDB = Depends(get_current_user),
    service=Depends(get_discovery_service_extended),
):
    niches = await service.list_monitored_niches(current_user.id)
    return success_response(data=niches)


@router.post("/niche/watch")
async def watch_niche(
    request: NicheAlertRequest,
    current_user: UserDB = Depends(get_current_user),
    service=Depends(get_discovery_service_extended),
):
    result = await service.watch_niche(
        user_id=current_user.id,
        niche=request.niche,
        threshold=request.threshold,
        enabled=request.enabled,
    )
    return success_response(data=result)


@router.post("/interact")
async def record_interaction(
    request: InteractionRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    from src.api.utils.models import DiscoveryInteractionDB

    candidate_id = request.candidate_id
    if not candidate_id and request.content_url:
        stmt = select(ContentCandidateDB).filter(ContentCandidateDB.source_uri == request.content_url)
        result = await db.execute(stmt)
        candidate = result.scalar_one_or_none()
        if candidate:
            candidate_id = candidate.id
        else:
            candidate_id = f"ext_{hashlib.md5(request.content_url.encode()).hexdigest()}"

    try:
        new_interaction = DiscoveryInteractionDB(
            candidate_id=candidate_id or "unknown",
            user_id=current_user.id,
            action=request.action,
            status=1,
            details={
                "niche": request.niche,
                "platform": request.platform,
                "content_url": request.content_url,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        )
        db.add(new_interaction)
        await db.commit()
        await db.refresh(new_interaction)

        return success_response(
            data={
                "status": "Handshake Established",
                "candidate_id": candidate_id,
                "interaction_id": new_interaction.id,
                "timestamp": new_interaction.created_at.isoformat(),
                "message": "Protocol established with target node.",
            }
        )
    except Exception as e:
        logger.exception(f"Interaction record failed: {e}")
        return handle_exception(e)


@router.post("/favorites/bulk")
async def bulk_favorites(
    request: BulkFavoriteRequest,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    from src.api.utils.models import DiscoveryFavoriteDB

    try:
        added = 0
        removed = 0

        for candidate_id in request.candidate_ids:
            existing = await db.get(DiscoveryFavoriteDB, candidate_id)

            if request.action == "add" and not existing:
                fav = DiscoveryFavoriteDB(
                    id=candidate_id,
                    user_id=current_user.id,
                )
                db.add(fav)
                added += 1
            elif request.action == "remove" and existing:
                await db.delete(existing)
                removed += 1

        await db.commit()

        return success_response(
            data={
                "status": "bulk_complete",
                "action": request.action,
                "added": added,
                "removed": removed,
            }
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"Bulk favorite failed: {e}")
        return handle_exception(e)


@router.get("/favorites")
async def get_favorites(
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
    limit: int = 50,
):
    from src.api.utils.models import DiscoveryFavoriteDB

    try:
        stmt = (
            select(ContentCandidateDB)
            .join(DiscoveryFavoriteDB, DiscoveryFavoriteDB.id == ContentCandidateDB.id)
            .where(DiscoveryFavoriteDB.user_id == current_user.id)
            .order_by(ContentCandidateDB.viral_score.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        favorites = result.scalars().all()

        return success_response(
            data={
                "favorites": [
                    {
                        "id": f.id,
                        "title": f.title,
                        "platform": f.platform,
                        "viral_score": f.viral_score,
                        "source_uri": f.source_uri,
                    }
                    for f in favorites
                ],
                "count": len(favorites),
            }
        )
    except Exception as e:
        logger.exception(f"Get favorites failed: {e}")
        return handle_exception(e)


@router.get("/alerts")
async def get_niche_alerts(
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    from src.api.utils.models import DiscoveryAlertDB

    try:
        stmt = select(DiscoveryAlertDB).filter(
            DiscoveryAlertDB.user_id == current_user.id,
            DiscoveryAlertDB.is_active,
        )
        result = await db.execute(stmt)
        alerts = result.scalars().all()

        return success_response(
            data={
                "alerts": [
                    {
                        "id": a.id,
                        "niche": a.niche,
                        "threshold": a.threshold,
                        "enabled": a.is_active,
                        "message": f"High viral velocity detected in {a.niche}",
                        "severity": "high" if (a.threshold or 7) > 8 else "medium"
                    }
                    for a in alerts
                ]
            }
        )
    except Exception as e:
        logger.exception(f"Get alerts failed: {e}")
        return handle_exception(e)


@router.post("/alerts")
async def create_niche_alert(
    request: NicheAlertRequest,
    current_user: UserDB = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from src.api.utils.models import DiscoveryAlertDB, MonitoredNiche

    try:
        stmt_monitor = select(MonitoredNiche).filter(
            and_(
                MonitoredNiche.user_id == current_user.id,
                MonitoredNiche.niche == request.niche,
            )
        )
        monitor_result = await db.execute(stmt_monitor)
        monitor = monitor_result.scalar_one_or_none()

        if not monitor:
            monitor = MonitoredNiche(user_id=current_user.id, niche=request.niche, is_active=True)
            db.add(monitor)
        else:
            monitor.is_active = True

        stmt = select(DiscoveryAlertDB).filter(
            and_(
                DiscoveryAlertDB.user_id == current_user.id,
                DiscoveryAlertDB.niche == request.niche,
            )
        )
        result = await db.execute(stmt)
        alert = result.scalar_one_or_none()

        if alert:
            alert.threshold = request.threshold
            alert.is_active = request.enabled
        else:
            alert = DiscoveryAlertDB(
                user_id=current_user.id,
                niche=request.niche,
                threshold=request.threshold,
                is_active=request.enabled,
            )
            db.add(alert)

        await db.commit()
        return success_response(
            data={
                "status": "alert_established",
                "alert_id": alert.id,
                "niche": request.niche,
                "threshold": request.threshold,
            }
        )
    except Exception as e:
        await db.rollback()
        logger.exception(f"Create alert failed: {e}")
        return handle_exception(e)


@router.delete("/alerts/{alert_id}")
async def delete_niche_alert(
    alert_id: int,
    current_user: UserDB = Depends(get_current_user),
    db=Depends(get_db),
):
    from src.api.utils.models import DiscoveryAlertDB

    try:
        alert = await db.get(DiscoveryAlertDB, alert_id)
        if not alert or alert.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Alert not found")

        await db.delete(alert)
        await db.commit()

        return success_response(data={"status": "alert_deleted", "alert_id": alert_id})
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.exception(f"Delete alert failed: {e}")
        return handle_exception(e)
