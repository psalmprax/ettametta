from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
import os
from .utils.hardware_detector import hardware_detector


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "ettametta API"
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: Optional[str] = None  # Must be set via environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    INTERNAL_API_TOKEN: Optional[str] = None  # Master token for internal services
    AI_CLUSTER_SECRET: Optional[str] = "psalm_cluster_v1"  # Secret for remote GPU nodes
    PORT: int = 8000  # API port

    # AI Settings - Multi-Provider LLM Support
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    XAI_API_KEY: Optional[str] = None  # xAI (Grok)
    DEEPSEEK_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None  # Claude
    COHERE_API_KEY: Optional[str] = None  # Cohere - 20 RPM, 1K tokens/mo free
    MISTRAL_API_KEY: Optional[str] = None  # Mistral AI - 1 req/s, 1B tokens/mo free
    CEREBRAS_API_KEY: Optional[str] = None  # Cerebras - 30 RPM, 14,400 RPD free
    CLOUDFLARE_API_KEY: Optional[str] = None  # Cloudflare Workers AI
    CLOUDFLARE_ACCOUNT_ID: Optional[str] = None  # Cloudflare Account ID
    HUGGING_FACE_API_KEY: Optional[str] = None  # Hugging Face - $0.10/mo free credits
    OPENROUTER_API_KEY: Optional[str] = None  # OpenRouter - 50 RPD free, 1K with $10
    NVIDIA_API_KEY: Optional[str] = None  # NVIDIA NIM - 40 RPM free
    OLLAMA_CLOUD_API_KEY: Optional[str] = None  # Ollama Cloud
    SILICONFLOW_API_KEY: Optional[str] = None  # SiliconFlow - 1K RPM, 50K TPM free
    OLLAMA_URL: str = "http://localhost:11434"  # Local Ollama server
    LM_STUDIO_URL: str = "http://localhost:1234"  # Local LM Studio server
    DEFAULT_LLM_PROVIDER: str = "groq"  # groq, openai, xai, deepseek, anthropic, cohere, mistral, cerebras, cloudflare, huggingface, openrouter, nvidia, ollama_cloud, siliconflow, ollama, lm_studio

    USE_OS_MODELS: bool = True

    # Neural Asset Keys
    ELEVENLABS_API_KEY: Optional[str] = None
    FISH_SPEECH_ENDPOINT: str = "http://voiceover:8080"
    VOICE_ENGINE: str = "fish_speech"  # Options: elevenlabs, fish_speech
    MONETIZATION_MODE: str = "selective"  # Options: selective, all
    PEXELS_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_CX: Optional[str] = None  # Custom Search Engine ID for Google Search
    DEFAULT_VLM_MODEL: str = "gemini-1.5-flash"

    # Video Generation
    FONT_PATH: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    # Social API Keys
    YOUTUBE_API_KEY: Optional[str] = None
    TIKTOK_API_KEY: Optional[str] = None

    # Payment Processing
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # OAuth Credentials
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # TikTok keys might be loaded from env with slightly different names in some setups,
    # but we standardize here.
    TIKTOK_CLIENT_KEY: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[str] = None

    # Webhook Signatures
    YOUTUBE_WEBHOOK_SECRET: Optional[str] = None
    TIKTOK_WEBHOOK_SECRET: Optional[str] = None
    INSTAGRAM_WEBHOOK_SECRET: Optional[str] = None
    FACEBOOK_WEBHOOK_SECRET: Optional[str] = None
    LINKEDIN_WEBHOOK_SECRET: Optional[str] = None
    X_WEBHOOK_SECRET: Optional[str] = None

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_ADMIN_ID: int = 0

    # Shopify Configuration
    SHOPIFY_SHOP_URL: Optional[str] = None
    SHOPIFY_ACCESS_TOKEN: Optional[str] = None

    # Scraper Cookies (Bypass Bot Detection)
    YOUTUBE_COOKIES_PATH: Optional[str] = "cookies/youtube_cookies.txt"
    TIKTOK_COOKIES_PATH: Optional[str] = "cookies/tiktok_cookies.txt"

    # Infrastructure
    PRODUCTION_DOMAIN: str = "http://localhost:8000"
    API_URL: str = "http://api:8000"  # Internal service URL
    INTERNAL_API_TOKEN: Optional[str] = (
        None  # Token for internal service-to-service auth
    )
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8080"  # Comma-separated list
    )
    RENDER_NODE_URL: Optional[str] = None  # Colab/Remote GPU Node URL

    # ComfyUI Self-Hosting
    COMFYUI_URL: str = "http://220.135.0.171:8188"
    COMFYUI_WORKFLOWS_DIR: str = "services/video_engine/workflows"
    COMFYUI_MODELS_DIR: str = "services/video_engine/models"
    CLEANUP_TRANSIENT_MODELS: bool = True
    GPU_QUEUE_SLOTS: int = (
        1  # Concurrent generations allowed (auto-detected from hardware)
    )
    GPU_QUEUE_TIMEOUT: int = 300  # Seconds to wait for a slot
    GPU_OPTIMIZATION_LEVEL: str = "safe"  # safe, medium, extreme - affects VRAM usage
    GPU_FORCE_VRAM_GB: Optional[int] = (
        None  # Override auto-detected VRAM (for testing or manual config)
    )

    # Hardware detection (auto-populated)
    _detected_gpu_info: Dict[str, Any] = hardware_detector.get_gpu_info()

    # Rate Limiting (Requests per hour)
    LIMIT_FREE: int = 5
    LIMIT_PRO: int = 50
    LIMIT_SOVEREIGN: int = 500

    @property
    def DETECTED_GPU_VRAM_GB(self) -> Optional[int]:
        """Returns GPU VRAM (forced override or auto-detected)."""
        return self.GPU_FORCE_VRAM_GB or hardware_detector.vram_gb

    @property
    def EFFECTIVE_GPU_QUEUE_SLOTS(self) -> int:
        """
        Auto-calculate optimal concurrent jobs based on detected hardware and optimization level.
        Uses VRAM optimization guide recommendations and hardware-specific tuning.
        """
        # Use environment override if set
        env_slots = os.getenv("GPU_QUEUE_SLOTS")
        if env_slots:
            try:
                return max(1, int(env_slots))
            except ValueError:
                pass

        # Use hardware detector for optimal calculation
        return hardware_detector.calculate_optimal_slots(self.GPU_OPTIMIZATION_LEVEL)

    @property
    def GPU_HARDWARE_INFO(self) -> dict:
        """Returns detected GPU hardware information."""
        return self._detected_gpu_info

    @property
    def GOOGLE_AUTH_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/auth/callback/google"

    @property
    def GOOGLE_YOUTUBE_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/publish/auth/youtube/callback"

    @property
    def TIKTOK_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/publish/auth/tiktok/callback"

    @property
    def META_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/publish/auth/instagram/callback"

    @property
    def TWITTER_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/publish/auth/x/callback"

    @property
    def LINKEDIN_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/publish/auth/linkedin/callback"

    # Multi-Cloud Storage Engine
    STORAGE_PROVIDER: str = "LOCAL"  # Options: AWS, OCI, GCP, AZURE, CUSTOM, LOCAL
    STORAGE_ENDPOINT: Optional[str] = None
    STORAGE_BUCKET: str = ""
    STORAGE_ACCESS_KEY: Optional[str] = None
    STORAGE_SECRET_KEY: Optional[str] = None
    STORAGE_REGION: str = "us-east-1"

    # Sound Design (Tier 3 Enhancement)
    ENABLE_SOUND_DESIGN: bool = False
    SOUND_LIBRARY_PATH: str = "/var/lib/ettametta/sounds"
    MUSIC_VOLUME: float = 0.15
    SFX_VOLUME: float = 0.3

    # Motion Graphics (Tier 3 Enhancement)
    ENABLE_MOTION_GRAPHICS: bool = False
    MOTION_GRAPHICS_ENGINE: str = "local"  # local, cloud

    # AI Video Generation (Tier 3 Enhancement)
    AI_VIDEO_PROVIDER: str = (
        "none"  # none, zsky, kling, pixverse, replicate, runway, pika, stability
    )
    AI_VIDEO_FALLBACKS: str = ""
    RUNWAY_API_KEY: Optional[str] = None
    PIKA_API_KEY: Optional[str] = None
    ZSKY_API_KEY: Optional[str] = None  # ~50 credits/day
    KLING_API_KEY: Optional[str] = None  # ~100 credits/day
    PIXVERSE_API_KEY: Optional[str] = None  # ~20 credits/day
    REPLICATE_API_KEY: Optional[str] = None  # Free trial credits
    STABILITY_API_KEY: Optional[str] = None  # ~25 credits/day

    # Video Quality Tier (default processing level)
    DEFAULT_QUALITY_TIER: str = "standard"  # standard, enhanced, premium

    # Agent Frameworks (Optional - disabled by default)
    ENABLE_LANGCHAIN: bool = False
    ENABLE_CREWAI: bool = False
    ENABLE_INTERPRETER: bool = False
    ENABLE_AFFILIATE_API: bool = False
    ENABLE_TRADING: bool = True

    # opencli-rs Integration (per-user Chrome session bridge)
    ENABLE_OPENCLI: bool = False
    OPENCLI_BIN: str = "opencli"  # Path to opencli-rs binary
    OPENCLI_SESSIONS_DIR: str = "/tmp/opencli_sessions"  # Per-user session storage

    # Affiliate API Keys
    AMAZON_ASSOCIATES_TAG: Optional[str] = None
    AMAZON_PAAPI_KEY: Optional[str] = None
    AMAZON_PAAPI_TAG: Optional[str] = None
    IMPACT_RADIUS_API_KEY: Optional[str] = None
    SHAREASALE_API_KEY: Optional[str] = None

    # Trading API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    COINGECKO_API_KEY: Optional[str] = None

    # Twilio/WhatsApp Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None

    # Print-on-Demand
    PRINTFUL_API_KEY: Optional[str] = None

    # Email Marketing
    MAILCHIMP_API_KEY: Optional[str] = None
    MAILCHIMP_LIST_ID: Optional[str] = None
    CONVERTKIT_API_KEY: Optional[str] = None

    # LangChain Settings
    LANGCHAIN_MODEL: str = "llama-3.3-70b-versatile"
    LANGCHAIN_TEMPERATURE: float = 0.7

    # CrewAI Settings
    CREWAI_AGENTS: str = "researcher,writer,editor"

    # Deprecated (Keeping for backward sync during migration)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_STORAGE_BUCKET_NAME: Optional[str] = None

    # Database & Redis
    DATABASE_URL: str = "sqlite:///./ettametta.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Validation Warning
    def validate_critical_config(self):
        """
        Runs a mission-critical check of environment variables.
        Returns a dict with 'errors' (blocking) and 'warnings' (non-blocking).
        """
        from typing import Dict, List

        result = {"errors": [], "warnings": [], "info": []}

        # Production-specific checks (blocking errors)
        if self.ENV == "production":
            # OAuth Credentials
            if not self.GOOGLE_CLIENT_ID:
                result["errors"].append("GOOGLE_CLIENT_ID - Required for YouTube OAuth")
            if not self.GOOGLE_CLIENT_SECRET:
                result["errors"].append(
                    "GOOGLE_CLIENT_SECRET - Required for YouTube OAuth"
                )
            if not self.TIKTOK_CLIENT_KEY:
                result["errors"].append("TIKTOK_CLIENT_KEY - Required for TikTok OAuth")
            if not self.TIKTOK_CLIENT_SECRET:
                result["errors"].append(
                    "TIKTOK_CLIENT_SECRET - Required for TikTok OAuth"
                )

            # Security
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY.startswith("dev_")
                or len(self.SECRET_KEY) < 32
            ):
                result["errors"].append(
                    "SECRET_KEY - Must be set with 32+ characters in production"
                )

            # Domain
            if not self.PRODUCTION_DOMAIN or "localhost" in self.PRODUCTION_DOMAIN:
                result["errors"].append(
                    "PRODUCTION_DOMAIN - Must be set to production URL"
                )

            if not self.CORS_ORIGINS or "localhost" in self.CORS_ORIGINS:
                result["warnings"].append(
                    "CORS_ORIGINS - Contains localhost or is empty in production"
                )

            # Required for core functionality
            has_llm = any(
                [
                    self.GROQ_API_KEY,
                    self.OPENAI_API_KEY,
                    self.XAI_API_KEY,
                    self.DEEPSEEK_API_KEY,
                    self.ANTHROPIC_API_KEY,
                    self.GOOGLE_API_KEY,
                ]
            )
            if not has_llm:
                result["errors"].append(
                    "At least one LLM API key required: GROQ_API_KEY, OPENAI_API_KEY, XAI_API_KEY, DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY"
                )

        # Development warnings (non-blocking)
        else:
            # Warn if no LLM API keys are configured
            has_llm = any(
                [
                    self.GROQ_API_KEY,
                    self.OPENAI_API_KEY,
                    self.XAI_API_KEY,
                    self.DEEPSEEK_API_KEY,
                    self.ANTHROPIC_API_KEY,
                    self.GOOGLE_API_KEY,
                ]
            )
            if not has_llm:
                result["warnings"].append(
                    "No LLM API keys configured - AI features will use fallback mode. Set GROQ_API_KEY, OPENAI_API_KEY, XAI_API_KEY, DEEPSEEK_API_KEY, or ANTHROPIC_API_KEY"
                )

            # Warn if OAuth credentials missing
            if not self.GOOGLE_CLIENT_ID:
                result["warnings"].append(
                    "GOOGLE_CLIENT_ID not set - YouTube OAuth will not work"
                )
            if not self.TIKTOK_CLIENT_KEY:
                result["warnings"].append(
                    "TIKTOK_CLIENT_KEY not set - TikTok OAuth will not work"
                )

        # Optional service warnings
        if not self.ELEVENLABS_API_KEY and self.VOICE_ENGINE == "elevenlabs":
            result["warnings"].append(
                "ELEVENLABS_API_KEY not set - ElevenLabs voice engine unavailable"
            )

        if not self.PEXELS_API_KEY:
            result["info"].append(
                "PEXELS_API_KEY not set - Stock media will use fallback images"
            )

        if not self.STRIPE_SECRET_KEY:
            result["info"].append(
                "STRIPE_SECRET_KEY not set - Payment processing unavailable"
            )

        if not self.SHOPIFY_SHOP_URL:
            result["info"].append(
                "SHOPIFY_SHOP_URL not set - Commerce features unavailable"
            )

        # AWS S3 checks
        if self.STORAGE_PROVIDER == "AWS":
            if not self.AWS_ACCESS_KEY_ID:
                result["errors"].append(
                    "AWS_ACCESS_KEY_ID required when STORAGE_PROVIDER=AWS"
                )
            if not self.AWS_SECRET_ACCESS_KEY:
                result["errors"].append(
                    "AWS_SECRET_ACCESS_KEY required when STORAGE_PROVIDER=AWS"
                )
            if not self.AWS_STORAGE_BUCKET_NAME:
                result["errors"].append(
                    "AWS_STORAGE_BUCKET_NAME required when STORAGE_PROVIDER=AWS"
                )

        # Redis check
        if not self.REDIS_URL:
            result["errors"].append("REDIS_URL is required for Celery workers")

        # Database check
        if not self.DATABASE_URL:
            result["errors"].append("DATABASE_URL is required")

        # GPU Hardware Validation
        gpu_info = self.GPU_HARDWARE_INFO
        if gpu_info.get("device") != "cpu":
            if not gpu_info.get("detected"):
                result["warnings"].append(
                    "GPU VRAM auto-detection failed - using conservative defaults. Set GPU_QUEUE_SLOTS env var to override."
                )
            else:
                vram_gb = gpu_info.get("vram_gb")
                effective_slots = self.EFFECTIVE_GPU_QUEUE_SLOTS
                result["info"].append(
                    f"GPU detected: {gpu_info.get('gpu_name', 'Unknown')} ({vram_gb}GB VRAM) - allowing {effective_slots} concurrent video jobs"
                )

        return result

    def print_validation_report(self):
        """Print a formatted validation report."""
        validation = self.validate_critical_config()

        if validation["errors"]:
            print("\n" + "❌" * 40)
            print(f"🚨 CRITICAL ERRORS ({len(validation['errors'])}):")
            for err in validation["errors"]:
                print(f"   • {err}")
            print("❌" * 40 + "\n")

        if validation["warnings"]:
            print("\n" + "⚠️" * 40)
            print(f"⚠️  WARNINGS ({len(validation['warnings'])}):")
            for warn in validation["warnings"]:
                print(f"   • {warn}")
            print("⚠️" * 40 + "\n")

        if validation["info"]:
            print("\n" + "ℹ️" * 40)
            print(f"ℹ️  INFO ({len(validation['info'])}):")
            for info in validation["info"]:
                print(f"   • {info}")
            print("ℹ️" * 40 + "\n")

        # Summary
        total_issues = len(validation["errors"]) + len(validation["warnings"])
        if total_issues == 0:
            print("✅ All configuration checks passed!\n")
        else:
            print(
                f"📊 Configuration check complete: {len(validation['errors'])} errors, {len(validation['warnings'])} warnings\n"
            )

        return validation["errors"]

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True


settings = Settings()

# Apply VRAM override if specified
if settings.GPU_FORCE_VRAM_GB is not None:
    hardware_detector.set_vram_override(settings.GPU_FORCE_VRAM_GB)

# Immediate startup validation
validation = settings.validate_critical_config()
if validation["errors"] or validation["warnings"]:
    settings.print_validation_report()
