# Coding Conventions

**Analysis Date:** 2026-04-09

## Naming Patterns

**Files:**
- Python: snake_case (e.g., `auth.py`, `user_models.py`, `conftest.py`)
- TypeScript: camelCase (e.g., `utils.ts`, `useNiches.ts`)

**Functions:**
- Python: snake_case (e.g., `get_db()`, `verify_password()`)
- TypeScript: camelCase (e.g., `cn()`)

**Variables:**
- Python: snake_case (e.g., `hashed_pwd`, `db_user`)
- TypeScript: camelCase (e.g., `inputs`)

**Types:**
- Python: PascalCase for classes (e.g., `UserCreate`, `Token`)
- TypeScript: PascalCase for types and interfaces

## Code Style

**Formatting:**
- Python: No explicit formatter detected (no black, autopep8)
- TypeScript: No explicit formatter detected (no prettier config)

**Linting:**
- TypeScript: ESLint with Next.js config (`eslint.config.mjs`)
- Python: No linting tools detected (no flake8, pylint, mypy)

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports (fastapi, sqlalchemy, etc.)
3. Local imports (api.utils.*, services.*)

**Path Aliases:**
- Python: Relative imports (e.g., `from api.utils.database import get_db`)
- TypeScript: Not observed

## Error Handling

**Patterns:**
- Structured JSON responses with error codes
- HTTPException for API errors
- Global exception handlers for uncaught errors
- Logging errors with context

## Logging

**Framework:** Standard library logging

**Patterns:**
- Logger per module: `logger = logging.getLogger(__name__)`
- Levels: info, warning, error
- Structured messages with request context

## Comments

**When to Comment:**
- Module-level docstrings describing purpose
- Complex business logic
- API endpoint descriptions

**JSDoc/TSDoc:**
- Not observed in sampled files

## Function Design

**Size:** Varies; main.py is 325 lines, smaller utilities are concise

**Parameters:** Dependency injection with FastAPI Depends()

**Return Values:** Pydantic models for structured responses

## Module Design

**Exports:** Explicit imports in __init__.py for router modules

**Barrel Files:** Not observed

---

*Convention analysis: 2026-04-09*</content>
<parameter name="filePath">ALL_PROJECTS/ettametta/.planning/codebase/CONVENTIONS.md