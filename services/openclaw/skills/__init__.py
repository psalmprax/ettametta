import logging

logger = logging.getLogger(__name__)


def safe_import_skill(module_path: str, skill_name: str):
    """Safely import a skill, returning None if dependencies are missing."""
    try:
        # Use relative import for the package
        module = __import__(
            module_path, fromlist=[skill_name], globals=globals(), level=1
        )
        return getattr(module, skill_name)
    except (ImportError, ModuleNotFoundError, AttributeError) as e:
        logger.warning(
            f"Skill '{skill_name}' at '{module_path}' disabled due to missing dependency or name error: {e}"
        )
        return None


# Standard imports (No heavy dependencies)
from .research import research_skill
from .ingestion import data_ingestion_skill
from .metrics import social_metrics_skill
from .model_settings import (
    MODEL_SETTINGS,
    get_model_settings,
    get_recommended_settings,
    get_image_recommended_settings,
    list_providers,
)
from .discovery import discovery_skill
from .system import system_skill
from .analytics import analytics_skill
from .content import content_skill
from .publishing import publishing_skill
from .niche import niche_skill
from .security import security_skill
from .no_face import noface_skill
from .outreach import outreach_skill
from .memory import memory_skill
from .self_improve import self_improve_skill
from .repurpose import repurpose_skill
from .trend_prediction import trend_prediction_skill
from .competitor import competitor_skill
from .audit import audit_skill
from .notifications import notification_skill
from .workflow import workflow_skill
from .self_healing import self_healing_skill
from .luma import luma_skill
from .video_lead_discovery import video_lead_skill
from .scene_based_video import scene_based_video_skill
from .video_production_assistant import video_production_assistant_skill

# Safe imports for dependency-heavy skills (Playwright based)
perchance_skill = safe_import_skill(".perchance", "perchance_skill")
paperclip_skill = safe_import_skill(
    ".external.paperclip_integration", "paperclip_skill"
)
claw4science_skill = safe_import_skill(
    ".external.claw4science_integration", "claw4science_skill"
)
remotion_skill = safe_import_skill(".render_remotion", "remotion_skill")
cashclaw_skill = safe_import_skill(".cashclaw", "cashclaw_skill")
pixverse_skill = safe_import_skill(".pixverse", "pixverse_skill")

__all__ = [
    "research_skill",
    "data_ingestion_skill",
    "social_metrics_skill",
    "perchance_skill",
    "MODEL_SETTINGS",
    "get_model_settings",
    "get_recommended_settings",
    "get_image_recommended_settings",
    "list_providers",
    "discovery_skill",
    "system_skill",
    "analytics_skill",
    "content_skill",
    "publishing_skill",
    "niche_skill",
    "security_skill",
    "noface_skill",
    "outreach_skill",
    "paperclip_skill",
    "claw4science_skill",
    "remotion_skill",
    "memory_skill",
    "self_improve_skill",
    "repurpose_skill",
    "trend_prediction_skill",
    "competitor_skill",
    "audit_skill",
    "notification_skill",
    "workflow_skill",
    "self_healing_skill",
    "cashclaw_skill",
    "pixverse_skill",
    "luma_skill",
    "video_lead_skill",
    "scene_based_video_skill",
    "video_production_assistant_skill",
]
