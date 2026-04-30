import aiohttp
import logging
from typing import Any
from .models import ContentCandidate
from src.api.config import settings


class PublicDomainScanner:
    def __init__(self):
        self.pexels_base_url = "https://api.pexels.com/videos/search"
        self.archive_base_url = "https://archive.org/advancedsearch.php"

    async def scan_trends(
        self, niche: str, published_after: Any | None = None
    ) -> list[ContentCandidate]:
        """
        Scans Archive.org and Pexels for relevant historical and stock footage.
        Includes a relaxation loop to ensure results.
        """
        # Clean the niche for search
        clean_niche = "".join(e for e in niche if e.isalnum() or e.isspace()).strip()
        keywords = clean_niche.split()
        
        # Relaxation attempts: full query -> first two words -> first word
        attempts = [
            clean_niche,
            " ".join(keywords[:2]) if len(keywords) > 2 else None,
            keywords[0] if keywords else "cinematic"
        ]
        
        for query in attempts:
            if not query: continue
            candidates = await self._perform_scan(query)
            if candidates:
                logging.info(f"✨ [PublicDomain] Found {len(candidates)} candidates for '{query}'")
                return candidates
        
        return []

    async def _perform_scan(self, niche: str) -> list[ContentCandidate]:
        """Internal scan logic for a specific query string"""
        candidates = []
        
        # 1. Pexels Stock Sourcing
        if settings.PEXELS_API_KEY:
            try:
                headers = {"Authorization": settings.PEXELS_API_KEY}
                params = {"query": niche, "per_page": 5, "orientation": "portrait"}
                async with aiohttp.ClientSession(headers=headers) as session:
                    async with session.get(self.pexels_base_url, params=params) as res:
                        if res.status == 200:
                            data = await res.json()
                            for v in data.get("videos", []):
                                duration = v.get("duration", 0)
                                quality_score = (min(1.0, duration / 60.0) if duration else 0.0)
                                candidates.append(
                                    ContentCandidate(
                                        id=f"pexels_{v['id']}",
                                        platform="Pexels",
                                        source_uri=v["url"],
                                        creator_name=v["user"]["name"],
                                        title=f"Stock: {niche}",
                                        view_count=0,
                                        like_count=0,
                                        comment_count=0,
                                        share_count=0,
                                        engagement_score=quality_score,
                                        metadata={"video_files": v["video_files"]},
                                    )
                                )
            except Exception as e:
                logging.error(f"[PublicDomain] Pexels Error: {e}")

        # 2. Archive.org Public Domain (More restrictive title search)
        try:
            # Clean for Archive quoting
            safe_niche = niche.replace('"', '').replace('(', '').replace(')', '')
            params = {
                "q": f"title:({safe_niche}) AND mediatype:(movies)",
                "output": "json",
                "rows": 3,
                "sort[]": "downloads desc",
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(self.archive_base_url, params=params) as res:
                    if res.status == 200:
                        data = await res.json()
                        docs = data.get("response", {}).get("docs", [])
                        for doc in docs:
                            downloads = doc.get("downloads", 0)
                            engagement = min(1.0, (downloads / 10000.0) if downloads else 0.0)
                            candidates.append(
                                ContentCandidate(
                                    id=f"archive_{doc['identifier']}",
                                    platform="Archive.org",
                                    source_uri=f"https://archive.org/details/{doc['identifier']}",
                                    creator_name=", ".join(doc.get("creator", ["Public Domain"])) 
                                           if isinstance(doc.get("creator"), list) 
                                           else doc.get("creator", "Public Domain"),
                                    title=doc.get("title", "Historical Footage"),
                                    view_count=downloads,
                                    like_count=0,
                                    comment_count=0,
                                    share_count=0,
                                    engagement_score=engagement,
                                    metadata={"identifier": doc["identifier"]},
                                )
                            )
        except Exception as e:
            logging.error(f"[PublicDomain] Archive.org Error: {e}")

        return candidates


base_public_domain_service = PublicDomainScanner()
