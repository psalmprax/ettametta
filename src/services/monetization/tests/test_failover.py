import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.services.monetization.orchestrator import MonetizationOrchestrator
from src.services.monetization.strategies.base import BaseMonetizationStrategy

class MockFailingStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche):
        raise Exception("API Down")
    async def generate_cta(self, niche, context):
        raise Exception("API Down")

class MockWorkingStrategy(BaseMonetizationStrategy):
    async def get_assets(self, niche):
        return [{"id": "work", "name": "Working Product"}]
    async def generate_cta(self, niche, context):
        return "Buy Now!"

@pytest.mark.asyncio
async def test_orchestrator_failover():
    """Verify that the orchestrator fails over to a working strategy when the primary fails."""
    orchestrator = MonetizationOrchestrator()
    
    # Setup strategies
    failing = MockFailingStrategy()
    failing.circuit_breaker.failure_threshold = 1
    working = MockWorkingStrategy()
    
    orchestrator.strategies = {
        "primary": failing,
        "secondary": working
    }
    
    # Mock get_active_strategy to return the failing one
    orchestrator.get_active_strategy = AsyncMock(return_value=failing)
    
    # Mock should_monetize to avoid DB connection
    orchestrator.should_monetize = AsyncMock(return_value=True)
    
    # Execute call
    cta = await orchestrator.get_monetization_cta("tech", "context")
    
    # Should have failed over to 'working'
    assert cta == "Buy Now!"
    assert failing.circuit_breaker.state == "OPEN"
    assert failing.circuit_breaker.failure_count >= 1
