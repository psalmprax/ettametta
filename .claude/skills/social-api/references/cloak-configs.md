# CloakBrowser Platform Configurations

Defined in `src/services/discovery/cloak_platform_config.py`.

## Architecture

```
CloakBrowserScanner (cloak_scanner.py)
  │
  ├─ HTTP client: httpx
  ├─ Endpoint: http://discovery-scraper:8010
  ├─ Concurrency: Semaphore(3)
  ├─ Retry: configurable backoff per platform
  └─ Parsers: per-platform view count extraction
```

## Platform Configs

### YouTube
- **Endpoint:** `/scrape/youtube` (dedicated)
- **Wait selector:** `ytd-video-renderer`
- **Scroll:** No
- **Notes:** Dedicated endpoint with YouTube-specific parsing

### TikTok
- **Endpoint:** `/scrape/web` (generic)
- **Wait selector:** `[data-e2e="search_video-item"]`
- **Scroll:** Yes
- **URL pattern:** `https://www.tiktok.com/search/video?q={niche}`

### Instagram
- **Endpoint:** `/scrape/web` (generic)
- **Wait selector:** `article` or post containers
- **Scroll:** Yes
- **URL pattern:** `https://www.instagram.com/explore/tags/{niche}/`

### Facebook
- **Endpoint:** `/scrape/web` (generic)
- **Wait selector:** Video containers
- **Scroll:** Yes
- **URL pattern:** `https://www.facebook.com/watch/search/?q={niche}`

### X/Twitter
- **Endpoint:** `/scrape/web` (generic)
- **Wait selector:** `[data-testid="tweet"]`
- **Scroll:** Yes
- **URL pattern:** `https://x.com/search?q={niche}&f=live`

### LinkedIn
- **Endpoint:** `/scrape/web` (generic)
- **Wait selector:** Content cards
- **Scroll:** Yes
- **URL pattern:** `https://www.linkedin.com/search/results/content/?keywords={niche}`

## Fallback Pattern

Each `cloak_*_scanner.py` follows this pattern:

```python
class CloakPlatformScanner:
    async def scan_trends(self, niche, limit=20):
        try:
            # Primary: CloakBrowser stealth engine
            results = await self.cloak_scanner.scan_platform(
                platform="platform_name",
                niche=niche,
                limit=limit,
            )
            if results:
                return results
        except Exception as e:
            logger.warning(f"CloakBrowser failed for platform: {e}")
        
        # Fallback: httpx-based scraper
        return await self.httpx_scanner.scan_trends(niche=niche, limit=limit)
```

## View Count Parsing

The CloakBrowser scanner handles multiple view count formats:
- `"1.2M"` → 1,200,000
- `"500K"` → 500,000
- `"1,234"` → 1,234
- `"1.2万"` → 12,000 (Chinese)

## No CloakBrowser Support

These platforms have httpx-only scrapers:
- Snapchat
- Twitch
- Pinterest
- Bilibili
- Rumble
- Reddit (uses `.json` endpoints, no browser needed)
- DuckDuckGo
- Google Search
- Google Trends
