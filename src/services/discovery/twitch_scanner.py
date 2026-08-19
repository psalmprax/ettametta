import httpx
import logging
import json
import re
import random
from .models import ContentCandidate

logger = logging.getLogger(__name__)


class TwitchScanner:
    """
    Scans Twitch for top clips in specified categories using web scraping.
    Twitch API requires Client-ID authentication, but we can scrape the
    directory pages for free discovery.
    """

    def __init__(self):
        self.platform = "Twitch"
        self.base_url = "https://www.twitch.tv"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ]

    async def scan_trends(self, niche: str, **kwargs) -> list[ContentCandidate]:
        """
        Scans Twitch for top clips in categories related to the niche.
        Uses the directory and search pages for discovery.
        """
        logger.info(f"[TwitchScanner] Scanning Twitch for clips in: {niche}")

        candidates = []

        # Try browsing categories
        try:
            results = await self._browse_categories(niche)
            candidates.extend(results)
        except Exception as e:
            logger.warning(f"[TwitchScanner] Category browse failed: {e}")

        # Try searching
        if not candidates:
            try:
                results = await self._search_clips(niche)
                candidates.extend(results)
            except Exception as e:
                logger.warning(f"[TwitchScanner] Search failed: {e}")

        # Remove duplicates
        seen = set()
        unique = []
        for c in candidates:
            if c.source_uri not in seen:
                seen.add(c.source_uri)
                unique.append(c)

        logger.info(f"[TwitchScanner] Found {len(unique)} clips")
        return unique[:15]

    async def _browse_categories(self, niche: str) -> list[ContentCandidate]:
        """Browse Twitch categories/directory."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        url = f"{self.base_url}/directory"
        candidates = []

        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    return []

                # Look for JSON data in script tags
                script_matches = re.findall(
                    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    response.text,
                    re.DOTALL
                )

                for json_str in script_matches:
                    try:
                        data = json.loads(json_str)
                        clips = self._extract_clips_from_json(data, niche)
                        candidates.extend(clips)
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"[TwitchScanner] Browse error: {e}")

        return candidates

    async def _search_clips(self, niche: str) -> list[ContentCandidate]:
        """Search Twitch for clips."""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # Twitch search URL
        url = f"{self.base_url}/search/clips?term={niche.replace(' ', '%20')}"

        candidates = []

        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15.0) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    return []

                # Extract JSON data
                script_matches = re.findall(
                    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    response.text,
                    re.DOTALL
                )

                for json_str in script_matches:
                    try:
                        data = json.loads(json_str)
                        clips = self._extract_clips_from_json(data, niche)
                        candidates.extend(clips)
                    except Exception:
                        pass

        except Exception as e:
            logger.warning(f"[TwitchScanner] Search error: {e}")

        return candidates

    def _extract_clips_from_json(self, data: dict, niche: str) -> list[ContentCandidate]:
        """Extract clip data from Twitch JSON."""
        try:
            edges = self._find_clips_edges(data)
            candidates = []

            for edge in edges:
                node = edge.get("node", edge)
                candidate = self._parse_single_clip(node, niche)
                if candidate:
                    candidates.append(candidate)

            return candidates

        except Exception as e:
            logger.debug(f"[TwitchScanner] Clip extraction error: {e}")
            return []

    def _find_clips_edges(self, data: dict) -> list:
        """Navigate Twitch's complex JSON structure to find clip edges."""
        props = data.get("props", {})
        page_props = props.get("pageProps", {})

        # Try different paths for clips data
        clips_data = page_props.get("clips") or page_props.get("directory")
        if not clips_data or not isinstance(clips_data, dict):
            return []

        # Return the first list found among common keys
        for key in ["edges", "clips", "items"]:
            if key in clips_data:
                return clips_data.get(key, [])

        return []

    def _parse_single_clip(self, node: dict, niche: str) -> ContentCandidate | None:
        """Parse a single Twitch clip node into a ContentCandidate."""
        clip_id = node.get("slug") or node.get("id")
        slug = node.get("slug", "")
        if not clip_id or not slug:
            return None

        # Basic Info
        title = node.get("title", "Twitch Clip")
        streamer = node.get("broadcaster", {}).get("displayName", "Unknown")
        game = node.get("game", {}).get("displayName", niche)

        # Metrics & Engagement
        views = node.get("viewCount") or node.get("view_count") or 0
        engagement_score = 0.05 if views > 1000 else 0.08

        # Image & URL
        thumbnail = self._get_thumbnail_url(node)
        url = f"{self.base_url}/clip/{slug}"

        return ContentCandidate(
            id=f"twitch_{clip_id}",
            platform="Twitch Clips",
            source_uri=url,
            creator_name=streamer,
            title=title[:100],
            view_count=views,
            like_count=0,
            comment_count=0,
            share_count=0,
            engagement_score=engagement_score,
            thumbnail_uri=thumbnail,
            metadata={"game": game, "niche": niche}
        )

    def _get_thumbnail_url(self, node: dict) -> str:
        """Handle different Twitch thumbnail data structures."""
        thumb = node.get("thumbnailURL") or node.get("thumbnail")
        if isinstance(thumb, dict):
            return thumb.get("url", "")
        return str(thumb) if thumb else ""


base_twitch_service = TwitchScanner()
