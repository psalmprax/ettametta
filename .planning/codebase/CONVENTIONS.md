# Coding Conventions

**Analysis Date:** 2024-04-08

## Naming Patterns

**Files:**
- Python: snake_case (e.g., `config.py`, `database.py`)
- TypeScript/React: PascalCase for components (e.g., `Sidebar.tsx`, `AuthContext.tsx`), camelCase for utilities (e.g., `utils.ts`)

**Functions:**
- Python: snake_case (e.g., `get_current_user`, `create_access_token`)
- TypeScript: camelCase (e.g., `handleSubmit`, `useAuth`)

**Variables:**
- Python: snake_case (e.g., `hashed_pwd`, `access_token`)
- TypeScript: camelCase (e.g., `navItems`, `collapsed`)

**Types:**
- Python: PascalCase for classes (e.g., `TestConfigSettings`, `UserCreate`)
- TypeScript: PascalCase for interfaces and types (e.g., `SidebarProps`, `UserResponse`)

## Code Style

**Formatting:**
- Python: No explicit formatter detected (no black, autopep8 config)
- TypeScript: ESLint with Next.js config, no Prettier config detected

**Linting:**
- Python: No dedicated linter config (no .flake8, pylint.ini)
- TypeScript: ESLint with `eslint-config-next` (core-web-vitals and typescript rules)

## Import Organization

**Order:**
1. Standard library imports (e.g., `import os`, `import secrets`)
2. Third-party imports (e.g., `from fastapi import FastAPI`, `import React from "react"`)
3. Local imports (e.g., `from api.config import settings`, `import { cn } from "@/lib/utils"`)

**Path Aliases:**
- TypeScript: `@/` for `src/` (e.g., `@/lib/utils`)

## Error Handling

**Patterns:**
- Python: HTTPException for API errors, global exception handlers in main.py
- TypeScript: Error boundaries (e.g., `GlobalErrorBoundary.tsx`), try-catch in async functions

## Logging

**Framework:** Python logging module, configured in main.py

**Patterns:**
- Logger instances with `__name__` (e.g., `logger = logging.getLogger(__name__)`)
- Info for requests, error for exceptions
- Structured error responses with error codes

## Comments

**When to Comment:**
- Module-level docstrings for test files and complex functions
- Inline comments for complex logic
- JSDoc not observed in TypeScript files

**JSDoc/TSDoc:**
- Not used

## Function Design

**Size:** Variable, some functions span multiple screens (e.g., main.py startup)

**Parameters:** Dependency injection with FastAPI Depends, optional parameters with defaults

**Return Values:** Consistent types (e.g., Pydantic models for API responses)

## Module Design

**Exports:** Default exports for React components, named exports for utilities

**Barrel Files:** Not observed

---

*Convention analysis: 2024-04-08*</content>
<parameter name="filePath">.planning/codebase/CONVENTIONS.md