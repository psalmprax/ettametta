from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict
from typing import Any
import os
import logging
from pathlib import Path
from src.api.utils.hardware_detector import hardware_detector
from src.api.config.validation import validate_critical_config, print_validation_report

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # Base Directories (Dynamic Portability)
    BASE_DIR: Path = Path(__file__).parent.parent.parent.parent
    REMOTION_APP_DIR: Path = (
        Path(__file__).parent.parent.parent.parent / "apps/remotion-studio"
    )
    REMOTION_OUTPUT_DIR: Path = Path(__file__).parent.parent.parent.parent / "outputs"

    # App Settings
    APP_NAME: str = "Ettametta API"
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str | None = None  # Must be set via environment variable
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    INTERNAL_API_TOKEN: str | None = None  # Master token for internal services
    AI_CLUSTER_SECRET: str | None = None  # Must be set for cluster/gateway operations
    PORT: int = 8000  # API port

    # Lean Infrastructure (CPU-First Hardening)
    CPU_AUTODETECT_THREADS: bool = True
    RESOURCE_CONSTRAINED_MODE: bool = False  # Set to True for small VPS (e.g. 2GB RAM)
    REMOTION_STUDIO_PATH: str = "apps/remotion-studio"
    REMOTION_CONCURRENCY_LIMIT: int = 2  # Max simultaneous rendering processes
    
    # Resilience Settings (Global Hardening)
    DEFAULT_TIMEOUT: int = 60
    LLM_TIMEOUT: int = 300
    VIDEO_GEN_TIMEOUT: int = 600
    VOICEOVER_TIMEOUT: int = 30
    SEARCH_TIMEOUT: int = 30
    STOCK_TIMEOUT: int = 30
    REMOTION_TIMEOUT_SECONDS: int = 2400  # 40 min — CPU rendering 1500+ frames at 0.75 scale needs 30-40 min
    NEXUS_COMPOSE_TIMEOUT: int = 600  # 10 min global timeout for compose background task
    DEFAULT_RETRY_COUNT: int = 3
    RETRY_MULTIPLIER: int = 1
    RETRY_MIN_WAIT: int = 2
    RETRY_MAX_WAIT: int = 10

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
    OLLAMA_URL: str = "http://ettametta-ollama:11434"  # Local Ollama server (Docker service)
    OLLAMA_MODEL: str = "llama3.2:1b"  # 1B model — 2-3x faster than 3b on CPU
    LM_STUDIO_URL: str = "http://localhost:1234"  # Local LM Studio server
    DEFAULT_LLM_PROVIDER: str = "ollama"  # groq, openai, xai, deepseek, anthropic, cohere, mistral, cerebras, cloudflare, huggingface, openrouter, nvidia, ollama_cloud, siliconflow, ollama, lm_studio, dify
    FALLBACK_LLM_PROVIDER: str = "openai"

    # Dify AI Orchestration
    DIFY_API_URL: str = "http://localhost:7200/api/v1"
    DIFY_API_KEY: str | None = None
    DIFY_DATASET_API_KEY: str | None = None
    DIFY_TIMEOUT: int = 120

    USE_OS_MODELS: bool = True
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    TRANSCRIPTION_TIMEOUT: int = 300

    # Neural Asset Keys
    ELEVENLABS_API_KEY: str | None = None
    FISH_SPEECH_ENDPOINT: str = "http://voiceover:8080"
    VOICE_ENGINE: str = "gtts"  # Options: elevenlabs, fish_speech, gtts (gtts works without API key)
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

    @field_validator("TELEGRAM_ADMIN_ID", mode="before")
    @classmethod
    def parse_admin_id(cls, v: Any) -> int:
        if isinstance(v, str) and v.strip() == "":
            return 0
        try:
            return int(v) if v else 0
        except (ValueError, TypeError):
            return 0

    # Shopify Configuration
    SHOPIFY_SHOP_URL: str | None = None
    SHOPIFY_ACCESS_TOKEN: str | None = None

    # Scraper Cookies (Bypass Bot Detection)
    COOKIES_DIR: str = "data/storage/cookies"
    YOUTUBE_COOKIES_PATH: str | None = "data/storage/cookies/youtube_cookies.txt"
    TIKTOK_COOKIES_PATH: str | None = "data/storage/cookies/tiktok_cookies.txt"

    # Infrastructure
    PRODUCTION_DOMAIN: str = "http://localhost:8000"
    API_URL: str = "http://api:8000"  # Internal service URL
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:8080"  # Comma-separated list
    )
    RENDER_NODE_URL: str | None = None  # Colab/Remote GPU Node URL

    # ComfyUI Self-Hosting
    COMFYUI_URL: str = "http://localhost:8188"
    COMFYUI_WORKFLOWS_DIR: str = "services/video_engine/workflows"
    COMFYUI_MODELS_DIR: str = "services/video_engine/models"
    STORAGE_OUTPUT_DIR: str = "data/storage/outputs"
    REMOTE_STORAGE_OUTPUT_DIR: str = "/workspace/outputs"
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
    LIMIT_FREE: int = 100
    LIMIT_PRO: int = 500
    LIMIT_SOVEREIGN: int = 5000

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
        """Google OAuth callback for general authentication (standard account login)."""
        base = self.PRODUCTION_DOMAIN.rstrip('/')
        if base.endswith("/api/v1"):
            return f"{base}/auth/callback/google"
        return f"{base}/api/v1/auth/callback/google"

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
    LUMA_API_KEY: str | None = None  # Luma Ray API key (Phase 13)
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

    def validate_critical_config(self):
        """Delegate to standalone validation function."""
        return validate_critical_config(self)

    def print_validation_report(self):
        """Delegate to standalone validation logging function."""
        return print_validation_report(self)

    model_config = ConfigDict(env_file=".env", extra="ignore", case_sensitive=True)


settings = Settings()

# Apply VRAM override if specified
if settings.GPU_FORCE_VRAM_GB is not None:
    hardware_detector.set_vram_override(settings.GPU_FORCE_VRAM_GB)

# Immediate startup validation
validation = settings.validate_critical_config()
if validation["errors"] or validation["warnings"]:
    settings.print_validation_report()
