import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Mock version check for email-validator BEFORE any other imports
mock_metadata = MagicMock()
mock_metadata.version.return_value = "2.0.0"
sys.modules["importlib.metadata"] = mock_metadata

# Mock missing optional dependencies globally for tests
sys.modules["langchain"] = MagicMock()
sys.modules["langchain.prompts"] = MagicMock()
sys.modules["langchain.schema"] = MagicMock()
sys.modules["langchain_community.chat_models"] = MagicMock()
sys.modules["langchain.chains"] = MagicMock()
sys.modules["langchain.memory"] = MagicMock()
sys.modules["langchain.output_parsers"] = MagicMock()
sys.modules["google_auth_oauthlib"] = MagicMock()
sys.modules["google_auth_oauthlib.flow"] = MagicMock()
sys.modules["email_validator"] = MagicMock()

import pytest
from services.openclaw.agent import OpenClawAgent
from services.discovery.service import DiscoveryService
from services.langchain.service import langchain_service, LangChainService
from services.crewai.service import crewai_service
from services.openclaw.skills.self_improve import self_improve_skill

@pytest.mark.asyncio
async def test_self_improvement_critic():
    """Test that SkillCritic blocks unsafe code and allows valid code."""
    # 1. Valid code
    valid_code = "print('Hello world')"
    result = await self_improve_skill.critic.analyze_improvement("test", valid_code, "fix")
    assert result["valid"] is True
    
    # 2. Syntax error
    invalid_syntax = "print('Hello world'"
    result = await self_improve_skill.critic.analyze_improvement("test", invalid_syntax, "fix")
    assert result["valid"] is False
    assert "Syntax Error" in result["reason"]
    
    # 3. Safety violation
    unsafe_code = "import os; os.system('rm -rf /')"
    result = await self_improve_skill.critic.analyze_improvement("test", unsafe_code, "fix")
    assert result["valid"] is False
    assert "Safety Violation" in result["reason"]

@pytest.mark.asyncio
async def test_openclaw_hardening():
    agent = OpenClawAgent()
    
    # Check dependency report
    report = agent.get_dependency_report()
    assert "status" in report
    assert "impact" in report
    
    # Check circuit breaker
    agent.circuit_breaker.record_failure()
    agent.circuit_breaker.record_failure()
    agent.circuit_breaker.record_failure()
    assert agent.circuit_breaker.is_open() is True

@pytest.mark.asyncio
async def test_trading_discovery_integration(test_db):
    with patch("services.trading.service.TradingService.is_enabled", return_value=True):
        with patch("services.trading.service.TradingService.get_market_sentiment", new_callable=AsyncMock) as mock_sentiment:
            mock_sentiment.return_value = {
                "sentiment": "Bullish",
                "confidence": "High",
                "crypto_quote": {"change_24h": 15.5}
            }
            
            discovery = DiscoveryService()
            # Scan a financial niche
            candidates = await discovery.find_trending_content("bitcoin", horizon="24h")
            
            # Verify trading candidates were found
            trading_candidates = [c for c in candidates if c.platform == "market_news"]
            assert len(trading_candidates) > 0
            assert "🚨 BREAKING: BITCOIN" in trading_candidates[0].title

@pytest.mark.asyncio
async def test_langchain_virality_prediction():
    # Mock LLM for LangChain
    with patch.object(LangChainService, "is_enabled", return_value=True):
        # Patch the LLMChain class at the module where it is used
        with patch("services.langchain.service.LLMChain") as mock_chain_class:
            mock_instance = MagicMock()
            mock_instance.arun = AsyncMock(return_value='{"viral_score": 85, "probability": 0.85, "feedback": "Great hook!", "suggested_edits": []}')
            mock_chain_class.return_value = mock_instance
            
            with patch("services.langchain.service._langchain_available", True):
                result = await langchain_service.predict_virality_score("Test script", "funny")
                assert result["viral_score"] == 85
                assert result["feedback"] == "Great hook!"
