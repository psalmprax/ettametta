from pydantic import field_validator
from typing import Any
import logging
from src.core.config import CoreSettings
from src.api.utils.hardware_detector import hardware_detector
from src.api.config.validation import validate_critical_config, print_validation_report

logger = logging.getLogger(__name__)


class Settings(CoreSettings):
    # API-specific: Public gateway hostname
    GATEWAY_HOST: str = "localhost"

    # API-specific: Persisted analysis for discovery pipeline
    ENABLE_PERSISTED_ANALYSIS: bool = False

    @property
    def SNAPCHAT_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/publish/auth/snapchat/callback"

    @property
    def TWITCH_REDIRECT_URI(self) -> str:
        return f"{self.PRODUCTION_DOMAIN.rstrip('/')}/publish/auth/twitch/callback"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            normalized = v.strip().lower()
            if normalized in ("1", "true", "yes", "on", "release"):
                return True
            if normalized in ("0", "false", "no", "off", "production"):
                return False
        raise ValueError(f"Invalid boolean value for DEBUG: {v!r}")

    def validate_critical_config(self):
        """Delegate to standalone validation function."""
        return validate_critical_config(self)

    def print_validation_report(self):
        """Delegate to standalone validation logging function."""
        return print_validation_report(self)


settings = Settings()

# Apply VRAM override if specified
if settings.GPU_FORCE_VRAM_GB is not None:
    hardware_detector.set_vram_override(settings.GPU_FORCE_VRAM_GB)

# Immediate startup validation
validation = settings.validate_critical_config()
if validation["errors"] or validation["warnings"]:
    settings.print_validation_report()
