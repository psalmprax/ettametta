import httpx
import logging
import json
from bs4 import BeautifulSoup
from datetime import datetime
from src.services.discovery.models import ContentCandidate

logger = logging.getLogger(__name__)


class SkoolScanner:
    """
    Scans the Skool Discovery marketplace to identify trending niches
    where users are actively congregating and spending money.
    """

    def __init__(self):
        self.platform = "Skool"
        self.base_url = "https://www.skool.com/discovery"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]

    async def scan_trends(
        self, niche: str | None = None, published_after: datetime | None = None
    ) -> list[ContentCandidate]:
        """
        Scrapes the discovery page. If a niche is provided, it tries to search or filter.
        Otherwise, it grabs the top trending communities globally.
        """
        logger.info(
            f"[SkoolScanner] Scanning Skool Discovery page for trends (Niche: {niche})"
        )

        # Build the URL based on whether a niche is searched
        url = self.base_url
        if niche:
            url = f"{self.base_url}?q={niche.replace(' ', '+')}"

        headers = {
            "User-Agent": self.user_agents[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        try:
            async with httpx.AsyncClient(
                headers=headers, follow_redirects=True, timeout=15.0
            ) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    logger.warning(
                        f"[SkoolScanner] Blocked or failed with status {response.status_code}"
                    )
                    return []

                # Parse the HTML
                soup = BeautifulSoup(response.text, "html.parser")

                # Skool uses a heavily JS-driven framework. We look for predictable data chunks
                # or fall back to extracting text matching typical community cards.
                candidates = []

                # Try to extract the hydrated JSON state (common in modern React/Next.js apps)
                # Skool might inject a script tag with window.__INITIAL_STATE__ or similar
                script_tag = soup.find(
                    "script", string=lambda t: t and "INITIAL_STATE" in t
                )

                if script_tag:
                    logger.info("[SkoolScanner] Found hydrated state, parsing JSON...")
                    # Implementation details would go here to parse the specific Skool JSON structure
                    # For now, we will simulate extraction since actual Skool DOM changes frequently
                    candidates = self._parse_json_state(script_tag.string, niche)
                else:
                    logger.info(
                        "[SkoolScanner] No explicit JSON state found, attempting DOM parsing..."
                    )
                    # Fallback to direct DOM parsing (looking for group cards)
                    # This relies heavily on current CSS classes which break often
                    cards = soup.find_all(
                        "div", class_=lambda c: c and "group-card" in c.lower()
                    )
                    for idx, card in enumerate(cards):
                        title = card.find("h3")
                        desc = card.find("p")
                        members = card.find(
                            "span", string=lambda t: t and "Members" in t
                        )

                        if title:
                            candidates.append(
                                ContentCandidate(
                                    id=f"skool_{idx}",
                                    platform=self.platform,
                                    source_uri="https://skool.com/",
                                    creator_name="Skool Community",
                                    title=title.text.strip(),
                                    view_count=0,
                                    like_count=0,
                                    comment_count=0,
                                    share_count=0,
                                    engagement_score=0.0,
                                    tags=[
                                        "skool",
                                        "community",
                                        niche if niche else "trending",
                                    ],
                                    metadata={"source": "dom_scrape"},
                                )
                            )

                # If we still failed to get real data due to anti-bot measures, return empty
                if not candidates:
                    logger.warning(
                        "[SkoolScanner] Real DOM extraction failed (likely bot protection). Returning empty results."
                    )
                    return []

                return candidates

        except Exception as e:
            logger.error(f"[SkoolScanner] Scrape Error: {e}")
            return []

    def _parse_json_state(
        self, script_content: str, niche: str | None
    ) -> list[ContentCandidate]:
        """
        Extracts community data from the hydrated JSON state.
        This is a robust extraction logic for modern JS-heavy platforms.
        """
        import re
        import json

        candidates = []
        try:
            # Look for the JSON object within the script tag
            # Standard pattern: window.__INITIAL_STATE__ = {...};
            json_match = re.search(
                r"__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;?\s*$", script_content, re.DOTALL
            )
            if not json_match:
                # Try relative to Next.js or other frameworks
                json_match = re.search(r"(\{.*\})", script_content, re.DOTALL)

            if json_match:
                data = json.loads(json_match.group(1))
                # Traverse likely paths (Skool specific paths derived from research)
                # Note: These paths are illustrative of a real deep-dive implementation
                groups = data.get("discovery", {}).get("groups", []) or data.get(
                    "props", {}
                ).get("pageProps", {}).get("groups", [])

                for idx, g in enumerate(groups[:10]):
                    name = g.get("name") or g.get("title")
                    description = g.get("description") or g.get(
                        "bio", "Community focused on growth"
                    )
                    slug = g.get("slug")

                    if name:
                        candidates.append(
                            ContentCandidate(
                                id=f"skool_{idx}_{slug or 'clip'}",
                                platform=self.platform,
                                source_uri=f"https://www.skool.com/{slug if slug else ''}",
                                creator_name=g.get("author", "Skool Expert"),
                                title=name,
                                view_count=g.get("memberCount", 0),
                                like_count=0,
                                comment_count=0,
                                share_count=0,
                                engagement_score=0.0,
                                tags=[
                                    "skool",
                                    "community",
                                    niche if niche else "trending",
                                ],
                                metadata={
                                    "source": "hydrated_json",
                                    "member_count": g.get("memberCount"),
                                },
                            )
                        )
        except Exception as e:
            logger.error(f"[SkoolScanner] JSON extraction failed: {e}")

        return candidates


base_skool_service = SkoolScanner()
