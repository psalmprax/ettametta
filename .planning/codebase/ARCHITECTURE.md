# Architecture

**Analysis Date:** 2026-04-10

## Pattern Overview

**Overall:** Modular microservices architecture with shared database, asynchronous task processing, and containerized deployment.

**Key Characteristics:**
- REST API layer with FastAPI for HTTP request handling
- Business logic encapsulated in service modules with dependency injection
- Shared PostgreSQL database with SQLAlchemy ORM
- Asynchronous processing using Celery workers
- Containerized deployment with Docker Compose
- Frontend applications in separate directories

## Layers

**API Layer:**
- Purpose: HTTP request handling, routing, authentication, and response formatting
- Location: `api/`
- Contains: FastAPI routes, middleware, exception handlers, utilities
- Depends on: Services layer, Database layer, External APIs
- Used by: Frontend applications, external clients

**Services Layer:**
- Purpose: Business logic and external integrations
- Location: `services/`
- Contains: Domain-specific services (video_engine, nexus_engine, discovery, optimization, etc.)
- Depends on: Database layer, External APIs, AI providers
- Used by: API layer, Background tasks

**Utilities Layer:**
- Purpose: Shared utilities, database connections, authentication, and cross-cutting concerns
- Location: `api/utils/`
- Contains: Database configuration, authentication helpers, caching, validation
- Depends on: External dependencies (PostgreSQL, Redis)
- Used by: API and Services layers

**Data Layer:**
- Purpose: Data persistence and asynchronous processing
- Location: Database models in `api/utils/models.py`, `api/utils/user_models.py`
- Contains: SQLAlchemy models, database connections, Celery configuration
- Depends on: PostgreSQL, Redis
- Used by: All layers

## Data Flow

**Request Flow:**

1. HTTP request received by FastAPI app in `api/main.py`
2. Authentication middleware validates JWT token via `Depends(get_current_user)`
3. Request routed to appropriate endpoint in `api/routes/`
4. Route handler calls service methods with dependency injection
5. Service performs business logic, interacts with database via SQLAlchemy
6. Response formatted and returned to client

**Async Processing Flow:**

1. API endpoint queues task with Celery
2. Celery worker picks up task from Redis queue
3. Worker executes service logic (e.g., video generation)
4. Results stored in database or file system
5. Client polls for status updates via WebSocket or API

**Database:** SQLAlchemy ORM with PostgreSQL for persistent data, Redis for caching and session data

**File Storage:** Local file system for generated videos and assets, cloud storage integration

## Key Abstractions

**Service Classes:**
- Purpose: Encapsulate business logic and external API integrations
- Examples: `services/nexus_engine/orchestrator.py`, `services/video_engine/processor.py`
- Pattern: Singleton instances with `base_` prefix (e.g., `base_nexus_orchestrator`)

**Database Models:**
- Purpose: Data persistence and relationships
- Examples: `api/utils/models.py` (VideoJobDB, NexusJobDB), `api/utils/user_models.py` (UserDB)
- Pattern: SQLAlchemy declarative models with UUID primary keys

**API Routers:**
- Purpose: HTTP endpoint definitions and request/response schemas
- Examples: `api/routes/video.py`, `api/routes/auth.py`
- Pattern: FastAPI router modules with Pydantic schemas and dependency injection

**Dependency Injection:**
- Purpose: Manage service dependencies and database sessions
- Examples: `Depends(get_db)`, `Depends(get_current_user)`
- Pattern: FastAPI dependency system for authentication and database access

## Entry Points

**Main API:**
- Location: `api/main.py`
- Triggers: HTTP requests on port 8000
- Responsibilities: Route dispatching, middleware setup, exception handling, startup initialization

**AI Processing Service:**
- Location: `remote_ai_setup/main.py`
- Triggers: Celery task queue messages
- Responsibilities: AI model processing, video generation, external API calls

**Frontend Applications:**
- Location: `apps/dashboard/` (Next.js), `apps/remotion-studio/`
- Triggers: User interactions in browser
- Responsibilities: UI rendering, API consumption, video editing interface

**Background Workers:**
- Location: Various `services/*/main.py` files
- Triggers: Celery tasks, scheduled jobs
- Responsibilities: Asynchronous processing of video jobs, data scraping

## Error Handling

**Strategy:** Centralized exception handling with structured error responses

**Patterns:**
- Global exception handlers in `api/main.py` for database errors, validation errors, and unhandled exceptions
- HTTPException for API-specific errors with status codes and error codes
- Structured error responses with JSON format including error code, message, and timestamp
- Logging integration for debugging and monitoring

## Cross-Cutting Concerns

**Authentication:** JWT-based with OAuth2PasswordBearer, dependency injection via `Depends(get_current_user)`

**Authorization:** Role-based access control with UserRole enum, subscription tier checks

**Logging:** Python logging with structured messages, request logging middleware

**Caching:** Redis-backed FastAPICache for API responses and session data

**Rate Limiting:** SlowAPI with Redis backend, user-based limits per subscription tier

**Validation:** Pydantic models for request/response validation

**Security:** CORS middleware, security headers, input sanitization

---

*Architecture analysis: 2026-04-10*