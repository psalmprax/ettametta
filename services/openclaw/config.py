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
    
    # ettametta Internal APIs
    API_URL: str = "http://api:8000"
    INTERNAL_API_TOKEN: str = ""  # Token for internal service-to-service auth
    
    # Service Config
    PORT: int = 3001
    HOST: str = "0.0.0.0"

    # Twilio Configuration (Optional)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
