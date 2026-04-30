<!-- GSD:project-start source:PROJECT.md -->
## Project

**ettametta**

ettametta is an autonomous multi-platform viral content discovery, transformation, optimization, and publishing engine — powered by AI. It provides a comprehensive platform for content creators to discover trending content across platforms, transform it using AI video generation, optimize for virality, and publish to multiple social media platforms.

**Core Value:** **Empower content creators** with AI-driven automation to discover, create, and monetize viral content efficiently, removing the manual work of trend research and content optimization.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.10 - Main application logic, API, services
- TypeScript/JavaScript - Frontend apps (dashboard, remotion-studio), external skills
- Go - Discovery service (discovery-go)
## Runtime
- Python 3.10-slim - Containerized with Docker
- Node.js 18-alpine - For frontend/dashboard apps
- pip - Python dependencies via requirements.txt
- npm/yarn - Node.js dependencies via package.json
- Lockfile: No explicit lockfiles detected (requirements.txt without hashes)
## Frameworks
- FastAPI - REST API framework with async support
- SQLAlchemy - ORM with Alembic migrations
- Celery - Asynchronous task processing
- Redis - Caching and message broker
- pytest - Test framework (inferred from test files)
- Docker Compose - Multi-service orchestration
- Traefik - Reverse proxy and load balancing
- Prometheus/Grafana - Monitoring stack
## Key Dependencies
- fastapi - API framework
- sqlalchemy - Database ORM
- celery - Task queue
- redis - Cache and broker
- pydantic - Data validation
- postgres:15-alpine - Primary database
- traefik:v3.0 - API gateway
- nginx:alpine - Static file serving
## Configuration
- Pydantic Settings - Configuration management with .env support
- Environment variables - API keys, database URLs, secrets
- Multi-stage Docker builds for API and services
- Docker Compose for service orchestration
## Platform Requirements
- Docker and Docker Compose
- Python 3.10+
- Node.js 18+ for frontend apps
- Kubernetes/Docker Swarm for orchestration
- PostgreSQL database
- Redis cluster
- External AI provider APIs (OpenAI, Groq, etc.)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Test Framework
- pytest with pytest-asyncio and pytest-mock
- Config: No dedicated pytest.ini, uses default settings
- Command: `pytest tests/ -v --tb=short`
- Built-in pytest assertions
## Test File Organization
- `api/tests/` directory for API-related tests
- Co-located with source code (tests/ subdirectory)
- `test_*.py` for test files
- `Test*` class prefix for test classes
- `test_*` function prefix for test methods
## Test Structure
- Class-based organization
- Async test methods with @pytest.mark.asyncio
- Descriptive docstrings for classes and methods

## Architectural Conventions
- **Service Singletons**: All business logic services MUST expose a singleton instance named `base_[service_name]_service`.
  - Example: `base_intelligence_service`, `base_script_service`, `base_vision_service`.
  - This pattern ensures uniform access and easy dependency tracking across the codebase.
- **Import Consistency**: Services should be imported from their respective module's singleton instance whenever possible.
## Mocking
- External API calls
- Database operations
- Heavy ML/AI dependencies
- File system operations
- Core business logic under test
- Simple utility functions
## Fixtures and Factories
- `conftest.py` for shared fixtures
- Session and function scope fixtures
- Test-specific fixtures in test files
## Coverage
## Test Types
- Service layer testing with mocked dependencies
- Individual function/method testing
- API route testing with TestClient
- Database integration tests
- Playwright for frontend testing
- Docker Compose stack testing
## Common Patterns
- Session-scoped fixtures for test DB setup
- Clean teardown after each test</content>
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Modular services for business logic separation
- Shared database with SQLAlchemy ORM
- Asynchronous processing with Celery workers
- REST API with FastAPI framework
- Containerized deployment with Docker Compose
## Layers
- Purpose: HTTP request handling, routing, and response formatting
- Location: `api/`
- Contains: FastAPI routes, middleware, utilities
- Depends on: Services layer, Database layer
- Used by: External clients (web/mobile apps)
- Purpose: Business logic and external integrations
- Location: `services/`
- Contains: Domain-specific services (video_engine, nexus_engine, etc.)
- Depends on: Database layer, External APIs
- Used by: API layer, Background tasks
- Purpose: Shared utilities and cross-cutting concerns
- Location: `api/utils/`
- Contains: Database connections, authentication, caching
- Depends on: External dependencies (Redis, database)
- Used by: API and Service layers
- Purpose: Data persistence and async processing
- Location: Database models in `api/utils/models.py`, Celery config
- Contains: SQLAlchemy models, migration scripts
- Depends on: PostgreSQL, Redis
- Used by: All layers
## Data Flow
- Database: SQLAlchemy ORM with PostgreSQL
- Cache: Redis for session data and API responses
- Files: Local or cloud storage for generated content
## Key Abstractions
- Purpose: Encapsulate business logic and external integrations
- Examples: `services/video_engine/synthesis_service.py`, `services/nexus_engine/orchestrator.py`
- Pattern: Class-based services with dependency injection
- Purpose: Data persistence and relationships
- Examples: `api/utils/models.py` (UserDB, VideoJobDB, etc.)
- Pattern: SQLAlchemy declarative models
- Purpose: HTTP endpoint definitions
- Examples: `api/routes/video.py`, `api/routes/auth.py`
- Pattern: FastAPI router modules with Pydantic schemas
## Entry Points
- Location: `api/main.py`
- Triggers: HTTP requests on port 8000
- Responsibilities: Route dispatching, middleware, error handling
- Location: `remote_ai_setup/main.py`
- Triggers: Celery task queue
- Responsibilities: AI processing, video generation
- Location: `apps/dashboard/` (Next.js), `apps/remotion-studio/`
- Triggers: User interactions
- Responsibilities: UI rendering, API consumption
## Error Handling
- HTTPException for API errors with status codes
- Global exception handler for uncaught errors
- Structured error responses with error codes
- Logging integration for debugging
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
