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
            detail="Administrative access required",
        )
    return current_user


@router.get("/")
async def get_settings(
    db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)
):
    from api.config import settings as app_settings
    from api.utils.models import UserSetting

    # 1. Fetch system-wide defaults from DB
    db_items = db.query(SystemSettings).all()
    system_dict = {s.key: s.value for s in db_items}

    # 2. Fetch user-specific overrides
    user_items = (
        db.query(UserSetting).filter(UserSetting.user_id == current_user.id).all()
    )
    user_dict = {s.key: s.value for s in user_items}

    # 3. Defaults from app config (hardcoded fallback)
    config_dict = {
        "groq_api_key": app_settings.GROQ_API_KEY,
        "youtube_api_key": app_settings.YOUTUBE_API_KEY,
        "tiktok_client_key": app_settings.TIKTOK_CLIENT_KEY,
        "tiktok_client_secret": app_settings.TIKTOK_CLIENT_SECRET,
        "scan_frequency": "Every 1 hour",
        "force_originality": "true",
        "auto_pilot": "false",
        "monetization_aggression": "80",
        "shopify_access_token": app_settings.SHOPIFY_ACCESS_TOKEN or "",
        "shopify_shop_url": app_settings.SHOPIFY_SHOP_URL or "",
        "elevenlabs_api_key": app_settings.ELEVENLABS_API_KEY,
        "fish_speech_endpoint": "http://voiceover:8080",
        "voice_engine": "fish_speech",
        "pexels_api_key": app_settings.PEXELS_API_KEY,
        "google_client_id": app_settings.GOOGLE_CLIENT_ID,
        "google_client_secret": app_settings.GOOGLE_CLIENT_SECRET,
        "monetization_mode": "selective",
        "active_monetization_strategy": "commerce",
        # Video Quality Tiers (Defaults)
        "enable_sound_design": "false",
        "enable_motion_graphics": "false",
        "ai_video_provider": "none",
        "default_quality_tier": "standard",
        "ai_matching_enabled": "true",
        "auto_promo_enabled": "true",
        "auto_merch_enabled": "false",
        "lead_gen_url": "",
        "digital_product_url": "",
    }

    # Cascade: Config -> System -> User (User wins)
    merged = {**config_dict, **system_dict, **user_dict}
    return merged


@router.post("/")
async def update_setting(
    request: SettingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    from api.utils.models import UserSetting

    # Non-admins can only update their own UserSetting overrides
    # Adms can update SystemSettings via /admin routes, but we'll allow them to have personal overrides too if they use this route.

    setting = (
        db.query(UserSetting)
        .filter(
            UserSetting.user_id == current_user.id,
            UserSetting.key == request.key.lower(),
        )
        .first()
    )

    if setting:
        setting.value = request.value
        setting.category = request.category or setting.category
    else:
        setting = UserSetting(
            user_id=current_user.id,
            key=request.key.lower(),
            value=request.value,
            category=request.category,
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return {"status": "success", "key": setting.key, "scope": "user"}


@router.get("/monetization/strategies")
async def get_monetization_strategies(db: Session = Depends(get_db)):
    """Returns all available monetization strategies with their configuration status"""
    from api.config import settings as app_settings

    # Get system settings to check configuration status
    db_items = db.query(SystemSettings).all()
    system_dict = {s.key: s.value for s in db_items}

    def _configured(key: str) -> bool:
        return bool(system_dict.get(key) or getattr(app_settings, key.upper(), None))

    strategies = [
        {
            "id": "commerce",
            "name": "E-Commerce",
            "description": "Sell physical/digital products via Shopify",
            "required_settings": ["shopify_shop_url", "shopify_access_token"],
            "configured": _configured("shopify_shop_url")
            and _configured("shopify_access_token"),
        },
        {
            "id": "affiliate",
            "name": "Affiliate Marketing",
            "description": "Earn commissions from product recommendations",
            "required_settings": [],
            "configured": True,
        },
        {
            "id": "lead_gen",
            "name": "Lead Generation",
            "description": "Capture leads with free resources",
            "required_settings": [],
            "configured": True,
        },
        {
            "id": "digital_product",
            "name": "Digital Products",
            "description": "Sell ebooks, templates, and digital downloads",
            "required_settings": [],
            "configured": True,
        },
        {
            "id": "membership",
            "name": "Membership/Patreon",
            "description": "Recurring revenue through supporter tiers",
            "required_settings": ["membership_platform_url"],
            "configured": _configured("membership_platform_url"),
        },
        {
            "id": "course",
            "name": "Online Courses",
            "description": "Sell online courses and tutorials",
            "required_settings": ["course_platform_url"],
            "configured": _configured("course_platform_url"),
        },
        {
            "id": "sponsorship",
            "name": "Sponsorships",
            "description": "Brand deals and sponsored content",
            "required_settings": [],
            "configured": True,
        },
        {
            "id": "crypto",
            "name": "Crypto/Donations",
            "description": "Accept crypto tips or donations",
            "required_settings": ["donation_link"],
            "configured": _configured("donation_link"),
        },
    ]

    return {
        "strategies": strategies,
        "active_strategies": [s["id"] for s in strategies if s["configured"]],
    }


@router.get("/system")
async def get_system_settings(
    db: Session = Depends(get_db), _admin=Depends(admin_required)
):
    """Get all system-wide settings (admin only)"""
    db_items = db.query(SystemSettings).all()
    system_dict = {s.key: s.value for s in db_items}
    return system_dict


@router.post("/system")
async def update_system_settings(
    settings_dict: dict, db: Session = Depends(get_db), _admin=Depends(admin_required)
):
    """Update system-wide settings (admin only)"""
    for key, value in settings_dict.items():
        if key in ("id", "created_at", "updated_at"):
            continue
        setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            setting = SystemSettings(key=key, value=str(value), category="system")
            db.add(setting)

    db.commit()
    return {"status": "success", "updated_count": len(settings_dict)}


@router.post("/bulk")
async def bulk_update_settings(
    settings_list: List[SettingUpdateRequest],
    db: Session = Depends(get_db),
    _admin=Depends(admin_required),
):
    for req in settings_list:
        setting = db.query(SystemSettings).filter(SystemSettings.key == req.key).first()
        if setting:
            setting.value = req.value
            setting.category = req.category or setting.category
        else:
            setting = SystemSettings(
                key=req.key, value=req.value, category=req.category
            )
            db.add(setting)

    db.commit()
    return {"status": "success"}


@router.post("/user")
async def bulk_update_user_settings(
    settings_list: List[SettingUpdateRequest],
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Bulk update user-specific settings (non-admin users)"""
    from api.utils.models import UserSetting

    for req in settings_list:
        setting = (
            db.query(UserSetting)
            .filter(
                UserSetting.user_id == current_user.id,
                UserSetting.key == req.key.lower(),
            )
            .first()
        )
        if setting:
            setting.value = req.value
            setting.category = req.category or setting.category
        else:
            setting = UserSetting(
                user_id=current_user.id,
                key=req.key.lower(),
                value=req.value,
                category=req.category or "general",
            )
            db.add(setting)

    db.commit()
    return {"status": "success", "updated_count": len(settings_list)}


@router.post("/filters/{filter_id}/toggle")
async def toggle_filter(
    filter_id: str,
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    # Handle service-level filters (Sound Design, Motion Graphics)
    if filter_id in ("sound_design", "motion_graphics"):
        env_key = (
            "ENABLE_SOUND_DESIGN"
            if filter_id == "sound_design"
            else "ENABLE_MOTION_GRAPHICS"
        )
        current = db.query(SystemSettings).filter(SystemSettings.key == env_key).first()
        new_value = "false" if current and current.value.lower() == "true" else "true"
        if current:
            current.value = new_value
        else:
            db.add(SystemSettings(key=env_key, value=new_value, category="engine"))
        db.commit()

        return {
            "id": filter_id,
            "name": "Sound Design Engine"
            if filter_id == "sound_design"
            else "Motion Graphics Engine",
            "enabled": new_value.lower() == "true",
            "description": "Auto background music & SFX"
            if filter_id == "sound_design"
            else "Animated text overlays & titles",
            "type": "service",
        }

    # Handle standard video filter toggles
    from api.utils.models import VideoFilterDB

    filter_item = db.query(VideoFilterDB).filter(VideoFilterDB.id == filter_id).first()
    if not filter_item:
        raise HTTPException(status_code=404, detail="Filter not found")

    filter_item.enabled = not filter_item.enabled
    db.commit()
    db.refresh(filter_item)
    return {
        "id": filter_item.id,
        "name": filter_item.name,
        "enabled": filter_item.enabled,
        "description": filter_item.description,
        "type": "video_filter",
    }


@router.get("/filters")
async def get_available_filters(
    db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)
):
    from api.utils.models import VideoFilterDB
    from api.config import settings as app_settings

    filters = db.query(VideoFilterDB).all()

    # Auto-seed defaults if table is empty
    if not filters:
        default_filters = [
            {
                "id": "f1",
                "name": "Mirror Transform",
                "enabled": True,
                "description": "Bypasses horizontal matching",
            },
            {
                "id": "f2",
                "name": "Dynamic Zoom",
                "enabled": True,
                "description": "Subtle 1.02x-1.08x zoom shifts",
            },
            {
                "id": "f3",
                "name": "HLS Color Grade",
                "enabled": True,
                "description": "Unique saturation & contrast mapping",
            },
            {
                "id": "f4",
                "name": "Pattern Interrupts",
                "enabled": True,
                "description": "Random frame offsets & visual hooks",
            },
            {
                "id": "f5",
                "name": "AI Captions",
                "enabled": True,
                "description": "High-impact yellow captions on bottom 1/3",
            },
            {
                "id": "f6",
                "name": "Speed Ramping",
                "enabled": True,
                "description": "Dynamic velocity shifts (0.9x - 1.1x)",
            },
            {
                "id": "f7",
                "name": "Cinematic Overlays",
                "enabled": True,
                "description": "High-energy texture & light leak overlays",
            },
            {
                "id": "f8",
                "name": "Dynamic Jitter",
                "enabled": True,
                "description": "Handheld camera motion simulation",
            },
        ]
        for df in default_filters:
            db.add(VideoFilterDB(**df))
        db.commit()
        filters = db.query(VideoFilterDB).all()

    # Include Sound Design and Motion Graphics as virtual system filters
    import os

    sound_design_enabled = os.getenv("ENABLE_SOUND_DESIGN", "false").lower() == "true"
    motion_graphics_enabled = (
        os.getenv("ENABLE_MOTION_GRAPHICS", "false").lower() == "true"
    )

    result = []
    for f in filters:
        result.append(
            {
                "id": f.id,
                "name": f.name,
                "enabled": f.enabled,
                "description": f.description,
                "type": "video_filter",
            }
        )

    result.append(
        {
            "id": "sound_design",
            "name": "Sound Design Engine",
            "enabled": sound_design_enabled,
            "description": "Auto background music & SFX injection by niche mood",
            "type": "service",
        }
    )
    result.append(
        {
            "id": "motion_graphics",
            "name": "Motion Graphics Engine",
            "enabled": motion_graphics_enabled,
            "description": "Animated text overlays, titles & cinematic motion",
            "type": "service",
        }
    )

    return result
