import logging
from typing import Any

logger = logging.getLogger(__name__)

MISSING_LLM_KEYS = (
    "GROQ_API_KEY, OPENAI_API_KEY, XAI_API_KEY, DEEPSEEK_API_KEY, "
    "ANTHROPIC_API_KEY, GOOGLE_API_KEY, or DIFY_API_KEY"
)

NO_LLM_KEYS_WARNING = "LLM key required: set GROQ, OPENAI, XAI, DEEPSEEK, or ANTHROPIC"
SECRET_KEY_MIN = 32
SECRET_KEY_MSG = "SECRET_KEY - Must be set with 32+ characters in production"


def validate_critical_config(settings: Any) -> dict:
    """
    Runs a mission-critical check of environment variables.
    Returns a dict with 'errors' (blocking) and 'warnings' (non-blocking).
    """
    result = {"errors": [], "warnings": [], "info": []}

    # Production-specific checks (blocking errors)
    if settings.ENV == "production":
        # OAuth Credentials
        if not settings.GOOGLE_CLIENT_ID:
            result["errors"].append("GOOGLE_CLIENT_ID - Required for YouTube OAuth")
        if not settings.GOOGLE_CLIENT_SECRET:
            result["errors"].append(
                "GOOGLE_CLIENT_SECRET - Required for YouTube OAuth"
            )
        if not settings.TIKTOK_CLIENT_KEY:
            result["errors"].append("TIKTOK_CLIENT_KEY - Required for TikTok OAuth")
        if not settings.TIKTOK_CLIENT_SECRET:
            result["errors"].append(
                "TIKTOK_CLIENT_SECRET - Required for TikTok OAuth"
            )

        # Security
        if (
            not settings.SECRET_KEY
            or settings.SECRET_KEY.startswith("dev_")
            or len(settings.SECRET_KEY) < 32
        ):
            result["errors"].append(SECRET_KEY_MSG)

        # Domain
        if not settings.PRODUCTION_DOMAIN or "localhost" in settings.PRODUCTION_DOMAIN:
            result["errors"].append(
                "PRODUCTION_DOMAIN - Must be set to production URL"
            )

        if not settings.CORS_ORIGINS or "localhost" in settings.CORS_ORIGINS:
            result["warnings"].append(
                "CORS_ORIGINS - Contains localhost or is empty in production"
            )

        # Required for core functionality
        has_llm = any(
            [
                settings.GROQ_API_KEY,
                settings.OPENAI_API_KEY,
                settings.XAI_API_KEY,
                settings.DEEPSEEK_API_KEY,
                settings.ANTHROPIC_API_KEY,
                settings.GOOGLE_API_KEY,
            ]
        )
        if not has_llm and not settings.DIFY_API_KEY:
            result["errors"].append(
                f"At least one LLM API key required: "
                f"{MISSING_LLM_KEYS}"
            )

    # Development warnings (non-blocking)
    else:
        # Warn if no LLM API keys are configured
        has_llm = any(
            [
                settings.GROQ_API_KEY,
                settings.OPENAI_API_KEY,
                settings.XAI_API_KEY,
                settings.DEEPSEEK_API_KEY,
                settings.ANTHROPIC_API_KEY,
                settings.GOOGLE_API_KEY,
            ]
        )
        if not has_llm:
            result["warnings"].append(NO_LLM_KEYS_WARNING)

        # Warn if OAuth credentials missing
        if not settings.GOOGLE_CLIENT_ID:
            result["warnings"].append(
                "GOOGLE_CLIENT_ID not set - YouTube OAuth will not work"
            )
        if not settings.TIKTOK_CLIENT_KEY:
            result["warnings"].append(
                "TIKTOK_CLIENT_KEY not set - TikTok OAuth will not work"
            )

    # Any service warnings
    if not settings.ELEVENLABS_API_KEY and settings.VOICE_ENGINE == "elevenlabs":
        result["warnings"].append(
            "ELEVENLABS_API_KEY not set - ElevenLabs voice engine unavailable"
        )

    if not settings.PEXELS_API_KEY:
        result["info"].append(
            "PEXELS_API_KEY not set - Stock media will use fallback images"
        )

    if not settings.STRIPE_SECRET_KEY:
        result["info"].append(
            "STRIPE_SECRET_KEY not set - Payment processing unavailable"
        )

    if not settings.SHOPIFY_SHOP_URL:
        result["info"].append(
            "SHOPIFY_SHOP_URL not set - Commerce features unavailable"
        )

    # AWS S3 checks
    if settings.STORAGE_PROVIDER == "AWS":
        if not settings.AWS_ACCESS_KEY_ID:
            result["errors"].append(
                "AWS_ACCESS_KEY_ID required when STORAGE_PROVIDER=AWS"
            )
        if not settings.AWS_SECRET_ACCESS_KEY:
            result["errors"].append(
                "AWS_SECRET_ACCESS_KEY required when STORAGE_PROVIDER=AWS"
            )
        if not settings.AWS_STORAGE_BUCKET_NAME:
            result["errors"].append(
                "AWS_STORAGE_BUCKET_NAME required when STORAGE_PROVIDER=AWS"
            )

    # Redis check
    if not settings.REDIS_URL:
        result["errors"].append("REDIS_URL is required for Celery workers")

    # Database check
    if not settings.DATABASE_URL:
        result["errors"].append("DATABASE_URL is required")

    # GPU Hardware Validation
    gpu_info = settings.GPU_HARDWARE_INFO
    if gpu_info.get("device") != "cpu":
        if not gpu_info.get("detected"):
            result["warnings"].append(
                "GPU VRAM auto-detection failed. Set GPU_QUEUE_SLOTS to override."
            )
        else:
            vram_gb = gpu_info.get("vram_gb")
            effective_slots = settings.EFFECTIVE_GPU_QUEUE_SLOTS
            result["info"].append(
                f"GPU detected: {gpu_info.get('gpu_name', '?')} ({vram_gb}GB) - "
                f"{effective_slots} concurrent video jobs allowed"
            )

    return result


def print_validation_report(settings: Any) -> list:
    """Log a formatted validation report."""
    validation = validate_critical_config(settings)

    if validation["errors"]:
        logger.error(
            f"🚨 CRITICAL ERRORS ({len(validation['errors'])}): "
            + " | ".join(validation["errors"])
        )

    if validation["warnings"]:
        logger.warning(
            f"⚠️  WARNINGS ({len(validation['warnings'])}): "
            + " | ".join(validation["warnings"])
        )

    if validation["info"]:
        logger.info(
            f"ℹ️  INFO ({len(validation['info'])}): "
            + " | ".join(validation["info"])
        )

    # Summary
    total_issues = len(validation["errors"]) + len(validation["warnings"])
    if total_issues == 0:
        logger.info("✅ All configuration checks passed!")
    else:
        logger.warning(
            f"📊 Configuration check complete: {len(validation['errors'])} errors, "
            f"{len(validation['warnings'])} warnings"
        )

    return validation["errors"]
