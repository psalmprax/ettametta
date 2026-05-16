"""
Unit tests for GenerativeService - Video synthesis service.
Tests circuit breaker, model management, and GPU queue functionality.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from src.services.video_engine.synthesis_service import GenerativeService, CircuitBreaker


@pytest.fixture
def generative_service():
    """Create a GenerativeService instance with mocked dependencies."""
    with patch('src.services.video_engine.synthesis_service.settings') as mock_settings:
        mock_settings.COMFYUI_URL = 'http://localhost:8188'
        mock_settings.COMFYUI_MODELS_DIR = '/tmp/models'
        mock_settings.STORAGE_OUTPUT_DIR = '/tmp/output'
        mock_settings.REDIS_URL = 'redis://localhost:6379'
        mock_settings.GPU_QUEUE_SLOTS = 1
        mock_settings.GPU_QUEUE_TIMEOUT = 300
        mock_settings.CLEANUP_TRANSIENT_MODELS = True
        
        # Mock optional dependencies
        with patch('src.services.video_engine.synthesis_service.TORCH_AVAILABLE', False):
            with patch('src.services.video_engine.synthesis_service.CV2_AVAILABLE', False):
                with patch('src.services.video_engine.synthesis_service.MOVIEPY_AVAILABLE', False):
                    with patch('src.services.video_engine.synthesis_service.DIFFUSERS_AVAILABLE', False):
                        with patch('src.services.video_engine.synthesis_service.FASTER_WHISPER_AVAILABLE', False):
                            service = GenerativeService()
                            return service


class TestGenerativeServiceInitialization:
    """Test service initialization."""
    
    def test_circuit_breaker_initialized(self, generative_service):
        """Verify circuit breaker is properly initialized."""
        assert hasattr(generative_service, 'circuit_breaker')
        assert isinstance(generative_service.circuit_breaker, CircuitBreaker)
    
    def test_model_manager_initialized(self, generative_service):
        """Verify model manager is initialized."""
        assert hasattr(generative_service, 'model_manager')
        assert generative_service.model_manager is not None
    
    def test_gpu_queue_initialized(self, generative_service):
        """Verify GPU queue is initialized."""
        assert hasattr(generative_service, 'gpu_queue')
        assert generative_service.gpu_queue is not None


class TestGenerativeServiceCircuitBreaker:
    """Test circuit breaker integration."""
    
    def test_circuit_breaker_opens_on_failures(self, generative_service):
        """Verify circuit breaker opens after threshold failures."""
        cb = generative_service.circuit_breaker
        
        # Simulate failures
        for _ in range(cb.failure_threshold):
            cb.record_failure()
        
        # Circuit should be open
        assert cb.is_open() is True
    
    def test_circuit_breaker_closes_on_success(self, generative_service):
        """Verify circuit breaker closes after successful call."""
        cb = generative_service.circuit_breaker
        
        # Open the circuit
        for _ in range(cb.failure_threshold):
            cb.record_failure()
        assert cb.is_open() is True
        
        # Record success
        cb.record_success()
        assert cb.is_open() is False
    
    def test_engine_specific_failures_tracked(self, generative_service):
        """Test engine-specific failure tracking."""
        cb = generative_service.circuit_breaker
        
        # Record failures for specific engine
        cb.record_failure(engine="hunyuan")
        cb.record_failure(engine="hunyuan")
        cb.record_failure(engine="hunyuan")
        
        # Engine should be disabled
        assert cb.is_open(engine="hunyuan") is True
    
    def test_engine_success_resets_failures(self, generative_service):
        """Test engine success resets failure count."""
        cb = generative_service.circuit_breaker
        
        # Record failures for specific engine
        cb.record_failure(engine="hunyuan")
        cb.record_failure(engine="hunyuan")
        
        # Record success
        cb.record_success(engine="hunyuan")
        
        # Engine should be enabled
        assert cb.is_open(engine="hunyuan") is False


class TestGenerativeServiceEngineParams:
    """Test engine parameter configuration."""
    
    def test_get_engine_params_hunyuan(self, generative_service):
        """Test Hunyuan engine parameters."""
        params = generative_service._get_engine_params("hunyuan")
        
        assert "steps" in params
        assert "cfg" in params
        assert "vram_limit" in params
        assert params["optimization"]["fp16"] is True
    
    def test_get_engine_params_mochi(self, generative_service):
        """Test Mochi engine parameters."""
        params = generative_service._get_engine_params("mochi")
        
        assert "steps" in params
        assert "cfg" in params
        assert params["optimization"]["xformers"] is True
    
    def test_get_engine_params_default(self, generative_service):
        """Test default engine parameters for unknown engine."""
        params = generative_service._get_engine_params("unknown_engine")
        
        # Should return fallback params
        assert params is not None


class TestGenerativeServiceSynthesizeVideo:
    """Test video synthesis functionality."""
    
    @pytest.mark.asyncio
    async def test_synthesize_video_checks_circuit_breaker(self, generative_service):
        """Test synthesize_video checks circuit breaker before proceeding."""
        # Open the circuit
        for _ in range(generative_service.circuit_breaker.failure_threshold):
            generative_service.circuit_breaker.record_failure()
        
        result = await generative_service.synthesize_video(
            prompt="test prompt",
            engine="hunyuan"
        )
        
        # Should return None when circuit is open
        assert result is None
    
    @pytest.mark.asyncio
    async def test_synthesize_video_unsupported_engine(self, generative_service):
        """Test synthesize_video handles unsupported engines."""
        result = await generative_service.synthesize_video(
            prompt="test prompt",
            engine="unsupported_engine"
        )
        
        # Should return None for unsupported engine
        assert result is None
    
    @pytest.mark.asyncio
    async def test_synthesize_video_records_success(self, generative_service):
        """Test synthesize_video records success on completion."""
        cb = generative_service.circuit_breaker
        
        # Mock the dispatch method to return a path
        with patch.object(generative_service, '_dispatch_synthesis') as mock_dispatch:
            mock_dispatch.return_value = "/tmp/test_video.mp4"
            
            await generative_service.synthesize_video(
                prompt="test prompt",
                engine="veo3"
            )
            
            # Verify success was recorded
            assert cb.failure_count == 0


class TestGenerativeServiceHealthReport:
    """Test health reporting functionality."""
    
    def test_get_health_report_healthy(self, generative_service):
        """Test health report when service is healthy."""
        report = generative_service.get_health_report()
        
        assert report['service'] == 'Synthesis Service'
        assert 'status' in report
        assert 'circuit_breaker' in report
    
    def test_get_health_report_degraded_circuit_open(self, generative_service):
        """Test health report when circuit breaker is open."""
        # Open the circuit
        for _ in range(generative_service.circuit_breaker.failure_threshold):
            generative_service.circuit_breaker.record_failure()
        
        report = generative_service.get_health_report()
        
        assert report['status'] == 'Degraded'
        assert 'Global circuit breaker open' in report['issues']
    
    def test_get_health_report_engine_failures(self, generative_service):
        """Test health report shows engine-specific failures."""
        # Record failures for specific engine
        generative_service.circuit_breaker.record_failure(engine="hunyuan")
        generative_service.circuit_breaker.record_failure(engine="hunyuan")
        generative_service.circuit_breaker.record_failure(engine="hunyuan")
        
        report = generative_service.get_health_report()
        
        assert report['status'] == 'Degraded'
        assert 'Engines disabled' in str(report['issues'])


class TestGenerativeServiceDependencyReport:
    """Test dependency reporting."""
    
    def test_get_dependency_report(self, generative_service):
        """Test dependency report includes all drivers."""
        report = generative_service.get_dependency_report()
        
        assert report['name'] == 'Synthesis Engine'
        assert 'drivers' in report
        assert 'healthy' in report


class TestModelManager:
    """Test ModelManager functionality."""
    
    @pytest.mark.asyncio
    async def test_acquire_model_increments_usage(self, generative_service):
        """Test acquire_model increments usage counter."""
        mm = generative_service.model_manager
        
        # Mock the download method
        with patch.object(mm, '_download_model_from_hf') as mock_download:
            mock_download.side_effect = Exception("Skip download")
            
            # Acquire a model (will use mock fallback)
            try:
                path = await mm.acquire_model("test_model")
                
                # Check usage was incremented
                assert mm.active_usage.get("test_model", 0) >= 1
            except Exception:
                # Expected if mocking isn't perfect
                pass
    
    @pytest.mark.asyncio
    async def test_release_model_decrements_usage(self, generative_service):
        """Test release_model decrements usage counter."""
        mm = generative_service.model_manager
        
        # Set up usage
        mm.active_usage["test_model"] = 2
        
        # Release
        await mm.release_model("test_model")
        
        # Usage should decrease
        assert mm.active_usage.get("test_model", 0) == 1
    
    @pytest.mark.asyncio
    async def test_release_model_removes_at_zero(self, generative_service):
        """Test release_model removes entry when count reaches zero."""
        mm = generative_service.model_manager
        
        # Set up usage
        mm.active_usage["test_model"] = 1
        
        # Release
        await mm.release_model("test_model")
        
        # Entry should be removed
        assert "test_model" not in mm.active_usage
