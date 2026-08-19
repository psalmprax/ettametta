"""
CloakBrowser — Stealth Scraping Service
Playwright-based headless browser with anti-detection for multi-platform content discovery.
"""

import asyncio
import hashlib
import logging
import re
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cloakbrowser")

# ── Browser Pool ──────────────────────────────────────────────

_browser = None
_playwright = None
_browser_lock = asyncio.Lock()
_scrape_semaphore = asyncio.Semaphore(3)  # Max 3 concurrent scrapes

async def get_browser():
    """Get or create browser with auto-recovery on crash."""
    global _browser, _playwright
    async with _browser_lock:
        # Check if existing browser is still alive
        if _browser is not None:
            try:
                if _browser.is_connected():
                    return _browser
                else:
                    logger.warning("[CloakBrowser] Browser disconnected, restarting...")
                    await _cleanup_browser()
            except Exception:
                logger.warning("[CloakBrowser] Browser check failed, restarting...")
                await _cleanup_browser()

        # Launch fresh browser
        from playwright.async_api import async_playwright
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-sync",
                "--no-first-run",
                "--no-zygote",
                "--js-flags=--max-old-space-size=256",
            ],
        )
        logger.info("[CloakBrowser] Chromium launched")
        return _browser

async def _cleanup_browser():
    """Safely cleanup browser and playwright."""
    global _browser, _playwright
    try:
        if _browser:
            await _browser.close()
    except Exception:
        pass
    _browser = None
    try:
        if _playwright:
            await _playwright.stop()
    except Exception:
        pass
    _playwright = None

async def close_browser():
    """Shutdown browser on app exit."""
    global _browser
    async with _browser_lock:
        await _cleanup_browser()
    logger.info("[CloakBrowser] Browser closed")

# ── Stealth helpers ───────────────────────────────────────────

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
window.chrome = {runtime: {}};
Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
"""

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
    "sign up with phone or email",
    "community guidelines",
}

NOISE_URL_PATTERNS = [
    "/about", "/careers", "/blog", "/help", "/support", "/faq",
    "/terms", "/privacy", "/cookie", "/legal", "/contact",
    "/download", "/install", "/settings", "/notifications",
    "/accounts/", "/explore/", "/search", "/directory",
]

def is_noise(title: str, url: str = "") -> bool:
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

async def new_stealth_context(browser):
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        locale="en-US",
        timezone_id="America/New_York",
        java_script_enabled=True,
        ignore_https_errors=True,
    )
    await context.add_init_script(STEALTH_JS)
    return context

async def _safe_close_context(context):
    """Close context without raising on already-closed browser."""
    try:
        await context.close()
    except Exception:
        pass

# ── YouTube scraper ───────────────────────────────────────────

async def scrape_youtube(niche: str, region: str = "US", max_results: int = 10) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_youtube_inner(niche, region, max_results)

async def _scrape_youtube_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "+")
        url = f"https://www.youtube.com/results?search_query={query}&sp=CAMSAhAB"
        logger.info(f"[YouTube] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_selector("ytd-video-renderer", timeout=15000)
        await asyncio.sleep(2)

        # Extract video data
        items = await page.query_selector_all("ytd-video-renderer")
        for item in items[:max_results]:
            try:
                title_el = await item.query_selector("#video-title")
                title = await title_el.get_attribute("title") or await title_el.inner_text() if title_el else ""
                href = await title_el.get_attribute("href") if title_el else ""
                video_id = href.split("v=")[-1].split("&")[0] if href and "v=" in href else ""

                channel_el = await item.query_selector("#channel-name #text")
                channel = await channel_el.inner_text() if channel_el else "Unknown"

                views_el = await item.query_selector("#metadata-line span:first-child")
                views_text = await views_el.inner_text() if views_el else "0"

                thumb_el = await item.query_selector("img")
                thumbnail = await thumb_el.get_attribute("src") if thumb_el else ""

                if video_id and title and not is_noise(title, href):
                    results.append({
                        "id": video_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "title": title.strip(),
                        "channel": channel.strip(),
                        "views": views_text.strip(),
                        "thumbnail": thumbnail,
                    })
            except Exception as e:
                logger.debug(f"[YouTube] Skip item: {e}")
                continue

        logger.info(f"[YouTube] Found {len(results)} videos for {niche}")
    except Exception as e:
        logger.error(f"[YouTube] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── TikTok scraper ────────────────────────────────────────────

async def scrape_tiktok(niche: str, region: str = "US", max_results: int = 10) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_tiktok_inner(niche, region, max_results)

async def _scrape_tiktok_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "+")
        url = f"https://www.tiktok.com/search/video?q={query}"
        logger.info(f"[TikTok] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for page to load - try multiple selectors
        for selector in ['[data-e2e="search_video-item"]', 'div[class*="DivItemContainer"]', 'div[class*="video-card"]', 'a[href*="/video/"]']:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                break
            except Exception:
                continue
        await asyncio.sleep(3)

        # Scroll to load more
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)

        # Try multiple selector strategies
        items = await page.query_selector_all('[data-e2e="search_video-item"]')
        if not items:
            items = await page.query_selector_all('div[class*="DivItemContainer"]')
        if not items:
            items = await page.query_selector_all('div[class*="video-card"]')

        for item in items[:max_results * 2]:  # Extra to account for noise
            try:
                # Try to get video link
                link_el = await item.query_selector('a[href*="/video/"]')
                if not link_el:
                    link_el = await item.query_selector('a[href*="tiktok.com"]')
                if not link_el:
                    continue

                href = await link_el.get_attribute("href") or ""
                if "/video/" not in href:
                    continue

                # Extract video ID from URL
                vid_match = re.search(r'/video/(\d+)', href)
                video_id = vid_match.group(1) if vid_match else ""
                if not video_id:
                    continue

                # Get title/description
                title_el = await item.query_selector('[data-e2e="search-card-desc"]')
                if not title_el:
                    title_el = await item.query_selector('p[class*="PDesc"]')
                title = await title_el.inner_text() if title_el else ""
                if not title:
                    title = f"TikTok video {video_id}"

                # Get author
                author_el = await item.query_selector('[data-e2e="search-card-user-unique-id"]')
                if not author_el:
                    author_el = await item.query_selector('span[class*="SpanUniqueId"]')
                author = await author_el.inner_text() if author_el else "Unknown"

                # Get views
                views_el = await item.query_selector('[data-e2e="search-card-like-container"]')
                views_text = await views_el.inner_text() if views_el else "0"

                # Get thumbnail
                thumb_el = await item.query_selector('img')
                thumbnail = await thumb_el.get_attribute("src") if thumb_el else ""

                # Filter noise
                if is_noise(title, href):
                    continue

                results.append({
                    "id": video_id,
                    "url": href if href.startswith("http") else f"https://www.tiktok.com{href}",
                    "title": title.strip()[:200],
                    "author": author.strip(),
                    "views": views_text.strip(),
                    "thumbnail": thumbnail,
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[TikTok] Skip item: {e}")
                continue

        logger.info(f"[TikTok] Found {len(results)} videos for {niche}")
    except Exception as e:
        logger.error(f"[TikTok] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── X (Twitter) scraper ───────────────────────────────────────

async def scrape_x(niche: str, region: str = "US", max_results: int = 10) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_x_inner(niche, region, max_results)

async def _scrape_x_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "+")
        url = f"https://x.com/search?q={query}&f=live"
        logger.info(f"[X] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for page to load - try multiple selectors
        for selector in ['[data-testid="tweet"]', 'article', 'a[href*="/status/"]', '[data-testid="tweetText"]']:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                break
            except Exception:
                continue
        await asyncio.sleep(3)

        # Scroll to load more
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)

        # Get tweet articles
        items = await page.query_selector_all('[data-testid="tweet"]')
        if not items:
            items = await page.query_selector_all('article')

        for item in items[:max_results * 2]:
            try:
                # Get tweet link
                link_el = await item.query_selector('a[href*="/status/"]')
                if not link_el:
                    continue
                href = await link_el.get_attribute("href") or ""
                if "/status/" not in href:
                    continue

                # Extract tweet ID
                tid_match = re.search(r'/status/(\d+)', href)
                tweet_id = tid_match.group(1) if tid_match else ""
                if not tweet_id:
                    continue

                # Get tweet text
                text_el = await item.query_selector('[data-testid="tweetText"]')
                text = await text_el.inner_text() if text_el else ""
                if not text or len(text.strip()) < 10:
                    continue

                # Get author
                author_el = await item.query_selector('[data-testid="User-Name"]')
                author_text = await author_el.inner_text() if author_el else ""
                author = author_text.split("@")[-1].split("\n")[0].strip() if author_text else "Unknown"

                # Get engagement
                likes_el = await item.query_selector('[data-testid="like"]')
                likes_text = await likes_el.inner_text() if likes_el else "0"
                retweets_el = await item.query_selector('[data-testid="retweet"]')
                retweets_text = await retweets_el.inner_text() if retweets_el else "0"

                # Filter noise
                if is_noise(text, href):
                    continue

                full_url = href if href.startswith("http") else f"https://x.com{href}"
                results.append({
                    "id": tweet_id,
                    "url": full_url,
                    "title": text.strip()[:200],
                    "author": author,
                    "views": "0",
                    "likes": likes_text.strip(),
                    "retweets": retweets_text.strip(),
                    "thumbnail": "",
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[X] Skip item: {e}")
                continue

        logger.info(f"[X] Found {len(results)} tweets for {niche}")
    except Exception as e:
        logger.error(f"[X] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── Instagram scraper ─────────────────────────────────────────

async def scrape_instagram(niche: str, region: str = "US", max_results: int = 10) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_instagram_inner(niche, region, max_results)

async def _scrape_instagram_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "").replace("+", "")
        url = f"https://www.instagram.com/explore/tags/{query}/"
        logger.info(f"[Instagram] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for page to load - try multiple selectors
        for selector in ["article", 'a[href*="/reel/"]', 'a[href*="/p/"]', 'img[alt]']:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                break
            except Exception:
                continue
        await asyncio.sleep(3)

        # Scroll to load more
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)

        # Get reel/video links
        links = await page.query_selector_all('a[href*="/reel/"]')
        if not links:
            links = await page.query_selector_all('a[href*="/p/"]')

        seen = set()
        for link in links[:max_results * 2]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen:
                    continue
                seen.add(href)

                # Extract shortcode
                sc_match = re.search(r'/(?:reel|p)/([A-Za-z0-9_-]+)', href)
                shortcode = sc_match.group(1) if sc_match else ""
                if not shortcode:
                    continue

                # Get title from alt text or aria
                img_el = await link.query_selector("img")
                title = await img_el.get_attribute("alt") if img_el else ""
                if not title or is_noise(title, href):
                    title = f"Instagram Reel {shortcode}"

                # Get thumbnail
                thumbnail = await img_el.get_attribute("src") if img_el else ""

                full_url = href if href.startswith("http") else f"https://www.instagram.com{href}"
                results.append({
                    "id": shortcode,
                    "url": full_url,
                    "title": title.strip()[:200],
                    "author": "Unknown",
                    "views": "0",
                    "thumbnail": thumbnail,
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Instagram] Skip item: {e}")
                continue

        logger.info(f"[Instagram] Found {len(results)} reels for {niche}")
    except Exception as e:
        logger.error(f"[Instagram] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── Facebook scraper ──────────────────────────────────────────

async def scrape_facebook(niche: str, region: str = "US", max_results: int = 10) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_facebook_inner(niche, region, max_results)

async def _scrape_facebook_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "+")
        url = f"https://www.facebook.com/watch/search/?q={query}"
        logger.info(f"[Facebook] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for page to load - try multiple selectors
        for selector in ['[role="article"]', 'a[href*="/watch/"]', 'a[href*="/videos/"]', 'div[data-pagelet]']:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                break
            except Exception:
                continue
        await asyncio.sleep(3)

        # Scroll to load more
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)

        # Get video links
        links = await page.query_selector_all('a[href*="/watch/"]')
        if not links:
            links = await page.query_selector_all('a[href*="/videos/"]')

        seen = set()
        for link in links[:max_results * 2]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen:
                    continue
                seen.add(href)

                # Extract video ID
                vid_match = re.search(r'/watch/\?v=(\d+)', href)
                if not vid_match:
                    vid_match = re.search(r'/videos/(\d+)', href)
                video_id = vid_match.group(1) if vid_match else ""
                if not video_id:
                    continue

                # Get title
                title_el = await link.query_selector("span")
                title = await title_el.inner_text() if title_el else ""
                if not title or is_noise(title, href):
                    title = f"Facebook Video {video_id}"

                full_url = href if href.startswith("http") else f"https://www.facebook.com{href}"
                results.append({
                    "id": video_id,
                    "url": full_url,
                    "title": title.strip()[:200],
                    "author": "Unknown",
                    "views": "0",
                    "thumbnail": "",
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Facebook] Skip item: {e}")
                continue

        logger.info(f"[Facebook] Found {len(results)} videos for {niche}")
    except Exception as e:
        logger.error(f"[Facebook] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── LinkedIn scraper ──────────────────────────────────────────

async def scrape_linkedin(niche: str, region: str = "US", max_results: int = 10) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_linkedin_inner(niche, region, max_results)

async def _scrape_linkedin_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "+")
        url = f"https://www.linkedin.com/search/results/content/?keywords={query}"
        logger.info(f"[LinkedIn] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for page to load - try multiple selectors
        for selector in [".feed-shared-update-v2", "article", 'a[href*="/feed/update/"]', 'a[href*="linkedin.com/posts/"]']:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                break
            except Exception:
                continue
        await asyncio.sleep(3)

        # Scroll to load more
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)

        # Get post articles
        items = await page.query_selector_all(".feed-shared-update-v2")
        if not items:
            items = await page.query_selector_all("article")

        for item in items[:max_results * 2]:
            try:
                # Get post link
                link_el = await item.query_selector('a[href*="/feed/update/"]')
                if not link_el:
                    link_el = await item.query_selector('a[href*="linkedin.com/posts/"]')
                if not link_el:
                    continue

                href = await link_el.get_attribute("href") or ""
                if not href:
                    continue

                # Extract post ID
                pid_match = re.search(r'(?:update/|posts/)([A-Za-z0-9_-]+)', href)
                post_id = pid_match.group(1) if pid_match else hashlib.md5(href.encode()).hexdigest()[:12]

                # Get text
                text_el = await item.query_selector('.feed-shared-update-v2__description')
                if not text_el:
                    text_el = await item.query_selector('.feed-shared-text')
                text = await text_el.inner_text() if text_el else ""
                if not text or len(text.strip()) < 15:
                    continue
                if is_noise(text, href):
                    continue

                # Get author
                author_el = await item.query_selector('.feed-shared-actor__name')
                author = await author_el.inner_text() if author_el else "Unknown"

                full_url = href if href.startswith("http") else f"https://www.linkedin.com{href}"
                results.append({
                    "id": post_id,
                    "url": full_url,
                    "title": text.strip()[:200],
                    "author": author.strip(),
                    "views": "0",
                    "thumbnail": "",
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[LinkedIn] Skip item: {e}")
                continue

        logger.info(f"[LinkedIn] Found {len(results)} posts for {niche}")
    except Exception as e:
        logger.error(f"[LinkedIn] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── Reddit scraper ────────────────────────────────────────────

async def scrape_reddit(niche: str, region: str = "US", max_results: int = 10) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_reddit_inner(niche, region, max_results)

async def _scrape_reddit_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "+")
        url = f"https://www.reddit.com/search/?q={query}&type=link&sort=relevance"
        logger.info(f"[Reddit] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for page to load - try multiple selectors
        for selector in ['shreddit-post', '[data-testid="post-container"]', 'a[href*="/comments/"]', '[slot="post"]']:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                break
            except Exception:
                continue
        await asyncio.sleep(3)

        # Scroll to load more
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)

        # Get posts
        items = await page.query_selector_all('shreddit-post')
        if not items:
            items = await page.query_selector_all('[data-testid="post-container"]')

        for item in items[:max_results * 2]:
            try:
                # Get post link
                href = await item.get_attribute("permalink") or ""
                if not href:
                    link_el = await item.query_selector('a[href*="/comments/"]')
                    href = await link_el.get_attribute("href") if link_el else ""
                if not href or "/comments/" not in href:
                    continue

                # Extract post ID
                pid_match = re.search(r'/comments/([a-z0-9]+)/', href)
                post_id = pid_match.group(1) if pid_match else ""

                # Get title
                title = await item.get_attribute("post-title") or ""
                if not title:
                    title_el = await item.query_selector('[data-testid="post-content"] h2')
                    title = await title_el.inner_text() if title_el else ""
                if not title or is_noise(title, href):
                    continue

                # Get author
                author = await item.get_attribute("author") or "Unknown"

                # Get score
                score = await item.get_attribute("score") or "0"

                full_url = href if href.startswith("http") else f"https://www.reddit.com{href}"
                results.append({
                    "id": post_id,
                    "url": full_url,
                    "title": title.strip()[:200],
                    "author": author.strip(),
                    "views": score,
                    "thumbnail": "",
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Reddit] Skip item: {e}")
                continue

        logger.info(f"[Reddit] Found {len(results)} posts for {niche}")
    except Exception as e:
        logger.error(f"[Reddit] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── Twitch scraper ────────────────────────────────────────────

async def scrape_twitch(niche: str, region: str = "US", max_results: int = 10) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_twitch_inner(niche, region, max_results)

async def _scrape_twitch_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "+")
        url = f"https://www.twitch.tv/search?term={query}"
        logger.info(f"[Twitch] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        # Wait for page to load - try multiple selectors
        for selector in ['[data-a-target="search-result"]', '.search-result', 'a[href*="/videos/"]', 'a[href*="/clip/"]']:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                break
            except Exception:
                continue
        await asyncio.sleep(3)

        # Get search results
        items = await page.query_selector_all('[data-a-target="search-result"]')
        if not items:
            items = await page.query_selector_all('.search-result')

        for item in items[:max_results * 2]:
            try:
                # Get link
                link_el = await item.query_selector("a")
                href = await link_el.get_attribute("href") if link_el else ""
                if not href:
                    continue

                # Get title
                title_el = await item.query_selector('[data-a-target="search-result-title"]')
                if not title_el:
                    title_el = await item.query_selector("h3")
                title = await title_el.inner_text() if title_el else ""
                if not title or is_noise(title, href):
                    continue

                # Extract ID from URL
                item_id = hashlib.md5(href.encode()).hexdigest()[:12]

                # Get channel name
                channel_el = await item.query_selector('[data-a-target="search-result-channel"]')
                channel = await channel_el.inner_text() if channel_el else "Unknown"

                full_url = href if href.startswith("http") else f"https://www.twitch.tv{href}"
                results.append({
                    "id": item_id,
                    "url": full_url,
                    "title": title.strip()[:200],
                    "author": channel.strip(),
                    "views": "0",
                    "thumbnail": "",
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Twitch] Skip item: {e}")
                continue

        logger.info(f"[Twitch] Found {len(results)} results for {niche}")
    except Exception as e:
        logger.error(f"[Twitch] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── Etsy scraper ──────────────────────────────────────────────

async def scrape_etsy(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_etsy_inner(niche, region, max_results)

async def _scrape_etsy_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "+")
        url = f"https://www.etsy.com/search?q={query}&ref=search_bar"
        logger.info(f"[Etsy] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=45000)

        # Wait for product grid to load
        for selector in [
            'div[data-search-results]',
            'ul[data-search-results]',
            'div.results-list',
            '[class*="listing-card"]',
            'div[class*="v2-listing"]',
        ]:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                break
            except Exception:
                continue

        # Scroll to load more products
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(2)

        # Try multiple selector strategies for product cards
        items = await page.query_selector_all('div[data-search-results] > div')
        if not items:
            items = await page.query_selector_all('ul[data-search-results] > li')
        if not items:
            items = await page.query_selector_all('[class*="listing-card"]')
        if not items:
            items = await page.query_selector_all('div[class*="v2-listing"]')
        if not items:
            items = await page.query_selector_all('li[class*="wt-grid__item-xs-6"]')

        logger.info(f"[Etsy] Found {len(items)} raw product cards")

        for item in items[:max_results * 2]:
            try:
                # Get listing link
                link_el = await item.query_selector('a[href*="/listing/"]')
                if not link_el:
                    link_el = await item.query_selector('a[href*="etsy.com"]')
                if not link_el:
                    continue

                href = await link_el.get_attribute("href") or ""
                if not href or "/listing/" not in href:
                    continue

                # Extract listing ID from URL
                lid_match = re.search(r'/listing/(\d+)', href)
                listing_id = lid_match.group(1) if lid_match else ""
                if not listing_id:
                    listing_id = hashlib.md5(href.encode()).hexdigest()[:12]

                # Get title
                title_el = await item.query_selector('h3')
                if not title_el:
                    title_el = await item.query_selector('[class*="listing-title"]')
                if not title_el:
                    title_el = await item.query_selector('a[href*="/listing/"] span')
                title = await title_el.inner_text() if title_el else ""
                if not title or is_noise(title, href):
                    continue

                # Get price
                price_el = await item.query_selector('[class*="currency-value"]')
                if not price_el:
                    price_el = await item.query_selector('span[class*="price"]')
                if not price_el:
                    price_el = await item.query_selector('p[class*="price"]')
                price_text = await price_el.inner_text() if price_el else "0"
                price = price_text.strip().replace("$", "").replace(",", "").split()[0] if price_text else "0"

                # Get sales/reviews count
                sales_el = await item.query_selector('[class*="reviews-count"]')
                if not sales_el:
                    sales_el = await item.query_selector('span[class*="star"]')
                if not sales_el:
                    sales_el = await item.query_selector('a[href*="#reviews"]')
                sales_text = await sales_el.inner_text() if sales_el else "0"
                sales = re.sub(r'[^0-9.]', '', sales_text) if sales_text else "0"

                # Get shop name
                shop_el = await item.query_selector('[class*="shop-name"]')
                if not shop_el:
                    shop_el = await item.query_selector('span[class*="seller"]')
                shop = await shop_el.inner_text() if shop_el else "Unknown"

                # Get thumbnail
                thumb_el = await item.query_selector('img')
                thumbnail = ""
                if thumb_el:
                    thumbnail = await thumb_el.get_attribute("src") or ""
                    if not thumbnail:
                        thumbnail = await thumb_el.get_attribute("data-src") or ""

                # Get star rating
                rating_el = await item.query_selector('[class*="star-rating"]')
                if not rating_el:
                    rating_el = await item.query_selector('[aria-label*="star"]')
                rating_text = await rating_el.get_attribute("aria-label") if rating_el else ""
                rating_match = re.search(r'([\d.]+)', rating_text) if rating_text else None
                rating = float(rating_match.group(1)) if rating_match else 0.0

                full_url = href if href.startswith("http") else f"https://www.etsy.com{href}"
                results.append({
                    "id": listing_id,
                    "url": full_url,
                    "title": title.strip()[:200],
                    "price": price,
                    "sales": sales,
                    "shop": shop.strip(),
                    "rating": rating,
                    "views": sales,
                    "thumbnail": thumbnail,
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Etsy] Skip item: {e}")
                continue

        logger.info(f"[Etsy] Found {len(results)} products for '{niche}'")
    except Exception as e:
        logger.error(f"[Etsy] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── Generic web scraper ───────────────────────────────────────

async def scrape_web(
    url: str,
    platform: str = "generic",
    niche: str = "",
    max_results: int = 10,
    wait_selector: Optional[str] = None,
    scroll: bool = False,
    region: str = "US",
) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_web_inner(url, platform, niche, max_results, wait_selector, scroll, region)

async def _scrape_web_inner(
    url: str,
    platform: str,
    niche: str,
    max_results: int,
    wait_selector: Optional[str],
    scroll: bool,
    region: str,
) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        logger.info(f"[Web:{platform}] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=10000)
            except Exception:
                logger.warning(f"[Web:{platform}] Wait selector {wait_selector} timed out")

        if scroll:
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(1.5)

        await asyncio.sleep(2)

        # Extract links and titles from the page
        links = await page.query_selector_all("a[href]")
        seen_urls = set()
        for link in links:
            try:
                href = await link.get_attribute("href") or ""
                title = await link.inner_text()
                title = title.strip() if title else ""

                # Apply noise filter
                if is_noise(title, href):
                    continue
                if href in seen_urls:
                    continue
                seen_urls.add(href)

                # Resolve relative URLs
                if href.startswith("/"):
                    from urllib.parse import urljoin
                    href = urljoin(url, href)

                # Filter for content-like URLs
                is_content = any(p in href for p in [
                    "/watch", "/reel", "/shorts", "/video", "/post", "/clip",
                    "tiktok.com", "instagram.com", "facebook.com",
                    "x.com", "twitter.com", "linkedin.com",
                    "reddit.com", "twitch.tv",
                ])

                if is_content or platform in ["tiktok", "instagram", "facebook", "x (twitter)", "linkedin", "reddit", "twitch"]:
                    item_id = hashlib.md5(href.encode()).hexdigest()[:12]
                    results.append({
                        "id": item_id,
                        "url": href,
                        "title": title[:200],
                        "author": platform,
                        "views": "0",
                        "thumbnail": "",
                    })

                if len(results) >= max_results:
                    break
            except Exception:
                continue

        logger.info(f"[Web:{platform}] Found {len(results)} items from {url}")
    except Exception as e:
        logger.error(f"[Web:{platform}] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

# ── FastAPI app ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[CloakBrowser] Starting stealth scraper service")
    yield
    await close_browser()
    logger.info("[CloakBrowser] Shutting down")

app = FastAPI(title="CloakBrowser", version="2.0.0", lifespan=lifespan)

@app.get("/health")
async def health():
    browser_ok = False
    try:
        if _browser and _browser.is_connected():
            browser_ok = True
    except Exception:
        pass
    return {"status": "ok", "service": "cloakbrowser", "browser_connected": browser_ok}

@app.post("/restart")
async def restart_browser():
    """Force restart the browser (admin endpoint)."""
    async with _browser_lock:
        await _cleanup_browser()
    return {"status": "restarted"}

@app.get("/scrape/youtube")
async def scrape_youtube_endpoint(
    niche: str = Query(..., description="Search niche/query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(10, ge=1, le=50),
):
    try:
        candidates = await scrape_youtube(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[YouTube] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

@app.get("/scrape/tiktok")
async def scrape_tiktok_endpoint(
    niche: str = Query(..., description="Search niche/query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(10, ge=1, le=50),
):
    try:
        candidates = await scrape_tiktok(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[TikTok] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

@app.get("/scrape/x")
async def scrape_x_endpoint(
    niche: str = Query(..., description="Search niche/query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(10, ge=1, le=50),
):
    try:
        candidates = await scrape_x(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[X] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

@app.get("/scrape/instagram")
async def scrape_instagram_endpoint(
    niche: str = Query(..., description="Search niche/query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(10, ge=1, le=50),
):
    try:
        candidates = await scrape_instagram(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[Instagram] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

@app.get("/scrape/facebook")
async def scrape_facebook_endpoint(
    niche: str = Query(..., description="Search niche/query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(10, ge=1, le=50),
):
    try:
        candidates = await scrape_facebook(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[Facebook] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

@app.get("/scrape/linkedin")
async def scrape_linkedin_endpoint(
    niche: str = Query(..., description="Search niche/query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(10, ge=1, le=50),
):
    try:
        candidates = await scrape_linkedin(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[LinkedIn] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

@app.get("/scrape/reddit")
async def scrape_reddit_endpoint(
    niche: str = Query(..., description="Search niche/query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(10, ge=1, le=50),
):
    try:
        candidates = await scrape_reddit(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[Reddit] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

@app.get("/scrape/twitch")
async def scrape_twitch_endpoint(
    niche: str = Query(..., description="Search niche/query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(10, ge=1, le=50),
):
    try:
        candidates = await scrape_twitch(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[Twitch] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

@app.get("/scrape/etsy")
async def scrape_etsy_endpoint(
    niche: str = Query(..., description="Product search query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(20, ge=1, le=50),
):
    try:
        candidates = await scrape_etsy(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[Etsy] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

# ── Pinterest scraper ────────────────────────────────────────

async def scrape_pinterest(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_pinterest_inner(niche, region, max_results)

async def _scrape_pinterest_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []

    try:
        query = niche.replace(" ", "+")
        url = f"https://www.pinterest.com/search/pins/?q={query}&rs=typed"
        logger.info(f"[Pinterest] Scraping: {url}")

        await page.goto(url, wait_until="domcontentloaded", timeout=45000)

        # Wait for pin grid to load
        for selector in [
            '[data-test-id="search-page"]',
            '[data-test-id="pinGrid"]',
            'div[data-grid-item]',
            '[role="list"]',
            'div[class*="GrowthUnauthPin"]',
        ]:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                break
            except Exception:
                continue

        await asyncio.sleep(2)

        # Scroll to load more pins
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(2)

        # Extract pin links
        pin_links = await page.query_selector_all('a[href*="/pin/"]')
        if not pin_links:
            pin_links = await page.query_selector_all('a[data-test-id="pin"]')
        if not pin_links:
            pin_links = await page.query_selector_all('div[data-grid-item] a')

        seen_urls = set()
        logger.info(f"[Pinterest] Found {len(pin_links)} pin links")

        for link in pin_links[:max_results * 3]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or "/pin/" not in href or href in seen_urls:
                    continue
                seen_urls.add(href)

                # Extract pin ID
                pin_match = re.search(r'/pin/(\d+)', href)
                pin_id = pin_match.group(1) if pin_match else ""
                if not pin_id:
                    pin_id = hashlib.md5(href.encode()).hexdigest()[:12]

                # Get image
                img_el = await link.query_selector("img")
                title = ""
                thumbnail = ""
                if img_el:
                    title = await img_el.get_attribute("alt") or ""
                    thumbnail = await img_el.get_attribute("src") or ""
                    if not thumbnail:
                        thumbnail = await img_el.get_attribute("data-src") or ""

                if not title or is_noise(title, href):
                    title = f"Pinterest pin {pin_id}"

                # Get description from nearby text
                desc_el = await link.query_selector("[title]")
                if desc_el:
                    alt_title = await desc_el.get_attribute("title") or ""
                    if alt_title and len(alt_title) > len(title):
                        title = alt_title

                full_url = href if href.startswith("http") else f"https://www.pinterest.com{href}"
                results.append({
                    "id": pin_id,
                    "url": full_url,
                    "title": title.strip()[:200],
                    "author": "Unknown",
                    "views": "0",
                    "thumbnail": thumbnail,
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Pinterest] Skip item: {e}")
                continue

        logger.info(f"[Pinterest] Found {len(results)} pins for '{niche}'")
    except Exception as e:
        logger.error(f"[Pinterest] Scrape failed: {e}")
        if "Target page, context or browser has been closed" in str(e):
            async with _browser_lock:
                await _cleanup_browser()
    finally:
        await _safe_close_context(context)

    return results

@app.get("/scrape/pinterest")
async def scrape_pinterest_endpoint(
    niche: str = Query(..., description="Search query"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(20, ge=1, le=50),
):
    try:
        candidates = await scrape_pinterest(niche, region, max_results)
        return {"success": True, "candidates": candidates}
    except Exception as e:
        logger.exception(f"[Pinterest] Endpoint error: {e}")
        return {"success": False, "error": str(e), "candidates": []}

# ── Gumroad scraper ──────────────────────────────────────────

async def scrape_gumroad(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_gumroad_inner(niche, region, max_results)

async def _scrape_gumroad_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://gumroad.com/discover?query={query}"
        logger.info(f"[Gumroad] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        for selector in ['[class*="product"]', '[class*="discover"]', 'a[href*="/l/"]']:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                break
            except Exception:
                continue
        await asyncio.sleep(2)
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)
        links = await page.query_selector_all('a[href*="/l/"]')
        if not links:
            links = await page.query_selector_all('[class*="product-card"] a')
        seen = set()
        for link in links[:max_results * 2]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen:
                    continue
                seen.add(href)
                lid_match = re.search(r'/l/([^/?]+)', href)
                prod_id = lid_match.group(1) if lid_match else hashlib.md5(href.encode()).hexdigest()[:12]
                title_el = await link.query_selector("h3, h4, [class*='title'], p")
                title = await title_el.inner_text() if title_el else ""
                if not title or is_noise(title, href):
                    title = f"Gumroad product {prod_id}"
                price_el = await link.query_selector("[class*='price'], span")
                price_text = await price_el.inner_text() if price_el else "0"
                price = re.sub(r'[^0-9.]', '', price_text.split()[0]) if price_text else "0"
                full_url = href if href.startswith("http") else f"https://gumroad.com{href}"
                results.append({"id": prod_id, "url": full_url, "title": title.strip()[:200], "price": price, "author": "Unknown", "views": "0", "thumbnail": ""})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Gumroad] Skip: {e}")
                continue
        logger.info(f"[Gumroad] Found {len(results)} products for '{niche}'")
    except Exception as e:
        logger.error(f"[Gumroad] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/gumroad")
async def scrape_gumroad_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_gumroad(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── Product Hunt scraper ─────────────────────────────────────

async def scrape_producthunt(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_producthunt_inner(niche, region, max_results)

async def _scrape_producthunt_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://www.producthunt.com/search?q={query}"
        logger.info(f"[ProductHunt] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        await asyncio.sleep(4)

        # Product Hunt uses spotlight-result-product-* buttons (not links!)
        items = await page.query_selector_all('[data-test*="spotlight-result-product"]')
        logger.info(f"[ProductHunt] Found {len(items)} spotlight items")

        for item in items[:max_results]:
            try:
                # Extract product ID from data-test attribute
                dt = await item.get_attribute("data-test") or ""
                prod_match = re.search(r'product-(\d+)', dt)
                prod_id = prod_match.group(1) if prod_match else hashlib.md5(dt.encode()).hexdigest()[:12]

                # Get title (first line of text)
                text = await item.inner_text() or ""
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                title = lines[0] if lines else f"Product Hunt {prod_id}"

                if not title or is_noise(title, ""):
                    title = f"Product Hunt {prod_id}"

                full_url = f"https://www.producthunt.com/products/{prod_id}"
                results.append({"id": prod_id, "url": full_url, "title": title[:200], "author": "Unknown", "views": "0", "thumbnail": ""})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[ProductHunt] Skip: {e}")
                continue
        logger.info(f"[ProductHunt] Found {len(results)} products for '{niche}'")
    except Exception as e:
        logger.error(f"[ProductHunt] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/producthunt")
async def scrape_producthunt_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_producthunt(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── DeviantArt scraper ───────────────────────────────────────

async def scrape_deviantart(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_deviantart_inner(niche, region, max_results)

async def _scrape_deviantart_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://www.deviantart.com/search?q={query}"
        logger.info(f"[DeviantArt] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        for selector in ['[class*="result"]', 'a[href*="/art/"]', '[data-hook="thumb"]']:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                break
            except Exception:
                continue
        await asyncio.sleep(2)
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)
        links = await page.query_selector_all('a[href*="/art/"]')
        seen = set()
        for link in links[:max_results * 2]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen or "/art/" not in href:
                    continue
                seen.add(href)
                art_id = hashlib.md5(href.encode()).hexdigest()[:12]
                img_el = await link.query_selector("img")
                title = ""
                thumbnail = ""
                if img_el:
                    title = await img_el.get_attribute("alt") or ""
                    thumbnail = await img_el.get_attribute("src") or ""
                if not title or is_noise(title, href):
                    title = f"DeviantArt {art_id}"
                full_url = href if href.startswith("http") else f"https://www.deviantart.com{href}"
                results.append({"id": art_id, "url": full_url, "title": title.strip()[:200], "author": "Unknown", "views": "0", "thumbnail": thumbnail})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[DeviantArt] Skip: {e}")
                continue
        logger.info(f"[DeviantArt] Found {len(results)} items for '{niche}'")
    except Exception as e:
        logger.error(f"[DeviantArt] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/deviantart")
async def scrape_deviantart_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_deviantart(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── Behance scraper ──────────────────────────────────────────

async def scrape_behance(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_behance_inner(niche, region, max_results)

async def _scrape_behance_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://www.behance.net/search/projects?search={query}"
        logger.info(f"[Behance] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        for selector in ['[class*="ProjectCover"]', 'a[href*="/gallery/"]', '[class*="project"]']:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                break
            except Exception:
                continue
        await asyncio.sleep(2)
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)
        links = await page.query_selector_all('a[href*="/gallery/"]')
        seen = set()
        for link in links[:max_results * 2]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen:
                    continue
                seen.add(href)
                proj_id = hashlib.md5(href.encode()).hexdigest()[:12]
                img_el = await link.query_selector("img")
                title = ""
                thumbnail = ""
                if img_el:
                    title = await img_el.get_attribute("alt") or ""
                    thumbnail = await img_el.get_attribute("src") or ""
                if not title or is_noise(title, href):
                    title = f"Behance project {proj_id}"
                full_url = href if href.startswith("http") else f"https://www.behance.net{href}"
                results.append({"id": proj_id, "url": full_url, "title": title.strip()[:200], "author": "Unknown", "views": "0", "thumbnail": thumbnail})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Behance] Skip: {e}")
                continue
        logger.info(f"[Behance] Found {len(results)} projects for '{niche}'")
    except Exception as e:
        logger.error(f"[Behance] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/behance")
async def scrape_behance_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_behance(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── Dribbble scraper ─────────────────────────────────────────

async def scrape_dribbble(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_dribbble_inner(niche, region, max_results)

async def _scrape_dribbble_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://dribbble.com/search/{query}"
        logger.info(f"[Dribbble] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        for selector in ['[class*="shot"]', 'a[href*="/shots/"]', '[class*="screenshot"]']:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                break
            except Exception:
                continue
        await asyncio.sleep(2)
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)
        links = await page.query_selector_all('a[href*="/shots/"]')
        seen = set()
        for link in links[:max_results * 2]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen or "/shots/" not in href:
                    continue
                seen.add(href)
                shot_id = hashlib.md5(href.encode()).hexdigest()[:12]
                img_el = await link.query_selector("img")
                title = ""
                thumbnail = ""
                if img_el:
                    title = await img_el.get_attribute("alt") or ""
                    thumbnail = await img_el.get_attribute("src") or ""
                if not title or is_noise(title, href):
                    title = f"Dribbble shot {shot_id}"
                full_url = href if href.startswith("http") else f"https://dribbble.com{href}"
                results.append({"id": shot_id, "url": full_url, "title": title.strip()[:200], "author": "Unknown", "views": "0", "thumbnail": thumbnail})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Dribbble] Skip: {e}")
                continue
        logger.info(f"[Dribbble] Found {len(results)} shots for '{niche}'")
    except Exception as e:
        logger.error(f"[Dribbble] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/dribbble")
async def scrape_dribbble_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_dribbble(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── Unsplash scraper ─────────────────────────────────────────

async def scrape_unsplash(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_unsplash_inner(niche, region, max_results)

async def _scrape_unsplash_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://unsplash.com/s/photos/{query}"
        logger.info(f"[Unsplash] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=35000)
        for selector in ['[class*="photo"]', 'figure', 'a[href*="/photos/"]']:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                break
            except Exception:
                continue
        await asyncio.sleep(2)
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)
        links = await page.query_selector_all('a[href*="/photos/"]')
        seen = set()
        for link in links[:max_results * 2]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen or "/photos/" not in href:
                    continue
                seen.add(href)
                photo_id = hashlib.md5(href.encode()).hexdigest()[:12]
                img_el = await link.query_selector("img")
                title = ""
                thumbnail = ""
                if img_el:
                    title = await img_el.get_attribute("alt") or ""
                    thumbnail = await img_el.get_attribute("src") or ""
                if not title or is_noise(title, href):
                    title = f"Unsplash photo {photo_id}"
                full_url = href if href.startswith("http") else f"https://unsplash.com{href}"
                results.append({"id": photo_id, "url": full_url, "title": title.strip()[:200], "author": "Unknown", "views": "0", "thumbnail": thumbnail})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Unsplash] Skip: {e}")
                continue
        logger.info(f"[Unsplash] Found {len(results)} photos for '{niche}'")
    except Exception as e:
        logger.error(f"[Unsplash] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/unsplash")
async def scrape_unsplash_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_unsplash(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── Pexels scraper ───────────────────────────────────────────

async def scrape_pexels(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_pexels_inner(niche, region, max_results)

async def _scrape_pexels_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://www.pexels.com/search/{query}/"
        logger.info(f"[Pexels] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=35000)
        for selector in ['[class*="photo"]', 'a[href*="/photo/"]', '[data-testid*="image"]']:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                break
            except Exception:
                continue
        await asyncio.sleep(2)
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)
        links = await page.query_selector_all('a[href*="/photo/"]')
        seen = set()
        for link in links[:max_results * 2]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen or "/photo/" not in href:
                    continue
                seen.add(href)
                photo_id = hashlib.md5(href.encode()).hexdigest()[:12]
                img_el = await link.query_selector("img")
                title = ""
                thumbnail = ""
                if img_el:
                    title = await img_el.get_attribute("alt") or ""
                    thumbnail = await img_el.get_attribute("src") or ""
                if not title or is_noise(title, href):
                    title = f"Pexels photo {photo_id}"
                full_url = href if href.startswith("http") else f"https://www.pexels.com{href}"
                results.append({"id": photo_id, "url": full_url, "title": title.strip()[:200], "author": "Unknown", "views": "0", "thumbnail": thumbnail})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Pexels] Skip: {e}")
                continue
        logger.info(f"[Pexels] Found {len(results)} photos for '{niche}'")
    except Exception as e:
        logger.error(f"[Pexels] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/pexels")
async def scrape_pexels_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_pexels(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── Hacker News scraper ──────────────────────────────────────

async def scrape_hackernews(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_hackernews_inner(niche, region, max_results)

async def _scrape_hackernews_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://hn.algolia.com/?q={query}&sort=byDate"
        logger.info(f"[HackerNews] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        for selector in ['.Story', '[class*="story"]', 'a[href*="item?id="]']:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                break
            except Exception:
                continue
        await asyncio.sleep(2)
        items = await page.query_selector_all('.Story')
        if not items:
            items = await page.query_selector_all('[class*="Story"]')
        for item in items[:max_results]:
            try:
                title_el = await item.query_selector('.Story_title a, [class*="title"] a')
                if not title_el:
                    title_el = await item.query_selector("a")
                title = await title_el.inner_text() if title_el else ""
                href = await title_el.get_attribute("href") if title_el else ""
                if not title or is_noise(title, href or ""):
                    continue
                item_id = hashlib.md5((href or title).encode()).hexdigest()[:12]
                score_el = await item.query_selector('[class*="score"], [class*="points"]')
                score_text = await score_el.inner_text() if score_el else "0"
                score = re.sub(r'[^0-9]', '', score_text)
                results.append({"id": item_id, "url": href or "", "title": title.strip()[:200], "author": "Unknown", "views": score, "thumbnail": ""})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[HackerNews] Skip: {e}")
                continue
        logger.info(f"[HackerNews] Found {len(results)} stories for '{niche}'")
    except Exception as e:
        logger.error(f"[HackerNews] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/hackernews")
async def scrape_hackernews_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_hackernews(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── Indie Hackers scraper ────────────────────────────────────

async def scrape_indiehackers(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_indiehackers_inner(niche, region, max_results)

async def _scrape_indiehackers_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://www.indiehackers.com/search?q={query}"
        logger.info(f"[IndieHackers] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        for selector in ['[class*="post"]', 'a[href*="/post/"]', '[class*="feed"]']:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                break
            except Exception:
                continue
        await asyncio.sleep(2)
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)
        links = await page.query_selector_all('a[href*="/post/"]')
        seen = set()
        for link in links[:max_results * 2]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen:
                    continue
                seen.add(href)
                post_id = hashlib.md5(href.encode()).hexdigest()[:12]
                title_el = await link.query_selector("h3, h4, [class*='title']")
                title = await title_el.inner_text() if title_el else ""
                if not title:
                    title = await link.inner_text()
                if not title or is_noise(title, href):
                    title = f"IndieHackers post {post_id}"
                full_url = href if href.startswith("http") else f"https://www.indiehackers.com{href}"
                results.append({"id": post_id, "url": full_url, "title": title.strip()[:200], "author": "Unknown", "views": "0", "thumbnail": ""})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[IndieHackers] Skip: {e}")
                continue
        logger.info(f"[IndieHackers] Found {len(results)} posts for '{niche}'")
    except Exception as e:
        logger.error(f"[IndieHackers] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/indiehackers")
async def scrape_indiehackers_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_indiehackers(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── GitHub Trending scraper ──────────────────────────────────

async def scrape_github(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_github_inner(niche, region, max_results)

async def _scrape_github_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        url = "https://github.com/trending?since=daily"
        logger.info(f"[GitHub] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=35000)
        await asyncio.sleep(3)

        # Get all repo links directly
        links = await page.query_selector_all('h2 a')
        logger.info(f"[GitHub] Found {len(links)} h2 links")
        seen = set()
        for link in links[:max_results]:
            try:
                href = await link.get_attribute("href") or ""
                if not href or href in seen:
                    continue
                seen.add(href)
                title = await link.inner_text() or ""
                title = title.strip()
                if not title or is_noise(title, href):
                    logger.debug(f"[GitHub] Skipping: title={title[:30]}, noise={is_noise(title, href)}")
                    continue
                repo_id = href.strip().replace("/", "_")
                full_url = f"https://github.com{href}"
                author = href.split("/")[1] if href.startswith("/") and "/" in href else "Unknown"
                results.append({"id": repo_id, "url": full_url, "title": title[:200], "author": author, "views": "0", "thumbnail": ""})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[GitHub] Skip: {e}")
                continue
        logger.info(f"[GitHub] Found {len(results)} repos for '{niche}'")
    except Exception as e:
        logger.error(f"[GitHub] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/github")
async def scrape_github_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_github(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── Amazon scraper ───────────────────────────────────────────

async def scrape_amazon(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_amazon_inner(niche, region, max_results)

async def _scrape_amazon_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://www.amazon.com/s?k={query}"
        logger.info(f"[Amazon] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=50000)
        for selector in ['#search', '[data-component-type="s-search-result"]', '.s-result-item']:
            try:
                await page.wait_for_selector(selector, timeout=10000)
                break
            except Exception:
                continue
        await asyncio.sleep(3)
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(2)
        items = await page.query_selector_all('[data-component-type="s-search-result"]')
        if not items:
            items = await page.query_selector_all('.s-result-item')
        for item in items[:max_results * 2]:
            try:
                link_el = await item.query_selector("h2 a, a.a-link-normal[href*='/dp/']")
                if not link_el:
                    continue
                href = await link_el.get_attribute("href") or ""
                if not href or "/dp/" not in href:
                    continue
                asin_match = re.search(r'/dp/([A-Z0-9]{10})', href)
                asin = asin_match.group(1) if asin_match else hashlib.md5(href.encode()).hexdigest()[:12]
                title_el = await item.query_selector("h2 span")
                title = await title_el.inner_text() if title_el else ""
                if not title or is_noise(title, href):
                    continue
                price_el = await item.query_selector(".a-price .a-offscreen, .a-price-whole")
                price_text = await price_el.inner_text() if price_el else "0"
                price = re.sub(r'[^0-9.]', '', price_text.split()[0]) if price_text else "0"
                rating_el = await item.query_selector(".a-icon-alt")
                rating_text = await rating_el.inner_text() if rating_el else ""
                rating_match = re.search(r'([\d.]+)', rating_text)
                rating = float(rating_match.group(1)) if rating_match else 0.0
                reviews_el = await item.query_selector('[aria-label*="stars"] + span, .a-size-base.s-underline-text')
                reviews_text = await reviews_el.inner_text() if reviews_el else "0"
                reviews = re.sub(r'[^0-9]', '', reviews_text)
                full_url = f"https://www.amazon.com{href.split('?')[0]}"
                results.append({"id": asin, "url": full_url, "title": title.strip()[:200], "price": price, "rating": rating, "sales": reviews, "shop": "Amazon", "views": reviews, "thumbnail": ""})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[Amazon] Skip: {e}")
                continue
        logger.info(f"[Amazon] Found {len(results)} products for '{niche}'")
    except Exception as e:
        logger.error(f"[Amazon] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/amazon")
async def scrape_amazon_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_amazon(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

# ── eBay scraper ─────────────────────────────────────────────

async def scrape_ebay(niche: str, region: str = "US", max_results: int = 20) -> list[dict]:
    async with _scrape_semaphore:
        return await _scrape_ebay_inner(niche, region, max_results)

async def _scrape_ebay_inner(niche: str, region: str, max_results: int) -> list[dict]:
    browser = await get_browser()
    context = await new_stealth_context(browser)
    page = await context.new_page()
    results = []
    try:
        query = niche.replace(" ", "+")
        url = f"https://www.ebay.com/sch/i.html?_nkw={query}"
        logger.info(f"[eBay] Scraping: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        for selector in ['.srp-results', '[class*="item"]', 'a[href*="/itm/"]']:
            try:
                await page.wait_for_selector(selector, timeout=8000)
                break
            except Exception:
                continue
        await asyncio.sleep(2)
        for _ in range(2):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1.5)
        items = await page.query_selector_all('.s-item')
        if not items:
            items = await page.query_selector_all('[class*="item__info"]')
        for item in items[:max_results * 2]:
            try:
                link_el = await item.query_selector('a[href*="/itm/"]')
                if not link_el:
                    continue
                href = await link_el.get_attribute("href") or ""
                if not href or "/itm/" not in href:
                    continue
                item_match = re.search(r'/itm/(\d+)', href)
                item_id = item_match.group(1) if item_match else hashlib.md5(href.encode()).hexdigest()[:12]
                title_el = await item.query_selector('.s-item__title, [class*="title"]')
                title = await title_el.inner_text() if title_el else ""
                if not title or is_noise(title, href) or "Shop on eBay" in title:
                    continue
                price_el = await item.query_selector('.s-item__price, [class*="price"]')
                price_text = await price_el.inner_text() if price_el else "0"
                price = re.sub(r'[^0-9.]', '', price_text.split()[0]) if price_text else "0"
                full_url = href.split("?")[0] if "?" in href else href
                results.append({"id": item_id, "url": full_url, "title": title.strip()[:200], "price": price, "author": "eBay", "views": "0", "thumbnail": ""})
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug(f"[eBay] Skip: {e}")
                continue
        logger.info(f"[eBay] Found {len(results)} products for '{niche}'")
    except Exception as e:
        logger.error(f"[eBay] Scrape failed: {e}")
    finally:
        await _safe_close_context(context)
    return results

@app.get("/scrape/ebay")
async def scrape_ebay_endpoint(niche: str = Query(...), region: str = Query("US"), max_results: int = Query(20, ge=1, le=50)):
    try:
        return {"success": True, "candidates": await scrape_ebay(niche, region, max_results)}
    except Exception as e:
        return {"success": False, "error": str(e), "candidates": []}

@app.get("/scrape/web")
async def scrape_web_endpoint(
    url: str = Query(..., description="URL to scrape"),
    platform: str = Query("generic", description="Platform name"),
    niche: str = Query("", description="Search niche"),
    region: str = Query("US", description="Region code"),
    max_results: int = Query(10, ge=1, le=50),
    wait_selector: Optional[str] = Query(None, description="CSS selector to wait for"),
    scroll: bool = Query(False, description="Enable scroll loading"),
):
    try:
        results = await scrape_web(url, platform, niche, max_results, wait_selector, scroll, region)
        return {"success": True, "results": results}
    except Exception as e:
        logger.exception(f"[Web:{platform}] Endpoint error: {e}")
        return {"success": False, "error": str(e), "results": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
