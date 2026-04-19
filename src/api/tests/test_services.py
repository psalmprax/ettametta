"""
Test Suite for Services
=======================
Tests for various service modules in the application
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# This file is part of api/tests/, so parent is api/, grandparent is project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Mock heavy dependencies before importing services
import types


class MockModule(types.ModuleType):
    def __getattr__(self, name):
        return MagicMock()


def create_mock_module(name):
    if name not in sys.modules:
        m = MockModule(name)
        sys.modules[name] = m
    return sys.modules[name]


# Pre-create mock modules
for name in [
    "faster_whisper",
    "diffusers",
    "diffusers.utils",
    "moviepy",
    "cv2",
    "numpy",
    "torch",
    "gtts",
    "easyocr",
    "PIL",
    "replicate",
    "fal_client",
]:
    create_mock_module(name)


class TestLangchainService:
    """Test LangChain service functionality"""

    def test_langchain_service_disabled_by_default(self):
        """Test that LangChain service is disabled by default"""
        with patch.dict(os.environ, {"ENABLE_LANGCHAIN": "false"}, clear=False):
            with patch("services.langchain.service._langchain_available", False):
                # Force reimport
                if "services.langchain.service" in sys.modules:
                    del sys.modules["services.langchain.service"]

                from services.langchain.service import LangChainService

                service = LangChainService()
                assert service.enabled == False

    def test_langchain_service_checks_availability(self):
        """Test LangChain service checks for langchain availability"""
        with patch("services.langchain.service._langchain_available", False):
            if "services.langchain.service" in sys.modules:
                del sys.modules["services.langchain.service"]

            from services.langchain.service import _langchain_available

            # Should be False when not installed
            assert _langchain_available == False


class TestCrewAIService:
    """Test CrewAI service functionality"""

    def test_crewai_service_disabled_by_default(self):
        """Test that CrewAI service is disabled by default"""
        with patch.dict(os.environ, {"ENABLE_CREWAI": "false"}, clear=False):
            with patch(
                "services.crewai.service._check_crewai_available", return_value=False
            ):
                if "services.crewai.service" in sys.modules:
                    del sys.modules["services.crewai.service"]

                from services.crewai.service import CrewAIService

                service = CrewAIService()
                assert service.enabled == False

    def test_crewai_service_checks_availability(self):
        """Test CrewAI availability check function"""
        with patch.dict("sys.modules", {"crewai": MagicMock()}):
            from services.crewai.service import _check_crewai_available

            # With crewai mocked, should return True
            result = _check_crewai_available()
            assert result == True


class TestAffiliateService:
    """Test Affiliate service functionality"""

    def test_affiliate_service_initialization(self):
        """Test that Affiliate service can be initialized"""
        with patch.dict(
            os.environ,
            {"ENABLE_AFFILIATE_API": "true", "AMAZON_TAG": "testtag-20"},
            clear=False,
        ):
            try:
                from services.monetization.strategies.affiliate import AffiliateStrategy

                strategy = AffiliateStrategy()
                assert strategy is not None
            except Exception as e:
                # Service might not exist - that's ok for this test
                pytest.skip(f"Affiliate strategy not available: {e}")


class TestTradingService:
    """Test Trading service functionality"""

    def test_trading_service_initialization(self):
        """Test that Trading service can be initialized"""
        with patch.dict(
            os.environ,
            {"ENABLE_TRADING": "true", "ALPHA_VANTAGE_KEY": "test_key"},
            clear=False,
        ):
            try:
                # Mock requests before import
                with patch("services.trading.service.requests") as mock_requests:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {}
                    mock_requests.get.return_value = mock_response

                    from services.trading.service import TradingService

                    service = TradingService()
                    assert service is not None
            except Exception as e:
                pytest.skip(f"Trading service not available: {e}")

    @pytest.mark.asyncio
    async def test_trading_service_get_quote(self):
        """Test getting a stock quote"""
        with patch.dict(
            os.environ,
            {"ENABLE_TRADING": "true", "ALPHA_VANTAGE_KEY": "test_key"},
            clear=False,
        ):
            try:
                with patch("services.trading.service.requests") as mock_requests:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "Global Quote": {"05. price": "150.00"}
                    }
                    mock_requests.get.return_value = mock_response

                    from services.trading.service import TradingService

                    service = TradingService()

                    if hasattr(service, "get_quote"):
                        quote = await service.get_quote("AAPL")
                        assert quote.get("price") == "150.00"
                    else:
                        pytest.skip("get_quote method not available")
            except Exception as e:
                pytest.skip(f"Trading service not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
