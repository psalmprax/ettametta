"""
Test Configuration and Fixtures
================================
Shared test fixtures for API integration tests
"""

import sys
from unittest.mock import MagicMock

# Patch importlib.metadata.version to satisfy email-validator version check
# WITHOUT replacing the entire module (which breaks OpenTelemetry on Python 3.10)
import importlib.metadata as _real_metadata
_original_version = _real_metadata.version
def _patched_version(name):
    if name == "email-validator":
        return "2.0.0"
    return _original_version(name)
_real_metadata.version = _patched_version

import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch

# Mock heavy dependencies BEFORE any service imports to allow tests to run in light environments
import types

class MockModule(types.ModuleType):
    def __init__(self, name):
        super().__init__(name)
        import importlib.machinery
        self.__spec__ = importlib.machinery.ModuleSpec(name, None)

    def __getattr__(self, name):
        return MagicMock()

def create_mock_module(name):
    m = MockModule(name)
    sys.modules[name] = m
    return m

mock_names = [
    "faster_whisper", "diffusers", "diffusers.utils", "moviepy", "moviepy.editor", 
    "moviepy.video.io", "moviepy.video.io.VideoFileClip", "moviepy.video.compositing",
    "moviepy.audio.AudioClip", "moviepy.audio.fx", "moviepy.audio.fx.all", "moviepy.afx",
    "moviepy.audio.AudioClip.CompositeAudioClip",
    "cv2", "torch", "gtts", "easyocr", "PIL", "pil", "replicate", "fal_client", "remotion",
    "langsmith", "langsmith.testing", "langsmith.client",
    "opentelemetry", "opentelemetry.trace", "opentelemetry.context",
    "opentelemetry.instrumentation", "opentelemetry.instrumentation.celery",
    "opentelemetry.instrumentation.fastapi", "opentelemetry.instrumentation.asgi",
    "opentelemetry.sdk", "opentelemetry.sdk.trace", "opentelemetry.sdk.trace.export",
    "opentelemetry.sdk.resources",
    "opentelemetry.exporter", "opentelemetry.exporter.otlp",
    "opentelemetry.exporter.otlp.proto", "opentelemetry.exporter.otlp.proto.grpc",
    "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
    "opentelemetry.util", "opentelemetry.util.http",
    "opentelemetry.semconv", "opentelemetry.semconv.trace",
]
for name in mock_names:
    create_mock_module(name)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set test environment before importing app
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test_ettametta.db"

# Load Redis credentials from .env and point to host-accessible port
_project_root = str(Path(__file__).parent.parent.parent)
_env_path = os.path.join(_project_root, ".env")
_redis_password = ""
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line.startswith("REDIS_PASSWORD=") and "=" in _line:
                _redis_password = _line.split("=", 1)[1]
                break
os.environ["REDIS_URL"] = f"redis://:{_redis_password}@127.0.0.1:7204/0"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_purposes_123"
os.environ["GROQ_API_KEY"] = "test_groq_key"


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


@pytest.fixture
def client(test_db):
    """Create a test client for the FastAPI app."""
    from src.api.main import app
    from src.api.utils.database import Base, engine, async_engine
    
    # Wipe all table data via sync engine
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    
    # Force the async engine to drop its connection pool so new async
    # sessions see the clean state (SQLite uses separate connections
    # for sync vs async drivers).
    import asyncio
    try:
        asyncio.run(async_engine.dispose())
    except RuntimeError:
        pass  # Already inside an event loop — disposal will happen naturally
            
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing."""
    # Create a test user and get token
    # For now, return empty dict - tests should handle auth themselves
    return {}


@pytest.fixture
def mock_groq():
    """Mock Groq API responses."""
    with patch("services.optimization.llm.get_groq_client") as mock:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))]
        )
        mock.return_value = mock_client
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis responses."""
    with patch("redis.Redis") as mock:
        mock_redis = MagicMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.exists.return_value = 0
        mock.return_value = mock_redis
        yield mock_redis


@pytest.fixture(autouse=True)
def mock_redis_async():
    """Mock async Redis client methods used in auth/routes."""
    from unittest.mock import AsyncMock
    with patch("src.api.utils.redis.get_async_redis", new_callable=AsyncMock) as mock_get_redis:
        mock_redis = AsyncMock()
        mock_redis.sismember = AsyncMock(return_value=False)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.exists = AsyncMock(return_value=False)
        mock_get_redis.return_value = mock_redis
        yield mock_redis


@pytest.fixture
def sample_video_path(tmp_path):
    """Create a sample video file for testing."""
    video_file = tmp_path / "test_video.mp4"
    # Create an empty file (in real tests, this would be a valid video)
    video_file.write_bytes(b"fake video data")
    return str(video_file)


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample image file for testing."""
    image_file = tmp_path / "test_image.jpg"
    image_file.write_bytes(b"fake image data")
    return str(image_file)


# Test data fixtures
@pytest.fixture
def test_user_data():
    """Test user registration data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "full_name": "Test User"
    }


@pytest.fixture
def test_niche_data():
    """Test niche data."""
    return {
        "niche": "Technology",
        "platforms": ["youtube", "tiktok"],
        "is_active": True
    }


@pytest.fixture
def test_video_job_data():
    """Test video job data."""
    return {
        "source_uri": "https://example.com/video.mp4",
        "niche": "Technology",
        "transformation": {
            "face_blur": True,
            "speed_ramp": True
        }
    }


@pytest.fixture
def auth_token(client):
    """Get auth token for authenticated requests."""
    client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "Password123!",
        "full_name": "Test User"
    })
    
    response = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "Password123!"
    })
    return response.json()["data"]["access_token"]
