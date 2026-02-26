from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "ettametta API"
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: Optional[str] = None  # Must be set via environment variable
    ALGORITHM: str = "HS256"
    INTERNAL_API_TOKEN: Optional[str] = None # Master token for internal services

    # AI Settings
    GROQ_API_KEY: str = ""
    USE_OS_MODELS: bool = True
    
    # Neural Asset Keys
    ELEVENLABS_API_KEY: str = ""
    FISH_SPEECH_ENDPOINT: str = "http://voiceover:8080"
    VOICE_ENGINE: str = "fish_speech" # Options: elevenlabs, fish_speech
    MONETIZATION_MODE: str = "selective" # Options: selective, all
    PEXELS_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_SEARCH_CX: str = ""  # Custom Search Engine ID for Google Search
    DEFAULT_VLM_MODEL: str = "gemini-1.5-flash"
    
    # Video Generation
    FONT_PATH: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    # Social API Keys
    YOUTUBE_API_KEY: str = ""
    TIKTOK_API_KEY: str = ""
    
    # Payment Processing
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # OAuth Credentials
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # TikTok keys might be loaded from env with slightly different names in some setups, 
    # but we standardize here.
    TIKTOK_CLIENT_KEY: str = ""
    TIKTOK_CLIENT_SECRET: str = ""
    
    # Shopify Configuration
    SHOPIFY_SHOP_URL: str = ""
    SHOPIFY_ACCESS_TOKEN: str = ""
    
    # Scraper Cookies (Bypass Bot Detection)
    YOUTUBE_COOKIES_PATH: Optional[str] = "cookies/youtube_cookies.txt"
    TIKTOK_COOKIES_PATH: Optional[str] = "cookies/tiktok_cookies.txt"
    
    # Infrastructure
    PRODUCTION_DOMAIN: str = "http://localhost:8000"
    RENDER_NODE_URL: Optional[str] = None # Colab/Remote GPU Node URL
    
    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/publish/auth/youtube/callback"

    @property
    def TIKTOK_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/publish/auth/tiktok/callback"
    
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
    AI_VIDEO_PROVIDER: str = "none"  # none, runway, pika
    RUNWAY_API_KEY: str = ""
    PIKA_API_KEY: str = ""
    
    # Video Quality Tier (default processing level)
    DEFAULT_QUALITY_TIER: str = "standard"  # standard, enhanced, premium
    
    # Agent Frameworks (Optional - disabled by default)
    ENABLE_LANGCHAIN: bool = False
    ENABLE_CREWAI: bool = False
    ENABLE_INTERPRETER: bool = False
    ENABLE_AFFILIATE_API: bool = False
    ENABLE_TRADING: bool = False
    
    # Affiliate API Keys
    AMAZON_ASSOCIATES_TAG: str = ""
    IMPACT_RADIUS_API_KEY: str = ""
    SHAREASALE_API_KEY: str = ""
    
    # Trading API Keys
    ALPHA_VANTAGE_API_KEY: str = ""
    COINGECKO_API_KEY: str = ""
    
    # Twilio/WhatsApp Configuration
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""
    
    # LangChain Settings
    LANGCHAIN_MODEL: str = "llama-3.3-70b-versatile"
    LANGCHAIN_TEMPERATURE: float = 0.7
    
    # CrewAI Settings
    CREWAI_AGENTS: str = "researcher,writer,editor"
    
    # Deprecated (Keeping for backward sync during migration)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_STORAGE_BUCKET_NAME: str = ""

    # Database & Redis
    DATABASE_URL: str = "sqlite:///./ettametta.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Validation Warning
    def validate_critical_config(self):
        """
        Runs a mission-critical check of environment variables.
        """
        missing_critical = []
        if self.ENV == "production":
            if not self.GOOGLE_CLIENT_ID: missing_critical.append("GOOGLE_CLIENT_ID")
            if not self.TIKTOK_CLIENT_KEY: missing_critical.append("TIKTOK_CLIENT_KEY")
            if self.SECRET_KEY.startswith("dev_"): missing_critical.append("SECRET_KEY (insecure)")
            if "localhost" in self.PRODUCTION_DOMAIN: missing_critical.append("PRODUCTION_DOMAIN (pointing to localhost)")
            
        return missing_critical

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True

settings = Settings()

# Immediate startup validation
warnings = settings.validate_critical_config()
if warnings:
    print("\n" + "!" * 80)
    print(f"⚠️ CONFIGURATION ALERT: Detected {len(warnings)} critical gaps for {settings.ENV} mode")
    for w in warnings:
        print(f"  - {w}")
    print("!" * 80 + "\n")
