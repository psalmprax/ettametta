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
    from src.api.utils import models, user_models, credit_models  # Ensure models are registered
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
async def cleanup_after_test():
    yield
    from src.api.utils.database import async_engine
    await async_engine.dispose()
    try:
        from src.services.distribution.experiment_batcher import base_experiment_service
        base_experiment_service.active_batches = []
    except Exception:
        pass
