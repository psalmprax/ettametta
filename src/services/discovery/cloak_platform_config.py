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
    "etsy": CloakPlatformConfig(
        name="Etsy",
        id_prefix="cloak_etsy",
        platform_label="Etsy",
        search_url_template="https://www.etsy.com/search?q={query}&ref=search_bar",
        scrape_endpoint="/scrape/etsy",
        use_generic_endpoint=False,
        timeout=50.0,
        max_results=20,
        category="commerce",
        requires_scroll=True,
        wait_selector="div[data-search-results]",
        tags_extra=["cloak-scraped", "etsy", "digital-products"],
    ),
    "pinterest": CloakPlatformConfig(
        name="Pinterest",
        id_prefix="cloak_pin",
        platform_label="Pinterest",
        search_url_template="https://www.pinterest.com/search/pins/?q={query}",
        scrape_endpoint="/scrape/pinterest",
        use_generic_endpoint=False,
        timeout=45.0,
        max_results=20,
        category="visual",
        requires_scroll=True,
        wait_selector="[data-test-id='search-page']",
        tags_extra=["cloak-scraped", "pinterest", "visual-research"],
    ),
    "gumroad": CloakPlatformConfig(
        name="Gumroad",
        id_prefix="cloak_gr",
        platform_label="Gumroad",
        search_url_template="https://gumroad.com/discover?query={query}",
        scrape_endpoint="/scrape/gumroad",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=20,
        category="commerce",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "gumroad", "digital-products"],
    ),
    "producthunt": CloakPlatformConfig(
        name="Product Hunt",
        id_prefix="cloak_ph",
        platform_label="Product Hunt",
        search_url_template="https://www.producthunt.com/search?q={query}",
        scrape_endpoint="/scrape/producthunt",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=20,
        category="launches",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "producthunt", "new-products"],
    ),
    "deviantart": CloakPlatformConfig(
        name="DeviantArt",
        id_prefix="cloak_da",
        platform_label="DeviantArt",
        search_url_template="https://www.deviantart.com/search?q={query}",
        scrape_endpoint="/scrape/deviantart",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=20,
        category="design",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "deviantart", "art"],
    ),
    "behance": CloakPlatformConfig(
        name="Behance",
        id_prefix="cloak_be",
        platform_label="Behance",
        search_url_template="https://www.behance.net/search/projects?search={query}",
        scrape_endpoint="/scrape/behance",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=20,
        category="design",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "behance", "portfolio"],
    ),
    "dribbble": CloakPlatformConfig(
        name="Dribbble",
        id_prefix="cloak_dr",
        platform_label="Dribbble",
        search_url_template="https://dribbble.com/search/{query}",
        scrape_endpoint="/scrape/dribbble",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=20,
        category="design",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "dribbble", "design"],
    ),
    "unsplash": CloakPlatformConfig(
        name="Unsplash",
        id_prefix="cloak_us",
        platform_label="Unsplash",
        search_url_template="https://unsplash.com/s/photos/{query}",
        scrape_endpoint="/scrape/unsplash",
        use_generic_endpoint=False,
        timeout=35.0,
        max_results=20,
        category="media",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "unsplash", "photos"],
    ),
    "pexels": CloakPlatformConfig(
        name="Pexels",
        id_prefix="cloak_px",
        platform_label="Pexels",
        search_url_template="https://www.pexels.com/search/{query}/",
        scrape_endpoint="/scrape/pexels",
        use_generic_endpoint=False,
        timeout=35.0,
        max_results=20,
        category="media",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "pexels", "photos"],
    ),
    "hackernews": CloakPlatformConfig(
        name="Hacker News",
        id_prefix="cloak_hn",
        platform_label="Hacker News",
        search_url_template="https://hn.algolia.com/?q={query}&sort=byDate",
        scrape_endpoint="/scrape/hackernews",
        use_generic_endpoint=False,
        timeout=30.0,
        max_results=20,
        category="tech",
        requires_scroll=False,
        tags_extra=["cloak-scraped", "hackernews", "tech"],
    ),
    "indiehackers": CloakPlatformConfig(
        name="Indie Hackers",
        id_prefix="cloak_ih",
        platform_label="Indie Hackers",
        search_url_template="https://www.indiehackers.com/search?q={query}",
        scrape_endpoint="/scrape/indiehackers",
        use_generic_endpoint=False,
        timeout=40.0,
        max_results=20,
        category="community",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "indiehackers", "saas"],
    ),
    "github": CloakPlatformConfig(
        name="GitHub Trending",
        id_prefix="cloak_gh",
        platform_label="GitHub Trending",
        search_url_template="https://github.com/trending?since=daily",
        scrape_endpoint="/scrape/github",
        use_generic_endpoint=False,
        timeout=35.0,
        max_results=20,
        category="tech",
        requires_scroll=False,
        tags_extra=["cloak-scraped", "github", "open-source"],
    ),
    "amazon": CloakPlatformConfig(
        name="Amazon",
        id_prefix="cloak_amz",
        platform_label="Amazon",
        search_url_template="https://www.amazon.com/s?k={query}",
        scrape_endpoint="/scrape/amazon",
        use_generic_endpoint=False,
        timeout=50.0,
        max_results=20,
        category="commerce",
        requires_scroll=True,
        wait_selector="#search",
        tags_extra=["cloak-scraped", "amazon", "products"],
    ),
    "ebay": CloakPlatformConfig(
        name="eBay",
        id_prefix="cloak_eb",
        platform_label="eBay",
        search_url_template="https://www.ebay.com/sch/i.html?_nkw={query}",
        scrape_endpoint="/scrape/ebay",
        use_generic_endpoint=False,
        timeout=45.0,
        max_results=20,
        category="commerce",
        requires_scroll=True,
        tags_extra=["cloak-scraped", "ebay", "products"],
        max_retries=0,
    ),
}


def get_platform_config(platform: str) -> Optional[CloakPlatformConfig]:
    """Retrieve a platform config by key."""
    return CLOAK_PLATFORMS.get(platform.lower())


def get_all_platform_keys() -> list[str]:
    """Return all available platform keys."""
    return list(CLOAK_PLATFORMS.keys())
