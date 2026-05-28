from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict
from typing import Any


class Settings(BaseSettings):
    APP_NAME: str = "OpenClaw Gateway"
    ENV: str = "development"

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str = ""
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

    # AI Configuration
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    XAI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    # Ollama (Self-hosted LLM)
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    PEXELS_API_KEY: str = ""
    MODEL: str = "llama-3.3-70b-versatile"

    # ettametta Internal APIs
    API_URL: str = "http://nginx/api/v1"
    INTERNAL_API_TOKEN: str = ""  # Token for internal service-to-service auth

    # Service Config
    PORT: int = 3001
    HOST: str = "0.0.0.0"

    # Twilio Configuration (Any)
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = ""

    model_config = ConfigDict(env_file=".env", extra="ignore")


settings = Settings()
