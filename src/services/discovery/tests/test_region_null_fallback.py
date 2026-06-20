"""
Unit tests for NULL region fallback in DiscoveryService.

Verifies that all 3 DB query methods treat NULL region as equivalent to 'US'
when querying for US specifically, ensuring backward compatibility with
pre-migration rows that had no region set.

Covers:
- _fetch_db_fallback (via find_trending_content)
- search_content (region parameter)
- get_global_trending (region parameter)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.discovery.service import DiscoveryService


def make_mock_db_row(id_val, title, niche, region, view_count=1000):
    """Create a mock ContentCandidateDB row with the given fields."""
    row = MagicMock()
    row.id = id_val
    row.platform = "youtube"
    row.source_uri = f"https://youtube.com/watch?v={id_val}"
    row.creator_name = "Test Creator"
    row.creator_id = "creator_123"
    row.title = title
    row.description = "Test description"
    row.thumbnail_uri = f"https://picsum.photos/seed/{id_val}/1280/720"
    row.view_count = view_count
    row.like_count = 100
    row.comment_count = 20
    row.share_count = 5
    row.engagement_score = 0.5
    row.viral_score = 75
    row.duration_seconds = 60.0
    row.category = "video"
    row.tags = ["test"]
    row.published_at = None
    row.scanned_at = None
    row.niche = niche
    row.metadata_json = {}
    row.region = region
    return row


class TestNullRegionFallbackFetchDbFallback:
    """Test NULL region fallback in _fetch_db_fallback via find_trending_content."""

    @pytest.mark.asyncio
    async def test_fetch_db_fallback_returns_null_region_rows_for_us(self):
        """
        When querying for niche='Business Ideas' region='US', rows with
        region=NULL should be returned alongside rows with region='US'.
        This is the core backward-compatibility fix.
        """
        mock_row_null = make_mock_db_row("null_1", "NULL Region Video", "Business Ideas", None)
        mock_row_us = make_mock_db_row("us_1", "US Region Video", "Business Ideas", "US")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row_null, mock_row_us]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()
            service.scanners = []
            service.global_scanners = []
            service.video_lead_scanner = MagicMock()

            with patch.object(service, "_log"):
                with patch.object(service, "_run_parallel_scans", new_callable=AsyncMock, return_value=[]):
                    with patch.object(service, "_check_cache", new_callable=AsyncMock, return_value=None):
                        with patch.object(service, "_persist_candidates_batch", new_callable=AsyncMock):
                            with patch.object(service, "_audit_candidates_quality", new_callable=AsyncMock):
                                with patch.object(service, "_filter_candidates", new_callable=AsyncMock, return_value=[]):
                                    with patch.object(service, "_recalculate_viral_scores", new_callable=AsyncMock, return_value=[]):
                                        with patch.object(service, "_ingest_aggregate_signal"):
                                            result = await service.find_trending_content(
                                                niche="Business Ideas",
                                                horizon="30d",
                                                region="US",
                                            )

        # Verify both NULL-region and US-region rows were returned
        assert len(result) == 2
        ids = {r.id for r in result}
        assert ids == {"null_1", "us_1"}

    @pytest.mark.asyncio
    async def test_fetch_db_fallback_does_not_return_other_null_regions_for_non_us(self):
        """
        When querying for region='DE', rows with region=NULL should NOT be
        returned — the NULL fallback only applies to US queries.
        """
        mock_row_de = make_mock_db_row("de_1", "DE Region Video", "Business Ideas", "DE")
        make_mock_db_row("null_2", "NULL Region Video", "Business Ideas", None)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row_de]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()
            service.scanners = []
            service.global_scanners = []
            service.video_lead_scanner = MagicMock()

            with patch.object(service, "_log"):
                with patch.object(service, "_run_parallel_scans", new_callable=AsyncMock, return_value=[]):
                    with patch.object(service, "_check_cache", new_callable=AsyncMock, return_value=None):
                        with patch.object(service, "_persist_candidates_batch", new_callable=AsyncMock):
                            with patch.object(service, "_audit_candidates_quality", new_callable=AsyncMock):
                                with patch.object(service, "_filter_candidates", new_callable=AsyncMock, return_value=[]):
                                    with patch.object(service, "_recalculate_viral_scores", new_callable=AsyncMock, return_value=[]):
                                        with patch.object(service, "_ingest_aggregate_signal"):
                                            result = await service.find_trending_content(
                                                niche="Business Ideas",
                                                horizon="30d",
                                                region="DE",
                                            )

        # Only DE row should be returned, NULL region row excluded
        assert len(result) == 1
        assert result[0].id == "de_1"


class TestNullRegionFallbackSearchContent:
    """Test NULL region fallback in search_content."""

    @pytest.mark.asyncio
    async def test_search_content_returns_null_region_rows_for_us(self):
        """
        search_content(query='Business', region='US') should return rows
        where region='US' OR region IS NULL.
        """
        mock_row_null = make_mock_db_row("null_search_1", "Business NULL", "Business Ideas", None)
        mock_row_us = make_mock_db_row("us_search_1", "Business US", "Business Ideas", "US")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row_null, mock_row_us]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()

            result = await service.search_content(
                query="Business",
                region="US",
                limit=50,
            )

        assert len(result) == 2
        ids = {r.id for r in result}
        assert "null_search_1" in ids
        assert "us_search_1" in ids

    @pytest.mark.asyncio
    async def test_search_content_null_region_only_for_us_not_other_regions(self):
        """
        search_content with region='FR' should NOT return rows with region=NULL.
        Only US queries get the NULL fallback.
        """
        mock_row_fr = make_mock_db_row("fr_1", "Business FR", "Business", "FR")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row_fr]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()

            result = await service.search_content(
                query="Business",
                region="FR",
                limit=50,
            )

        # Only FR row should be returned
        assert len(result) == 1
        assert result[0].id == "fr_1"

    @pytest.mark.asyncio
    async def test_search_content_with_no_region_returns_all(self):
        """
        search_content with region=None should not apply any region filter.
        """
        mock_row_1 = make_mock_db_row("no_region_1", "Business None", "Business", "US")
        mock_row_2 = make_mock_db_row("no_region_2", "Business None 2", "Business", None)
        mock_row_3 = make_mock_db_row("no_region_3", "Business DE", "Business", "DE")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row_1, mock_row_2, mock_row_3]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()

            result = await service.search_content(
                query="Business",
                region=None,
                limit=50,
            )

        assert len(result) == 3


class TestNullRegionFallbackGetGlobalTrending:
    """Test NULL region fallback in get_global_trending."""

    @pytest.mark.asyncio
    async def test_get_global_trending_returns_null_region_rows_for_us(self):
        """
        get_global_trending(region='US') should return rows where region='US'
        OR region IS NULL.
        """
        mock_row_null = make_mock_db_row("global_null_1", "Global NULL", "Motivation", None)
        mock_row_us = make_mock_db_row("global_us_1", "Global US", "Motivation", "US")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row_null, mock_row_us]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()

            result = await service.get_global_trending(
                limit=50,
                min_viral_score=0.0,
                region="US",
            )

        assert len(result) == 2
        ids = {r.id for r in result}
        assert "global_null_1" in ids
        assert "global_us_1" in ids

    @pytest.mark.asyncio
    async def test_get_global_trending_null_region_only_for_us(self):
        """
        get_global_trending(region='CA') should NOT return rows with region=NULL.
        """
        mock_row_ca = make_mock_db_row("ca_1", "CA Video", "Tech", "CA")

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row_ca]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()

            result = await service.get_global_trending(
                limit=50,
                min_viral_score=0.0,
                region="CA",
            )

        assert len(result) == 1
        assert result[0].id == "ca_1"

    @pytest.mark.asyncio
    async def test_get_global_trending_respects_min_viral_score_with_null_region(self):
        """
        get_global_trending should combine min_viral_score filter with
        NULL-region fallback correctly.
        """
        # Row with NULL region and high viral score
        mock_row_null_high = make_mock_db_row("null_high", "High Score NULL", "Tech", None, view_count=50000)
        mock_row_null_high.viral_score = 90

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row_null_high]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()

            result = await service.get_global_trending(
                limit=50,
                min_viral_score=80.0,
                region="US",
            )

        # Should include NULL-region row that meets min_viral_score
        assert len(result) == 1
        assert result[0].id == "null_high"


class TestNullRegionFallbackEdgeCases:
    """Edge case tests for NULL region fallback."""

    @pytest.mark.asyncio
    async def test_fetch_db_fallback_empty_result_when_only_null_rows_exist_for_non_us(self):
        """
        If only NULL-region rows exist for a niche, a 'DE' query should return 0.
        The NULL fallback only applies to US, so 'DE' must match exactly.
        """
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # No DE rows

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()
            service.scanners = []
            service.global_scanners = []
            service.video_lead_scanner = MagicMock()

            with patch.object(service, "_log"):
                with patch.object(service, "_run_parallel_scans", new_callable=AsyncMock, return_value=[]):
                    with patch.object(service, "_check_cache", new_callable=AsyncMock, return_value=None):
                        with patch.object(service, "_persist_candidates_batch", new_callable=AsyncMock):
                            with patch.object(service, "_audit_candidates_quality", new_callable=AsyncMock):
                                with patch.object(service, "_filter_candidates", new_callable=AsyncMock, return_value=[]):
                                    with patch.object(service, "_recalculate_viral_scores", new_callable=AsyncMock, return_value=[]):
                                        with patch.object(service, "_ingest_aggregate_signal"):
                                            result = await service.find_trending_content(
                                                niche="SomeNiche",
                                                horizon="30d",
                                                region="DE",
                                            )

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_db_fallback_returns_null_rows_when_only_null_rows_exist_for_us(self):
        """
        If only NULL-region rows exist for a niche (pre-migration state),
        a 'US' query should still return them via the NULL fallback.
        """
        mock_row_null = make_mock_db_row("old_null_row", "Old NULL Video", "LegacyNiche", None)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_row_null]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_context = AsyncMock()
        mock_db_context.__aenter__ = AsyncMock(return_value=mock_session)
        mock_db_context.__aexit__ = AsyncMock(return_value=None)

        with patch("src.services.discovery.service.async_session_factory", return_value=mock_db_context):
            service = DiscoveryService()
            service.scanners = []
            service.global_scanners = []
            service.video_lead_scanner = MagicMock()

            with patch.object(service, "_log"):
                with patch.object(service, "_run_parallel_scans", new_callable=AsyncMock, return_value=[]):
                    with patch.object(service, "_check_cache", new_callable=AsyncMock, return_value=None):
                        with patch.object(service, "_persist_candidates_batch", new_callable=AsyncMock):
                            with patch.object(service, "_audit_candidates_quality", new_callable=AsyncMock):
                                with patch.object(service, "_filter_candidates", new_callable=AsyncMock, return_value=[]):
                                    with patch.object(service, "_recalculate_viral_scores", new_callable=AsyncMock, return_value=[]):
                                        with patch.object(service, "_ingest_aggregate_signal"):
                                            result = await service.find_trending_content(
                                                niche="LegacyNiche",
                                                horizon="30d",
                                                region="US",
                                            )

        # NULL-region row should be found via the NULL fallback
        assert len(result) == 1
        assert result[0].id == "old_null_row"