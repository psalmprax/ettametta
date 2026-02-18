from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.utils.database import get_db
from api.utils.models import AffiliateLinkDB, RevenueLogDB
from api.routes.auth import get_current_user
from services.monetization.service import base_monetization_engine
from services.monetization.promo_generator import base_promo_generator
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/monetization", tags=["Monetization"])

class LinkRecommendationRequest(BaseModel):
    niche: str
    script_text: str

@router.post("/recommend-links")
async def recommend_links(request: LinkRecommendationRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Recommends products/links based on script content.
    """
    recommendations = await base_monetization_engine.recommend_products(request.niche, request.script_text)
    
    # Check if we have actual links in DB for these categories
    # (In a real app, we'd search AffiliateLinkDB by niche/type)
    db_links = db.query(AffiliateLinkDB).filter(AffiliateLinkDB.niche == request.niche).all()
    
    return {
        "suggestions": recommendations,
        "available_links": db_links
    }

@router.get("/report")
async def get_monetization_report(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Aggregates revenue tracking data for the dashboard.
    """
    logs = db.query(RevenueLogDB).filter(RevenueLogDB.user_id == current_user.id).all()
    
    total_rev = sum(log.amount for log in logs)
    total_views = sum(log.views for log in logs)
    epm = base_monetization_engine.calculate_epm(total_rev, total_views)
    
    return {
        "total_revenue": total_rev,
        "epm": epm,
        "logs": logs
    }

@router.get("/empire/metrics")
async def get_empire_metrics(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    from services.monetization.empire_service import base_empire_service
    return base_empire_service.get_empire_metrics(db, current_user.id)

class CloneRequest(BaseModel):
    source_niche: str
    target_niche: str

@router.get("/empire/blueprints")
async def get_winning_blueprints(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    from services.monetization.empire_service import base_empire_service
    return base_empire_service.get_winning_blueprints(db, current_user.id)

@router.get("/empire/network")
async def get_network_graph(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the visualization graph (nodes/links) for the empire mesh.
    """
    from services.monetization.empire_service import base_empire_service
    return base_empire_service.get_network_graph(db, current_user.id)

@router.post("/commerce/sync")
async def sync_commerce_products(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Triggers a test sync with the configured Shopify store.
    """
    from services.monetization.commerce_service import base_commerce_service
    # Test with a generic niche to verify connection
    products = await base_commerce_service.get_relevant_products("Growth")
    if not products:
        return {"status": "warning", "message": "No products found. Check credentials or niche tags."}
    return {"status": "success", "sample_count": len(products), "source": products[0].get("source")}

@router.post("/empire/clone")
async def clone_strategy(request: CloneRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    from services.monetization.empire_service import base_empire_service
    success = await base_empire_service.clone_strategy(db, current_user.id, request.source_niche, request.target_niche)
    if not success:
        raise HTTPException(status_code=500, detail="Cloning failed")
    return {"status": "success", "message": f"Strategy cloned to {request.target_niche}"}

class LinkCreate(BaseModel):
    product_name: str
    niche: str
    link: str
    cta_text: Optional[str] = "Check link in bio"

@router.post("/links")
async def create_affiliate_link(link: LinkCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Registers a new affiliate link.
    """
    db_link = AffiliateLinkDB(**link.dict())
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link

class PromoRequest(BaseModel):
    product_name: str
    niche: str
    duration: int = 30

@router.post("/promo/generate")
async def generate_promo(request: PromoRequest, current_user = Depends(get_current_user)):
    """
    Generates a conversion-optimized promo script.
    """
    script = await base_promo_generator.generate_promo_script(request.product_name, request.niche, request.duration)
    return script
