# Testing Patterns

**Analysis Date:** 2026-04-08

## Test Framework

**Runner:**
- pytest with pytest-asyncio and pytest-mock
- Config: No dedicated pytest.ini, uses default settings
- Command: `pytest tests/ -v --tb=short`

**Assertion Library:**
- Built-in pytest assertions

**Run Commands:**
```bash
pytest tests/ -v --tb=short              # Run all tests with verbose output
pytest tests/test_services.py -v         # Run specific test file
pytest tests/ -k "test_langchain"         # Run tests matching pattern
```

## Test File Organization

**Location:**
- `api/tests/` directory for API-related tests
- Co-located with source code (tests/ subdirectory)

**Naming:**
- `test_*.py` for test files
- `Test*` class prefix for test classes
- `test_*` function prefix for test methods

**Structure:**
```
api/
├── tests/
│   ├── conftest.py          # Shared fixtures
│   ├── test_services.py     # Service layer tests
│   ├── test_routes/         # Route-specific tests
│   └── test_*.py           # Other test files
```

## Test Structure

**Suite Organization:**
```python
class TestServiceName:
    """Test suite description"""

    @pytest.mark.asyncio
    async def test_feature_name(self):
        """Test specific functionality"""
        # Arrange
        # Act
        # Assert
```

**Patterns:**
- Class-based organization
- Async test methods with @pytest.mark.asyncio
- Descriptive docstrings for classes and methods

## Mocking

**Framework:** unittest.mock (patch, MagicMock, AsyncMock)

**Patterns:**
```python
# Environment mocking
with patch.dict(os.environ, {"KEY": "value"}):
    # Test code

# Module mocking
with patch("module.path.Class") as mock:
    mock.return_value = expected_value

# Async mocking
mock_instance = AsyncMock(return_value=expected)
```

**What to Mock:**
- External API calls
- Database operations
- Heavy ML/AI dependencies
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
        "password": "testpassword123",
        "full_name": "Test User"
    }
```

**Location:**
- `conftest.py` for shared fixtures
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

**Integration Tests:**
- API route testing with TestClient
- Database integration tests

**E2E Tests:**
- Playwright for frontend testing
- Docker Compose stack testing

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
with pytest.raises(ExpectedException):
    service.method(invalid_input)
```

**Database Testing:**
- Session-scoped fixtures for test DB setup
- Clean teardown after each test</content>
<parameter name="filePath">.planning/codebase/TESTING.md