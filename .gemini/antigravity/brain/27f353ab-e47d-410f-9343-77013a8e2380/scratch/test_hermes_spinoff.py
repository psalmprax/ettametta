import sys
import os
import asyncio
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

async def run_test():
    print("Verifying Hermes Recursive Spinoff Logic...")
    
    # Mock settings
    mock_settings = MagicMock()
    mock_settings.GROQ_API_KEY = "gsk_test_key"
    
    # Patch dependencies
    sys.modules["api.config"] = MagicMock()
    sys.modules["api.config"].settings = mock_settings
    
    # Mock Celery
    mock_celery_app = MagicMock()
    sys.modules["api.utils.celery"] = MagicMock()
    sys.modules["api.utils.celery"].celery_app = mock_celery_app
    
    from services.hermes.service import HermesSkillService
    hermes = HermesSkillService()
    
    job_data = {"job_id": "test_job_123", "niche": "Technology", "user_id": 1}
    metrics = {"views": 100000}
    pattern = "Winning hook pattern"
    
    await hermes._trigger_recursive_spinoff(job_data, metrics, pattern)
    
    # Verify Celery task call
    if mock_celery_app.send_task.called:
        args, kwargs = mock_celery_app.send_task.call_args
        task_name = args[0]
        spinoff_kwargs = kwargs.get("kwargs", {})
        
        print(f"✅ Celery task triggered: {task_name}")
        print(f"✅ Target Niche: {spinoff_kwargs.get('niche')}")
        print(f"✅ Pattern Injected: {spinoff_kwargs.get('analysis_data', {}).get('hermes_seed')}")
        
        if task_name == "video.narrative_fusion":
            print("🏆 HERMES SPINOFF TEST PASSED")
        else:
            print(f"❌ FAIL: Wrong task name: {task_name}")
    else:
        print("❌ FAIL: Celery send_task was not called")

if __name__ == "__main__":
    asyncio.run(run_test())
