from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "OpenClaw Gateway"
    ENV: str = "development"
    
    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_ID: int = 0  # Default to 0 to prevent crash if not set
    
    # AI Configuration
    GROQ_API_KEY: str
    MODEL: str = "llama-3.3-70b-versatile"
    
    # ViralForge Internal APIs
    API_URL: str = "http://api:8000"
    
    # Service Config
    PORT: int = 3001
    HOST: str = "0.0.0.0"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
