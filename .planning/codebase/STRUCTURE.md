# Codebase Structure

**Analysis Date:** 2026-04-08

## Directory Layout

```
viral_forge/
├── api/                    # FastAPI application
├── services/               # Business logic services
├── apps/                   # Additional applications
├── remote_ai_setup/        # AI worker setup
├── alembic/                # Database migrations
├── external-skills/        # Node.js skill modules
├── e2e/                    # End-to-end tests
├── monitoring/             # Observability stack
├── .planning/              # Planning documentation
├── scripts/                # Utility scripts
├── docker-compose.yml      # Service orchestration
└── requirements.txt        # Python dependencies
```

## Directory Purposes

**api/:**
- Purpose: Main FastAPI application with routes and utilities
- Contains: Route handlers, database models, authentication, middleware
- Key files: `main.py` (entry point), `config.py` (settings), `routes/*.py`

**services/:**
- Purpose: Modular business services for video generation, analytics, etc.
- Contains: Service classes, workflows, external API integrations
- Key files: `video_engine/`, `nexus_engine/`, `optimization/`

**apps/:**
- Purpose: Separate frontend/web applications
- Contains: Next.js dashboard, Remotion video editor
- Key files: `dashboard/package.json`, `remotion-studio/`

**remote_ai_setup/:**
- Purpose: AI worker processes and GPU management
- Contains: Worker scripts, model management, hardware detection
- Key files: `main.py`, `ai_actions.py`, `hardware_manager.py`

**alembic/:**
- Purpose: Database schema migrations
- Contains: Migration scripts and configuration
- Key files: `alembic.ini`, `versions/*.py`

## Key File Locations

**Entry Points:**
- `api/main.py`: FastAPI application server
- `remote_ai_setup/main.py`: AI processing workers

**Configuration:**
- `api/config.py`: Application settings and environment variables
- `docker-compose.yml`: Service definitions and networking

**Core Logic:**
- `services/video_engine/`: Video generation and processing
- `services/nexus_engine/`: AI agent orchestration
- `services/optimization/`: Social media publishing

**Testing:**
- `api/tests/`: API and integration tests
- `e2e/`: End-to-end test suites

## Naming Conventions

**Files:**
- snake_case.py for Python files
- camelCase.ts/.tsx for TypeScript/React files
- kebab-case for configuration files

**Directories:**
- snake_case for Python packages
- camelCase for apps and components
- kebab-case for external tools

## Where to Add New Code

**New Feature:**
- API endpoints: `api/routes/new_feature.py`
- Business logic: `services/new_service/`
- Database models: `api/utils/models.py`

**New Component/Module:**
- Service module: `services/new_module/`
- API utility: `api/utils/new_utility.py`

**Utilities:**
- Shared helpers: `api/utils/` for API-related, `services/shared/` for service utilities

## Special Directories

**external-skills/:**
- Purpose: Node.js modules for specialized AI skills
- Generated: No, manually maintained
- Committed: Yes

**.planning/:**
- Purpose: Documentation and planning artifacts
- Generated: Yes, by tools
- Committed: Yes

**monitoring/:**
- Purpose: Prometheus/Grafana configuration files
- Generated: No, configuration files
- Committed: Yes

---

*Structure analysis: 2026-04-08*