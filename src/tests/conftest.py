import os
import sys
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set test environment before importing app
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test_ettametta.db"

@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    from src.api.utils.database import Base, engine
    
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

