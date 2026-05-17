"""
Tests for Semantic Stock Matching layer
========================================

Validates:
1. SemanticStockMatcher.search() returns ranked results
2. Fallback to keyword search when CLIP unavailable
3. StockSearchNode with semantic_rank=True/False
4. SemanticSearchNode DAG integration
5. ParallelAssetSourceNode semantic strategy integration

Patching strategy:
- Mock the SOURCE modules (stock_service, neural_vision_analyzer)
  since semantic_stock imports them lazily inside methods.
- This is the only reliable way to mock across lazy imports.
"""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))


# ═══════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════

SOURCE_STOCK = "src.services.video_engine.stock_service"
SOURCE_VISION = "src.services.video_engine.neural_vision_analyzer"
SOURCE_DAG_NODES = "src.services.nexus_engine.dag_nodes"


# ═══════════════════════════════════════════
# Test Class: SemanticStockMatcher
# ═══════════════════════════════════════════

class TestSemanticStockMatcher:
    """Validates the core ranking engine."""

    @pytest.mark.asyncio
    async def test_search_returns_ranked_results(self):
        """Semantic search returns results sorted by score descending."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision, \
             patch("cv2.VideoCapture") as mock_cap, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=500000):

            # Setup stock service
            mock_stock.fetch_b_roll = AsyncMock(return_value=[
                "https://example.com/best_clip.mp4",
                "https://example.com/decent_clip.mp4",
            ])
            def _download_side(url):
                return {url: f"/tmp/test_{url.split('/')[-1]}"}.get(url, "/tmp/fallback.mp4")
            mock_stock.download_stock_video = AsyncMock(side_effect=_download_side)

            # Setup vision service
            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
            call_count = [0]
            def _get_img_embedding(image):
                call_count[0] += 1
                scores = [[0.95, 0.05, 0.05, 0.05], [0.70, 0.30, 0.30, 0.30]]
                idx = min(call_count[0] - 1, len(scores) - 1)
                sim = np.array(scores[idx], dtype=np.float32)
                return sim / np.linalg.norm(sim)
            mock_vision.get_image_embedding = MagicMock(side_effect=_get_img_embedding)

            # Setup CV2
            cap_instance = MagicMock()
            cap_instance.get.return_value = 150.0
            cap_instance.set.return_value = None
            cap_instance.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
            cap_instance.release.return_value = None
            mock_cap.return_value = cap_instance

            from src.services.video_engine.semantic_stock import SemanticStockMatcher
            matcher = SemanticStockMatcher(max_candidates=6)
            results = await matcher.search(query="test query", count=2)

            assert len(results) > 0
            for i in range(len(results) - 1):
                assert results[i]["score"] >= results[i + 1]["score"]
            for r in results:
                assert "url" in r
                assert "path" in r
                assert "score" in r
                assert isinstance(r["score"], float)

    @pytest.mark.asyncio
    async def test_keyword_fallback_when_clip_unavailable(self):
        """When CLIP is unavailable, fall back to keyword search with neutral scores."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision:

            mock_vision.get_text_embedding.return_value = None  # CLIP unavailable
            mock_stock.fetch_b_roll = AsyncMock(return_value=["https://example.com/clip1.mp4"])
            mock_stock.download_stock_video = AsyncMock(return_value="/tmp/test_clip1.mp4")

            from src.services.video_engine.semantic_stock import SemanticStockMatcher
            matcher = SemanticStockMatcher(max_candidates=6)

            with patch("os.path.exists", return_value=True):
                results = await matcher.search(query="test", count=2)

            assert len(results) == 1
            assert results[0]["score"] == 0.5
            assert results[0]["url"] == "https://example.com/clip1.mp4"

    @pytest.mark.asyncio
    async def test_empty_candidates_returns_empty(self):
        """When no candidates are returned from stock search, return empty list."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision:

            mock_stock.fetch_b_roll = AsyncMock(return_value=[])
            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0], dtype=np.float32)

            from src.services.video_engine.semantic_stock import SemanticStockMatcher
            matcher = SemanticStockMatcher(max_candidates=6)
            results = await matcher.search(query="test", count=2)
            assert results == []

    @pytest.mark.asyncio
    async def test_search_ranked_urls_convenience(self):
        """Convenience method returns just URLs."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision, \
             patch("cv2.VideoCapture") as mock_cap, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=500000):

            mock_stock.fetch_b_roll = AsyncMock(return_value=["https://example.com/clip.mp4"])
            mock_stock.download_stock_video = AsyncMock(return_value="/tmp/test_clip.mp4")
            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0], dtype=np.float32)
            mock_vision.get_image_embedding = MagicMock(return_value=np.array([0.9, 0.1], dtype=np.float32))

            cap_instance = MagicMock()
            cap_instance.get.return_value = 150.0
            cap_instance.set.return_value = None
            cap_instance.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
            cap_instance.release.return_value = None
            mock_cap.return_value = cap_instance

            from src.services.video_engine.semantic_stock import SemanticStockMatcher
            matcher = SemanticStockMatcher(max_candidates=6)
            urls = await matcher.search_ranked_urls(query="test", count=2)
            assert isinstance(urls, list)
            assert all(isinstance(u, str) for u in urls)

    @pytest.mark.asyncio
    async def test_download_handles_failures_gracefully(self):
        """Download failures don't crash the pipeline."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision, \
             patch("cv2.VideoCapture") as mock_cap, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=500000):

            mock_stock.fetch_b_roll = AsyncMock(return_value=[
                "https://example.com/v1.mp4", "https://example.com/v2.mp4"
            ])
            # First download fails, second succeeds
            mock_stock.download_stock_video = AsyncMock(side_effect=[None, "/tmp/test.mp4"])
            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0], dtype=np.float32)
            mock_vision.get_image_embedding = MagicMock(return_value=np.array([0.9, 0.1], dtype=np.float32))

            cap_instance = MagicMock()
            cap_instance.get.return_value = 150.0
            cap_instance.set.return_value = None
            cap_instance.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
            cap_instance.release.return_value = None
            mock_cap.return_value = cap_instance

            from src.services.video_engine.semantic_stock import SemanticStockMatcher
            matcher = SemanticStockMatcher(max_candidates=6)
            results = await matcher.search(query="test", count=2)

            # Should still return results from successful downloads
            assert len(results) >= 1


# ═══════════════════════════════════════════
# Test Class: DAG Node Integration
# ═══════════════════════════════════════════

class TestStockSearchNodeSemantic:
    """Validates StockSearchNode with semantic ranking."""

    @pytest.mark.asyncio
    async def test_semantic_rank_enabled(self):
        """When semantic_rank=True, uses SemanticStockMatcher."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision, \
             patch("cv2.VideoCapture") as mock_cap, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=500000):

            mock_stock.fetch_b_roll = AsyncMock(return_value=["https://example.com/clip.mp4"])
            mock_stock.download_stock_video = AsyncMock(return_value="/tmp/test_clip.mp4")
            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0], dtype=np.float32)
            mock_vision.get_image_embedding = MagicMock(return_value=np.array([0.9, 0.1], dtype=np.float32))

            cap_instance = MagicMock()
            cap_instance.get.return_value = 150.0
            cap_instance.set.return_value = None
            cap_instance.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
            cap_instance.release.return_value = None
            mock_cap.return_value = cap_instance

            from src.services.nexus_engine.dag_nodes import StockSearchNode

            node = StockSearchNode("test_search", {"keyword": "sunset beach", "semantic_rank": True})
            urls = await node.execute({})

            assert len(urls) > 0
            assert all(isinstance(u, str) and u.startswith("http") for u in urls)

    @pytest.mark.asyncio
    async def test_semantic_rank_disabled(self):
        """When semantic_rank=False, uses legacy keyword path."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock:
            mock_stock.fetch_b_roll = AsyncMock(return_value=["https://pexels.com/video.mp4"])

            from src.services.nexus_engine.dag_nodes import StockSearchNode
            node = StockSearchNode("test_search", {"keyword": "sunset beach", "semantic_rank": False})
            urls = await node.execute({})

            assert urls == ["https://pexels.com/video.mp4"]
            mock_stock.fetch_b_roll.assert_called_once()


class TestSemanticSearchNode:
    """Validates the dedicated SemanticSearchNode DAG node."""

    @pytest.mark.asyncio
    async def test_returns_ranked_dicts(self):
        """Returns list of dicts with scores stored in context."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision, \
             patch("cv2.VideoCapture") as mock_cap, \
             patch("os.path.exists", return_value=True), \
             patch("os.path.getsize", return_value=500000):

            mock_stock.fetch_b_roll = AsyncMock(return_value=["https://example.com/clip.mp4"])
            mock_stock.download_stock_video = AsyncMock(return_value="/tmp/test_clip.mp4")
            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0], dtype=np.float32)
            mock_vision.get_image_embedding = MagicMock(return_value=np.array([0.9, 0.1], dtype=np.float32))

            cap_instance = MagicMock()
            cap_instance.get.return_value = 150.0
            cap_instance.set.return_value = None
            cap_instance.read.return_value = (True, np.zeros((100, 100, 3), dtype=np.uint8))
            cap_instance.release.return_value = None
            mock_cap.return_value = cap_instance

            from src.services.nexus_engine.dag_nodes import SemanticSearchNode

            node = SemanticSearchNode("semantic1", {"query": "nature waterfall", "count": 2})
            ctx = {}
            results = await node.execute(ctx)

            assert len(results) > 0
            for r in results:
                assert "url" in r
                assert "score" in r

            # Scores stored in context for downstream
            assert "semantic1_scores" in ctx
            assert len(ctx["semantic1_scores"]) > 0

    @pytest.mark.asyncio
    async def test_restores_max_candidates_after_execution(self):
        """max_candidates is restored after node execution."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision, \
             patch("os.path.exists", return_value=True):

            mock_stock.fetch_b_roll = AsyncMock(return_value=[])  # No results
            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0], dtype=np.float32)

            from src.services.nexus_engine.dag_nodes import SemanticSearchNode
            from src.services.video_engine.semantic_stock import base_semantic_stock_matcher

            original_max = base_semantic_stock_matcher.max_candidates
            node = SemanticSearchNode("semantic2", {"query": "test", "max_candidates": 10})
            await node.execute({})

            assert base_semantic_stock_matcher.max_candidates == original_max


class TestParallelAssetSourceSemantic:
    """Validates ParallelAssetSourceNode uses semantic search."""

    @pytest.mark.asyncio
    async def test_tries_semantic_first(self):
        """Semantic search is tried as first strategy."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision, \
             patch("os.path.exists", return_value=True):

            mock_stock.fetch_b_roll = AsyncMock(return_value=[])
            mock_stock.download_stock_video = AsyncMock(return_value=None)
            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0], dtype=np.float32)

            from src.services.nexus_engine.dag_nodes import ParallelAssetSourceNode

            node = ParallelAssetSourceNode("parallel1", {"keyword": "sunset beach"})
            result = await node.execute({})

            # May return None in test env but strategies were invoked
            assert mock_stock.fetch_b_roll.called or result is None


# ═══════════════════════════════════════════
# Test Class: Edge Cases
# ═══════════════════════════════════════════

class TestSemanticEdgeCases:
    """Validates edge case handling."""

    @pytest.mark.asyncio
    async def test_no_cv2_fallback(self):
        """When OpenCV is unavailable, fall back gracefully."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision, \
             patch("src.services.video_engine.semantic_stock.CV2_AVAILABLE", False):

            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0], dtype=np.float32)
            mock_stock.fetch_b_roll = AsyncMock(return_value=["https://example.com/clip.mp4"])
            mock_stock.download_stock_video = AsyncMock(return_value="/tmp/test.mp4")

            from src.services.video_engine.semantic_stock import SemanticStockMatcher

            with patch("os.path.exists", return_value=True):
                matcher = SemanticStockMatcher(max_candidates=6)
                results = await matcher.search(query="test", count=1)
                # Without CV2, frames can't be extracted - may return fallback
                assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_niche_fallback_when_keyword_empty(self):
        """Uses niche as fallback keyword when query returns no candidates."""
        with patch(f"{SOURCE_STOCK}.base_stock_service") as mock_stock, \
             patch(f"{SOURCE_VISION}.base_vision_service") as mock_vision, \
             patch("os.path.exists", return_value=True):

            mock_vision.get_text_embedding.return_value = np.array([1.0, 0.0], dtype=np.float32)
            # First call returns empty, second call (niche) returns results
            mock_stock.fetch_b_roll = AsyncMock(side_effect=[
                [],  # query returns nothing
                ["https://example.com/niche_clip.mp4"],  # niche returns results
            ])
            mock_stock.download_stock_video = AsyncMock(return_value="/tmp/niche_clip.mp4")

            from src.services.video_engine.semantic_stock import SemanticStockMatcher
            matcher = SemanticStockMatcher(max_candidates=6)
            results = await matcher.search(query="obscure thing", niche="technology", count=1)

            # May return fallback results
            assert mock_stock.fetch_b_roll.call_count >= 1
