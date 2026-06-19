import logging
from src.core.config import CoreSettings
from src.api.utils.hardware_detector import hardware_detector
from src.api.config.validation import validate_critical_config, print_validation_report

logger = logging.getLogger(__name__)


class Settings(CoreSettings):
    """Worker-side settings: inherits all shared config from CoreSettings.

    Override defaults here only when the worker needs a different value
    from the API side. All overrides can also be set via environment variables.
    """

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
