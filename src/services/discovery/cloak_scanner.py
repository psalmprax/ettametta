"""
CloakBrowser Scanner — Multi-Platform Stealth Scraping Engine

A DiscoveryScannerBase subclass that uses the containerized CloakBrowser
service for undetected web scraping of YouTube and other platforms.
Bypasses API quota limits and anti-bot protections entirely.
"""

import asyncio
import datetime
import logging
import re
from typing import Optional

import httpx

from .scanner_base import DiscoveryScannerBase
from .models import ContentCandidate
from .cloak_platform_config import (
    CloakPlatformConfig,
    get_platform_config,
    get_all_platform_keys,
)

logger = logging.getLogger(__name__)

# Semaphore to limit concurrent CloakBrowser scans (Playwright is heavy)
_CLOAK_SEMAPHORE = asyncio.Semaphore(3)

# ── Noise filtering ──────────────────────────────────────────

NOISE_TITLES = {
    "sign up", "log in", "login", "sign in", "register", "create account",
    "terms of service", "terms", "privacy policy", "privacy", "cookie policy",
    "cookies", "about", "about us", "about me", "careers", "jobs", "blog",
    "help", "support", "faq", "contact", "contact us", "advertise",
    "download", "download the app", "get the app", "install",
    "notifications", "settings", "profile", "explore", "following",
    "for you", "home", "search", "discover", "reels", "shorts",
    "trending", "popular", "live", "shop", "menu", "more",
    "sign up with phone or email", "community guidelines",
}

NOISE_URL_PATTERNS = [
    "/about", "/careers", "/blog", "/help", "/support", "/faq",
    "/terms", "/privacy", "/cookie", "/legal", "/contact",
    "/download", "/install", "/settings", "/notifications",
    "/accounts/", "/explore/", "/directory",
]


def _is_noise(title: str, url: str = "") -> bool:
    """Check if a scraped item is noise (nav links, footers, etc.)."""
    t = title.strip().lower()
    # Skip empty or very short titles
    if len(t) < 8:
        return True
    # Skip exact noise matches
    if t in NOISE_TITLES:
        return True
    # Skip titles that are just common nav words
    if len(t.split()) <= 2 and t in NOISE_TITLES:
        return True
    # Skip URL patterns
    if url:
        url_lower = url.lower()
        for pattern in NOISE_URL_PATTERNS:
            if pattern in url_lower:
                return True
    return False


class CloakBrowserScanner(DiscoveryScannerBase):
    """
    Scanner that delegates to the containerized CloakBrowser service
    powered by CloakBrowser + Playwright for stealth browsing.
    Supports multiple platforms via the platform config registry.
    """

    def __init__(
        self,
        scraper_url: str = "http://cloakbrowser:8010",
        timeout: float = 45.0,
        platform: str = "youtube",
    ):
        self.scraper_url = scraper_url
        self.timeout = timeout
        self.default_platform = platform
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    def __init_subclass__(cls, **kwargs):
        pass

    # ── Public API ──────────────────────────────────────────────

    async def scan_trends(
        self,
        niche: str,
        published_after: Optional[datetime.datetime] = None,
        region: Optional[str] = "US",
        **kwargs,
    ) -> list[ContentCandidate]:
        """Backward-compatible: scrape using the default platform (YouTube)."""
        return await self.scan_platform(
            self.default_platform, niche, published_after=published_after, region=region
        )

    async def scan_platform(
        self,
        platform_key: str,
        niche: str,
        published_after: Optional[datetime.datetime] = None,
        region: Optional[str] = "US",
    ) -> list[ContentCandidate]:
        """
        Generic multi-platform scrape via the CloakBrowser service.
        Uses the platform config registry for URL templates and parsing.
        """
        config = get_platform_config(platform_key)
        if not config:
            logger.warning(f"CloakBrowser: unknown platform '{platform_key}'")
            return []

        async with _CLOAK_SEMAPHORE:
            return await self._scrape_with_retry(config, niche, region)

    async def scan_all_platforms(
        self,
        niche: str,
        region: Optional[str] = "US",
        platforms: Optional[list[str]] = None,
    ) -> list[ContentCandidate]:
        """Scan multiple platforms concurrently."""
        keys = platforms or get_all_platform_keys()
        tasks = [self.scan_platform(k, niche, region=region) for k in keys]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        candidates = []
        for res in results:
            if isinstance(res, list):
                candidates.extend(res)
            elif isinstance(res, Exception):
                logger.error(f"CloakBrowser multi-scan error: {res}")
        return candidates

    # ── Internal: retry + dispatch ──────────────────────────────

    async def _scrape_with_retry(
        self,
        config: CloakPlatformConfig,
        niche: str,
        region: Optional[str],
    ) -> list[ContentCandidate]:
        last_err = None
        for attempt in range(1, config.max_retries + 1):
            try:
                return await self._do_scrape(config, niche, region)
            except httpx.TimeoutException:
                last_err = "timeout"
                wait = config.retry_backoff * attempt
                logger.warning(
                    f"CloakBrowser [{config.name}] timeout (attempt {attempt}/{config.max_retries}), "
                    f"retrying in {wait}s…"
                )
                await asyncio.sleep(wait)
            except httpx.ConnectError:
                logger.warning(
                    f"Cannot connect to CloakBrowser scraper at {self.scraper_url}"
                )
                return []
            except Exception as e:
                logger.exception(
                    f"CloakBrowser [{config.name}] scan failed for '{niche}': {e}"
                )
                return []

        logger.error(
            f"CloakBrowser [{config.name}] exhausted retries for '{niche}' (last: {last_err})"
        )
        return []

    async def _do_scrape(
        self,
        config: CloakPlatformConfig,
        niche: str,
        region: Optional[str],
    ) -> list[ContentCandidate]:
        """Execute a single scrape attempt against the CloakBrowser service."""
        params = {
            "niche": niche,
            "region": region or "US",
            "max_results": config.max_results,
            **config.extra_params,
        }

        if config.use_generic_endpoint:
            query = niche.replace(" ", "+")
            query_no_spaces = niche.replace(" ", "")
            url = config.search_url_template.format(
                query=query, query_no_spaces=query_no_spaces
            )
            params["url"] = url
            params["platform"] = config.name.lower()
            if config.wait_selector:
                params["wait_selector"] = config.wait_selector
            if config.requires_scroll:
                params["scroll"] = "true"

        endpoint = f"{self.scraper_url}{config.scrape_endpoint}"
        response = await self.client.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            logger.error(
                f"CloakBrowser [{config.name}] scraper failed: {data.get('error', 'unknown')}"
            )
            return []

        # Dispatch to platform-specific parser
        parser = self._get_parser(config.name.lower())
        raw_items = data.get("candidates", data.get("results", data.get("items", [])))
        candidates = parser(raw_items, config, niche, region)

        logger.info(
            f"CloakBrowser [{config.name}] returned {len(candidates)} candidates for '{niche}'"
        )
        return candidates

    # ── Platform parsers ────────────────────────────────────────

    def _get_parser(self, platform_name: str):
        parsers = {
            "youtube": self._parse_youtube,
            "tiktok": self._parse_tiktok,
            "instagram": self._parse_instagram,
            "facebook": self._parse_facebook,
            "x (twitter)": self._parse_x_twitter,
            "linkedin": self._parse_linkedin,
            "reddit": self._parse_reddit,
            "twitch": self._parse_twitch,
            "etsy": self._parse_etsy,
            "pinterest": self._parse_pinterest,
            "gumroad": self._parse_gumroad,
            "product hunt": self._parse_producthunt,
            "deviantart": self._parse_deviantart,
            "behance": self._parse_behance,
            "dribbble": self._parse_dribbble,
            "unsplash": self._parse_unsplash,
            "pexels": self._parse_pexels,
            "hacker news": self._parse_hackernews,
            "indie hackers": self._parse_indiehackers,
            "github trending": self._parse_github,
            "amazon": self._parse_amazon,
            "ebay": self._parse_ebay,
        }
        return parsers.get(platform_name, self._parse_generic)

    def _parse_youtube(self, items, config, niche, region):
        candidates = []
        for item in items:
            video_id = item.get("id", "")
            if not video_id:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{video_id}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("channel", "Unknown"),
                    title=title,
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=self._parse_views(item.get("views", "0")),
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category=config.category,
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "youtube_web"},
                )
            )
        return candidates

    def _parse_tiktok(self, items, config, niche, region):
        candidates = []
        for item in items:
            vid = item.get("id") or item.get("video_id", "")
            if not vid:
                continue
            title = item.get("title", item.get("desc", f"TikTok {niche}"))
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            author = item.get("author") or item.get("channel") or "Unknown"
            views = self._parse_views(str(item.get("views", item.get("playCount", 0))))
            likes = self._safe_int(item.get("likes", item.get("diggCount", 0)))
            comments = self._safe_int(item.get("comments", item.get("commentCount", 0)))
            shares = self._safe_int(item.get("shares", item.get("shareCount", 0)))
            engagement = (likes + comments + shares) / max(views, 1)
            viral = min(max(int((views / 5000) * (1 + engagement * 10)), 1), 95)
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{vid}",
                    platform=config.platform_label,
                    source_uri=url or f"https://www.tiktok.com/video/{vid}",
                    creator_name=author,
                    title=title,
                    thumbnail_uri=item.get("thumbnail", item.get("cover", "")),
                    view_count=views,
                    like_count=likes,
                    comment_count=comments,
                    share_count=shares,
                    engagement_score=engagement,
                    viral_score=viral,
                    region=region or "US",
                    category=config.category,
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "tiktok_web"},
                )
            )
        return candidates

    def _parse_instagram(self, items, config, niche, region):
        candidates = []
        for item in items:
            shortcode = item.get("shortcode") or item.get("id", "")
            if not shortcode:
                continue
            title = item.get("title") or item.get("caption", f"IG Reel: {niche}")[:100]
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            likes = self._safe_int(item.get("likes", 0))
            comments = self._safe_int(item.get("comments", 0))
            views_est = max(likes * 20, 1)
            engagement = (likes + comments) / max(views_est, 1)
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{shortcode}",
                    platform=config.platform_label,
                    source_uri=url or f"https://www.instagram.com/reel/{shortcode}/",
                    creator_name=item.get("author") or item.get("username", "Unknown"),
                    title=title,
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=views_est,
                    like_count=likes,
                    comment_count=comments,
                    engagement_score=engagement,
                    region=region or "US",
                    category=config.category,
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "instagram_web"},
                )
            )
        return candidates

    def _parse_facebook(self, items, config, niche, region):
        candidates = []
        for item in items:
            vid = item.get("id") or item.get("video_id", "")
            if not vid:
                continue
            title = item.get("title", f"Facebook Video: {niche}")[:100]
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            views = self._safe_int(item.get("views", item.get("view_count", 0)))
            likes = self._safe_int(item.get("likes", 0))
            comments = self._safe_int(item.get("comments", 0))
            shares = self._safe_int(item.get("shares", 0))
            engagement = (likes + comments + shares) / max(views, 1) if views else 0.05
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{vid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author") or item.get("page_name", "Unknown"),
                    title=title,
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=views,
                    like_count=likes,
                    comment_count=comments,
                    share_count=shares,
                    engagement_score=engagement,
                    region=region or "US",
                    category=config.category,
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "facebook_web"},
                )
            )
        return candidates

    def _parse_x_twitter(self, items, config, niche, region):
        candidates = []
        for item in items:
            tid = item.get("id") or item.get("tweet_id", "")
            if not tid:
                continue
            text = (item.get("text", "") or item.get("title", f"X: {niche}"))[:100]
            url = item.get("url", "")
            if _is_noise(text, url):
                continue
            likes = self._safe_int(item.get("likes", item.get("favorite_count", 0)))
            retweets = self._safe_int(item.get("retweets", item.get("retweet_count", 0)))
            replies = self._safe_int(item.get("replies", item.get("reply_count", 0)))
            engagement_total = likes + retweets + replies
            views_est = max(engagement_total * 15, 1)
            engagement = engagement_total / max(views_est, 1)
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{tid}",
                    platform=config.platform_label,
                    source_uri=url or f"https://x.com/i/status/{tid}",
                    creator_name=item.get("author") or item.get("username", "Unknown"),
                    title=text,
                    thumbnail_uri=item.get("media_url", item.get("thumbnail", "")),
                    view_count=views_est,
                    like_count=likes,
                    comment_count=replies,
                    share_count=retweets,
                    engagement_score=engagement,
                    region=region or "US",
                    category=config.category,
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "x_twitter_web"},
                )
            )
        return candidates

    def _parse_linkedin(self, items, config, niche, region):
        candidates = []
        for item in items:
            pid = item.get("id") or item.get("post_id", "")
            if not pid:
                continue
            text = (item.get("title", "") or item.get("text", f"LinkedIn: {niche}"))[:100]
            url = item.get("url", "")
            if _is_noise(text, url):
                continue
            likes = self._safe_int(item.get("likes", 0))
            comments = self._safe_int(item.get("comments", 0))
            shares = self._safe_int(item.get("shares", 0))
            engagement_total = likes + comments + shares
            views_est = max(engagement_total * 30, 1)
            engagement = engagement_total / max(views_est, 1)
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{pid}",
                    platform=config.platform_label,
                    source_uri=url or f"https://www.linkedin.com/feed/update/{pid}",
                    creator_name=item.get("author", "Unknown"),
                    title=text,
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=views_est,
                    like_count=likes,
                    comment_count=comments,
                    share_count=shares,
                    engagement_score=engagement,
                    region=region or "US",
                    category=config.category,
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "linkedin_web"},
                )
            )
        return candidates

    def _parse_reddit(self, items, config, niche, region):
        candidates = []
        for item in items:
            pid = item.get("id") or item.get("post_id", "")
            if not pid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            score = self._safe_int(item.get("views", item.get("score", 0)))
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{pid}",
                    platform=config.platform_label,
                    source_uri=url or f"https://www.reddit.com/comments/{pid}/",
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=abs(score) * 10,  # Estimate views from score
                    like_count=score if score > 0 else 0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=min(max(score, 0), 95),
                    region=region or "US",
                    category="social",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "reddit_web"},
                )
            )
        return candidates

    def _parse_twitch(self, items, config, niche, region):
        candidates = []
        for item in items:
            item_id = item.get("id", "")
            if not item_id:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{item_id}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="video",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "twitch_web"},
                )
            )
        return candidates

    def _parse_etsy(self, items, config, niche, region):
        candidates = []
        for item in items:
            listing_id = item.get("id", "")
            if not listing_id:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            price = self._safe_float(item.get("price", 0))
            sales = self._safe_int(item.get("sales", 0))
            rating = self._safe_float(item.get("rating", 0))
            shop = item.get("shop", "Unknown")
            engagement = min(sales / 100, 1.0) if sales else 0.0
            viral = min(max(int(sales / 10), 1), 95) if sales else 0
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{listing_id}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=shop,
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=sales,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=engagement,
                    viral_score=viral,
                    region=region or "US",
                    category="commerce",
                    tags=[niche] + config.tags_extra,
                    metadata_json={
                        "scraper": "cloakbrowser",
                        "source": "etsy_web",
                        "price": price,
                        "sales": sales,
                        "rating": rating,
                        "shop": shop,
                    },
                )
            )
        return candidates

    def _parse_pinterest(self, items, config, niche, region):
        candidates = []
        for item in items:
            pin_id = item.get("id", "")
            if not pin_id:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{pin_id}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="visual",
                    tags=[niche] + config.tags_extra,
                    metadata_json={
                        "scraper": "cloakbrowser",
                        "source": "pinterest_web",
                    },
                )
            )
        return candidates

    def _parse_gumroad(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            price = self._safe_float(item.get("price", 0))
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="commerce",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "gumroad_web", "price": price},
                )
            )
        return candidates

    def _parse_producthunt(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="launches",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "producthunt_web"},
                )
            )
        return candidates

    def _parse_deviantart(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="design",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "deviantart_web"},
                )
            )
        return candidates

    def _parse_behance(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="design",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "behance_web"},
                )
            )
        return candidates

    def _parse_dribbble(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="design",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "dribbble_web"},
                )
            )
        return candidates

    def _parse_unsplash(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="media",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "unsplash_web"},
                )
            )
        return candidates

    def _parse_pexels(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="media",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "pexels_web"},
                )
            )
        return candidates

    def _parse_hackernews(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            score = self._safe_int(item.get("views", 0))
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=score,
                    like_count=score,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=min(max(score // 10, 0), 95),
                    region=region or "US",
                    category="tech",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "hackernews_web"},
                )
            )
        return candidates

    def _parse_indiehackers(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="community",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "indiehackers_web"},
                )
            )
        return candidates

    def _parse_github(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            stars = self._safe_int(item.get("views", 0))
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=stars,
                    like_count=stars,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=min(max(stars // 10, 0), 95),
                    region=region or "US",
                    category="tech",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "github_web", "language": item.get("language", ""), "description": item.get("description", "")},
                )
            )
        return candidates

    def _parse_amazon(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            price = self._safe_float(item.get("price", 0))
            rating = self._safe_float(item.get("rating", 0))
            reviews = self._safe_int(item.get("sales", 0))
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("shop", "Amazon"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=reviews,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=min(max(reviews // 100, 0), 95),
                    region=region or "US",
                    category="commerce",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "amazon_web", "price": price, "rating": rating, "reviews": reviews},
                )
            )
        return candidates

    def _parse_ebay(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            price = self._safe_float(item.get("price", 0))
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "eBay"),
                    title=title[:200],
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=0,
                    like_count=0,
                    comment_count=0,
                    share_count=0,
                    engagement_score=0.0,
                    viral_score=0,
                    region=region or "US",
                    category="commerce",
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": "ebay_web", "price": price},
                )
            )
        return candidates

    def _parse_generic(self, items, config, niche, region):
        candidates = []
        for item in items:
            cid = item.get("id", "")
            if not cid:
                continue
            title = item.get("title", "No Title")[:100]
            url = item.get("url", "")
            if _is_noise(title, url):
                continue
            candidates.append(
                ContentCandidate(
                    id=f"{config.id_prefix}_{cid}",
                    platform=config.platform_label,
                    source_uri=url,
                    creator_name=item.get("author", "Unknown"),
                    title=title,
                    thumbnail_uri=item.get("thumbnail", ""),
                    view_count=self._safe_int(item.get("views", 0)),
                    region=region or "US",
                    category=config.category,
                    tags=[niche] + config.tags_extra,
                    metadata_json={"scraper": "cloakbrowser", "source": f"{config.name.lower()}_web"},
                )
            )
        return candidates

    # ── Utilities ───────────────────────────────────────────────

    def _parse_views(self, views_str: str) -> int:
        """Parse view count strings like '1.2M views', '500K views', '1,234 views'."""
        if not views_str:
            return 0
        views_str = str(views_str).replace("views", "").replace("view", "").strip()
        views_str = views_str.replace(",", "")
        match = re.match(r"([\d.]+)\s*([MK]?)", views_str, re.IGNORECASE)
        if not match:
            return 0
        num = float(match.group(1))
        suffix = match.group(2).upper()
        if suffix == "M":
            return int(num * 1_000_000)
        elif suffix == "K":
            return int(num * 1_000)
        return int(num)

    def _safe_int(self, val) -> int:
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    def _safe_float(self, val) -> float:
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    async def close(self):
        """Clean up the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
