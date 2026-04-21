from pydantic_settings import BaseSettings
from typing import Any
import os
from pathlib import Path
from .utils.hardware_detector import hardware_detector


class Settings(BaseSettings):
    # Base Directories (Dynamic Portability)
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    REMOTION_APP_DIR: Path = (
        Path(__file__).parent.parent.parent / "apps/remotion-studio"
    )
    OUTPUT_DIR: Path = Path(__file__).parent.parent.parent / "outputs"

    # App Settings
    APP_NAME: str = "Ettametta API"
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str | None = None  # Must be set via environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    INTERNAL_API_TOKEN: str | None = None  # Master token for internal services
    AI_CLUSTER_SECRET: str | None = "psalm_cluster_v1"  # Secret for remote GPU nodes
    PORT: int = 8000  # API port

    # Lean Infrastructure (CPU-First Hardening)
    CPU_AUTODETECT_THREADS: bool = True
    RESOURCE_CONSTRAINED_MODE: bool = False  # Set to True for small VPS (e.g. 2GB RAM)
    REMOTION_STUDIO_PATH: str = "apps/remotion-studio"

    # AI Settings - Multi-Provider LLM Support
    GROQ_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    XAI_API_KEY: str | None = None  # xAI (Grok)
    DEEPSEEK_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None  # Claude
    COHERE_API_KEY: str | None = None  # Cohere - 20 RPM, 1K tokens/mo free
    MISTRAL_API_KEY: str | None = None  # Mistral AI - 1 req/s, 1B tokens/mo free
    CEREBRAS_API_KEY: str | None = None  # Cerebras - 30 RPM, 14,400 RPD free
    CLOUDFLARE_API_KEY: str | None = None  # Cloudflare Workers AI
    CLOUDFLARE_ACCOUNT_ID: str | None = None  # Cloudflare Account ID
    HUGGING_FACE_API_KEY: str | None = None  # Hugging Face - $0.10/mo free credits
    OPENROUTER_API_KEY: str | None = None  # OpenRouter - 50 RPD free, 1K with $10
    NVIDIA_API_KEY: str | None = None  # NVIDIA NIM - 40 RPM free
    OLLAMA_CLOUD_API_KEY: str | None = None  # Ollama Cloud
    SILICONFLOW_API_KEY: str | None = None  # SiliconFlow - 1K RPM, 50K TPM free
    OLLAMA_URL: str = "http://localhost:11434"  # Local Ollama server
    OLLAMA_MODEL: str = "llama3"  # Default model for Ollama
    LM_STUDIO_URL: str = "http://localhost:1234"  # Local LM Studio server
    DEFAULT_LLM_PROVIDER: str = "ollama"  # groq, openai, xai, deepseek, anthropic, cohere, mistral, cerebras, cloudflare, huggingface, openrouter, nvidia, ollama_cloud, siliconflow, ollama, lm_studio

    USE_OS_MODELS: bool = True

    # Neural Asset Keys
    ELEVENLABS_API_KEY: str | None = None
    FISH_SPEECH_ENDPOINT: str = "http://voiceover:8080"
    VOICE_ENGINE: str = "fish_speech"  # Options: elevenlabs, fish_speech
    MONETIZATION_MODE: str = "selective"  # Options: selective, all
    PEXELS_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None
    GOOGLE_SEARCH_CX: str | None = None  # Custom Search Engine ID for Google Search
    DEFAULT_VLM_MODEL: str = "gemini-1.5-flash"

    # Video Generation
    FONT_PATH: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    # Social API Keys
    YOUTUBE_API_KEY: str | None = None
    TIKTOK_API_KEY: str | None = None
    DOWNLOAD_PROXY_URL: str | None = None  # Resilient Proxy Gateway

    # Payment Processing
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    # OAuth Credentials
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

    # TikTok keys might be loaded from env with slightly different names in some setups,
    # but we standardize here.
    TIKTOK_CLIENT_KEY: str | None = None
    TIKTOK_CLIENT_SECRET: str | None = None

    # Webhook Signatures
    YOUTUBE_WEBHOOK_SECRET: str | None = None
    TIKTOK_WEBHOOK_SECRET: str | None = None
    INSTAGRAM_WEBHOOK_SECRET: str | None = None
    FACEBOOK_WEBHOOK_SECRET: str | None = None
    LINKEDIN_WEBHOOK_SECRET: str | None = None
    X_WEBHOOK_SECRET: str | None = None

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_ADMIN_ID: int = 0

    # Shopify Configuration
    SHOPIFY_SHOP_URL: str | None = None
    SHOPIFY_ACCESS_TOKEN: str | None = None

    # Scraper Cookies (Bypass Bot Detection)
    YOUTUBE_COOKIES_PATH: str | None = "cookies/youtube_cookies.txt"
    TIKTOK_COOKIES_PATH: str | None = "cookies/tiktok_cookies.txt"

    # Infrastructure
    PRODUCTION_DOMAIN: str = "http://localhost:8000"
    API_URL: str = "http://api:8000"  # Internal service URL
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8080"  # Comma-separated list
    )
    RENDER_NODE_URL: str | None = None  # Colab/Remote GPU Node URL

    # ComfyUI Self-Hosting
    COMFYUI_URL: str = "http://220.135.0.171:8188"
    COMFYUI_WORKFLOWS_DIR: str = "services/video_engine/workflows"
    COMFYUI_MODELS_DIR: str = "services/video_engine/models"
    VIDEO_OUTPUTS_DIR: str = "data/storage/outputs"
    REMOTE_VIDEO_OUTPUTS_DIR: str = "/workspace/outputs"
    CLEANUP_TRANSIENT_MODELS: bool = True
    GPU_QUEUE_SLOTS: int = (
        1  # Concurrent generations allowed (auto-detected from hardware)
    )
    GPU_QUEUE_TIMEOUT: int = 300  # Seconds to wait for a slot
    GPU_OPTIMIZATION_LEVEL: str = "safe"  # safe, medium, extreme - affects VRAM usage
    GPU_FORCE_VRAM_GB: int | None = (
        None  # Override auto-detected VRAM (for testing or manual config)
    )

    # Video Provider Credentials (for browser automation)
    PIXVERSE_EMAIL: str | None = None
    PIXVERSE_PASSWORD: str | None = None
    KLING_EMAIL: str | None = None
    KLING_PASSWORD: str | None = None
    HAIPER_EMAIL: str | None = None
    HAIPER_PASSWORD: str | None = None
    LUMA_EMAIL: str | None = None
    LUMA_PASSWORD: str | None = None
    RUNWAY_EMAIL: str | None = None
    RUNWAY_PASSWORD: str | None = None
    PIKA_EMAIL: str | None = None
    PIKA_PASSWORD: str | None = None

    # Hardware detection (auto-populated)
    _detected_gpu_info: dict[str, Any] = hardware_detector.get_gpu_info()

    # Rate Limiting (Requests per hour)
    LIMIT_FREE: int = 5
    LIMIT_PRO: int = 50
    LIMIT_SOVEREIGN: int = 500

    @property
    def DETECTED_GPU_VRAM_GB(self) -> int | None:
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
    def GOOGLE_OAUTH_REDIRECT_URI(self) -> str:
        """Google OAuth callback for general login (non-YouTube specific)."""
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
    STORAGE_ENDPOINT: str | None = None
    STORAGE_BUCKET: str = ""
    STORAGE_ACCESS_KEY: str | None = None
    STORAGE_SECRET_KEY: str | None = None
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
    RUNWAY_API_KEY: str | None = None
    PIKA_API_KEY: str | None = None
    ZSKY_API_KEY: str | None = None  # ~50 credits/day
    KLING_API_KEY: str | None = None  # ~100 credits/day
    PIXVERSE_API_KEY: str | None = None  # ~20 credits/day
    REPLICATE_API_KEY: str | None = None  # Free trial credits
    STABILITY_API_KEY: str | None = None  # ~25 credits/day

    # Video Quality Tier (default processing level)
    DEFAULT_QUALITY_TIER: str = "standard"  # standard, enhanced, premium

    # Agent Frameworks (Any - disabled by default)
    ENABLE_LANGCHAIN: bool = False
    ENABLE_CREWAI: bool = False
    ENABLE_INTERPRETER: bool = False
    ENABLE_AFFILIATE_API: bool = False

    # opencli-rs Integration (per-user Chrome session bridge)
    ENABLE_OPENCLI: bool = False
    OPENCLI_BIN: str = "opencli"  # Path to opencli-rs binary
    OPENCLI_SESSIONS_DIR: str = "/tmp/opencli_sessions"  # Per-user session storage

    # Affiliate API Keys
    AMAZON_ASSOCIATES_TAG: str | None = None
    AMAZON_PAAPI_KEY: str | None = None
    AMAZON_PAAPI_TAG: str | None = None
    IMPACT_RADIUS_API_KEY: str | None = None
    SHAREASALE_API_KEY: str | None = None

    # Monetization
    ENABLE_MONETIZATION: bool = True

    # Twilio/WhatsApp Configuration
    TWILIO_ACCOUNT_SID: str | None = None
    TWILIO_AUTH_TOKEN: str | None = None
    TWILIO_WHATSAPP_NUMBER: str | None = None

    # Print-on-Demand
    PRINTFUL_API_KEY: str | None = None

    # Email Marketing
    MAILCHIMP_API_KEY: str | None = None
    MAILCHIMP_LIST_ID: str | None = None
    CONVERTKIT_API_KEY: str | None = None

    # LangChain Settings
    MODEL: str = "llama-3.3-70b-versatile"
    LANGCHAIN_MODEL: str = "llama-3.3-70b-versatile"
    LANGCHAIN_TEMPERATURE: float = 0.7

    # CrewAI Settings
    CREWAI_AGENTS: str = "researcher,writer,editor"

    # Deprecated (Keeping for backward sync during migration)
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str = "us-east-1"
    AWS_STORAGE_BUCKET_NAME: str | None = None

    # Database & Redis
    DATABASE_URL: str = "sqlite:///./data/db/ettametta.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Validation Warning
    def validate_critical_config(self):
        """
        Runs a mission-critical check of environment variables.
        Returns a dict with 'errors' (blocking) and 'warnings' (non-blocking).
        """

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

        # Any service warnings
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
