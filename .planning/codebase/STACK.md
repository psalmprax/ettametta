# Technology Stack

**Analysis Date:** 2026-04-08

## Languages

**Primary:**
- Python 3.10 - Main application logic, API, services
- TypeScript/JavaScript - Frontend apps (dashboard, remotion-studio), external skills
- Go 1.23.0 - Discovery service

**Secondary:**
- Not detected

## Runtime

**Environment:**
- Python 3.10-slim - Containerized with Docker
- Node.js 18-alpine - For frontend/dashboard apps
- Go runtime - For discovery-go service

**Package Manager:**
- pip - Python dependencies via requirements.txt
- npm/yarn - Node.js dependencies via package.json
- go mod - Go dependencies
- Lockfile: No explicit lockfiles detected (requirements.txt without hashes, package-lock.json not detected)

## Frameworks

**Core:**
- FastAPI - REST API framework with async support
- Next.js 16.1.6 - React framework for dashboard
- Gin v1.11.0 - HTTP web framework for Go discovery service
- React 19.2.3 - UI library for frontend

**Testing:**
- pytest - Test framework with asyncio support
- Jest - Testing framework (inferred from Next.js setup)

**Build/Dev:**
- Docker Compose - Multi-service orchestration
- Traefik v3.0 - Reverse proxy and load balancing

## Key Dependencies

**Critical:**
- SQLAlchemy >=2.0.0 - ORM with Alembic migrations
- Celery - Asynchronous task processing
- Redis - Caching and message broker
- PostgreSQL 15-alpine - Primary database
- Pydantic >=2.0.0 - Data validation

**Infrastructure:**
- Uvicorn - ASGI server for FastAPI
- Prometheus/Grafana - Monitoring stack
- Loki/Promtail - Log aggregation
- Nginx alpine - Static file serving

## Configuration

**Environment:**
- Pydantic Settings - Configuration management with .env support
- Environment variables - API keys, database URLs, secrets
- Multi-stage Docker builds for API and services

**Build:**
- Docker Compose files for service orchestration
- Dockerfile for each service
- Jenkins for CI/CD pipeline

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
- External AI provider APIs (OpenAI, Groq, Google AI, etc.)
- AWS S3 for file storage
- Stripe for payments

---

*Stack analysis: 2026-04-08*