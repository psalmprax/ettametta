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
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080" # Comma-separated list
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
        Returns a dict with 'errors' (blocking) and 'warnings' (non-blocking).
        """
        from typing import Dict, List
        
        result = {
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # Production-specific checks (blocking errors)
        if self.ENV == "production":
            # OAuth Credentials
            if not self.GOOGLE_CLIENT_ID:
                result["errors"].append("GOOGLE_CLIENT_ID - Required for YouTube OAuth")
            if not self.GOOGLE_CLIENT_SECRET:
                result["errors"].append("GOOGLE_CLIENT_SECRET - Required for YouTube OAuth")
            if not self.TIKTOK_CLIENT_KEY:
                result["errors"].append("TIKTOK_CLIENT_KEY - Required for TikTok OAuth")
            if not self.TIKTOK_CLIENT_SECRET:
                result["errors"].append("TIKTOK_CLIENT_SECRET - Required for TikTok OAuth")
            
            # Security
            if not self.SECRET_KEY or self.SECRET_KEY.startswith("dev_") or len(self.SECRET_KEY) < 32:
                result["errors"].append("SECRET_KEY - Must be set with 32+ characters in production")
            
            # Domain
            if not self.PRODUCTION_DOMAIN or "localhost" in self.PRODUCTION_DOMAIN:
                result["errors"].append("PRODUCTION_DOMAIN - Must be set to production URL")
            
            if not self.CORS_ORIGINS or "localhost" in self.CORS_ORIGINS:
                result["warnings"].append("CORS_ORIGINS - Contains localhost or is empty in production")
            
            # Required for core functionality
            if not self.GROQ_API_KEY and not self.OPENAI_API_KEY:
                result["errors"].append("GROQ_API_KEY or OPENAI_API_KEY - At least one AI provider required")
        
        # Development warnings (non-blocking)
        else:
            # Warn if GROQ API key is missing
            if not self.GROQ_API_KEY:
                result["warnings"].append("GROQ_API_KEY not set - AI features will use fallback mode")
            
            # Warn if OAuth credentials missing
            if not self.GOOGLE_CLIENT_ID:
                result["warnings"].append("GOOGLE_CLIENT_ID not set - YouTube OAuth will not work")
            if not self.TIKTOK_CLIENT_KEY:
                result["warnings"].append("TIKTOK_CLIENT_KEY not set - TikTok OAuth will not work")
        
        # Optional service warnings
        if not self.ELEVENLABS_API_KEY and self.VOICE_ENGINE == "elevenlabs":
            result["warnings"].append("ELEVENLABS_API_KEY not set - ElevenLabs voice engine unavailable")
        
        if not self.PEXELS_API_KEY:
            result["info"].append("PEXELS_API_KEY not set - Stock media will use fallback images")
        
        if not self.STRIPE_SECRET_KEY:
            result["info"].append("STRIPE_SECRET_KEY not set - Payment processing unavailable")
        
        if not self.SHOPIFY_SHOP_URL:
            result["info"].append("SHOPIFY_SHOP_URL not set - Commerce features unavailable")
        
        # AWS S3 checks
        if self.STORAGE_PROVIDER == "AWS":
            if not self.AWS_ACCESS_KEY_ID:
                result["errors"].append("AWS_ACCESS_KEY_ID required when STORAGE_PROVIDER=AWS")
            if not self.AWS_SECRET_ACCESS_KEY:
                result["errors"].append("AWS_SECRET_ACCESS_KEY required when STORAGE_PROVIDER=AWS")
            if not self.AWS_STORAGE_BUCKET_NAME:
                result["errors"].append("AWS_STORAGE_BUCKET_NAME required when STORAGE_PROVIDER=AWS")
        
        # Redis check
        if not self.REDIS_URL:
            result["errors"].append("REDIS_URL is required for Celery workers")
        
        # Database check
        if not self.DATABASE_URL:
            result["errors"].append("DATABASE_URL is required")
        
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
            print(f"📊 Configuration check complete: {len(validation['errors'])} errors, {len(validation['warnings'])} warnings\n")
        
        return validation["errors"]

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True

settings = Settings()

# Immediate startup validation
validation = settings.validate_critical_config()
if validation["errors"] or validation["warnings"]:
    settings.print_validation_report()
