# Codebase Structure

**Analysis Date:** 2026-04-10

## Directory Layout

```
ettametta/
├── api/                    # FastAPI backend application
├── services/               # Business logic services
├── apps/                   # Frontend applications
├── remote_ai_setup/        # AI processing workers
├── alembic/                # Database migrations
├── external-skills/        # Node.js skill modules
├── e2e/                    # End-to-end tests
├── monitoring/             # Observability stack
├── scripts/                # Utility scripts
├── terraform/              # Infrastructure as code
├── docker-compose.yml      # Service orchestration
├── requirements.txt        # Python dependencies
├── .env*                   # Environment configurations
└── .planning/              # Planning artifacts
```

## Directory Purposes

**api/:**
- Purpose: REST API layer with FastAPI, routing, and utilities
- Contains: Route handlers, middleware, database models, authentication
- Key files: `main.py`, `routes/*.py`, `utils/models.py`

**services/:**
- Purpose: Modular services for business logic and external integrations
- Contains: Video engine, nexus agent, optimization, discovery services
- Key files: `video_engine/synthesis_service.py`, `nexus_engine/orchestrator.py`

**apps/:**
- Purpose: User-facing applications built with Next.js and Remotion
- Contains: Dashboard UI, video editing studio
- Key files: `dashboard/src/app/page.tsx`, `remotion-studio/src/index.ts`

**remote_ai_setup/:**
- Purpose: Asynchronous AI processing and GPU management
- Contains: Worker processes, model downloading, hardware detection
- Key files: `main.py`, `ai_actions.py`

**alembic/:**
- Purpose: Database schema versioning and migrations
- Contains: Migration scripts for PostgreSQL schema changes
- Key files: `versions/*.py`

## Key File Locations

**Entry Points:**
- `api/main.py`: Main FastAPI server
- `apps/dashboard/src/app/page.tsx`: Dashboard homepage
- `remote_ai_setup/main.py`: AI worker process
- `services/discovery-go/main.go`: Go-based discovery service

**Configuration:**
- `api/config.py`: Pydantic settings with environment variables
- `docker-compose.yml`: Multi-service container orchestration
- `.env`: Environment variables (secrets, API keys)

**Core Logic:**
- `services/video_engine/`: AI video generation services
- `services/nexus_engine/`: AI agent orchestration
- `services/optimization/`: Social media publishing optimization

**Testing:**
- `api/tests/`: pytest-based API tests
- `e2e/`: Playwright end-to-end tests

## Naming Conventions

**Files:**
- snake_case.py for Python modules and files
- camelCase.ts/.tsx for TypeScript and React components
- kebab-case for config files (docker-compose.yml)

**Directories:**
- snake_case for Python packages (api/, services/)
- camelCase for apps (dashboard/, remotion-studio/)
- kebab-case for tools and configs

## Where to Add New Code

**New API Endpoint:**
- Implementation: `api/routes/new_endpoint.py`
- Tests: `api/tests/test_new_endpoint.py`

**New Business Service:**
- Implementation: `services/new_service/`
- Base class: `services/new_service/service.py`

**New Frontend Page:**
- Implementation: `apps/dashboard/src/app/new-page/page.tsx`
- Components: `apps/dashboard/src/components/new-page/`

**New Database Model:**
- Implementation: `api/utils/models.py`
- Migration: `alembic/versions/`

**Utilities:**
- API-related: `api/utils/`
- Service-related: `services/shared/`
- Frontend: `apps/dashboard/src/lib/`

## Special Directories

**external-skills/:**
- Purpose: Node.js modules for AI skills and integrations
- Generated: No
- Committed: Yes

**.planning/:**
- Purpose: GSD planning documents and codebase analysis
- Generated: Yes, by GSD commands
- Committed: Yes

**monitoring/:**
- Purpose: Prometheus and Grafana configuration
- Generated: No
- Committed: Yes

**terraform/:**
- Purpose: Infrastructure provisioning scripts
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-04-10*</content>
<parameter name="filePath">.planning/codebase/STRUCTURE.md