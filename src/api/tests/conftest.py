"""
Test Configuration and Fixtures
================================
Shared test fixtures for API integration tests
"""

import sys
from unittest.mock import MagicMock

# Mock version check for email-validator BEFORE any other imports
mock_metadata = MagicMock()
mock_metadata.version.return_value = "2.0.0"
sys.modules["importlib.metadata"] = mock_metadata

import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Mock heavy dependencies BEFORE any service imports to allow tests to run in light environments
import types

class MockModule(types.ModuleType):
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
    "cv2", "numpy", "torch", "gtts", "easyocr", "PIL", "pil", "replicate", "fal_client", "remotion"
]
for name in mock_names:
    create_mock_module(name)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set test environment before importing app
os.environ["ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///./test_ettametta.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["SECRET_KEY"] = "test_secret_key_for_testing_purposes_123"
os.environ["GROQ_API_KEY"] = "test_groq_key"


@pytest.fixture(scope="session")
def test_db():
    """Create a test database."""
    from src.api.utils.database import Base, engine
    from src.api.utils import models, user_models  # Ensure models are registered
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create a test client for the FastAPI app."""
    from src.api.main import app
    
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
