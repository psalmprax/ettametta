"""
CloakBrowser Platform Configuration Registry

Defines how each platform should be scraped via the CloakBrowser stealth engine.
Each platform has its own search URL patterns, data extraction strategies,
timeout tuning, and candidate mapping rules.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CloakPlatformConfig:
    """Configuration for a single platform's CloakBrowser scraping."""

    name: str
    id_prefix: str
    platform_label: str
    search_url_template: str
    scrape_endpoint: str = "/scrape/youtube"
    use_generic_endpoint: bool = False
    timeout: float = 45.0
    max_results: int = 10
    max_retries: int = 2
    retry_backoff: float = 2.0
    category: str = "video"
    extra_params: dict = field(default_factory=dict)
    requires_scroll: bool = False
    wait_selector: Optional[str] = None
    tags_extra: list = field(default_factory=list)


CLOAK_PLATFORMS: dict[str, CloakPlatformConfig] = {
    "youtube": CloakPlatformConfig(
        name="YouTube",
        id_prefix="cloak_yt",
        platform_label="YouTube",
        search_url_template="https://www.youtube.com/results?search_query={query}&sp=CAMSAhAB",
        scrape_endpoint="/scrape/youtube",
        use_generic_endpoint=False,
        timeout=45.0,
        max_results=10,
        category="video",
        wait_selector="ytd-video-renderer",
        tags_extra=["cloak-scraped"],
    ),
    "tiktok": CloakPlatformConfig(
        name="TikTok",
        id_prefix="cloak_tt",
        platform_label="TikTok",
        search_url_template="https://www.tiktok.com/search/video?q={query}",
        scrape_endpoint="/scrape/tiktok",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=10,
        category="video",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "tiktok"],
    ),
    "instagram": CloakPlatformConfig(
        name="Instagram",
        id_prefix="cloak_ig",
        platform_label="Instagram Reels",
        search_url_template="https://www.instagram.com/explore/tags/{query_no_spaces}/",
        scrape_endpoint="/scrape/instagram",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=10,
        category="video",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "reels"],
    ),
    "facebook": CloakPlatformConfig(
        name="Facebook",
        id_prefix="cloak_fb",
        platform_label="Facebook Watch",
        search_url_template="https://www.facebook.com/watch/search/?q={query}",
        scrape_endpoint="/scrape/facebook",
        use_generic_endpoint=False,
        timeout=45.0,
        max_results=8,
        category="video",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "facebook-watch"],
    ),
    "x_twitter": CloakPlatformConfig(
        name="X (Twitter)",
        id_prefix="cloak_x",
        platform_label="X (Twitter)",
        search_url_template="https://x.com/search?q={query}&f=live",
        scrape_endpoint="/scrape/x",
        use_generic_endpoint=False,
        timeout=35.0,
        max_results=10,
        category="social",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "x-twitter"],
    ),
    "linkedin": CloakPlatformConfig(
        name="LinkedIn",
        id_prefix="cloak_li",
        platform_label="LinkedIn",
        search_url_template="https://www.linkedin.com/search/results/content/?keywords={query}",
        scrape_endpoint="/scrape/linkedin",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=8,
        category="social",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "linkedin"],
    ),
    "reddit": CloakPlatformConfig(
        name="Reddit",
        id_prefix="cloak_rd",
        platform_label="Reddit",
        search_url_template="https://www.reddit.com/search/?q={query}&type=link&sort=relevance",
        scrape_endpoint="/scrape/reddit",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=10,
        category="social",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "reddit"],
    ),
    "twitch": CloakPlatformConfig(
        name="Twitch",
        id_prefix="cloak_tw",
        platform_label="Twitch",
        search_url_template="https://www.twitch.tv/search?term={query}",
        scrape_endpoint="/scrape/twitch",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=10,
        category="video",
        tags_extra=["cloak-scraped", "twitch"],
    ),
}


def get_platform_config(platform: str) -> Optional[CloakPlatformConfig]:
    """Retrieve a platform config by key."""
    return CLOAK_PLATFORMS.get(platform.lower())


def get_all_platform_keys() -> list[str]:
    """Return all available platform keys."""
    return list(CLOAK_PLATFORMS.keys())
