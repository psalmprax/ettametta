# Testing Patterns

**Analysis Date:** 2026-04-09

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
pytest tests/test_services.py -v         # Run specific test file
pytest tests/ -k "auth"                  # Run tests matching pattern
pytest --cov=api tests/                  # With coverage
```

## Test File Organization

**Location:**
- `api/tests/` directory for API-related tests
- `scripts/` for some test scripts
- Co-located with source code (tests/ subdirectory)

**Naming:**
- `test_*.py` for test files
- `Test*` class prefix for test classes
- `test_*` function prefix for test methods

**Structure:**
```
api/tests/
├── conftest.py          # Shared fixtures
├── test_services.py     # Service tests
├── test_routes/         # Route-specific tests
└── test_*.py           # Other test files
```

## Test Structure

**Suite Organization:**
```python
class TestLangchainService:
    """Test LangChain service functionality"""

    @pytest.mark.asyncio
    async def test_langchain_service_initialization(self):
        """Test that LangChain service can be initialized"""
        # Test implementation
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
with patch.dict(os.environ, {"ENV": "test"}):
    # Test code

# Module mocking
with patch.dict("sys.modules", {"langchain": MagicMock()}):
    # Test code
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
```

## Test Types

**Unit Tests:**
- Service layer testing with mocked dependencies
- Individual function/method testing

**Integration Tests:**
- API route testing
- Database integration tests

**E2E Tests:**
- Playwright for frontend testing (inferred from .spec.ts files)

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

---

*Testing analysis: 2026-04-09*</content>
<parameter name="filePath">ALL_PROJECTS/viral_forge/.planning/codebase/TESTING.md