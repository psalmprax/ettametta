import pytest
from unittest.mock import AsyncMock, patch
from src.api.utils.resilience import CircuitBreaker


class TestCircuitBreakerCall:
    def setup_method(self):
        from src.services.nexus_engine.platform_composer import PlatformComposer
        self.composer = PlatformComposer()

    @pytest.mark.asyncio
    async def test_returns_default_when_breaker_open(self):
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=60)
        breaker.record_failure()
        assert breaker.is_open() is True
        result = await self.composer._circuit_breaker_call(
            breaker, AsyncMock(return_value="ok"), default="fallback"
        )
        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_success_records_success(self):
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        fn = AsyncMock(return_value="result")
        result = await self.composer._circuit_breaker_call(breaker, fn, "arg1", kwarg1="val")
        fn.assert_awaited_once_with("arg1", kwarg1="val")
        assert result == "result"
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_failure_records_failure(self):
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        fn = AsyncMock(side_effect=RuntimeError("boom"))
        result = await self.composer._circuit_breaker_call(breaker, fn, default="fallback")
        assert result == "fallback"
        assert breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_none_default(self):
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        fn = AsyncMock(return_value="ok")
        result = await self.composer._circuit_breaker_call(breaker, fn)
        assert result == "ok"


class TestGatherWithExceptions:
    def setup_method(self):
        from src.services.nexus_engine.platform_composer import PlatformComposer
        self.gather = PlatformComposer._gather_with_exceptions

    @pytest.mark.asyncio
    async def test_all_success(self):
        async def coro1():
            return [1, 2]
        async def coro2():
            return [3]
        results = await self.gather(coro1(), coro2())
        assert results == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_exception_is_skipped(self):
        async def ok():
            return [10]
        async def fail():
            raise RuntimeError("fail")
        results = await self.gather(ok(), fail())
        assert results == [10]

    @pytest.mark.asyncio
    async def test_all_fail(self):
        async def fail1():
            raise RuntimeError("a")
        async def fail2():
            raise RuntimeError("b")
        results = await self.gather(fail1(), fail2())
        assert results == []

    @pytest.mark.asyncio
    async def test_extract_transforms_results(self):
        async def coro():
            return [{"url": "http://a.com"}, {"url": "http://b.com"}]
        results = await self.gather(coro(), extract=lambda x: x.get("url"))
        assert results == ["http://a.com", "http://b.com"]

    @pytest.mark.asyncio
    async def test_extract_filters_none(self):
        async def coro():
            return [1, 2, 3]
        results = await self.gather(coro(), extract=lambda x: x if x > 1 else None)
        assert results == [2, 3]

    @pytest.mark.asyncio
    async def test_single_result_not_list(self):
        async def coro():
            return "hello"
        results = await self.gather(coro())
        assert results == ["hello"]

    @pytest.mark.asyncio
    async def test_none_result_skipped(self):
        async def none_coro():
            return None
        async def ok_coro():
            return "ok"
        results = await self.gather(none_coro(), ok_coro())
        assert results == ["ok"]


class TestComposeAssetDataclass:
    def test_defaults(self):
        from src.services.nexus_engine.platform_composer import ComposedAsset
        asset = ComposedAsset(url="http://example.com/v.mp4")
        assert asset.url == "http://example.com/v.mp4"
        assert asset.source == "stock"
        assert asset.score == 0.0
        assert asset.viral_score == 0
        assert asset.metadata == {}

    def test_custom_fields(self):
        from src.services.nexus_engine.platform_composer import ComposedAsset
        asset = ComposedAsset(
            url="http://example.com/v.mp4",
            source="platform",
            platform="tiktok",
            score=0.85,
            title="Test Video",
            viral_score=95,
        )
        assert asset.platform == "tiktok"
        assert asset.score == 0.85


class TestPlatformComposerInit:
    def test_breakers_initialized(self):
        from src.services.nexus_engine.platform_composer import PlatformComposer
        c = PlatformComposer()
        assert c.cloak_breaker.name == "PlatformComposer-Cloak"
        assert c.discovery_breaker.name == "PlatformComposer-Discovery"
        assert c.stock_breaker.name == "PlatformComposer-Stock"

    def test_default_platforms(self):
        from src.services.nexus_engine.platform_composer import DEFAULT_PLATFORMS
        assert "youtube" in DEFAULT_PLATFORMS
        assert "tiktok" in DEFAULT_PLATFORMS
        assert "instagram" in DEFAULT_PLATFORMS
        assert "reddit" in DEFAULT_PLATFORMS


class TestSearchStock:
    def setup_method(self):
        from src.services.nexus_engine.platform_composer import PlatformComposer
        self.composer = PlatformComposer()

    @pytest.mark.asyncio
    async def test_search_stock_returns_assets(self):
        with patch.object(self.composer, "_circuit_breaker_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = ["http://pexels.com/1.mp4", "http://pexels.com/2.mp4"]
            assets = await self.composer._search_stock("sunset", 5)
            assert len(assets) == 2
            assert assets[0].source == "stock"
            assert assets[0].platform == "pexels"

    @pytest.mark.asyncio
    async def test_search_stock_empty(self):
        with patch.object(self.composer, "_circuit_breaker_call", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = []
            assets = await self.composer._search_stock("sunset", 5)
            assert assets == []


class TestComposeForDag:
    def setup_method(self):
        from src.services.nexus_engine.platform_composer import PlatformComposer, ComposedAsset
        self.composer = PlatformComposer()
        self.ComposedAsset = ComposedAsset

    @pytest.mark.asyncio
    async def test_returns_two_lists(self):
        stock_asset = self.ComposedAsset(url="http://pexels.com/v.mp4", source="stock")
        with patch.object(self.composer, "_gather_with_exceptions", new_callable=AsyncMock) as mock_gather:
            mock_gather.return_value = [[stock_asset], ["http://yt.com/watch?v=1"]]
            platform_urls, stock_urls = await self.composer.compose_for_dag("sunset", "Nature", count=3)
            assert isinstance(platform_urls, list)
            assert isinstance(stock_urls, list)
            assert "http://yt.com/watch?v=1" in platform_urls
            assert "http://pexels.com/v.mp4" in stock_urls
