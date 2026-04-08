# Technology Stack

**Analysis Date:** 2026-04-08

## Languages

**Primary:**
- Python 3.10 - Main application logic, API, services

**Secondary:**
- TypeScript/JavaScript - Frontend apps (dashboard, remotion-studio), external skills
- Go - Discovery service (discovery-go)

## Runtime

**Environment:**
- Python 3.10-slim - Containerized with Docker
- Node.js 18-alpine - For frontend/dashboard apps

**Package Manager:**
- pip - Python dependencies via requirements.txt
- npm/yarn - Node.js dependencies via package.json
- Lockfile: No explicit lockfiles detected (requirements.txt without hashes)

## Frameworks

**Core:**
- FastAPI - REST API framework with async support
- SQLAlchemy - ORM with Alembic migrations
- Celery - Asynchronous task processing
- Redis - Caching and message broker

**Testing:**
- pytest - Test framework (inferred from test files)

**Build/Dev:**
- Docker Compose - Multi-service orchestration
- Traefik - Reverse proxy and load balancing
- Prometheus/Grafana - Monitoring stack

## Key Dependencies

**Critical:**
- fastapi - API framework
- sqlalchemy - Database ORM
- celery - Task queue
- redis - Cache and broker
- pydantic - Data validation

**Infrastructure:**
- postgres:15-alpine - Primary database
- traefik:v3.0 - API gateway
- nginx:alpine - Static file serving

## Configuration

**Environment:**
- Pydantic Settings - Configuration management with .env support
- Environment variables - API keys, database URLs, secrets

**Build:**
- Multi-stage Docker builds for API and services
- Docker Compose for service orchestration

## Platform Requirements

**Development:**
- Docker and Docker Compose
- Python 3.10+
- Node.js 18+ for frontend apps

**Production:**
- Kubernetes/Docker Swarm for orchestration
- PostgreSQL database
- Redis cluster
- External AI provider APIs (OpenAI, Groq, etc.)

---

*Stack analysis: 2026-04-08*