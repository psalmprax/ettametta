"""
Platform Composer — Unified Asset Sourcing for Nexus DAG
=========================================================

Aggregates video assets from all available sources (stock APIs,
CloakBrowser platform scraping, Discovery trending, direct URLs)
and ranks them by CLIP semantic similarity.

Usage:
    from src.services.nexus_engine.platform_composer import base_composer_service

    # Full compose: search + download + rank
    assets = await base_composer_service.compose("cinematic sunset", "Nature", count=3)

    # DAG-optimized: return URL lists without downloading
    platform_urls, stock_urls = await base_composer_service.compose_for_dag(
        "cinematic sunset", "Nature", count=3
    )
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from src.api.utils.resilience import CircuitBreaker

logger = logging.getLogger(__name__)

# CloakBrowser platforms to search (order = priority)
DEFAULT_PLATFORMS = ["youtube", "tiktok", "instagram", "reddit"]


@dataclass
class ComposedAsset:
    """A video asset from any source, ready for DAG consumption."""
    url: str
    path: str | None = None
    source: str = "stock"  # "stock" | "platform" | "discovery"
    platform: str | None = None  # "youtube" | "tiktok" | "pexels" | etc.
    score: float = 0.0  # CLIP semantic similarity (0-1)
    title: str | None = None
    viral_score: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class PlatformComposer:
    """Unified asset sourcing across stock, platform, and discovery sources.

    Searches all sources in parallel, downloads platform assets via yt-dlp,
    ranks everything by CLIP semantic similarity, and returns the top-N.
    """

    def __init__(self):
        self.cloak_breaker = CircuitBreaker(
            name="PlatformComposer-Cloak", failure_threshold=3, recovery_timeout=120
        )
        self.discovery_breaker = CircuitBreaker(
            name="PlatformComposer-Discovery", failure_threshold=3, recovery_timeout=120
        )
        self.stock_breaker = CircuitBreaker(
            name="PlatformComposer-Stock", failure_threshold=5, recovery_timeout=60
        )

    async def compose(
        self,
        query: str,
        niche: str,
        count: int = 3,
        platforms: list[str] | None = None,
    ) -> list[ComposedAsset]:
        """Search all sources in parallel, download, rank by CLIP, return top-N.

        Args:
            query:   Search text (e.g. "cinematic sunset beach")
            niche:   Content niche for fallback searches
            count:   Number of top results to return
            platforms: CloakBrowser platforms to search (default: youtube, tiktok, instagram, reddit)

        Returns:
            list[ComposedAsset] sorted by score descending, max `count` items
        """
        platforms = platforms or DEFAULT_PLATFORMS

        # Fire all sources concurrently
        stock_task = asyncio.create_task(self._search_stock(query, count * 2))
        platform_task = asyncio.create_task(
            self._search_platform(query, niche, platforms, count * 2)
        )
        discovery_task = asyncio.create_task(self._search_discovery(niche, count * 2))

        results = await asyncio.gather(
            stock_task, platform_task, discovery_task, return_exceptions=True
        )

        all_assets: list[ComposedAsset] = []
        for r in results:
            if isinstance(r, list):
                all_assets.extend(r)
            elif isinstance(r, Exception):
                logger.warning("[PlatformComposer] Source failed: %s", r)

        if not all_assets:
            logger.warning("[PlatformComposer] No assets from any source for '%s'", query)
            return []

        # Download platform/discovery assets that don't have local paths yet
        downloaded = await self._download_pending(all_assets)

        # Rank by CLIP semantic similarity
        ranked = await self._rank_by_semantics(downloaded, query, count)

        logger.info(
            "[PlatformComposer] Composed %d assets for '%s' (from %d candidates)",
            len(ranked), query, len(all_assets),
        )
        return ranked

    async def compose_for_dag(
        self,
        query: str,
        niche: str,
        count: int = 3,
        platforms: list[str] | None = None,
    ) -> tuple[list[str], list[str]]:
        """DAG-optimized: return (platform_urls, stock_urls) without downloading.

        Platform URLs need yt-dlp download; stock URLs are direct .mp4 links.
        Used by DAG builders to populate ParallelAssetSourceNode params.

        Returns:
            (platform_urls, stock_urls) — both list[str] of URLs
        """
        platforms = platforms or DEFAULT_PLATFORMS

        stock_task = asyncio.create_task(self._search_stock(query, count))
        platform_task = asyncio.create_task(
            self._search_platform_urls(query, niche, platforms, count)
        )

        results = await asyncio.gather(stock_task, platform_task, return_exceptions=True)

        stock_urls: list[str] = []
        platform_urls: list[str] = []

        if isinstance(results[0], list):
            stock_urls = [a.url for a in results[0]]
        if isinstance(results[1], list):
            platform_urls = results[1]

        logger.info(
            "[PlatformComposer] DAG compose for '%s': %d platform + %d stock URLs",
            query, len(platform_urls), len(stock_urls),
        )
        return platform_urls, stock_urls

    # ── Source: Stock APIs (Pexels/Coverr) ──────────────────────

    async def _search_stock(self, query: str, count: int) -> list[ComposedAsset]:
        """Search Pexels/Coverr stock video APIs."""
        if self.stock_breaker.is_open():
            logger.debug("[PlatformComposer] Stock breaker OPEN, skipping")
            return []

        try:
            from src.services.video_engine.stock_service import base_stock_service
            urls = await base_stock_service.fetch_b_roll(query, count=count)
            self.stock_breaker.record_success()
            return [
                ComposedAsset(url=url, source="stock", platform="pexels", score=0.5)
                for url in urls
            ]
        except Exception as e:
            self.stock_breaker.record_failure()
            logger.warning("[PlatformComposer] Stock search failed: %s", e)
            return []

    # ── Source: CloakBrowser Platform Scraping ──────────────────

    async def _search_platform(
        self,
        query: str,
        niche: str,
        platforms: list[str],
        count: int,
    ) -> list[ComposedAsset]:
        """Search CloakBrowser for platform content, return ComposedAssets with URLs."""
        if self.cloak_breaker.is_open():
            logger.debug("[PlatformComposer] Cloak breaker OPEN, skipping")
            return []

        try:
            from src.services.discovery.cloak_scanner import CloakBrowserScanner
            scanner = CloakBrowserScanner()

            # Search all platforms concurrently
            tasks = [
                scanner.scan_platform(p, niche if not query else query)
                for p in platforms
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            assets: list[ComposedAsset] = []
            for i, r in enumerate(results):
                if isinstance(r, list):
                    for candidate in r[:count]:
                        if candidate.source_uri:
                            assets.append(ComposedAsset(
                                url=candidate.source_uri,
                                source="platform",
                                platform=platforms[i] if i < len(platforms) else "unknown",
                                score=0.0,  # Will be ranked by CLIP later
                                title=candidate.title,
                                viral_score=candidate.viral_score or 0,
                            ))
                elif isinstance(r, Exception):
                    logger.debug("[PlatformComposer] Platform %s failed: %s", platforms[i], r)

            self.cloak_breaker.record_success()
            return assets[:count]
        except Exception as e:
            self.cloak_breaker.record_failure()
            logger.warning("[PlatformComposer] Platform search failed: %s", e)
            return []

    async def _search_platform_urls(
        self,
        query: str,
        niche: str,
        platforms: list[str],
        count: int,
    ) -> list[str]:
        """Search platforms and return raw URLs (for DAG compose_for_dag)."""
        assets = await self._search_platform(query, niche, platforms, count)
        return [a.url for a in assets]

    # ── Source: Discovery Service (Trending) ────────────────────

    async def _search_discovery(self, niche: str, count: int) -> list[ComposedAsset]:
        """Query Discovery service for trending content in the niche."""
        if self.discovery_breaker.is_open():
            logger.debug("[PlatformComposer] Discovery breaker OPEN, skipping")
            return []

        try:
            from src.services.discovery.service import base_discovery_service
            candidates = await base_discovery_service.find_trending_content(
                niche=niche, min_viral_score=30
            )
            self.discovery_breaker.record_success()

            assets: list[ComposedAsset] = []
            for c in candidates[:count]:
                if c.source_uri:
                    assets.append(ComposedAsset(
                        url=c.source_uri,
                        source="discovery",
                        platform=c.platform,
                        score=0.0,
                        title=c.title,
                        viral_score=c.viral_score or 0,
                    ))
            return assets
        except Exception as e:
            self.discovery_breaker.record_failure()
            logger.warning("[PlatformComposer] Discovery search failed: %s", e)
            return []

    # ── Download Pending Assets ─────────────────────────────────

    async def _download_pending(self, assets: list[ComposedAsset]) -> list[ComposedAsset]:
        """Download platform/discovery assets that don't have local paths yet.

        Stock assets already have direct .mp4 URLs and don't need yt-dlp.
        Platform URLs (YouTube, TikTok, etc.) need yt-dlp download.
        """
        from src.services.video_engine.downloader import base_downloader_service

        async def _download_one(asset: ComposedAsset) -> ComposedAsset:
            if asset.path and os.path.exists(asset.path):
                return asset  # Already downloaded
            if asset.source == "stock":
                return asset  # Stock URLs are direct .mp4, no download needed
            try:
                path = await base_downloader_service.download_video(asset.url)
                if path and os.path.exists(path):
                    asset.path = path
            except Exception as e:
                logger.debug("[PlatformComposer] Download failed for %s: %s", asset.url, e)
            return asset

        # Download platform assets concurrently (limit to 5 to avoid overload)
        semaphore = asyncio.Semaphore(5)

        async def _guarded_download(a: ComposedAsset) -> ComposedAsset:
            async with semaphore:
                return await _download_one(a)

        tasks = [_guarded_download(a) for a in assets]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        downloaded: list[ComposedAsset] = []
        for r in results:
            if isinstance(r, ComposedAsset):
                downloaded.append(r)
            elif isinstance(r, Exception):
                logger.debug("[PlatformComposer] Download error: %s", r)

        return downloaded

    # ── CLIP Semantic Ranking ───────────────────────────────────

    async def _rank_by_semantics(
        self,
        assets: list[ComposedAsset],
        query: str,
        count: int,
    ) -> list[ComposedAsset]:
        """Rank assets by CLIP semantic similarity to the query.

        Falls back to viral_score ordering if CLIP is unavailable.
        Only ranks assets that have local file paths (downloaded).
        """
        # Separate downloaded vs URL-only assets
        downloaded = [a for a in assets if a.path and os.path.exists(a.path)]
        url_only = [a for a in assets if not a.path or not os.path.exists(a.path)]

        if not downloaded:
            # Nothing to rank by CLIP — sort by viral_score
            url_only.sort(key=lambda a: a.viral_score, reverse=True)
            return url_only[:count]

        try:
            from src.services.video_engine.semantic_stock import base_semantic_stock_matcher

            # Build path list for CLIP ranking
            paths = [a.path for a in downloaded]

            # Use the semantic stock matcher's internal CLIP ranking
            # We'll extract frames and rank manually since search() does its own stock lookup
            ranked_items = []
            for asset in downloaded:
                try:
                    # Extract middle frame and CLIP-embed it
                    import cv2
                    cap = cv2.VideoCapture(asset.path)
                    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2 if total > 0 else 0)
                    ret, frame = cap.read()
                    cap.release()

                    if ret:
                        # Use the vision analyzer for CLIP embedding
                        from src.services.video_engine.vision_analyzer import base_vision_analyzer
                        frame_embedding = await base_vision_analyzer.embed_frame(frame)
                        query_embedding = await base_vision_analyzer.embed_text(query)

                        if frame_embedding is not None and query_embedding is not None:
                            import numpy as np
                            similarity = float(np.dot(frame_embedding, query_embedding) / (
                                np.linalg.norm(frame_embedding) * np.linalg.norm(query_embedding) + 1e-8
                            ))
                            asset.score = max(0.0, similarity)
                        else:
                            asset.score = 0.5  # Neutral if embedding fails
                except Exception:
                    asset.score = 0.5  # Neutral fallback

                ranked_items.append(asset)

            # Sort by score descending
            ranked_items.sort(key=lambda a: a.score, reverse=True)

            # Fill remaining slots with URL-only assets (sorted by viral_score)
            url_only.sort(key=lambda a: a.viral_score, reverse=True)
            result = ranked_items[:count]
            if len(result) < count:
                result.extend(url_only[: count - len(result)])

            return result

        except Exception as e:
            logger.warning("[PlatformComposer] CLIP ranking failed, using viral_score: %s", e)
            all_items = downloaded + url_only
            all_items.sort(key=lambda a: a.viral_score, reverse=True)
            return all_items[:count]


# Singleton
base_composer_service = PlatformComposer()
