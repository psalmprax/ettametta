"""
Unit tests for IntelligenceHub - Central LLM routing service.
Tests circuit breaker initialization, complexity routing, and failover behavior.
"""
import pytest
import asyncio
from unittest.mock import patch
from src.services.llm.intelligence_hub import IntelligenceHub
from src.api.utils.resilience import CircuitBreaker


@pytest.fixture
def intelligence_hub():
    """Create an IntelligenceHub instance with mocked dependencies."""
    with patch('src.services.llm.intelligence_hub.settings') as mock_settings:
        mock_settings.OPENAI_API_KEY = 'test_openai_key'
        mock_settings.GROQ_API_KEY = 'test_groq_key'
        mock_settings.GOOGLE_API_KEY = 'test_google_key'
        mock_settings.OLLAMA_URL = 'http://localhost:11434'
        mock_settings.DEFAULT_LLM_PROVIDER = 'groq'
        mock_settings.FALLBACK_LLM_PROVIDER = 'ollama'
        mock_settings.LLM_TIMEOUT = 60
        
        hub = IntelligenceHub()
        return hub


class TestIntelligenceHubInitialization:
    """Test service initialization and circuit breaker setup."""
    
    def test_breakers_initialized(self, intelligence_hub):
        """Verify that circuit breakers are properly initialized for all providers."""
        assert hasattr(intelligence_hub, 'breakers')
        assert isinstance(intelligence_hub.breakers, dict)
        
        # Check all expected providers have circuit breakers
        expected_providers = ['ollama', 'openai', 'groq', 'gemini', 'vllm', 'dify']
        for provider in expected_providers:
            assert provider in intelligence_hub.breakers
            assert isinstance(intelligence_hub.breakers[provider], CircuitBreaker)
    
    def test_breaker_names_correct(self, intelligence_hub):
        """Verify circuit breakers have correct names."""
        expected_names = {
            'ollama': 'Ollama-Local-Edge',
            'openai': 'OpenAI-Champion',
            'groq': 'Groq-Challenger',
            'gemini': 'Gemini-Titan',
            'vllm': 'vLLM-Production-Edge',
            'dify': 'Dify-Orchestrator'
        }
        
        for provider, expected_name in expected_names.items():
            assert intelligence_hub.breakers[provider].name == expected_name
    
    def test_api_keys_loaded(self, intelligence_hub):
        """Verify API keys are loaded from settings."""
        assert intelligence_hub.openai_key == 'test_openai_key'
        assert intelligence_hub.groq_key == 'test_groq_key'
        assert intelligence_hub.google_key == 'test_google_key'


class TestIntelligenceHubCircuitBreaker:
    """Test circuit breaker integration."""
    
    def test_circuit_breaker_opens_on_failures(self, intelligence_hub):
        """Verify circuit breaker opens after threshold failures."""
        breaker = intelligence_hub.breakers['groq']
        
        # Simulate failures
        for _ in range(breaker.failure_threshold):
            breaker.record_failure()
        
        # Circuit should be open
        assert breaker.is_open() is True
    
    def test_circuit_breaker_closes_on_success(self, intelligence_hub):
        """Verify circuit breaker closes after successful call."""
        breaker = intelligence_hub.breakers['groq']
        
        # Open the circuit
        for _ in range(breaker.failure_threshold):
            breaker.record_failure()
        assert breaker.is_open() is True
        
        # Record success
        breaker.record_success()
        assert breaker.is_open() is False
    
    def test_reset_circuit(self, intelligence_hub):
        """Test manual circuit breaker reset."""
        breaker = intelligence_hub.breakers['groq']
        
        # Open the circuit
        for _ in range(breaker.failure_threshold):
            breaker.record_failure()
        assert breaker.is_open() is True
        
        # Reset
        intelligence_hub.reset_circuit('groq')
        assert breaker.is_open() is False
    
    def test_reset_all_circuits(self, intelligence_hub):
        """Test resetting all circuit breakers."""
        # Open multiple circuits
        for provider in ['groq', 'openai']:
            breaker = intelligence_hub.breakers[provider]
            for _ in range(breaker.failure_threshold):
                breaker.record_failure()
            assert breaker.is_open() is True
        
        # Reset all
        intelligence_hub.reset_all_circuits()
        
        # All should be closed
        for provider in ['groq', 'openai']:
            assert intelligence_hub.breakers[provider].is_open() is False


class TestIntelligenceHubComplexityRouting:
    """Test complexity-based provider routing."""
    
    def test_route_complexity_low(self, intelligence_hub):
        """Test low complexity routes to ollama."""
        provider = intelligence_hub._route_complexity("low")
        assert provider == "ollama"
    
    def test_route_complexity_medium_with_gemini(self, intelligence_hub):
        """Test medium complexity routes to gemini when available."""
        provider = intelligence_hub._route_complexity("medium")
        # Should prefer gemini if key is available
        assert provider in ["gemini", "groq", "ollama"]
    
    def test_route_complexity_high_with_openai(self, intelligence_hub):
        """Test high complexity routes to openai when available."""
        provider = intelligence_hub._route_complexity("high")
        # Should prefer openai if key is available
        assert provider in ["openai", "dify", "gemini", "ollama"]


class TestIntelligenceHubChat:
    """Test chat functionality."""
    
    @pytest.mark.asyncio
    async def test_chat_with_timeout(self, intelligence_hub):
        """Test chat respects timeout parameter."""
        # Mock the internal _chat_inner method
        with patch.object(intelligence_hub, '_chat_inner') as mock_inner:
            mock_inner.return_value = {'response': 'Test response'}
            
            result = await intelligence_hub.chat(
                prompt="test",
                timeout_seconds=5
            )
            
            assert result['response'] == 'Test response'
    
    @pytest.mark.asyncio
    async def test_chat_global_timeout(self, intelligence_hub):
        """Test chat raises error on global timeout."""
        # Mock _chat_inner to hang
        async def slow_response(*args, **kwargs):
            await asyncio.sleep(10)
            return {'response': 'too late'}
        
        with patch.object(intelligence_hub, '_chat_inner', side_effect=slow_response):
            with pytest.raises(RuntimeError, match="global timeout"):
                await intelligence_hub.chat(
                    prompt="test",
                    timeout_seconds=0.1
                )
    
    @pytest.mark.asyncio
    async def test_chat_provider_selection(self, intelligence_hub):
        """Test chat uses specified provider."""
        with patch.object(intelligence_hub, '_call_provider') as mock_call:
            mock_call.return_value = {'response': 'Test'}
            
            await intelligence_hub.chat(
                prompt="test",
                provider="groq"
            )
            
            # Verify groq was called
            mock_call.assert_called_once()
            args = mock_call.call_args
            assert args[0][0] == "groq"
    
    @pytest.mark.asyncio
    async def test_chat_skip_open_circuits(self, intelligence_hub):
        """Test chat skips providers with open circuits."""
        # Open the groq circuit
        intelligence_hub.breakers['groq'].record_failure()
        intelligence_hub.breakers['groq'].record_failure()
        intelligence_hub.breakers['groq'].record_failure()
        assert intelligence_hub.breakers['groq'].is_open() is True
        
        # Mock _call_provider to track calls
        with patch.object(intelligence_hub, '_call_provider') as mock_call:
            mock_call.return_value = {'response': 'Test'}
            
            await intelligence_hub.chat(
                prompt="test",
                complexity="medium"  # Would normally try groq first
            )
            
            # Verify groq was NOT called (circuit is open)
            for call_args in mock_call.call_args_list:
                assert call_args[0][0] != "groq"
    
    @pytest.mark.asyncio
    async def test_chat_total_failure(self, intelligence_hub):
        """Test chat raises error when all providers fail."""
        # Mock all providers to fail
        with patch.object(intelligence_hub, '_call_provider') as mock_call:
            mock_call.side_effect = Exception("Provider down")
            
            with pytest.raises(RuntimeError, match="total failure"):
                await intelligence_hub.chat(prompt="test")


class TestIntelligenceHubRAGContext:
    """Test RAG context injection."""
    
    @pytest.mark.asyncio
    async def test_rag_context_passed_to_provider(self, intelligence_hub):
        """Test RAG context is passed to provider calls."""
        with patch.object(intelligence_hub, '_call_provider') as mock_call:
            mock_call.return_value = {'response': 'Test'}
            
            rag_context = "This is relevant context for the query"
            
            await intelligence_hub.chat(
                prompt="What is the answer?",
                rag_context=rag_context
            )
            
            # Verify rag_context was passed
            call_args = mock_call.call_args
            assert call_args[1]['rag_context'] == rag_context
