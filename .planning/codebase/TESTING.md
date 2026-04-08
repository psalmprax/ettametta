# Coding Conventions

**Analysis Date:** 2026-04-08

## Naming Patterns

**Files:**
- `snake_case.py` - Python files use lowercase with underscores
- `test_*.py` - Test files prefixed with 'test_'
- `conftest.py` - Pytest configuration file

**Functions:**
- `snake_case` - Functions use lowercase with underscores
- `async def` - Async functions follow same naming

**Variables:**
- `snake_case` - Variables use lowercase with underscores
- `UPPER_CASE` - Constants use uppercase with underscores

**Classes:**
- `PascalCase` - Classes use PascalCase (e.g., `TestLangchainService`, `AffiliateStrategy`)

**Types:**
- `PascalCase` - Type hints use PascalCase for custom types

## Code Style

**Formatting:**
- Ruff linter used for style enforcement
- No explicit formatter configured (black/isort not detected)
- 4-space indentation standard

**Linting:**
- Ruff for Python linting
- Bandit for security scanning
- Safety for dependency vulnerability checks

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports (FastAPI, SQLAlchemy, etc.)
3. Local imports (api.*, services.*)

**Path Aliases:**
- Relative imports with `from .` or `from ..`
- Absolute imports from project root

## Error Handling

**Patterns:**
- Try-except blocks with specific exception types
- Global exception handlers in FastAPI app
- Validation errors with custom JSON responses

## Logging

**Framework:** Standard library logging

**Patterns:**
- Logger instances per module: `logger = logging.getLogger(__name__)`
- Info level for requests: process time, method, status
- Error level for exceptions and failures
- Structured logging with context

## Comments

**When to Comment:**
- Module-level docstrings explaining purpose
- Class docstrings describing functionality
- Complex business logic explanations

**JSDoc/TSDoc:**
- Not used (Python project)

## Function Design

**Size:** Variable, some functions span 100+ lines (main.py)

**Parameters:** 
- Type hints used inconsistently
- Optional parameters with defaults

**Return Values:** 
- JSON responses for API endpoints
- Objects or None for internal functions

## Module Design

**Exports:** Explicit imports, no wildcard exports

**Barrel Files:** Not used</content>
<parameter name="filePath">.planning/codebase/CONVENTIONS.md