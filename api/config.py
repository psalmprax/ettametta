from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "ViralForge API"
    ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev_secret_key_vforge_2026_change_in_prod"
    ALGORITHM: str = "HS256"

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
    DEFAULT_VLM_MODEL: str = "gemini-1.5-flash"
    
    # Video Generation
    FONT_PATH: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    # Social API Keys
    YOUTUBE_API_KEY: str = ""
    TIKTOK_API_KEY: str = ""
    
    # OAuth Credentials
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # TikTok keys might be loaded from env with slightly different names in some setups, 
    # but we standardize here.
    TIKTOK_CLIENT_KEY: str = ""
    TIKTOK_CLIENT_SECRET: str = ""
    
    # Scraper Cookies (Bypass Bot Detection)
    YOUTUBE_COOKIES_PATH: Optional[str] = "cookies/youtube_cookies.txt"
    TIKTOK_COOKIES_PATH: Optional[str] = "cookies/tiktok_cookies.txt"
    
    # Infrastructure
    PRODUCTION_DOMAIN: str = "http://localhost:8000"
    
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
    
    # Deprecated (Keeping for backward sync during migration)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_STORAGE_BUCKET_NAME: str = ""

    # Database & Redis
    DATABASE_URL: str = "sqlite:///./viral_forge.db"
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
