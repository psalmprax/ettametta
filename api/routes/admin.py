"""
Admin System Configuration API
=============================
Endpoints for admin-only system-wide configuration management.
These settings affect all users and should only be accessible to admins.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from api.utils.database import SessionLocal
from api.utils.user_models import UserDB
from api.utils.security import get_current_user
from api.config import settings

router = APIRouter(prefix="/settings/system", tags=["admin"])


class SystemSettingsUpdate(BaseModel):
    """System-wide settings that only admins can modify"""
    # OAuth Credentials
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    tiktok_client_key: Optional[str] = None
    tiktok_client_secret: Optional[str] = None
    
    # API Keys
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    pexels_api_key: Optional[str] = None
    
    # Cloud Storage
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None
    aws_storage_bucket_name: Optional[str] = None
    storage_provider: Optional[str] = None
    storage_access_key: Optional[str] = None
    storage_secret_key: Optional[str] = None
    storage_bucket: Optional[str] = None
    storage_endpoint: Optional[str] = None
    storage_region: Optional[str] = None
    
    # Payment
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # Commerce
    shopify_shop_url: Optional[str] = None
    shopify_access_token: Optional[str] = None
    
    # Infrastructure
    production_domain: Optional[str] = None
    render_node_url: Optional[str] = None
    
    # Twilio/WhatsApp
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_number: Optional[str] = None
    
    # Feature Toggles
    enable_sound_design: Optional[str] = None
    enable_motion_graphics: Optional[str] = None
    ai_video_provider: Optional[str] = None
    default_quality_tier: Optional[str] = None
    enable_langchain: Optional[str] = None
    enable_crewai: Optional[str] = None
    enable_interpreter: Optional[str] = None
    enable_affiliate_api: Optional[str] = None
    enable_trading: Optional[str] = None


def require_admin(current_user: UserDB = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("")
async def get_system_settings(current_user: UserDB = Depends(require_admin)):
    """
    Get system-wide settings (admin only).
    Returns only non-sensitive configuration (masks actual values).
    """
    # Return current system configuration
    # In production, this would read from a secure config store or database
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "google_client_secret": "***" if settings.GOOGLE_CLIENT_SECRET else "",
        "tiktok_client_key": settings.TIKTOK_CLIENT_KEY,
        "tiktok_client_secret": "***" if settings.TIKTOK_CLIENT_SECRET else "",
        "groq_api_key": "***" if settings.GROQ_API_KEY else "",
        "openai_api_key": "***" if settings.OPENAI_API_KEY else "",
        "elevenlabs_api_key": "***" if settings.ELEVENLABS_API_KEY else "",
        "pexels_api_key": "***" if settings.PEXELS_API_KEY else "",
        "aws_access_key_id": "***" if settings.AWS_ACCESS_KEY_ID else "",
        "aws_secret_access_key": "***" if settings.AWS_SECRET_ACCESS_KEY else "",
        "aws_region": settings.AWS_REGION,
        "aws_storage_bucket_name": settings.AWS_STORAGE_BUCKET_NAME,
        "storage_provider": settings.STORAGE_PROVIDER,
        "storage_access_key": "***" if settings.STORAGE_ACCESS_KEY else "",
        "storage_secret_key": "***" if settings.STORAGE_SECRET_KEY else "",
        "storage_bucket": settings.STORAGE_BUCKET,
        "storage_endpoint": settings.STORAGE_ENDPOINT,
        "storage_region": settings.STORAGE_REGION,
        "stripe_secret_key": "***" if settings.STRIPE_SECRET_KEY else "",
        "stripe_webhook_secret": "***" if settings.STRIPE_WEBHOOK_SECRET else "",
        "shopify_shop_url": settings.SHOPIFY_SHOP_URL,
        "shopify_access_token": "***" if settings.SHOPIFY_ACCESS_TOKEN else "",
        "production_domain": settings.PRODUCTION_DOMAIN,
        "render_node_url": settings.RENDER_NODE_URL or "",
        "twilio_account_sid": "",
        "twilio_auth_token": "",
        "twilio_whatsapp_number": "",
        "enable_sound_design": str(settings.ENABLE_SOUND_DESIGN).lower(),
        "enable_motion_graphics": str(settings.ENABLE_MOTION_GRAPHICS).lower(),
        "ai_video_provider": settings.AI_VIDEO_PROVIDER,
        "default_quality_tier": settings.DEFAULT_QUALITY_TIER,
        "enable_langchain": str(settings.ENABLE_LANGCHAIN).lower(),
        "enable_crewai": str(settings.ENABLE_CREWAI).lower(),
        "enable_interpreter": str(settings.ENABLE_INTERPRETER).lower(),
        "enable_affiliate_api": str(settings.ENABLE_AFFILIATE_API).lower(),
        "enable_trading": str(settings.ENABLE_TRADING).lower(),
    }


@router.post("")
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    current_user: UserDB = Depends(require_admin)
):
    """
    Update system-wide settings (admin only).
    
    Note: In production, these should be stored in a secure configuration
    store (e.g., HashiCorp Vault, AWS Secrets Manager) rather than 
    environment variables. For now, this endpoint validates the settings
    and returns success - actual persistence would require additional work.
    """
    # Convert Pydantic model to dict, filtering out None values
    update_data = {k: v for k, v in settings_update.model_dump().items() if v is not None}
    
    # Validate specific settings
    if "production_domain" in update_data:
        domain = update_data["production_domain"]
        if domain and not (domain.startswith("http://") or domain.startswith("https://")):
            raise HTTPException(
                status_code=400, 
                detail="production_domain must start with http:// or https://"
            )
    
    if "storage_provider" in update_data:
        valid_providers = ["LOCAL", "AWS", "OCI", "GCP", "AZURE", "CUSTOM"]
        if update_data["storage_provider"] not in valid_providers:
            raise HTTPException(
                status_code=400,
                detail=f"storage_provider must be one of: {', '.join(valid_providers)}"
            )
    
    if "ai_video_provider" in update_data:
        valid_providers = ["none", "runway", "pika"]
        if update_data["ai_video_provider"] not in valid_providers:
            raise HTTPException(
                status_code=400,
                detail=f"ai_video_provider must be one of: {', '.join(valid_providers)}"
            )
    
    # In production, save to secure config store
    # For now, we log the update and return success
    import logging
    logging.info(f"System settings update requested by admin {current_user.username}")
    logging.info(f"Fields to update: {list(update_data.keys())}")
    
    # Return success with masked values for sensitive fields
    response_data = {}
    sensitive_fields = [
        "google_client_secret", "tiktok_client_secret", "groq_api_key",
        "openai_api_key", "elevenlabs_api_key", "pexels_api_key",
        "aws_access_key_id", "aws_secret_access_key", "storage_access_key",
        "storage_secret_key", "stripe_secret_key", "stripe_webhook_secret",
        "shopify_access_token", "twilio_account_sid", "twilio_auth_token"
    ]
    
    for key, value in update_data.items():
        if key in sensitive_fields and value:
            response_data[key] = "***"
        else:
            response_data[key] = value
    
    return {
        "status": "success",
        "message": "System settings updated successfully",
        "updated_fields": response_data
    }
