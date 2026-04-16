from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.utils.database import get_db
from api.utils.models import AffiliateLinkDB, RevenueLogDB
from api.routes.auth import get_current_user
from services.monetization.service import base_monetization_engine
from services.monetization.promo_generator import base_promo_generator
from api.utils.subscription import credits_required
from services.payment.credit_service import credit_service
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/monetization", tags=["Monetization"])


class LinkRecommendationRequest(BaseModel):
    niche: str
    script_text: str


class AutoMerchRequest(BaseModel):
    trend_topic: str


@router.post("/recommend-links")
async def recommend_links(
    request: LinkRecommendationRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Recommends products/links based on script content.
    """
    recommendations = await base_monetization_engine.recommend_products(
        request.niche, request.script_text
    )

    # Check if we have actual links in DB for these categories
    stmt = select(AffiliateLinkDB).where(AffiliateLinkDB.niche == request.niche)
    result = await db.execute(stmt)
    db_links = result.scalars().all()

    return {"suggestions": recommendations, "available_links": db_links}


@router.post("/auto-merch")
async def auto_merch(
    request: AutoMerchRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    credits_cost: int = Depends(credits_required("auto_merch")),
):
    """
    Triggers the Reverse Monetization flow: Trend -> Design -> Mockup -> Store.
    """
    from services.monetization.auto_merch import (
        base_auto_merch_service as auto_merch_service,
    )

    # Consume credits
    await credit_service.consume_credits(
        user_id=current_user.id,
        amount=credits_cost,
        action="auto_merch",
        description=f"Auto-merch generation for {request.trend_topic}",
        db=db,
    )

    product_data = await auto_merch_service.generate_and_publish_merch(
        request.trend_topic
    )

    if not product_data:
        raise HTTPException(
            status_code=500, detail="Failed to generate or publish merchandise."
        )

    return {
        "status": "success",
        "message": f"Successfully created merch for '{request.trend_topic}'",
        "product": product_data,
    }


@router.get("/report")
async def get_monetization_report(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Aggregates revenue tracking data for the dashboard.
    """
    stmt = select(RevenueLogDB).where(RevenueLogDB.user_id == current_user.id)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    total_rev = sum(log.amount for log in logs)
    total_views = sum(log.views for log in logs)
    epm = base_monetization_engine.calculate_epm(total_rev, total_views)

    return {"total_revenue": total_rev, "epm": epm, "logs": logs}


@router.get("/empire/metrics")
async def get_empire_metrics(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get empire metrics - returns basic stats for now."""
    import datetime
    from sqlalchemy import select, func, desc
    from api.utils.models import PublishedContentDB, SocialAccount, VideoJobDB

    now = datetime.datetime.utcnow()
    last_week = now - datetime.timedelta(days=7)

    # Total connected accounts
    account_result = await db.execute(
        select(func.count(SocialAccount.id)).where(
            SocialAccount.user_id == current_user.id
        )
    )
    total_accounts = account_result.scalar() or 0

    # Published content this week
    publish_result = await db.execute(
        select(func.count(PublishedContentDB.id)).where(
            PublishedContentDB.user_id == current_user.id,
            PublishedContentDB.published_at >= last_week,
        )
    )
    recent_published = publish_result.scalar() or 0

    # Total views this week
    views_result = await db.execute(
        select(func.sum(PublishedContentDB.view_count)).where(
            PublishedContentDB.user_id == current_user.id,
            PublishedContentDB.published_at >= last_week,
        )
    )
    total_views = views_result.scalar() or 0

    return {
        "total_accounts": total_accounts,
        "recent_published": recent_published,
        "total_views": int(total_views),
        "growth_rate": 0.0,
        "week_over_week": 0,
    }


@router.get("/empire/activity")
async def get_empire_activity(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Returns the recent activity logs for the empire timeline.
    """
    import datetime
    from sqlalchemy import select, desc
    from api.utils.models import PublishedContentDB

    # Get recent published content
    result = await db.execute(
        select(PublishedContentDB)
        .where(PublishedContentDB.user_id == current_user.id)
        .order_by(desc(PublishedContentDB.published_at))
        .limit(10)
    )
    recent = result.scalars().all()

    return {
        "activities": [
            {
                "type": "published",
                "title": p.title,
                "platform": p.platform,
                "published_at": p.published_at.isoformat() if p.published_at else None,
            }
            for p in recent
        ]
    }


class CloneRequest(BaseModel):
    source_niche: str
    target_niche: str


@router.get("/empire/blueprints")
async def get_winning_blueprints(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Get winning content blueprints from past publishes."""
    from sqlalchemy import select, desc, func
    from api.utils.models import PublishedContentDB

    # Get top performing content
    result = await db.execute(
        select(PublishedContentDB)
        .where(
            PublishedContentDB.user_id == current_user.id,
            PublishedContentDB.view_count > 0,
        )
        .order_by(desc(PublishedContentDB.view_count))
        .limit(20)
    )
    top_content = result.scalars().all()

    # Group by niche
    blueprints = {}
    for p in top_content:
        niche = p.niche or "general"
        if niche not in blueprints:
            blueprints[niche] = {"niche": niche, "count": 0, "total_views": 0}
        blueprints[niche]["count"] += 1
        blueprints[niche]["total_views"] += p.view_count or 0

    return {"blueprints": list(blueprints.values())}


@router.get("/empire/network")
async def get_network_graph(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Returns the visualization graph (nodes/links) for the empire mesh.
    """
    from sqlalchemy import select
    from api.utils.models import PublishedContentDB, SocialAccount

    # Get connected accounts as nodes
    accounts_result = await db.execute(
        select(SocialAccount).where(SocialAccount.user_id == current_user.id)
    )
    accounts = accounts_result.scalars().all()

    # Get published content for connections
    content_result = await db.execute(
        select(PublishedContentDB)
        .where(PublishedContentDB.user_id == current_user.id)
        .limit(50)
    )
    content = content_result.scalars().all()

    nodes = []
    links = []

    # Create nodes for accounts
    for acc in accounts:
        nodes.append(
            {
                "id": f"account_{acc.id}",
                "type": "account",
                "platform": acc.platform,
                "name": acc.username,
            }
        )

    # Create nodes for content and links
    for c in content:
        nodes.append(
            {
                "id": f"content_{c.id}",
                "type": "content",
                "title": c.title[:30],
            }
        )
        links.append(
            {
                "source": f"account_{c.account_id}",
                "target": f"content_{c.id}",
            }
        )

    return {"nodes": nodes, "links": links}

    return await base_empire_service.get_network_graph(db, current_user.id)


@router.post("/commerce/sync")
async def sync_commerce_products(
    niche: str = "General",
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Triggers a test sync with the configured Shopify store.
    """
    from services.monetization.commerce_service import base_commerce_service

    # Test with the provided niche to verify connection
    products = await base_commerce_service.get_relevant_products(niche)
    if not products:
        return {
            "status": "warning",
            "message": "No products found. Check credentials or niche tags.",
        }
    return {
        "status": "success",
        "sample_count": len(products),
        "source": products[0].get("source"),
    }


@router.post("/empire/clone")
async def clone_strategy(
    request: CloneRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from services.monetization.empire_service import base_empire_service

    success = await base_empire_service.clone_strategy(
        db, current_user.id, request.source_niche, request.target_niche
    )
    if not success:
        raise HTTPException(status_code=500, detail="Cloning failed")
    return {
        "status": "success",
        "message": f"Strategy cloned to {request.target_niche}",
    }


class LinkCreate(BaseModel):
    product_name: str
    niche: str
    link: str
    cta_text: Optional[str] = "Check link in bio"


@router.get("/links")
async def list_affiliate_links(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    Lists all affiliate links for the current user.
    """
    stmt = select(AffiliateLinkDB).where(AffiliateLinkDB.user_id == current_user.id)
    result = await db.execute(stmt)
    links = result.scalars().all()
    return {"links": links}


@router.post("/links")
async def create_affiliate_link(
    link: LinkCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Registers a new affiliate link.
    """
    db_link = AffiliateLinkDB(**link.model_dump())
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return db_link


class PromoRequest(BaseModel):
    product_name: str
    niche: str
    duration: int = 30


@router.post("/promo/generate")
async def generate_promo(request: PromoRequest, current_user=Depends(get_current_user)):
    """
    Generates a conversion-optimized promo script.
    """
    script = await base_promo_generator.generate_promo_script(
        request.product_name, request.niche, request.duration
    )
    return script
