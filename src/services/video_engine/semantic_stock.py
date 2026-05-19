"""
Semantic Stock Matcher
======================

Ranks stock footage by semantic similarity to the script/query using CLIP embeddings.

Instead of returning any Pexels result for "sunset beach", this service:

1. Fetches candidates via keyword search (existing StockService)
2. Downloads them in parallel
3. Extracts key frames (first + middle)
4. CLIP-embeds each frame via NeuralVisionAnalyzer
5. Ranks by cosine similarity to the query text embedding
6. Returns top-N semantically matched clips

This is the "Stock Video Intelligence Layer" from the reference architecture —
turning keyword search into semantic search without needing a vector DB of
pre-indexed stock clips.

Usage:
    from src.services.video_engine.semantic_stock import base_semantic_stock_matcher

    # Rank stock clips for a prompt
    results = await base_semantic_stock_matcher.search(
        query="cinematic tech intro with neon city",
        niche="technology",
        count=3,
    )
    # Returns: [{"url": "...", "path": "/path/to/clip.mp4", "score": 0.89, ...}]
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from typing import Any

import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class SemanticStockMatcher:
    """Ranks stock footage by CLIP embedding similarity to the query text.

    Architecture:
        query text → text embedding (CLIP)
        keyword search → download candidates → frame extraction → image embeddings (CLIP)
        → cosine similarity ranking → top-N results

    The ranking is computed IN-MEMORY per-query (no FAISS persistence needed).
    For frequently-used clips, the ``NeuralVisionAnalyzer`` FAISS index serves
    as a persistent cache across queries.
    """

    def __init__(self, max_candidates: int = 6, download_timeout: int = 60):
        self.max_candidates = max_candidates
        self.download_timeout = download_timeout
        self._download_semaphore = asyncio.Semaphore(4)  # Max 4 concurrent downloads
        self._clip_available: bool | None = None  # Lazily probed, then cached

    async def search(
        self,
        query: str,
        niche: str | None = None,
        count: int = 3,
    ) -> list[dict[str, Any]]:
        """Search and rank stock footage semantically.

        Steps:
        1. Keyword search via StockService (fast, gets candidates)
        2. Download candidates in parallel
        3. Extract frames + CLIP-embed each
        4. Rank by cosine similarity to query text
        5. Return top-K results

        Args:
            query: The semantic query text (e.g., script line or prompt).
            niche: Fallback niche keyword if ``query`` returns no results.
            count: Number of top results to return.

        Returns:
            List of ranked results, sorted by similarity score descending.
            Each item has keys: ``url``, ``path``, ``score``, ``frame_count``.
            Empty list if nothing matched.
        """
        from src.services.video_engine.stock_service import base_stock_service
        from src.services.video_engine.neural_vision_analyzer import base_vision_service

        # Guard: CLIP model must be available (probed once, then cached)
        if self._clip_available is None:
            try:
                probe = await asyncio.wait_for(
                    asyncio.to_thread(base_vision_service.get_text_embedding, "test"),
                    timeout=30.0,
                )
                self._clip_available = probe is not None and not (
                    isinstance(probe, np.ndarray) and probe.size == 0
                )
            except Exception as exc:
                logger.warning("[SemanticStock] CLIP probe timed out or failed: %s", exc)
                self._clip_available = False
        if not self._clip_available:
            logger.warning("[SemanticStock] CLIP model unavailable, falling back to keyword search")
            return await self._keyword_fallback(query, niche, count)

        # Step 1: Keyword search for candidates
        candidates = await base_stock_service.fetch_b_roll(
            keyword=query,
            count=self.max_candidates,
        )
        if not candidates and niche:
            logger.info("[SemanticStock] No candidates for '%s', trying niche '%s'", query, niche)
            candidates = await base_stock_service.fetch_b_roll(
                keyword=niche,
                count=self.max_candidates,
            )

        if not candidates:
            logger.info("[SemanticStock] No candidates found for '%s'", query)
            return []

        logger.info("[SemanticStock] Evaluating %d candidates for query '%s'", len(candidates), query[:40])

        # Step 2: Download candidates in parallel
        downloaded = await self._download_candidates(candidates)

        if not downloaded:
            return []

        # Step 3: Extract frames and compute embeddings
        query_embedding = await asyncio.to_thread(base_vision_service.get_text_embedding, query)
        if query_embedding is None:
            return await self._keyword_fallback(query, niche, count)

        scored: list[dict[str, Any]] = []
        for item in downloaded:
            score = await self._score_clip(item["path"], query_embedding, base_vision_service)
            if score is not None:
                scored.append({
                    "url": item["url"],
                    "path": item["path"],
                    "score": score,
                    "frame_count": item.get("frame_count", 0),
                })

        # Step 4: Rank by similarity
        scored.sort(key=lambda x: x["score"], reverse=True)

        results = scored[:count]
        for r in results:
            logger.info("[SemanticStock] Ranked: %.3f — %s", r["score"], os.path.basename(r["path"]))

        return results

    async def _keyword_fallback(self, query: str, niche: str | None, count: int) -> list[dict[str, Any]]:
        """Fallback: regular keyword search without semantic ranking."""
        from src.services.video_engine.stock_service import base_stock_service

        urls = await base_stock_service.fetch_b_roll(query, count=count)
        if not urls and niche:
            urls = await base_stock_service.fetch_b_roll(niche, count=count)

        results = []
        for url in urls:
            path = await base_stock_service.download_stock_video(url)
            results.append({
                "url": url,
                "path": path or url,
                "score": 0.5,  # Neutral score for fallback
                "frame_count": 0,
            })
        return results

    async def _download_candidates(self, urls: list[str]) -> list[dict[str, Any]]:
        """Download multiple candidate videos in parallel with a semaphore."""
        from src.services.video_engine.stock_service import base_stock_service

        async def _download_one(url: str) -> dict[str, Any] | None:
            async with self._download_semaphore:
                try:
                    path = await asyncio.wait_for(
                        base_stock_service.download_stock_video(url),
                        timeout=self.download_timeout,
                    )
                    if path and os.path.exists(path) and os.path.getsize(path) > 1024:
                        return {"url": url, "path": path, "frame_count": 0}
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning("[SemanticStock] Download failed for %s: %s", url, e)
                return None

        tasks = [_download_one(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, dict) and r is not None:
                downloaded.append(r)
            # isinstance(r, Exception) is silently dropped; _download_one logged the failure already

        logger.info("[SemanticStock] Downloaded %d/%d candidates", len(downloaded), len(urls))
        return downloaded

    async def _score_clip(
        self,
        path: str,
        query_embedding: np.ndarray,
        vision_service: Any,
    ) -> float | None:
        """Score a single clip by its frame embedding similarity to the query.

        Takes the max score across 3 frames (first, middle, last) to be
        robust to different shot compositions within a single clip.
        """
        if not CV2_AVAILABLE or not PIL_AVAILABLE or not os.path.exists(path):
            return None

        try:
            cap = cv2.VideoCapture(path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                cap.release()
                return None

            # Extract frames at beginning, middle, and end
            frame_positions = [0, total_frames // 2, total_frames - 1]
            frames = []
            for pos in frame_positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, min(pos, total_frames - 1)))
                ret, frame = cap.read()
                if ret:
                    # Convert BGR to RGB
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(rgb)
                    frames.append(pil_img)
            cap.release()

            if not frames:
                return None

            # Compute CLIP embeddings for each frame concurrently
            tasks = [
                asyncio.to_thread(vision_service.get_image_embedding, frame_img)
                for frame_img in frames
            ]
            embeddings = await asyncio.gather(*tasks)
            valid_embeddings = [emb for emb in embeddings if emb is not None]
            if not valid_embeddings:
                return None

            # Cosine similarity (both embeddings are already L2-normalized)
            stacked_embeddings = np.stack(valid_embeddings)
            sims = stacked_embeddings @ query_embedding
            best_score = float(np.max(sims))

            return best_score if best_score > 0 else None

        except Exception as e:
            logger.warning("[SemanticStock] Scoring failed for %s: %s", os.path.basename(path), e)
            return None

    async def search_ranked_urls(
        self,
        query: str,
        niche: str | None = None,
        count: int = 3,
    ) -> list[str]:
        """Convenience method: return just the ranked URLs (for DAG node compatibility)."""
        results = await self.search(query, niche=niche, count=count)
        return [r["url"] for r in results]

    async def search_ranked_paths(
        self,
        query: str,
        niche: str | None = None,
        count: int = 3,
    ) -> list[str]:
        """Convenience method: return just the ranked local paths."""
        results = await self.search(query, niche=niche, count=count)
        return [r["path"] for r in results if r.get("path") and os.path.exists(r["path"])]

    async def search_ranked_full(
        self,
        query: str,
        niche: str | None = None,
        count: int = 3,
    ) -> list[dict[str, Any]]:
        """Convenience method: return full ranked results with metadata."""
        return await self.search(query, niche=niche, count=count)


# Singleton
base_semantic_stock_matcher = SemanticStockMatcher()
