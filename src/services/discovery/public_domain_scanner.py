import aiohttp
import logging
from typing import List, Optional
from .models import ContentCandidate
from api.config import settings


class PublicDomainScanner:
    def __init__(self):
        self.pexels_base_url = "https://api.pexels.com/videos/search"
        self.archive_base_url = "https://archive.org/advancedsearch.php"

    async def scan_trends(
        self, niche: str, published_after: Optional[any] = None
    ) -> List[ContentCandidate]:
        """
        Scans Archive.org and Pexels for relevant historical and stock footage.
        """
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
                                # Compute engagement from available Pexels data
                                duration = v.get("duration", 0)
                                quality_score = (
                                    min(1.0, duration / 60.0) if duration else 0.0
                                )
                                candidates.append(
                                    ContentCandidate(
                                        id=f"pexels_{v['id']}",
                                        platform="Pexels",
                                        url=v["url"],
                                        author=v["user"]["name"],
                                        title=f"Stock B-Roll: {niche}",
                                        view_count=0,
                                        engagement_rate=quality_score,
                                        metadata={"video_files": v["video_files"]},
                                    )
                                )
            except Exception as e:
                logging.error(f"[PublicDomain] Pexels Error: {e}")

        # 2. Archive.org Public Domain
        try:
            params = {
                "q": f"title:({niche}) AND mediatype:(movies)",
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
                            # Derive engagement from download count (log-scaled 0-1)
                            downloads = doc.get("downloads", 0)
                            engagement = min(
                                1.0, (downloads / 10000.0) if downloads else 0.0
                            )
                            candidates.append(
                                ContentCandidate(
                                    id=f"archive_{doc['identifier']}",
                                    platform="Archive.org",
                                    url=f"https://archive.org/details/{doc['identifier']}",
                                    author=", ".join(
                                        doc.get("creator", ["Public Domain"])
                                    )
                                    if isinstance(doc.get("creator"), list)
                                    else doc.get("creator", "Public Domain"),
                                    title=doc.get("title", "Historical Footage"),
                                    view_count=downloads,
                                    engagement_rate=engagement,
                                    metadata={"identifier": doc["identifier"]},
                                )
                            )
        except Exception as e:
            logging.error(f"[PublicDomain] Archive.org Error: {e}")

        return candidates


base_public_domain_scanner = PublicDomainScanner()
