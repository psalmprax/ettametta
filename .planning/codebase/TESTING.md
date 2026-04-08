# Testing Patterns

**Analysis Date:** 2024-04-08

## Test Framework

**Runner:**
- pytest with pytest-asyncio and pytest-mock
- Config: `api/pytest.ini`
- Command: `pytest tests/ -v --tb=short`

**Assertion Library:**
- Built-in pytest assertions

**Run Commands:**
```bash
pytest tests/ -v --tb=short              # Run all tests
pytest tests/test_config.py -v           # Run specific test file
pytest tests/ -k "auth"                  # Run tests matching pattern
pytest --cov=api tests/                  # With coverage
```

## Test File Organization

**Location:**
- `api/tests/` directory for API-related tests
- `e2e/tests/` for end-to-end tests
- Co-located with source code (tests/ subdirectory)

**Naming:**
- `test_*.py` for Python unit/integration tests
- `*Test` class prefix for test classes
- `test_*` function prefix for test methods
- `*.spec.ts` for Playwright e2e tests

**Structure:**
```
api/tests/
├── conftest.py          # Shared fixtures
├── test_config.py       # Config tests
├── test_routes/         # Route-specific tests
└── test_*.py           # Other test files

e2e/tests/
├── auth/
│   ├── login.spec.ts
│   └── oauth.spec.ts
└── creation/
    └── video_creation.spec.ts
```

## Test Structure

**Suite Organization:**
```python
class TestConfigSettings:
    """Test configuration settings"""

    def test_default_settings_exist(self):
        """Test that default settings are defined"""
        # Arrange
        from api.config import settings

        # Act & Assert
        assert settings.APP_NAME == "ettametta API"
```

**Patterns:**
- Class-based organization for unit tests
- Async test methods with @pytest.mark.asyncio
- Descriptive docstrings for classes and methods
- beforeEach for e2e setup

## Mocking

**Framework:** unittest.mock (patch, MagicMock)

**Patterns:**
```python
# Environment mocking
with patch.dict(os.environ, {"ENV": "test"}):
    settings = Settings()

# Module mocking
with patch("services.optimization.llm.get_groq_client") as mock:
    mock_client = MagicMock()
    mock.return_value = mock_client

# Heavy dependencies mocked at module level in conftest.py
```

**What to Mock:**
- External API calls (Groq, Redis)
- Database operations
- Heavy ML/AI dependencies (faster_whisper, diffusers, etc.)
- File system operations

**What NOT to Mock:**
- Core business logic under test
- Simple utility functions

## Fixtures and Factories

**Test Data:**
```python
@pytest.fixture
def test_user_data():
    """Test user registration data."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
```

**Location:**
- `api/tests/conftest.py` for shared fixtures
- Session and function scope fixtures
- Test-specific fixtures in test files

## Coverage

**Requirements:** Not enforced (no coverage thresholds)

**View Coverage:**
```bash
pytest --cov=api tests/
pytest --cov-report=html tests/
```

## Test Types

**Unit Tests:**
- Service layer testing with mocked dependencies
- Individual function/method testing
- Configuration validation

**Integration Tests:**
- API route testing with TestClient
- Database integration tests

**E2E Tests:**
- Playwright for frontend testing
- Multi-browser support (Chrome, Firefox, Safari)
- Mobile testing (Pixel 5, iPhone 12)
- Visual regression testing

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_async_function(self):
    result = await service.method()
    assert result == expected
```

**Error Testing:**
```python
with pytest.raises(HTTPException):
    await register(invalid_user, db)
```

**API Testing:**
```python
def test_route(self, client):
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
```

---

*Testing analysis: 2024-04-08*</content>
<parameter name="filePath">.planning/codebase/TESTING.md