import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock
import types
import inspect

# Set test environment before any imports
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test_ettametta.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["GROQ_API_KEY"] = "test_key"
os.environ["ENABLE_LANGCHAIN"] = "false"

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

# Mock langsmith before any imports
class MockModule(types.ModuleType):
    def __getattr__(self, name):
        return MagicMock()

def create_mock_module(name):
    m = MockModule(name)
    sys.modules[name] = m
    return m

mock_names = ["langsmith", "langsmith.testing", "langsmith.client"]
for name in mock_names:
    create_mock_module(name)

async def run_tests():
    from src.api.utils.database import Base, engine
    from src.api.utils import models, user_models
    
    # Create tables in test DB
    Base.metadata.create_all(bind=engine)
    
    import src.api.tests.test_nexus_real_first as tests
    
    test_functions = [obj for name, obj in inspect.getmembers(tests) if inspect.isfunction(obj) and name.startswith("test_")]
    
    results = []
    for test_func in test_functions:
        print(f"\n🚀 Running {test_func.__name__}...")
        try:
            if inspect.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            print(f"✅ {test_func.__name__} PASSED")
            results.append((test_func.__name__, "PASSED"))
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED: {e}")
            results.append((test_func.__name__, "FAILED", str(e)))
            # import traceback
            # traceback.print_exc()

    print("\n" + "="*30)
    print("TEST SUMMARY")
    print("="*30)
    for res in results:
        status = res[1]
        name = res[0]
        print(f"{status}: {name}")
    print("="*30)

if __name__ == "__main__":
    asyncio.run(run_tests())
