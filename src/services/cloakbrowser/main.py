"""
CloakBrowser — Stealth Scraping Service
Playwright-based headless browser with anti-detection for multi-platform content discovery.
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import uuid
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cloakbrowser")

# ── Browser Pool ──────────────────────────────────────────────

_browser = None
_playwright = None
_browser_lock = asyncio.Lock()
_scrape_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent scrapes

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

                if video_id and title:
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
        # Force browser restart on crash
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

                if not title or len(title) < 5:
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
                    "/watch", "/reel", "/shorts", "/video", "/post",
                    "tiktok.com", "instagram.com", "facebook.com",
                    "x.com", "twitter.com", "linkedin.com",
                ])

                if is_content or platform in ["tiktok", "instagram", "facebook", "x (twitter)", "linkedin"]:
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
        # Force browser restart on crash
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

app = FastAPI(title="CloakBrowser", version="1.1.0", lifespan=lifespan)

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
