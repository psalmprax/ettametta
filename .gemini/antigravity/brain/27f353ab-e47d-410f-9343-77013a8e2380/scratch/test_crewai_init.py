import sys
import os
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

def run_test():
    print("Verifying CrewAI Service Initialization...")
    
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.ENABLE_CREWAI = True
    mock_settings.GROQ_API_KEY = "gsk_test_key"
    mock_settings.OPENAI_API_KEY = "sk-test-key"
    
    # Patch settings
    sys.modules["api.config"] = MagicMock()
    sys.modules["api.config"].settings = mock_settings
    
    # Try import and initialization
    try:
        from services.crewai.service import CrewAIService
        service = CrewAIService()
        
        print(f"✅ Service created (Enabled: {service.enabled})")
        
        # Check if it handled missing dependencies gracefully
        if not service._check_crewai_available():
            print("ℹ️ Dependencies missing as expected, but service initialized correctly.")
        
        print("🏆 CREWAI INITIALIZATION TEST PASSED")
        
    except Exception as e:
        print(f"❌ FAIL: CrewAI Service crashed during init: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_test()
