from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.utils.database import get_db
from api.utils.models import SystemSettings
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingUpdateRequest(BaseModel):
    key: str
    value: str
    category: Optional[str] = "general"

def admin_required(current_user: UserDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative access required"
        )
    return current_user

@router.get("/")
async def get_settings(db: Session = Depends(get_db), _admin = Depends(admin_required)):
    from api.config import settings as app_settings
    db_items = db.query(SystemSettings).all()
    db_dict = {s.key: s.value for s in db_items}
    
    # Defaults from config
    config_dict = {
        "groq_api_key": app_settings.GROQ_API_KEY,
        "youtube_api_key": app_settings.YOUTUBE_API_KEY,
        "tiktok_client_id": app_settings.TIKTOK_CLIENT_KEY, 
        "tiktok_client_secret": app_settings.TIKTOK_CLIENT_SECRET,
        "scan_frequency": "Every 1 hour",
        "force_originality": "true",
        "auto_pilot": "false",
        "monetization_aggression": "80",
        "shopify_access_token": "shpat_xxxxxxxxxxxxxxxx",
        "shopify_shop_url": "your-store.myshopify.com",
        "elevenlabs_api_key": app_settings.ELEVENLABS_API_KEY,
        "fish_speech_endpoint": "http://voiceover:8080",
        "voice_engine": "fish_speech",
        "pexels_api_key": app_settings.PEXELS_API_KEY,
        "aws_access_key_id": app_settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": app_settings.AWS_SECRET_ACCESS_KEY,
        "aws_region": app_settings.AWS_REGION,
        "aws_storage_bucket_name": app_settings.AWS_STORAGE_BUCKET_NAME,
        "active_monetization_strategy": "commerce"
    }
    
    # Merge: DB takes precedence
    merged = {**config_dict, **db_dict}
    return merged

@router.post("/")
async def update_setting(request: SettingUpdateRequest, db: Session = Depends(get_db), _admin = Depends(admin_required)):
    setting = db.query(SystemSettings).filter(SystemSettings.key == request.key).first()
    if setting:
        setting.value = request.value
        setting.category = request.category or setting.category
    else:
        setting = SystemSettings(
            key=request.key,
            value=request.value,
            category=request.category
        )
        db.add(setting)
    
    db.commit()
    db.refresh(setting)
    return {"status": "success", "key": setting.key}

@router.post("/bulk")
async def bulk_update_settings(settings_list: List[SettingUpdateRequest], db: Session = Depends(get_db), _admin = Depends(admin_required)):
    for req in settings_list:
        setting = db.query(SystemSettings).filter(SystemSettings.key == req.key).first()
        if setting:
            setting.value = req.value
            setting.category = req.category or setting.category
        else:
            setting = SystemSettings(
                key=req.key,
                value=req.value,
                category=req.category
            )
            db.add(setting)
    
    db.commit()
    return {"status": "success"}

@router.post("/filters/{filter_id}/toggle")
async def toggle_filter(filter_id: str, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    from api.utils.models import VideoFilterDB
    filter_item = db.query(VideoFilterDB).filter(VideoFilterDB.id == filter_id).first()
    if not filter_item:
        raise HTTPException(status_code=404, detail="Filter not found")
    
    filter_item.enabled = not filter_item.enabled
    db.commit()
    db.refresh(filter_item)
    return filter_item

@router.get("/filters")
async def get_available_filters(db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    from api.utils.models import VideoFilterDB
    filters = db.query(VideoFilterDB).all()
    
    # Auto-seed defaults if table is empty
    if not filters:
        default_filters = [
            { "id": "f1", "name": "Mirror Transform", "enabled": True, "description": "Bypasses horizontal matching" },
            { "id": "f2", "name": "Dynamic Zoom", "enabled": True, "description": "Subtle 1.02x-1.08x zoom shifts" },
            { "id": "f3", "name": "HLS Color Grade", "enabled": True, "description": "Unique saturation & contrast mapping" },
            { "id": "f4", "name": "Pattern Interrupts", "enabled": True, "description": "Random frame offsets & visual hooks" },
            { "id": "f5", "name": "AI Captions", "enabled": True, "description": "High-impact yellow captions on bottom 1/3" },
            { "id": "f6", "name": "Speed Ramping", "enabled": True, "description": "Dynamic velocity shifts (0.9x - 1.1x)" },
            { "id": "f7", "name": "Cinematic Overlays", "enabled": True, "description": "High-energy texture & light leak overlays" },
            { "id": "f8", "name": "Dynamic Jitter", "enabled": True, "description": "Handheld camera motion simulation" },
        ]
        for df in default_filters:
            db.add(VideoFilterDB(**df))
        db.commit()
        filters = db.query(VideoFilterDB).all()
        
    return filters
