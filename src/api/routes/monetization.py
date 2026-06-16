import hashlib
import hmac
import logging
import os
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from src.api.utils.database import get_db
from src.api.utils.models import AffiliateLinkDB, RevenueLogDB
from src.api.utils.auth import get_current_user
from src.api.utils.api_responses import success_response
from src.services.monetization.service import base_monetization_service
from src.services.monetization.promo_generator import base_promo_service
from src.api.utils.subscription import credits_required
from src.services.payment.credit_service import credit_service
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter(prefix="/monetization", tags=["Monetization"])

logger = logging.getLogger(__name__)

# ── Webhook security — per-network signature schemes ───────────────────────────────────
# Affiliate networks each have their own signature scheme. The original
# implementation used a single shared HMAC-SHA256 over <timestamp>.<body>
# with AFFILIATE_WEBHOOK_SECRET for ALL of them, which is NOT what any of
# these networks actually send. The current implementation verifies each
# network's real scheme:
#
#   Amazon (Associates): NO real postback/webhook system exists — conversion
#                        tracking is server-side via the Associates tag. We
#                        expose /webhook/amazon as a 501 stub. For
#                        programmatic product lookup use the PA-API (which
#                        uses AWS SigV4 — not implemented here).
#
#   Impact (Radius):     X-Signature / X-Impact-Signature header carries
#                        HMAC-SHA256(raw_body, IMPACT_WEBHOOK_SECRET).
#
#   ShareASale:          X-Ssc-Signature header carries
#                        HMAC-SHA256(trans_id + "|" + SHAREASALE_WEBHOOK_SECRET).
#                        The trans_id comes from the postback body.
#
# For backward compatibility, the original <timestamp>.<body> HMAC scheme
# is preserved at /webhook/internal-legacy for in-cluster test hooks. It
# is NOT a drop-in replacement for real network integrations.
#
# Migration: the AFFILIATE_WEBHOOK_SECRET env var is no longer consumed
# by the per-network endpoints. It is read ONLY by /webhook/internal-legacy.
# Configure the per-network secrets below.
# ─────────────────────────────────────────────────────────────────────────────

LEGACY_WEBHOOK_SECRET = os.getenv("AFFILIATE_WEBHOOK_SECRET", "")
IMPACT_WEBHOOK_SECRET = os.getenv("IMPACT_WEBHOOK_SECRET", "")
SHAREASALE_WEBHOOK_SECRET = os.getenv("SHAREASALE_WEBHOOK_SECRET", "")
# Amazon Associates has no real postback; tracked for forward-compat
AMAZON_WEBHOOK_SECRET = os.getenv("AMAZON_WEBHOOK_SECRET", "")

LEGACY_REPLAY_WINDOW_SECONDS = 300  # 5 minutes


def _emit_migration_banner() -> None:
    """Log a startup-time banner so operators see the migration status in
    container logs at boot — even before any webhook has fired."""
    warnings: list[str] = []
    if LEGACY_WEBHOOK_SECRET:
        warnings.append(
            "AFFILIATE_WEBHOOK_SECRET is set (legacy <timestamp>.<body> HMAC). "
            "Consumed ONLY by /webhook/internal-legacy; does NOT verify real "
            "Amazon/Impact/ShareASale postbacks."
        )
    if not IMPACT_WEBHOOK_SECRET:
        warnings.append(
            "IMPACT_WEBHOOK_SECRET is unset — /webhook/impact will return 503."
        )
    if not SHAREASALE_WEBHOOK_SECRET:
        warnings.append(
            "SHAREASALE_WEBHOOK_SECRET is unset — /webhook/sharesale will "
            "return 503."
        )
    if AMAZON_WEBHOOK_SECRET:
        warnings.append(
            "AMAZON_WEBHOOK_SECRET is set but Amazon Associates has no real "
            "postback/webhook; use PA-API (AWS SigV4) for product lookups. "
            "/webhook/amazon is a 501 stub."
        )
    if warnings:
        logger.warning("─" * 72)
        logger.warning("AFFILIATE WEBHOOK MIGRATION NOTICE")
        for w in warnings:
            logger.warning("  • " + w)
        logger.warning("─" * 72)


_emit_migration_banner()


# ── Per-network verifiers ──────────────────────────────────────────────────────────


def _verify_impact_signature(raw_body: bytes, signature_header: str | None) -> None:
    """Impact Radius: HMAC-SHA256(raw_body, secret) → hex digest in
    ``X-Signature`` header (some accounts use ``X-Impact-Signature`` — we
    accept either)."""
    if not IMPACT_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="IMPACT_WEBHOOK_SECRET not configured; refusing postback.",
        )
    sig = signature_header or ""
    if not sig:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Signature / X-Impact-Signature header.",
        )
    expected = hmac.new(
        IMPACT_WEBHOOK_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=401, detail="Invalid Impact signature.")


def _verify_shareasale_signature(
    raw_body: bytes,
    signature_header: str | None,
    trans_id: str,
) -> None:
    """ShareASale: HMAC-SHA256(trans_id + "|" + secret) → hex digest in the
    ``X-Ssc-Signature`` header. The trans_id is taken from the postback body
    (field ``trans_id`` or ``transaction_id``). The exact signing tuple
    should be re-confirmed with ShareASale support for production cutover."""
    if not SHAREASALE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="SHAREASALE_WEBHOOK_SECRET not configured; refusing postback.",
        )
    if not trans_id:
        raise HTTPException(
            status_code=401,
            detail="Missing trans_id for ShareASale signature verification.",
        )
    sig = signature_header or ""
    if not sig:
        raise HTTPException(
            status_code=401, detail="Missing X-Ssc-Signature header."
        )
    message = f"{trans_id}|{SHAREASALE_WEBHOOK_SECRET}".encode("utf-8")
    expected = hmac.new(message, b"", hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(
            status_code=401, detail="Invalid ShareASale signature."
        )


def _verify_legacy_signature(
    raw_body: bytes,
    signature_header: str | None,
    timestamp_header: str | None,
    secret: str = LEGACY_WEBHOOK_SECRET,
) -> None:
    """Legacy HMAC-SHA256 over ``<timestamp>.<raw_body>`` with
    ``AFFILIATE_WEBHOOK_SECRET``. Replay window: 5 minutes. Consumed ONLY by
    ``/webhook/internal-legacy`` for in-cluster test hooks — NOT a real
    network signature scheme."""
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="AFFILIATE_WEBHOOK_SECRET not configured; refusing postback.",
        )
    if not signature_header or not timestamp_header:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Webhook-Signature or X-Webhook-Timestamp header.",
        )
    try:
        ts = int(timestamp_header)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid timestamp header.")
    if abs(int(time.time()) - ts) > LEGACY_REPLAY_WINDOW_SECONDS:
        raise HTTPException(
            status_code=401, detail="Webhook timestamp outside replay window."
        )
    signed_payload = f"{ts}.".encode("utf-8") + raw_body
    expected = hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid webhook signature.")


async def _idempotent_insert_revenue_log(
    db,
    *,
    platform: str,
    amount: float,
    transaction_id: str,
    source_niche: str = "affiliate",
    view_count: int = 1,
    user_id: str | None = None,
    extra_metadata: dict | None = None,
) -> bool:
    """
    Atomically insert a RevenueLogDB row keyed by ``(platform, transaction_id)``.
    Returns ``True`` if a new row was inserted, ``False`` if a row with the
    same key already existed (i.e. duplicate webhook).

    The underlying mechanism is ``INSERT ... ON CONFLICT DO NOTHING`` against
    the ``uix_revenue_platform_txid`` unique constraint (see RevenueLogDB in
    ``src/api/utils/models.py``). Two concurrent webhook retries for the same
    transaction can no longer both insert; the second insert is a no-op.

    We still mirror ``transaction_id`` into ``metadata_json`` for backward
    compat with any analytics/aggregation queries that look there. New
    code should read the top-level column.

    Requires PostgreSQL — the ``dialect.postgresql.insert`` import is the
    Postgres-specific ON CONFLICT dialect. Project is Postgres-only in
    production; for local SQLite dev the table simply won't enforce the
    unique constraint, which is acceptable for unit tests.
    """
    if not transaction_id:
        # Defensive: a missing transaction_id would defeat dedup. Reject
        # before insert so callers don't accidentally create unbounded rows.
        raise ValueError(
            "_idempotent_insert_revenue_log requires a non-empty transaction_id"
        )

    metadata_json: dict = {"transaction_id": transaction_id}
    if extra_metadata:
        # Caller-supplied metadata wins on key collision so the legacy
        # `transaction_id` mirror cannot be accidentally overridden.
        merged = {**extra_metadata, "transaction_id": transaction_id}
        metadata_json = merged

    stmt = (
        pg_insert(RevenueLogDB)
        .values(
            id=str(uuid.uuid4()),
            platform=platform,
            niche=source_niche,
            amount=amount,
            view_count=view_count,
            transaction_id=transaction_id,
            metadata_json=metadata_json,
            user_id=user_id,
            date=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        .on_conflict_do_nothing(index_elements=["platform", "transaction_id"])
    )
    result = await db.execute(stmt)
    # rowcount is 1 when the row was actually inserted, 0 when ON CONFLICT
    # triggered (i.e. a duplicate). AsyncSession returns a CursorResult that
    # exposes rowcount directly.
    return bool(result.rowcount and result.rowcount > 0)


class LinkRecommendationRequest(BaseModel):
    niche: str
    script_text: str


class AutoMerchRequest(BaseModel):
    niche: str


@router.post("/recommend-links")
async def recommend_links(
    request: LinkRecommendationRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Recommends products/links based on script content.
    """
    recommendations = await base_monetization_service.recommend_products(
        request.niche, request.script_text
    )

    # Check if we have actual links in DB for these categories
    stmt = select(AffiliateLinkDB).where(AffiliateLinkDB.niche == request.niche)
    result = await db.execute(stmt)
    db_links = result.scalars().all()

    # Merge suggestions with actual DB links for the frontend
    return success_response(
        data={"links": db_links, "suggestions": recommendations}
    )


@router.post("/auto-merch")
async def auto_merch(
    request: AutoMerchRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    credits_cost: int = Depends(credits_required("auto_merch")),
):
    """
    Triggers the Reverse Monetization flow: Trend -> Design -> Mockup -> Store.
    """
    from src.services.monetization.auto_merch import (
        base_auto_merch_service as auto_merch_service,
    )

    # Consume credits
    await credit_service.consume_credits(
        user_id=current_user.id,
        amount=credits_cost,
        action="auto_merch",
        description=f"Auto-merch generation for {request.niche}",
        db=db,
    )

    product_data = await auto_merch_service.generate_and_publish_merch(request.niche)

    if not product_data:
        raise HTTPException(
            status_code=500, detail="Failed to generate or publish merchandise."
        )

    return success_response(
        data={
            "status": "success",
            "message": f"Successfully created merch for '{request.niche}'",
            "product": product_data,
        }
    )


@router.get("/report")
async def get_monetization_report(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Aggregates revenue tracking data for the dashboard.
    """
    stmt = select(RevenueLogDB).where(RevenueLogDB.user_id == current_user.id)
    result = await db.execute(stmt)
    logs = result.scalars().all()

    total_rev = sum(log.amount for log in logs)
    total_views = sum(log.view_count for log in logs)
    epm = base_monetization_service.calculate_epm(total_rev, total_views)

    # Group by platform
    by_platform = {}
    for log in logs:
        by_platform[log.platform] = by_platform.get(log.platform, 0) + log.amount

    return success_response(
        data={
            "total_revenue": total_rev,
            "epm": epm,
            "by_platform": by_platform,
            "logs": logs,
        }
    )


@router.get("/empire/metrics")
async def get_empire_metrics(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """Get empire metrics - returns basic stats for now."""
    import datetime
    from sqlalchemy import select, func
    from src.api.utils.models import PublishedContentDB, SocialAccount

    now = datetime.datetime.now(timezone.utc)
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

    return success_response(
        data={
            "total_accounts": total_accounts,
            "recent_published": recent_published,
            "total_views": int(total_views),
            "growth_rate": 0.0,
            "week_over_week": 0,
        }
    )


@router.get("/empire/activity")
async def get_empire_activity(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Returns the recent activity logs for the empire timeline.
    """
    from sqlalchemy import select, desc
    from src.api.utils.models import PublishedContentDB

    # Get recent published content
    result = await db.execute(
        select(PublishedContentDB)
        .where(PublishedContentDB.user_id == current_user.id)
        .order_by(desc(PublishedContentDB.published_at))
        .limit(10)
    )
    recent = result.scalars().all()

    return success_response(
        data={
            "activities": [
                {
                    "type": "published",
                    "title": p.title,
                    "platform": p.platform,
                    "published_at": p.published_at.isoformat()
                    if p.published_at
                    else None,
                }
                for p in recent
            ]
        }
    )


class CloneRequest(BaseModel):
    source_niche: str
    target_niche: str
    auto_publish: bool = False


@router.get("/empire/blueprints")
async def get_winning_blueprints(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """Get winning content blueprints from past publishes."""
    from sqlalchemy import select, desc
    from src.api.utils.models import PublishedContentDB

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

    return success_response(data={"blueprints": list(blueprints.values())})


@router.get("/empire/network")
async def get_network_graph(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Returns the visualization graph (nodes/links) for the empire mesh.
    """
    from sqlalchemy import select
    from src.api.utils.models import PublishedContentDB, SocialAccount

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

    return success_response(data={"nodes": nodes, "links": links})


@router.post("/commerce/sync")
async def sync_commerce_products(
    niche: str = "General",
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Triggers a test sync with the configured Shopify store.
    """
    from src.services.monetization.commerce_service import base_commerce_service

    # Test with the provided niche to verify connection
    products = await base_commerce_service.get_relevant_products(niche)
    if not products:
        return success_response(
            data={
                "status": "warning",
                "message": "No products found. Check credentials or niche tags.",
            }
        )
    return success_response(
        data={
            "status": "success",
            "sample_count": len(products),
            "source": products[0].get("source"),
        }
    )


@router.post("/empire/clone")
async def clone_strategy(
    request: CloneRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    from src.services.monetization.empire_service import base_empire_service
    from src.services.nexus_engine.auto_creator import base_creator_service

    # 1. Clone settings and affiliate links
    success = await base_empire_service.clone_strategy(
        db,
        current_user.id,
        request.source_niche,
        request.target_niche,
        request.auto_publish,
    )
    
    if not success:
        raise HTTPException(
            status_code=503, detail="Strategy cloning service unavailable"
        )
    
    # 2. Autonomous Expansion: Launch first video for the new niche if requested
    job_id = None
    if request.auto_publish:
        try:
            job_id = await base_creator_service.launch_automated_video(
                user_id=current_user.id,
                topic=f"Expansion into {request.target_niche}",
                niche=request.target_niche,
                style="Cinematic",
                duration=60,
                engine="cloud"
            )
        except Exception as e:
            logging.exception(f"[Monetization] Failed to launch automated video for clone: {e}")

    return success_response(
        data={
            "status": "success",
            "message": f"Strategy cloned to {request.target_niche}",
            "job_id": job_id
        }
    )


class LinkCreate(BaseModel):
    product_name: str
    niche: str
    link: str
    cta_text: str | None = "Check link in bio"


@router.get("/links")
async def list_affiliate_links(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Lists all affiliate links for the current user.
    """
    stmt = select(AffiliateLinkDB).where(AffiliateLinkDB.user_id == current_user.id)
    result = await db.execute(stmt)
    links = result.scalars().all()
    return success_response(data={"links": links})


@router.post("/links")
async def create_affiliate_link(
    link: LinkCreate,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Registers a new affiliate link.
    """
    db_link = AffiliateLinkDB(**link.model_dump())
    db.add(db_link)
    await db.commit()
    await db.refresh(db_link)
    return success_response(data=db_link)


class PromoRequest(BaseModel):
    product_name: str
    niche: str
    duration: int = 30


@router.post("/promo/generate")
async def generate_promo(request: PromoRequest, current_user=Depends(get_current_user)):
    """
    Generates a conversion-optimized promo script.
    """
    script = await base_promo_service.generate_promo_script(
        request.product_name, request.niche, request.duration
    )
    return success_response(data=script)


@router.post("/evolution/trigger")
async def trigger_evolution(current_user=Depends(get_current_user)):
    """
    Triggers a strategic scaling and optimization cycle for the empire.
    """
    # Simulate evolution process
    return success_response(
        data={
            "status": "initiated",
            "message": "Global Flywheel Evolution sequence activated.",
            "optimization_target": "70% pruning threshold",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


# --- Affiliate Network Webhooks ---

class AffiliatePostback(BaseModel):
    """Postback/conversion data from affiliate networks."""
    network: str  # amazon, impact, sharesale
    transaction_id: str
    affiliate_link_id: str | None = None
    order_id: str | None = None
    amount: float = 0.0
    commission: float = 0.0
    currency: str = "USD"
    status: str = "approved"  # approved, pending, rejected
    click_id: str | None = None
    sub_id: str | None = None
    timestamp: str | None = None


@router.post("/webhook/affiliate")
async def affiliate_webhook(
    request: Request,
    x_webhook_signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
    x_impact_signature: str | None = Header(default=None, alias="X-Impact-Signature"),
    x_ssc_signature: str | None = Header(default=None, alias="X-Ssc-Signature"),
    db=Depends(get_db),
):
    """
    Generic dispatcher for affiliate postbacks. Routes to the right
    per-network verifier based on the ``network`` field in the body.

    Auth schemes (per network):
      - impact:    HMAC-SHA256(body, IMPACT_WEBHOOK_SECRET)        — X-Impact-Signature
      - sharesale: HMAC-SHA256(trans_id + "|" + secret)            — X-Ssc-Signature
      - amazon:    not supported (501) — Amazon has no real postback

    Idempotency: duplicate (platform, transaction_id) pairs are rejected
    before any DB write so a retried postback cannot double-credit.
    """
    raw_body = await request.body()
    import json as _json

    try:
        postback_dict = _json.loads(raw_body.decode("utf-8") or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    network = (postback_dict.get("network") or "").lower()
    if network == "impact":
        _verify_impact_signature(raw_body, x_impact_signature or x_webhook_signature)
    elif network in ("sharesale", "shareasale"):
        trans_id = str(
            postback_dict.get("trans_id") or postback_dict.get("transaction_id") or ""
        )
        _verify_shareasale_signature(raw_body, x_ssc_signature, trans_id)
    elif network == "amazon":
        raise HTTPException(
            status_code=501,
            detail=(
                "Amazon Associates has no real postback/webhook system. "
                "Conversion tracking is server-side via the Associates tag. "
                "For programmatic product lookup use the PA-API (AWS SigV4)."
            ),
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown network '{network}'. Supported: impact, sharesale. "
                "Amazon postbacks are not supported (see /webhook/amazon)."
            ),
        )

    try:
        postback = AffiliatePostback(**postback_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid postback shape: {e}")

    logging.info(
        f"[Affiliate Webhook] {postback.network} conversion: "
        f"tx={postback.transaction_id}, amount={postback.amount}, "
        f"commission={postback.commission}"
    )

    # Idempotency + insert: atomic INSERT ... ON CONFLICT DO NOTHING
    # against the (platform, transaction_id) unique constraint. The helper
    # writes the row; if a duplicate fires concurrently the insert is a
    # no-op and ``is_new`` is False.
    is_new = await _idempotent_insert_revenue_log(
        db,
        platform=f"affiliate_{postback.network}",
        amount=postback.commission,
        transaction_id=postback.transaction_id,
        source_niche="affiliate",
        view_count=1,
    )
    if not is_new:
        logging.info(
            f"[Affiliate Webhook] Duplicate postback ignored: "
            f"tx={postback.transaction_id}"
        )
        await db.commit()
        return success_response(
            data={
                "status": "duplicate_ignored",
                "transaction_id": postback.transaction_id,
            }
        )

    # Update affiliate link stats if link_id provided
    if postback.affiliate_link_id:
        from sqlalchemy import update
        stmt = (
            update(AffiliateLinkDB)
            .where(AffiliateLinkDB.id == postback.affiliate_link_id)
            .values(
                click_count=(AffiliateLinkDB.click_count or 0) + 1,
                total_revenue=(AffiliateLinkDB.total_revenue or 0) + postback.commission,
            )
        )
        await db.execute(stmt)

    await db.commit()

    return success_response(
        data={
            "status": "received",
            "transaction_id": postback.transaction_id,
            "network": postback.network,
        }
    )


@router.post("/webhook/impact")
async def impact_webhook(
    request: Request,
    x_signature: str | None = Header(default=None, alias="X-Signature"),
    x_impact_signature: str | None = Header(default=None, alias="X-Impact-Signature"),
    db=Depends(get_db),
):
    """
    Impact Radius specific webhook handler.
    Auth: HMAC-SHA256(raw_body, IMPACT_WEBHOOK_SECRET) — header
    ``X-Signature`` (or ``X-Impact-Signature`` for accounts that use the
    Impact-branded variant).
    """
    raw_body = await request.body()
    _verify_impact_signature(raw_body, x_impact_signature or x_signature)
    import json as _json
    try:
        request_data = _json.loads(raw_body.decode("utf-8") or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    logging.info(f"[Impact Webhook] Received: {request_data}")

    # Extract Impact-specific fields
    action_id = request_data.get("actionId", request_data.get("id"))
    commission = float(request_data.get("commission", 0))

    if action_id:
        is_new = await _idempotent_insert_revenue_log(
            db,
            platform="affiliate_impact",
            amount=commission,
            transaction_id=str(action_id),
            source_niche="affiliate",
            view_count=1,
        )
        if not is_new:
            await db.commit()
            return success_response(
                data={"status": "duplicate_ignored", "action_id": action_id}
            )
        await db.commit()

    return success_response(data={"status": "received", "action_id": action_id})


@router.post("/webhook/sharesale")
async def sharesale_webhook(
    request: Request,
    x_ssc_signature: str | None = Header(default=None, alias="X-Ssc-Signature"),
    db=Depends(get_db),
):
    """
    ShareASale specific webhook handler.
    Auth: HMAC-SHA256(trans_id + "|" + SHAREASALE_WEBHOOK_SECRET) — header
    ``X-Ssc-Signature``. The exact field-tuple for production cutover
    should be re-confirmed with ShareASale support.
    """
    raw_body = await request.body()
    import json as _json
    try:
        request_data = _json.loads(raw_body.decode("utf-8") or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    trans_id = str(
        request_data.get("trans_id") or request_data.get("transaction_id") or ""
    )
    _verify_shareasale_signature(raw_body, x_ssc_signature, trans_id)

    logging.info(f"[ShareASale Webhook] Received: {request_data}")

    commission = float(request_data.get("commission", 0))

    if trans_id:
        is_new = await _idempotent_insert_revenue_log(
            db,
            platform="affiliate_sharesale",
            amount=commission,
            transaction_id=trans_id,
            source_niche="affiliate",
            view_count=1,
        )
        if not is_new:
            await db.commit()
            return success_response(
                data={"status": "duplicate_ignored", "trans_id": trans_id}
            )
        await db.commit()

    return success_response(data={"status": "received", "trans_id": trans_id})


@router.post("/webhook/amazon")
async def amazon_webhook(
    request: Request,
    db=Depends(get_db),
):
    """
    Amazon Associates postback stub.

    Amazon Associates does NOT provide a real postback/webhook system;
    conversion tracking is performed server-side via the Associates tag.
    For programmatic product lookup, integrate the PA-API (AWS SigV4),
    which is out of scope for this endpoint.

    Returns 501 with a clear migration message so anyone who tries to wire
    an Amazon postback to this URL immediately understands the situation.
    """
    # Drain the body to keep the connection healthy
    await request.body()
    raise HTTPException(
        status_code=501,
        detail=(
            "Amazon Associates has no real postback/webhook system. "
            "Conversion tracking is server-side via the Associates tag. "
            "For programmatic product lookup, use the PA-API (AWS SigV4) — "
            "see src/services/monetization/amazon_paapi.py."
        ),
    )


@router.post("/webhook/internal-legacy")
async def internal_legacy_webhook(
    request: Request,
    x_webhook_signature: str | None = Header(default=None, alias="X-Webhook-Signature"),
    x_webhook_timestamp: str | None = Header(default=None, alias="X-Webhook-Timestamp"),
    db=Depends(get_db),
):
    """
    Legacy HMAC webhook endpoint. Preserved for in-cluster test hooks
    (e.g. dev / Playwright / unit tests) that signed postbacks with the
    original ``<timestamp>.<body>`` scheme.

    NOT a real affiliate-network signature. New integrations must use the
    per-network endpoints:

      - /webhook/affiliate  (dispatcher; picks verifier from ``network``)
      - /webhook/impact     (real Impact HMAC-SHA256)
      - /webhook/sharesale  (real ShareASale HMAC-SHA256)
      - /webhook/amazon     (501 — Amazon has no real postback)
    """
    raw_body = await request.body()
    _verify_legacy_signature(raw_body, x_webhook_signature, x_webhook_timestamp)
    import json as _json
    try:
        request_data = _json.loads(raw_body.decode("utf-8") or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    logging.info(f"[Internal Legacy Webhook] Received: {request_data}")

    transaction_id = str(
        request_data.get("transaction_id")
        or request_data.get("trans_id")
        or request_data.get("actionId")
        or ""
    )
    platform = str(request_data.get("platform") or "affiliate_internal")
    amount = float(request_data.get("amount") or request_data.get("commission") or 0)

    if not transaction_id:
        raise HTTPException(
            status_code=400, detail="Missing transaction_id / trans_id / actionId."
        )

    is_new = await _idempotent_insert_revenue_log(
        db,
        platform=platform,
        amount=amount,
        transaction_id=transaction_id,
        source_niche="affiliate_internal",
        view_count=1,
        extra_metadata={"source": "internal_legacy"},
    )
    if not is_new:
        await db.commit()
        return success_response(
            data={"status": "duplicate_ignored", "transaction_id": transaction_id}
        )

    await db.commit()

    return success_response(
        data={"status": "received", "transaction_id": transaction_id, "platform": platform}
    )
