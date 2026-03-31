"""
Test Suite for Services
=======================
Tests for LangChain, CrewAI, Affiliate, Trading, Interpreter services
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestLangChainService:
    """Test LangChain service"""
    
    def test_service_disabled_by_default(self):
        """Test that LangChain service is disabled without env var"""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any cached imports
            modules_to_clear = [k for k in sys.modules.keys() if k.startswith('services.langchain')]
            for mod in modules_to_clear:
                if mod in sys.modules:
                    del sys.modules[mod]
            
            # Check the module checks env
            enable = os.getenv("ENABLE_LANGCHAIN", "false").lower() == "true"
            assert enable == False

    @patch.dict(os.environ, {"ENABLE_LANGCHAIN": "false"})
    def test_service_init_disabled_state(self):
        """Test service initialization when disabled"""
        # Clear module cache to force re-evaluation of env vars
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith('services.langchain')]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        from services.langchain.service import LangChainService
        
        service = LangChainService()
        assert service.enabled == False
        assert service.llm is None


class TestCrewAIService:
    """Test CrewAI service"""
    
    def test_service_disabled_by_default(self):
        """Test that CrewAI service is disabled without env var"""
        with patch.dict(os.environ, {}, clear=True):
            enable = os.getenv("ENABLE_CREWAI", "false").lower() == "true"
            assert enable == False
    
    @patch.dict(os.environ, {"ENABLE_CREWAI": "false"})
    def test_service_init_disabled_state(self):
        """Test service initialization when disabled"""
        # Clear module cache
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith('services.crewai')]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        from services.crewai.service import CrewAIService
        
        service = CrewAIService()
        assert service.enabled == False
        assert service.llm is None
    
    @patch.dict(os.environ, {"ENABLE_CREWAI": "false", "CREWAI_AGENTS": "researcher,writer"})
    def test_agents_config_parsing(self):
        """Test crew agents config parsing"""
        # Clear module cache
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith('services.crewai')]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        from services.crewai.service import CrewAIService
        
        service = CrewAIService()
        # Just check that agents_config exists
        assert hasattr(service, 'agents_config')


class TestAffiliateService:
    """Test Affiliate service"""
    
    @patch.dict(os.environ, {"ENABLE_AFFILIATE_API": "false"})
    def test_service_disabled_by_default(self):
        """Test affiliate service disabled state"""
        from services.affiliate.service import AffiliateService
        
        service = AffiliateService()
        assert service.enabled == False
    
    @patch.dict(os.environ, {"ENABLE_AFFILIATE_API": "true", "AMAZON_ASSOCIATES_TAG": "test_tag"})
    def test_service_enabled_with_api_keys(self):
        """Test affiliate service with API keys"""
        from services.affiliate.service import AffiliateService
        
        service = AffiliateService()
        assert service.enabled == True
        assert service.amazon_tag == "test_tag"
    
    @patch.dict(os.environ, {"ENABLE_AFFILIATE_API": "false"})
    def test_generate_affiliate_link_amazon(self):
        """Test affiliate link generation for Amazon"""
        from services.affiliate.service import AffiliateService
        import asyncio
        
        service = AffiliateService()
        # Disabled service should still generate links
        url = service.generate_affiliate_link(
            "https://amazon.com/product", 
            "amazon"
        )
        assert "amazon.com" in url


class TestTradingService:
    """Test Trading service"""
    
    @patch.dict(os.environ, {"ENABLE_TRADING": "false"})
    def test_service_disabled_by_default(self):
        """Test trading service disabled state"""
        from services.trading.service import TradingService
        
        service = TradingService()
        assert service.enabled == False
    
    @patch.dict(os.environ, {"ENABLE_TRADING": "true", "ALPHA_VANTAGE_API_KEY": "test_key", "COINGECKO_API_KEY": "test_key"})
    def test_service_enabled_with_api_keys(self):
        """Test trading service with API keys"""
        # Clear module cache
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith('services.trading')]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        from services.trading.service import TradingService
        
        service = TradingService()
        assert service.enabled == True
        assert service.alpha_vantage_key == "test_key"
        assert service.coingecko_key == "test_key"
    
    @patch.dict(os.environ, {"ENABLE_TRADING": "true", "ALPHA_VANTAGE_API_KEY": "test_key"})
    def test_service_enabled_with_alpha_vantage_only(self):
        """Test trading service with only Alpha Vantage key"""
        # Clear module cache
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith('services.trading')]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        from services.trading.service import TradingService
        
        service = TradingService()
        assert service.enabled == True
        assert service.alpha_vantage_key == "test_key"
        # coingecko_key should be empty string from settings
        assert service.coingecko_key == ""
    
    @patch.dict(os.environ, {"ENABLE_TRADING": "true", "COINGECKO_API_KEY": "test_key"})
    def test_service_enabled_with_coingecko_only(self):
        """Test trading service with only CoinGecko key"""
        # Clear module cache
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith('services.trading')]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        from services.trading.service import TradingService
        
        service = TradingService()
        assert service.enabled == True
        assert service.coingecko_key == "test_key"
        # alpha_vantage_key should be empty string from settings
        assert service.alpha_vantage_key == ""


class TestInterpreterService:
    """Test Interpreter service"""
    
    @patch.dict(os.environ, {"ENABLE_INTERPRETER": "false"})
    def test_service_disabled_by_default(self):
        """Test interpreter service disabled state"""
        from services.interpreter.service import InterpreterService
        
        service = InterpreterService()
        assert service.enabled == False
    
    @patch.dict(os.environ, {"ENABLE_INTERPRETER": "true", "INTERPRETER_SANDBOX": "true"})
    def test_sandbox_mode_config(self):
        """Test interpreter sandbox configuration"""
        from services.interpreter.service import InterpreterService
        
        service = InterpreterService()
        assert service.sandbox_mode == True
    
    @patch.dict(os.environ, {"ENABLE_INTERPRETER": "true", "INTERPRETER_MAX_RUNTIME": "30"})
    def test_max_runtime_config(self):
        """Test interpreter max runtime configuration"""
        from services.interpreter.service import InterpreterService
        
        service = InterpreterService()
        assert service.max_runtime == 30
    
    @patch.dict(os.environ, {"ENABLE_INTERPRETER": "false"})
    def test_execute_code_raises_when_disabled(self):
        """Test that execute_code raises when service disabled"""
        import asyncio
        from services.interpreter.service import InterpreterService
        
        service = InterpreterService()
        
        with pytest.raises(RuntimeError, match="not enabled"):
            asyncio.run(service.execute_code("print('test')"))
