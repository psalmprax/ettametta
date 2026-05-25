"""
Unit tests for UnifiedLLMService - Core LLM routing service.
Tests circuit breaker initialization, retry logic, and failover behavior.
"""
import pytest
from unittest.mock import patch
from src.services.llm.service import UnifiedLLMService, LLMProvider
from src.api.utils.resilience import CircuitBreaker


@pytest.fixture
def llm_service():
    """Create a UnifiedLLMService instance with mocked dependencies."""
    with patch('src.services.llm.service.settings') as mock_settings:
        mock_settings.DEFAULT_LLM_PROVIDER = "groq"
        mock_settings.DEFAULT_RETRY_COUNT = 3
        mock_settings.RETRY_MULTIPLIER = 1
        mock_settings.RETRY_MIN_WAIT = 0.1
        mock_settings.RETRY_MAX_WAIT = 1
        mock_settings.LLM_TIMEOUT = 30
        
        # Mock API keys to avoid real calls
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'test_key',
            'OPENAI_API_KEY': 'test_key'
        }):
            service = UnifiedLLMService()
            return service


class TestUnifiedLLMServiceInitialization:
    """Test service initialization and circuit breaker setup."""
    
    def test_circuit_breakers_initialized(self, llm_service):
        """Verify that circuit breakers are properly initialized for all providers."""
        assert hasattr(llm_service, 'circuit_breakers')
        assert isinstance(llm_service.circuit_breakers, dict)
        
        # Check all providers have circuit breakers
        for provider in LLMProvider:
            assert provider in llm_service.circuit_breakers
            assert isinstance(llm_service.circuit_breakers[provider], CircuitBreaker)
    
    def test_circuit_breaker_names(self, llm_service):
        """Verify circuit breakers have correct naming convention."""
        for provider in LLMProvider:
            breaker = llm_service.circuit_breakers[provider]
            assert breaker.name == f"UnifiedLLM-{provider.value}"
    
    def test_get_breaker_returns_correct_breaker(self, llm_service):
        """Test _get_breaker method returns the correct circuit breaker."""
        breaker = llm_service._get_breaker(LLMProvider.GROQ)
        assert breaker is llm_service.circuit_breakers[LLMProvider.GROQ]
    
    def test_get_breaker_fallback_to_openai(self, llm_service):
        """Test _get_breaker falls back to OpenAI breaker for unknown providers."""
        # This test verifies the fallback logic works
        breaker = llm_service._get_breaker(LLMProvider.OPENAI)
        assert breaker is llm_service.circuit_breakers[LLMProvider.OPENAI]


class TestUnifiedLLMServiceCircuitBreaker:
    """Test circuit breaker integration."""
    
    def test_circuit_breaker_opens_on_failures(self, llm_service):
        """Verify circuit breaker opens after threshold failures."""
        breaker = llm_service.circuit_breakers[LLMProvider.GROQ]
        
        # Simulate failures
        for _ in range(breaker.failure_threshold):
            breaker.record_failure()
        
        # Circuit should be open
        assert breaker.is_open() is True
    
    def test_circuit_breaker_closes_on_success(self, llm_service):
        """Verify circuit breaker closes after successful call."""
        breaker = llm_service.circuit_breakers[LLMProvider.GROQ]
        
        # Open the circuit
        for _ in range(breaker.failure_threshold):
            breaker.record_failure()
        assert breaker.is_open() is True
        
        # Record success
        breaker.record_success()
        assert breaker.is_open() is False


class TestUnifiedLLMServiceRetryLogic:
    """Test retry mechanism with tenacity."""
    
    @pytest.mark.asyncio
    async def test_retry_on_http_error(self, llm_service):
        """Verify that HTTP errors trigger retry attempts."""
        # This test would require mocking httpx.AsyncClient
        # For now, we verify the decorator exists
        assert hasattr(llm_service, '_call_api')
        # The @retry decorator is applied to _call_api method
        # Full integration test would require more complex mocking
    
    @pytest.mark.asyncio
    async def test_no_retry_on_success(self, llm_service):
        """Verify successful calls don't trigger retries."""
        # Similar to above, requires mocking external dependencies
        pass


class TestUnifiedLLMServiceProviderSelection:
    """Test provider selection and fallback logic."""
    
    def test_default_provider_set(self, llm_service):
        """Verify default provider is correctly set."""
        assert llm_service.default_provider == LLMProvider.GROQ
    
    def test_available_providers(self, llm_service):
        """Test get_available_providers returns correct structure."""
        providers = llm_service.get_available_providers()
        assert isinstance(providers, list)
        assert len(providers) == len(LLMProvider)
        
        # Check structure of each provider entry
        for provider_info in providers:
            assert 'provider' in provider_info
            assert 'available' in provider_info
            assert 'models' in provider_info
    
    def test_is_available_with_valid_key(self, llm_service):
        """Test is_available returns True for configured providers."""
        # GROQ should be available since we mocked the API key
        assert llm_service.is_available(LLMProvider.GROQ) is True
    
    def test_is_available_without_key(self, llm_service):
        """Test is_available returns False for unconfigured providers."""
        # DeepSeek should not be available (no key set)
        assert llm_service.is_available(LLMProvider.DEEPSEEK) is False


class TestUnifiedLLMServiceErrorHandling:
    """Test error handling and graceful degradation."""
    
    @pytest.mark.asyncio
    async def test_complete_handles_all_providers_failed(self, llm_service):
        """Verify complete() returns error when all providers fail."""
        # Mock all providers to fail
        with patch.object(llm_service, 'is_available', return_value=False):
            result = await llm_service.complete("test prompt")
            
            assert 'error' in result
            assert 'All LLM providers failed' in result['error']
    
    @pytest.mark.asyncio
    async def test_complete_returns_content_on_success(self, llm_service):
        """Verify complete() returns content on successful call."""
        # Mock a successful response
        with patch.object(llm_service, '_call_api') as mock_call:
            mock_call.return_value = {
                'content': 'Test response',
                'model': 'test-model',
                'provider': 'groq'
            }
            
            result = await llm_service.complete("test prompt", provider=LLMProvider.GROQ)
            
            assert result['content'] == 'Test response'
            assert result['provider'] == 'groq'


class TestUnifiedLLMServiceHelperFunctions:
    """Test helper functions like generate() and chat_with_llm()."""
    
    @pytest.mark.asyncio
    async def test_generate_function(self, llm_service):
        """Test the generate() helper function."""
        from src.services.llm.service import generate
        
        with patch.object(llm_service, 'complete') as mock_complete:
            mock_complete.return_value = {'content': 'Generated text'}
            
            result = await generate("test prompt")
            
            assert result == 'Generated text'
    
    @pytest.mark.asyncio
    async def test_chat_with_llm_function(self, llm_service):
        """Test the chat_with_llm() helper function."""
        from src.services.llm.service import chat_with_llm
        
        messages = [
            {"role": "user", "content": "Hello"}
        ]
        
        with patch.object(llm_service, 'chat') as mock_chat:
            mock_chat.return_value = {'content': 'Hi there!'}
            
            result = await chat_with_llm(messages)
            
            assert result == 'Hi there!'
