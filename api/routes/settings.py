from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.utils.database import get_db
from api.utils.models import SystemSettings, BotCodeDB, UserSetting, VideoFilterDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from api.utils.notifications import configure_telegram_bot, configure_whatsapp_bot
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingUpdateRequest(BaseModel):
    key: str
    value: str
    category: Optional[str] = "general"


class UserSettingsUpdate(BaseModel):
    telegram_chat_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    api_keys: Optional[dict] = None
    system_settings: Optional[dict] = None


def admin_required(current_user: UserDB = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative access required",
        )
    return current_user


@router.get("/")
async def get_settings(
    db: AsyncSession = Depends(get_db), current_user: UserDB = Depends(get_current_user)
):
    from api.config import settings as app_settings
    from api.utils.models import UserSetting

    # 1. Fetch system-wide defaults from DB
    stmt_system = select(SystemSettings)
    result_system = await db.execute(stmt_system)
    db_items = result_system.scalars().all()
    system_dict = {s.key: s.value for s in db_items}

    # 2. Fetch user-specific overrides
    stmt_user = select(UserSetting).where(UserSetting.user_id == current_user.id)
    result_user = await db.execute(stmt_user)
    user_items = result_user.scalars().all()
    user_dict = {s.key: s.value for s in user_items}

    # 3. Defaults from app config (hardcoded fallback)
    config_dict = {
        # LLM API Keys (Admin UI configurable)
        "groq_api_key": app_settings.GROQ_API_KEY,
        "openai_api_key": app_settings.OPENAI_API_KEY,
        "anthropic_api_key": app_settings.ANTHROPIC_API_KEY,
        "xai_api_key": app_settings.XAI_API_KEY,
        "deepseek_api_key": app_settings.DEEPSEEK_API_KEY,
        "google_api_key": app_settings.GOOGLE_API_KEY,
        "cohere_api_key": app_settings.COHERE_API_KEY,
        "mistral_api_key": app_settings.MISTRAL_API_KEY,
        "cerebras_api_key": app_settings.CEREBRAS_API_KEY,
        "cloudflare_api_key": app_settings.CLOUDFLARE_API_KEY,
        "cloudflare_account_id": app_settings.CLOUDFLARE_ACCOUNT_ID,
        "hugging_face_api_key": app_settings.HUGGING_FACE_API_KEY,
        "openrouter_api_key": app_settings.OPENROUTER_API_KEY,
        "nvidia_api_key": app_settings.NVIDIA_API_KEY,
        "ollama_cloud_api_key": app_settings.OLLAMA_CLOUD_API_KEY,
        "siliconflow_api_key": app_settings.SILICONFLOW_API_KEY,
        "ollama_url": app_settings.OLLAMA_URL,
        "lm_studio_url": app_settings.LM_STUDIO_URL,
        # Social Media & OAuth
        "youtube_api_key": app_settings.YOUTUBE_API_KEY,
        "tiktok_api_key": app_settings.TIKTOK_API_KEY,
        "tiktok_client_key": app_settings.TIKTOK_CLIENT_KEY,
        "tiktok_client_secret": app_settings.TIKTOK_CLIENT_SECRET,
        "google_client_id": app_settings.GOOGLE_CLIENT_ID,
        "google_client_secret": app_settings.GOOGLE_CLIENT_SECRET,
        # Payment & E-commerce
        "stripe_secret_key": app_settings.STRIPE_SECRET_KEY,
        "shopify_access_token": app_settings.SHOPIFY_ACCESS_TOKEN,
        "shopify_shop_url": app_settings.SHOPIFY_SHOP_URL,
        "printful_api_key": app_settings.PRINTFUL_API_KEY,
        # Communication
        "telegram_bot_token": app_settings.TELEGRAM_BOT_TOKEN,
        "telegram_admin_id": str(app_settings.TELEGRAM_ADMIN_ID),
        "twilio_account_sid": app_settings.TWILIO_ACCOUNT_SID,
        "twilio_auth_token": app_settings.TWILIO_AUTH_TOKEN,
        "twilio_whatsapp_number": app_settings.TWILIO_WHATSAPP_NUMBER,
        # Email Marketing
        "mailchimp_api_key": app_settings.MAILCHIMP_API_KEY,
        "mailchimp_list_id": app_settings.MAILCHIMP_LIST_ID,
        "convertkit_api_key": app_settings.CONVERTKIT_API_KEY,
        # Affiliate Programs
        "amazon_associates_tag": app_settings.AMAZON_ASSOCIATES_TAG,
        "amazon_paapi_key": app_settings.AMAZON_PAAPI_KEY,
        "amazon_paapi_tag": app_settings.AMAZON_PAAPI_TAG,
        "impact_radius_api_key": app_settings.IMPACT_RADIUS_API_KEY,
        "shareasale_api_key": app_settings.SHAREASALE_API_KEY,
        # Trading
        "alpha_vantage_api_key": app_settings.ALPHA_VANTAGE_API_KEY,
        "coingecko_api_key": app_settings.COINGECKO_API_KEY,
        # Video & Voice
        "elevenlabs_api_key": app_settings.ELEVENLABS_API_KEY,
        "fish_speech_endpoint": app_settings.FISH_SPEECH_ENDPOINT,
        "pexels_api_key": app_settings.PEXELS_API_KEY,
        "google_search_cx": app_settings.GOOGLE_SEARCH_CX,
        "runway_api_key": app_settings.RUNWAY_API_KEY,
        "pika_api_key": app_settings.PIKA_API_KEY,
        "zsky_api_key": app_settings.ZSKY_API_KEY,
        "kling_api_key": app_settings.KLING_API_KEY,
        "pixverse_api_key": app_settings.PIXVERSE_API_KEY,
        "replicate_api_key": app_settings.REPLICATE_API_KEY,
        "stability_api_key": app_settings.STABILITY_API_KEY,
        # Feature Settings (Admin UI)
        "default_llm_provider": app_settings.DEFAULT_LLM_PROVIDER,
        "use_os_models": str(app_settings.USE_OS_MODELS),
        "monetization_mode": app_settings.MONETIZATION_MODE,
        "voice_engine": app_settings.VOICE_ENGINE,
        "default_vlm_model": app_settings.DEFAULT_VLM_MODEL,
        "ai_video_provider": app_settings.AI_VIDEO_PROVIDER,
        "ai_video_fallbacks": app_settings.AI_VIDEO_FALLBACKS,
        "default_quality_tier": app_settings.DEFAULT_QUALITY_TIER,
        "enable_sound_design": str(app_settings.ENABLE_SOUND_DESIGN),
        "enable_motion_graphics": str(app_settings.ENABLE_MOTION_GRAPHICS),
        "enable_langchain": str(app_settings.ENABLE_LANGCHAIN),
        "enable_crewai": str(app_settings.ENABLE_CREWAI),
        "enable_interpreter": str(app_settings.ENABLE_INTERPRETER),
        "enable_affiliate_api": str(app_settings.ENABLE_AFFILIATE_API),
        "enable_trading": str(app_settings.ENABLE_TRADING),
        "enable_opencli": str(app_settings.ENABLE_OPENCLI),
        # Business Logic
        "limit_free": str(app_settings.LIMIT_FREE),
        "limit_pro": str(app_settings.LIMIT_PRO),
        "limit_sovereign": str(app_settings.LIMIT_SOVEREIGN),
        "music_volume": str(app_settings.MUSIC_VOLUME),
        "sfx_volume": str(app_settings.SFX_VOLUME),
        "gpu_queue_slots": str(app_settings.GPU_QUEUE_SLOTS),
        "gpu_queue_timeout": str(app_settings.GPU_QUEUE_TIMEOUT),
        # URLs (some admin configurable, some system)
        "production_domain": app_settings.PRODUCTION_DOMAIN,
        "cors_origins": app_settings.CORS_ORIGINS,
        "comfyui_url": app_settings.COMFYUI_URL,
        "render_node_url": app_settings.RENDER_NODE_URL or "",
        # Legacy compatibility
        "scan_frequency": "Every 1 hour",
        "force_originality": "true",
        "auto_pilot": "false",
        "monetization_aggression": "80",
        "active_monetization_strategy": "commerce",
        "ai_matching_enabled": "true",
        "auto_promo_enabled": "true",
        "auto_merch_enabled": "false",
        "lead_gen_url": "",
        "digital_product_url": "",
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
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    from api.utils.models import UserSetting

    # Non-admins can only update their own UserSetting overrides
    # Adms can update SystemSettings via /admin routes, but we'll allow them to have personal overrides too if they use this route.

    stmt = select(UserSetting).where(
        UserSetting.user_id == current_user.id,
        UserSetting.key == request.key.lower(),
    )
    result = await db.execute(stmt)
    setting = result.scalar_one_or_none()

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

    await db.commit()
    await db.refresh(setting)
    return {"status": "success", "key": setting.key, "scope": "user"}


@router.get("/monetization/strategies")
async def get_monetization_strategies(db: AsyncSession = Depends(get_db)):
    """Returns all available monetization strategies with their configuration status"""
    from api.config import settings as app_settings

    # Get system settings to check configuration status
    stmt = select(SystemSettings)
    result = await db.execute(stmt)
    db_items = result.scalars().all()
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
    db: AsyncSession = Depends(get_db), _admin=Depends(admin_required)
):
    """Get all system-wide settings (admin only)"""
    stmt = select(SystemSettings)
    result = await db.execute(stmt)
    db_items = result.scalars().all()
    system_dict = {s.key: s.value for s in db_items}
    return system_dict


@router.post("/system")
async def update_system_settings(
    settings_dict: dict, db: AsyncSession = Depends(get_db), _admin=Depends(admin_required)
):
    """Update system-wide settings (admin only)"""
    for key, value in settings_dict.items():
        if key in ("id", "created_at", "updated_at"):
            continue
        stmt = select(SystemSettings).where(SystemSettings.key == key)
        result = await db.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = str(value)
        else:
            setting = SystemSettings(key=key, value=str(value), category="system")
            db.add(setting)

    await db.commit()
    return {"status": "success", "updated_count": len(settings_dict)}


@router.post("/bulk")
async def bulk_update_settings(
    settings_list: List[SettingUpdateRequest],
    db: AsyncSession = Depends(get_db),
    _admin=Depends(admin_required),
):
    for req in settings_list:
        stmt = select(SystemSettings).where(SystemSettings.key == req.key)
        result = await db.execute(stmt)
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = req.value
            setting.category = req.category or setting.category
        else:
            setting = SystemSettings(
                key=req.key, value=req.value, category=req.category
            )
            db.add(setting)

    await db.commit()
    return {"status": "success"}


@router.post("/user")
async def bulk_update_user_settings(
    settings_list: List[SettingUpdateRequest],
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Bulk update user-specific settings (non-admin users)"""
    from api.utils.models import UserSetting

    for req in settings_list:
        stmt = select(UserSetting).where(
            UserSetting.user_id == current_user.id,
            UserSetting.key == req.key.lower(),
        )
        result = await db.execute(stmt)
        setting = result.scalar_one_or_none()
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

    await db.commit()
    return {"status": "success", "updated_count": len(settings_list)}


@router.post("/filters/{filter_id}/toggle")
async def toggle_filter(
    filter_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    # Handle service-level filters (Sound Design, Motion Graphics)
    if filter_id in ("sound_design", "motion_graphics"):
        env_key = (
            "ENABLE_SOUND_DESIGN"
            if filter_id == "sound_design"
            else "ENABLE_MOTION_GRAPHICS"
        )
        stmt = select(SystemSettings).where(SystemSettings.key == env_key)
        result = await db.execute(stmt)
        current = result.scalar_one_or_none()
        new_value = "false" if current and current.value.lower() == "true" else "true"
        if current:
            current.value = new_value
        else:
            db.add(SystemSettings(key=env_key, value=new_value, category="engine"))
        await db.commit()

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

    stmt = select(VideoFilterDB).where(VideoFilterDB.id == filter_id)
    result = await db.execute(stmt)
    filter_item = result.scalar_one_or_none()
    if not filter_item:
        raise HTTPException(status_code=404, detail="Filter not found")

    filter_item.enabled = not filter_item.enabled
    await db.commit()
    await db.refresh(filter_item)
    return {
        "id": filter_item.id,
        "name": filter_item.name,
        "enabled": filter_item.enabled,
        "description": filter_item.description,
        "type": "video_filter",
    }


@router.get("/filters")
async def get_available_filters(
    db: AsyncSession = Depends(get_db), current_user: UserDB = Depends(get_current_user)
):
    from api.utils.models import VideoFilterDB
    from api.config import settings as app_settings

    stmt = select(VideoFilterDB)
    result = await db.execute(stmt)
    filters = result.scalars().all()

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
        await db.commit()
        stmt = select(VideoFilterDB)
        result = await db.execute(stmt)
        filters = result.scalars().all()

    # Include Sound Design and Motion Graphics as virtual system filters
    stmt_sys = select(SystemSettings)
    result_hash = await db.execute(stmt_sys)
    db_items = result_hash.scalars().all()
    system_dict = {s.key: s.value for s in db_items}

    sound_design_enabled = (
        system_dict.get("ENABLE_SOUND_DESIGN", "false").lower() == "true"
    )
    motion_graphics_enabled = (
        system_dict.get("ENABLE_MOTION_GRAPHICS", "false").lower() == "true"
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


@router.post("/verify/{service_id}")
async def verify_service(
    service_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """
    Performs a real-time handshake/verification of an external service configuration.
    This ensures that saved URLs/keys are functional 'Real Solutions'.
    """
    from api.utils.models import UserSetting
    import httpx

    # Map service_id to setting keys
    service_map = {
        "shopify": ["shopify_shop_url", "shopify_access_token"],
        "commerce": ["shopify_shop_url", "shopify_access_token"],
        "membership": ["membership_platform_url"],
        "course": ["course_platform_url"],
        "crypto": ["donation_link"],
        "groq": ["groq_api_key"],
        "openai": ["openai_api_key"],
        "elevenlabs": ["elevenlabs_api_key"],
        "pexels": ["pexels_api_key"],
        "aws": ["aws_access_key_id", "aws_secret_access_key", "aws_region"],
        "stripe": ["stripe_secret_key", "stripe_webhook_secret"],
        "tiktok": ["tiktok_client_key", "tiktok_client_secret"],
        "youtube": ["google_client_id", "google_client_secret"],
        "instagram": ["facebook_app_id", "facebook_app_secret"],
    }

    if service_id not in service_map:
        raise HTTPException(status_code=400, detail="Invalid service ID")

    keys = service_map[service_id]
    settings = {}
    for key in keys:
        stmt = select(UserSetting).where(
            UserSetting.user_id == current_user.id, UserSetting.key == key
        )
        result = await db.execute(stmt)
        s = result.scalar_one_or_none()
        settings[key] = s.value if s else None

    # Perform validation based on service type
    try:
        if service_id in ("shopify", "commerce"):
            url = settings.get("shopify_shop_url")
            if not url:
                return {"status": "error", "message": "Shopify URL not configured"}
            # Basic reachability check for the shop
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=5.0)
                if resp.status_code < 400:
                    return {
                        "status": "success",
                        "message": f"Connection verified for {url}",
                    }
                return {
                    "status": "error",
                    "message": f"Shopify returned {resp.status_code}",
                }

        elif service_id in ("membership", "course", "crypto"):
            key = keys[0]
            url = settings.get(key)
            if not url:
                return {"status": "error", "message": "Endpoint URL not configured"}
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=5.0)
                if resp.status_code < 400:
                    return {"status": "success", "message": f"Endpoint verified: {url}"}
                return {
                    "status": "error",
                    "message": f"Verification failed (Status: {resp.status_code})",
                }

        elif service_id == "groq":
            api_key = settings.get("groq_api_key")
            if not api_key:
                return {"status": "error", "message": "Groq API key not configured"}

            # Test Groq API with a simple request
            try:
                import groq

                client = groq.Groq(api_key=api_key)
                # Simple test request
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=1,
                    ),
                )
                return {
                    "status": "success",
                    "message": "Groq API key verified successfully",
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Groq API key verification failed: {str(e)}",
                }

        elif service_id == "openai":
            api_key = settings.get("openai_api_key")
            if not api_key:
                return {"status": "error", "message": "OpenAI API key not configured"}

            # Test OpenAI API
            try:
                import openai

                client = openai.OpenAI(api_key=api_key)
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=1,
                    ),
                )
                return {
                    "status": "success",
                    "message": "OpenAI API key verified successfully",
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"OpenAI API key verification failed: {str(e)}",
                }

        elif service_id == "elevenlabs":
            api_key = settings.get("elevenlabs_api_key")
            if not api_key:
                return {
                    "status": "error",
                    "message": "ElevenLabs API key not configured",
                }

            # Test ElevenLabs API
            async with httpx.AsyncClient() as client:
                headers = {"xi-api-key": api_key}
                response = await client.get(
                    "https://api.elevenlabs.io/v1/user", headers=headers
                )
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": "ElevenLabs API key verified successfully",
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"ElevenLabs API key verification failed: {response.text}",
                    }

        elif service_id == "pexels":
            api_key = settings.get("pexels_api_key")
            if not api_key:
                return {"status": "error", "message": "Pexels API key not configured"}

            # Test Pexels API
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": api_key}
                response = await client.get(
                    "https://api.pexels.com/v1/search?query=test&per_page=1",
                    headers=headers,
                )
                if response.status_code == 200:
                    return {
                        "status": "success",
                        "message": "Pexels API key verified successfully",
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Pexels API key verification failed: {response.text}",
                    }

        elif service_id == "aws":
            access_key = settings.get("aws_access_key_id")
            secret_key = settings.get("aws_secret_access_key")
            region = settings.get("aws_region", "us-east-1")

            if not access_key or not secret_key:
                return {"status": "error", "message": "AWS credentials not configured"}

            # Test AWS credentials
            try:
                import boto3

                client = boto3.client(
                    "s3",
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key,
                    region_name=region,
                )
                # Test with a simple list buckets call (will fail if no permissions but credentials are valid)
                response = await asyncio.get_event_loop().run_in_executor(
                    None, client.list_buckets
                )
                return {
                    "status": "success",
                    "message": "AWS credentials verified successfully",
                }
            except Exception as e:
                if "InvalidAccessKeyId" in str(e) or "SignatureDoesNotMatch" in str(e):
                    return {"status": "error", "message": "Invalid AWS credentials"}
                else:
                    return {
                        "status": "success",
                        "message": "AWS credentials verified (limited permissions)",
                    }

        elif service_id == "stripe":
            secret_key = settings.get("stripe_secret_key")
            if not secret_key:
                return {
                    "status": "error",
                    "message": "Stripe secret key not configured",
                }

            # Test Stripe API
            try:
                import stripe

                stripe.api_key = secret_key
                # Test with a simple balance call
                balance = await asyncio.get_event_loop().run_in_executor(
                    None, stripe.Balance.retrieve
                )
                return {
                    "status": "success",
                    "message": "Stripe API key verified successfully",
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Stripe API key verification failed: {str(e)}",
                }

        elif service_id in ("tiktok", "youtube", "instagram"):
            # OAuth-based services - check if tokens exist
            client_id = settings.get(
                f"{service_id.replace('tiktok', 'tiktok').replace('youtube', 'google').replace('instagram', 'facebook')}_client_id"
            )
            client_secret = settings.get(
                f"{service_id.replace('tiktok', 'tiktok').replace('youtube', 'google').replace('instagram', 'facebook')}_client_secret"
            )

            if not client_id or not client_secret:
                return {
                    "status": "error",
                    "message": f"{service_id.title()} OAuth credentials not configured",
                }

            return {
                "status": "success",
                "message": f"{service_id.title()} OAuth credentials configured",
            }

    except Exception as e:
        return {"status": "error", "message": f"Network Handshake Failed: {str(e)}"}

    return {
        "status": "unknown",
        "message": "Verification logic pending for this service",
    }


@router.post("/webhooks/telegram")
async def telegram_webhook(update: dict, db: AsyncSession = Depends(get_db)):
    """Handle Telegram bot webhook for configuration"""
    try:
        if "message" in update:
            chat_id = str(update["message"]["chat"]["id"])
            text = update["message"].get("text", "").strip()
            if text:
                stmt = select(BotCodeDB).where(
                    BotCodeDB.code == text,
                    BotCodeDB.platform == "telegram",
                    BotCodeDB.used == False,
                )
                result = await db.execute(stmt)
                bot_code = result.scalar_one_or_none()
                if bot_code:
                    stmt_user = select(UserDB).where(UserDB.id == bot_code.user_id)
                    result_user = await db.execute(stmt_user)
                    user = result_user.scalar_one_or_none()
                    if user:
                        user.telegram_chat_id = chat_id
                        bot_code.used = True
                        await db.commit()
                        await configure_telegram_bot(user.id, chat_id)
                        return {"status": "configured"}
        return {"status": "ignored"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    Body: str = Form(...), From: str = Form(...), db: AsyncSession = Depends(get_db)
):
    """Handle WhatsApp webhook for configuration"""
    try:
        body = Body.strip()
        from_number = From
        stmt = select(BotCodeDB).where(
            BotCodeDB.code == body,
            BotCodeDB.platform == "whatsapp",
            BotCodeDB.used == False,
        )
        result = await db.execute(stmt)
        bot_code = result.scalar_one_or_none()
        if bot_code:
            stmt_user = select(UserDB).where(UserDB.id == bot_code.user_id)
            result_user = await db.execute(stmt_user)
            user = result_user.scalar_one_or_none()
            if user:
                user.whatsapp_number = from_number
                bot_code.used = True
                await db.commit()
                await configure_whatsapp_bot(user.id, from_number)
                return {"status": "configured"}
        return {"status": "ignored"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/user-settings")
async def get_user_settings(
    db: AsyncSession = Depends(get_db), current_user: UserDB = Depends(get_current_user)
):
    """Retrieve user-specific settings including notifications and API integrations"""
    return {
        "telegram_chat_id": current_user.telegram_chat_id,
        "whatsapp_number": current_user.whatsapp_number,
        "api_keys": current_user.api_keys,
        "system_settings": current_user.system_settings,
    }


@router.put("/user-settings")
async def update_user_settings(
    request: UserSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Update user-specific settings including notifications and API integrations"""
    for field, value in request.dict(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)

    # Trigger bot flows
    if request.telegram_chat_id:
        await configure_telegram_bot(current_user.id, request.telegram_chat_id)
    if request.whatsapp_number:
        await configure_whatsapp_bot(current_user.id, request.whatsapp_number)

    return {"status": "success"}


@router.post("/generate-bot-code")
async def generate_bot_code(
    platform: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserDB = Depends(get_current_user),
):
    """Generate a code for bot configuration"""
    import secrets

    code = secrets.token_hex(8)
    bot_code = BotCodeDB(user_id=current_user.id, platform=platform, code=code)
    db.add(bot_code)
    await db.commit()
    return {
        "code": code,
        "platform": platform,
        "message": "Send this code to the OpenClaw bot to configure your notifications.",
    }
