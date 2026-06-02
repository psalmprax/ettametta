import os
import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set test environment before importing app
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test_ettametta.db"

# Load Redis credentials from .env and point to host-accessible port (7204)
_env_path = str(Path(__file__).parent.parent.parent / ".env")
_redis_password = ""
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line.startswith("REDIS_PASSWORD=") and "=" in _line:
                _redis_password = _line.split("=", 1)[1]
                break
os.environ["REDIS_URL"] = f"redis://:{_redis_password}@127.0.0.1:7204/0"

@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    from src.api.utils.database import Base, engine
    # Explicitly import models to register them with Base.metadata
    from src.api.utils import user_models, models, credit_models
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
async def cleanup_after_session():
    """Dispose the async engine once after the entire test session."""
    yield
    try:
        from src.api.utils.database import async_engine
        await async_engine.dispose()
    except Exception:
        pass

