# Changelog

All notable changes to ettametta are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- LICENSE (MIT), CONTRIBUTING.md, CHANGELOG.md
- PR/issue templates, CODE_OF_CONDUCT.md, SECURITY.md
- Retry publish button for failed/pending-auth jobs in Egress Hub
- Analysis→creation flow in the Discovery page (poll + create video)
- Non-admin settings save via `/settings/user` endpoint

### Fixed
- Settings page now correctly uses `/settings/user` instead of admin-only `/settings/bulk`
- Global error boundary now reports errors to `/api/errors` endpoint

---

## [0.9.0] — 2025-03-15

### Added
- CloakBrowserScanner integration for authenticated scraping
- GitNexus submodule for multi-repo intelligence
- Remotion studio with Zod record schema and SVG filters
- Playwright-based TikTok/Instagram publishing automation

### Fixed
- Resource leak in `get_async_session()` database connection
- WebSocket telemetry crash and WebGL globe fallback
- Discovery service fallback chain and test mocks
- YouTube OAuth callback token exchange

### Changed
- Stabilized Nexus engine with production-grade Dify integration
- Migrated Python dependencies to Ubuntu 24.04 compatible packages
- Updated API path from `api/` to `src/api/` in CI workflows

---

## [0.8.0] — 2025-02-01

### Added
- Multi-platform video publishing (YouTube, TikTok, Instagram)
- AI-powered viral analysis and content deconstruction
- Celery async task processing for background jobs
- Redis caching layer for discovery results

### Changed
- Migrated from Flask to FastAPI for async performance
- Replaced single-threaded discovery with parallel scanner swarm

---

## [0.7.0] — 2025-01-15

### Added
- Initial discovery service with YouTube/TikTok integration
- Next.js dashboard with telemetry WebSocket
- Docker Compose orchestration with Traefik reverse proxy
- Prometheus/Grafana monitoring configuration

---

## [0.1.0] — 2024-12-01

### Added
- Project initialization with basic API structure
- SQLAlchemy ORM models and Alembic migrations
- Authentication system with JWT and Google OAuth
