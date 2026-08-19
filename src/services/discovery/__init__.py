"""
Discovery Service Package
========================

Contains services for discovering trending content across platforms:
- CloakBrowser Scanner (stealth YouTube/TikTok scraping)
- Content Analysis Service (AI-powered pattern detection)
- Video Content Pipeline (end-to-end discovery → analysis → generation)
- Various platform-specific scanners (Instagram, Twitter, etc.)
"""

# Make sure all submodules are imported when discovery package is imported
from .cloak_scanner import CloakBrowserScanner
from .cloak_tiktok_scanner import CloakTikTokScanner
from .cloak_instagram_scanner import CloakInstagramScanner
from .cloak_facebook_scanner import CloakFacebookScanner
from .cloak_x_scanner import CloakXScanner
from .cloak_linkedin_scanner import CloakLinkedInScanner
from .analysis_service import extract_content_patterns, get_persisted_analysis_report
from .video_content_pipeline import (
    ViralContentPipeline,
    discover_analyze_and_generate,
    discover_analyze_generate_compile
)

# Export scanner base for type hints
from .scanner_base import DiscoveryScannerBase

# Export models
from .models import ContentCandidate

__all__ = [
    # Scanners
    "CloakBrowserScanner",
    "CloakTikTokScanner",
    "CloakInstagramScanner",
    "CloakFacebookScanner",
    "CloakXScanner",
    "CloakLinkedInScanner",
    "DiscoveryScannerBase",

    # Analysis
    "extract_content_patterns",
    "get_persisted_analysis_report",

    # Pipeline
    "ViralContentPipeline",
    "discover_analyze_and_generate",
    "discover_analyze_generate_compile",

    # Models
    "ContentCandidate"
]
