import importlib
import logging

logger = logging.getLogger(__name__)


def safe_import_skill(module_path: str, skill_name: str):
    """Safely import a skill, returning None if dependencies are missing."""
    try:
        # If it starts with a dot, it's relative
        if module_path.startswith("."):
            module = importlib.import_module(module_path, package=__name__)
        else:
            module = importlib.import_module(module_path)
        return getattr(module, skill_name)
    except Exception as e:
        logger.warning(f"Skill '{skill_name}' at '{module_path}' disabled: {e}")
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
from .kaiber import kaiber_skill
from .video_lead_discovery import video_lead_skill
from .scene_based_video import scene_based_video_skill
from .intelligent_workflow import intelligent_workflow_skill
from .browser import browser_skill
from .document import document_skill
from .persona import persona_skill

# ettametta Official Skills
from .seo_auditor import seo_auditor_skill
from .reputation_manager import reputation_manager_skill
from .chat_sales import chat_sales_skill
from .landing_page import landing_page_skill
from .data_scraping import data_scraping_skill

# Safe imports for dependency-heavy skills (Playwright based)
perchance_skill = safe_import_skill(".perchance", "perchance_skill")
paperclip_skill = safe_import_skill(
    ".external.paperclip_integration", "paperclip_skill"
)
claw4science_skill = safe_import_skill(
    ".external.claw4science_integration", "claw4science_skill"
)
remotion_skill = safe_import_skill(".render_remotion", "remotion_skill")
ettametta_skill = safe_import_skill(".ettametta", "ettametta_skill")
pixverse_skill = safe_import_skill(".pixverse", "pixverse_skill")
branding_skill = safe_import_skill(".branding", "branding_skill")

# --- NEW POLYMORPHIC SKILLS ---
pika_skill = safe_import_skill(".pika", "pika_skill")
runway_skill = safe_import_skill(".runway", "runway_skill")
kling_skill = safe_import_skill(".kling", "kling_skill")
hailuo_skill = safe_import_skill(".hailuo", "hailuo_skill")
haiper_skill = safe_import_skill(".haiper", "haiper_skill")
genmo_skill = safe_import_skill(".genmo", "genmo_skill")
morph_skill = safe_import_skill(".morph", "morph_skill")
vidu_skill = safe_import_skill(".vidu", "vidu_skill")
wavespeed_skill = safe_import_skill(".wavespeed", "wavespeed_skill")
seedance_skill = safe_import_skill(".seedance", "seedance_skill")
frameloop_skill = safe_import_skill(".frameloop", "frameloop_skill")
leiapix_skill = safe_import_skill(".leiapix", "leiapix_skill")
videoany_skill = safe_import_skill(".videoany", "videoany_skill")
heygen_skill = safe_import_skill(".heygen", "heygen_skill")
ltx_skill = safe_import_skill(".ltx", "ltx_skill")
leonardo_skill = safe_import_skill(".leonardo", "leonardo_skill")
invideo_skill = safe_import_skill(".invideo", "invideo_skill")
fliki_skill = safe_import_skill(".fliki", "fliki_skill")
content_editor_skill = safe_import_skill(".content_editor", "content_editor_skill")
production_assistant_skill = safe_import_skill(
    ".video_production_assistant", "production_assistant_skill"
)

# Render and Agent Zero skills (must exist or be handled gracefully)
render_skill = safe_import_skill(".render", "render_skill")
agent_zero_skill = safe_import_skill(".agent_zero", "agent_zero_skill")

# Ensure render_skill has a fallback if import fails
if render_skill is None:
    from .base_skill import OpenClawBaseSkill

    class FallbackRenderSkill(OpenClawBaseSkill):
        """Fallback skill when render module is unavailable"""

        def execute(self, action: str = "render", **kwargs) -> str:
            return "⚠️ Render service unavailable - please install render dependencies"

    render_skill = FallbackRenderSkill()

if agent_zero_skill is None:
    from .base_skill import OpenClawBaseSkill

    class FallbackAgentZeroSkill(OpenClawBaseSkill):
        """Fallback skill when agent zero module is unavailable"""

        def execute(self, action: str = "status", **kwargs) -> str:
            return "⚠️ Agent Zero service unavailable - please install agent-zero dependencies"

    agent_zero_skill = FallbackAgentZeroSkill()

__all__ = [
    "research_skill",
    "data_ingestion_skill",
    "social_metrics_skill",
    "perchance_skill",
    "branding_skill",
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
    "ettametta_skill",
    "pixverse_skill",
    "luma_skill",
    "kaiber_skill",
    "video_lead_skill",
    "scene_based_video_skill",
    "intelligent_workflow_skill",
    "browser_skill",
    "document_skill",
    "persona_skill",
    "production_assistant_skill",
    "seo_auditor_skill",
    "reputation_manager_skill",
    "chat_sales_skill",
    "landing_page_skill",
    "data_scraping_skill",
    "render_skill",
    "agent_zero_skill",
    "pika_skill",
    "runway_skill",
    "kling_skill",
    "hailuo_skill",
    "haiper_skill",
    "genmo_skill",
    "morph_skill",
    "vidu_skill",
    "wavespeed_skill",
    "seedance_skill",
    "frameloop_skill",
    "leiapix_skill",
    "videoany_skill",
    "heygen_skill",
    "ltx_skill",
    "leonardo_skill",
    "invideo_skill",
    "fliki_skill",
    "content_editor_skill",
]
