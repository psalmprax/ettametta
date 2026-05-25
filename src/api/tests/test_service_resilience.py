import pytest
import time
import asyncio
import httpx
from unittest.mock import patch
from src.api.utils.resilience import CircuitBreaker
from src.services.llm.service import UnifiedLLMService, LLMProvider
from src.services.llm.intelligence_hub import IntelligenceHub

class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=1)
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
        assert not cb.is_open()

    def test_open_circuit(self):
        cb = CircuitBreaker(name="test", failure_threshold=2, recovery_timeout=1)
        cb.record_failure()
        assert cb.state == "CLOSED"
        
        cb.record_failure()
        assert cb.state == "OPEN"
        assert cb.is_open()

    def test_half_open_recovery(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        assert cb.is_open()
        
        # Wait for recovery timeout
        time.sleep(0.15)
        assert not cb.is_open()
        assert cb.state == "HALF_OPEN"

    def test_reset_after_success(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        time.sleep(0.15)
        cb.is_open() # Triggers transition to HALF_OPEN
        
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

class TestUnifiedLLMService:
    @patch("src.services.llm.service.os.getenv")
    def test_initialization(self, mock_getenv):
        def side_effect(key, default=None):
            if key == "DEFAULT_LLM_PROVIDER": return "openai"
            return "fake_key"
        mock_getenv.side_effect = side_effect
        service = UnifiedLLMService()
        
        # Verify circuit breakers are initialized (the bug I fixed)
        assert hasattr(service, "circuit_breakers")
        assert len(service.circuit_breakers) > 0
        assert LLMProvider.OPENAI in service.circuit_breakers
        assert isinstance(service.circuit_breakers[LLMProvider.OPENAI], CircuitBreaker)

    @patch("src.services.llm.service.os.getenv")
    @patch("httpx.AsyncClient.post")
    def test_circuit_breaker_integration(self, mock_post, mock_getenv):
        mock_getenv.return_value = "fake_key"
        mock_post.side_effect = httpx.ConnectError("API Down")
        
        service = UnifiedLLMService()
        # Set threshold to 3 to match tenacity default retries
        service.circuit_breakers[LLMProvider.GROQ].failure_threshold = 3
        
        with pytest.raises(httpx.ConnectError):
            asyncio.run(service._call_api(LLMProvider.GROQ, "model", "prompt", None, 0.7, 100))
        
        # Should have recorded 3 failures and opened the circuit
        assert service.circuit_breakers[LLMProvider.GROQ].failure_count == 3
        assert service.circuit_breakers[LLMProvider.GROQ].state == "OPEN"

class TestIntelligenceHub:
    def test_initialization(self):
        hub = IntelligenceHub()
        
        # Verify circuit breakers are initialized with names (the bug I fixed)
        assert len(hub.breakers) == 6
        for name, cb in hub.breakers.items():
            assert cb.name != "Generic" # Should be custom named
            assert isinstance(cb.failure_threshold, int)

    @patch.object(IntelligenceHub, "_route_complexity")
    def test_routing_with_open_circuit(self, mock_route):
        hub = IntelligenceHub()
        mock_route.return_value = "openai"
        
        # Manually open OpenAI circuit
        hub.breakers["openai"].failure_threshold = 2
        for _ in range(2):
            hub.breakers["openai"].record_failure()
        
        assert hub.breakers["openai"].is_open()
        
        # Verify that chat() will skip open circuits
        with patch.object(hub, "_call_provider", return_value={"response": "ok", "latency_sec": 0.1}) as mock_call:
            asyncio.run(hub.chat("test", complexity="high"))
            
            # Should NOT have called openai because it's open
            for call in mock_call.call_args_list:
                assert call.args[0] != "openai"
