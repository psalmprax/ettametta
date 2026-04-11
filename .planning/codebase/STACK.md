# Technology Stack

**Analysis Date:** 2026-04-10

## Languages

**Primary:**
- Python 3.10 - Main application logic, API, services
- TypeScript/JavaScript - Frontend apps (dashboard, remotion-studio), external skills
- Go - Discovery service (discovery-go)

**Secondary:**
- Not applicable

## Runtime

**Environment:**
- Python 3.10-slim - Containerized with Docker
- Node.js 18-alpine - For frontend/dashboard apps
- Node.js 18 - For external skills
- Go 1.23-alpine - For discovery service

**Package Manager:**
- pip - Python dependencies via requirements.txt
- npm/yarn - Node.js dependencies via package.json
- go mod - Go modules
- Lockfile: No explicit lockfiles detected (requirements.txt without hashes, no package-lock.json)

## Frameworks

**Core:**
- FastAPI - REST API framework with async support
- Next.js 16.1.6 - React framework for dashboard
- React 19.2.3 - UI library
- Remotion 4.0.0 - Programmatic video production

**Testing:**
- pytest - Python testing framework
- Playwright - End-to-end testing

**Build/Dev:**
- Docker Compose - Multi-service orchestration
- Traefik v3.0 - Reverse proxy and load balancing
- Prometheus/Grafana - Monitoring stack

## Key Dependencies

**Critical:**
- SQLAlchemy >=2.0.0 - ORM with Alembic migrations
- Celery - Asynchronous task processing
- Redis - Caching and message broker
- Pydantic >=2.0.0 - Data validation
- PostgreSQL 15-alpine - Primary database

**Infrastructure:**
- Uvicorn - ASGI server for FastAPI
- Nginx alpine - Static file serving
- Loki - Log aggregation

## Configuration

**Environment:**
- Pydantic Settings - Configuration management with .env support
- Environment variables - API keys, database URLs, secrets from .env file

**Build:**
- Multi-stage Docker builds for API and services
- Docker Compose for service orchestration

## Platform Requirements

**Development:**
- Docker and Docker Compose
- Python 3.10+
- Node.js 18+ for frontend apps
- Go 1.23+ for discovery service

**Production:**
- Kubernetes/Docker Swarm for orchestration
- PostgreSQL database
- Redis cluster
- External AI provider APIs (OpenAI, Groq, etc.)

---

*Stack analysis: 2026-04-10*