# Architecture

**Analysis Date:** 2026-04-08

## Pattern Overview

**Overall:** Service-oriented architecture within a monolithic application

**Key Characteristics:**
- Modular services for business logic separation
- Shared database with SQLAlchemy ORM
- Asynchronous processing with Celery workers
- REST API with FastAPI framework
- Containerized deployment with Docker Compose

## Layers

**API Layer:**
- Purpose: HTTP request handling, routing, and response formatting
- Location: `api/`
- Contains: FastAPI routes, middleware, utilities
- Depends on: Services layer, Database layer
- Used by: External clients (web/mobile apps)

**Service Layer:**
- Purpose: Business logic and external integrations
- Location: `services/`
- Contains: Domain-specific services (video_engine, nexus_engine, etc.)
- Depends on: Database layer, External APIs
- Used by: API layer, Background tasks

**Utility Layer:**
- Purpose: Shared utilities and cross-cutting concerns
- Location: `api/utils/`
- Contains: Database connections, authentication, caching
- Depends on: External dependencies (Redis, database)
- Used by: API and Service layers

**Infrastructure Layer:**
- Purpose: Data persistence and async processing
- Location: Database models in `api/utils/models.py`, Celery config
- Contains: SQLAlchemy models, migration scripts
- Depends on: PostgreSQL, Redis
- Used by: All layers

## Data Flow

**API Request Flow:**

1. HTTP request received by FastAPI route
2. Authentication and validation middleware applied
3. Route handler calls service method(s)
4. Service performs business logic, queries database
5. External API calls made if needed
6. Response formatted and returned to client

**Async Processing Flow:**

1. API route queues background task with Celery
2. Celery worker picks up task
3. Worker executes service logic
4. Results stored in database or cached
5. Optional: WebSocket notifications sent

**State Management:**
- Database: SQLAlchemy ORM with PostgreSQL
- Cache: Redis for session data and API responses
- Files: Local or cloud storage for generated content

## Key Abstractions

**Service Classes:**
- Purpose: Encapsulate business logic and external integrations
- Examples: `services/video_engine/synthesis_service.py`, `services/nexus_engine/orchestrator.py`
- Pattern: Class-based services with dependency injection

**Database Models:**
- Purpose: Data persistence and relationships
- Examples: `api/utils/models.py` (UserDB, VideoJobDB, etc.)
- Pattern: SQLAlchemy declarative models

**API Routes:**
- Purpose: HTTP endpoint definitions
- Examples: `api/routes/video.py`, `api/routes/auth.py`
- Pattern: FastAPI router modules with Pydantic schemas

## Entry Points

**Main API Server:**
- Location: `api/main.py`
- Triggers: HTTP requests on port 8000
- Responsibilities: Route dispatching, middleware, error handling

**Background Workers:**
- Location: `remote_ai_setup/main.py`
- Triggers: Celery task queue
- Responsibilities: AI processing, video generation

**Frontend Applications:**
- Location: `apps/dashboard/` (Next.js), `apps/remotion-studio/`
- Triggers: User interactions
- Responsibilities: UI rendering, API consumption

## Error Handling

**Strategy:** Centralized exception handling with FastAPI exception handlers

**Patterns:**
- HTTPException for API errors with status codes
- Global exception handler for uncaught errors
- Structured error responses with error codes
- Logging integration for debugging

## Cross-Cutting Concerns

**Logging:** Python logging with structured output and multiple levels
**Validation:** Pydantic models for request/response validation
**Authentication:** JWT tokens with FastAPI security dependencies
**Caching:** Redis-backed FastAPICache for API responses
**Rate Limiting:** slowapi library with Redis backend
**Monitoring:** Prometheus metrics, health checks

---

*Architecture analysis: 2026-04-08*