---
name: improve-codebase-architecture
description: Conduct a systematic architecture review of codebase modules. Identifies god-classes, tight coupling, missing singletons, dead code, and resilience gaps.
---

# Architecture Review Skill

Performs structured codebase health checks, adhering strictly to ettametta architectural standards.

## Audit Checklist

### 1. Architectural Conventions
- [ ] Every domain service exports a singleton instance named `base_[service_name]_service`.
- [ ] Circular dependencies are eliminated.
- [ ] Service interfaces are cleanly typed with Pydantic models.

### 2. Resilience & Circuit Breaking
- [ ] External API calls (Groq, OpenAI, Whisper, social platforms) are wrapped in `CircuitBreaker` and retries (`tenacity`).
- [ ] Failures degrade gracefully without crashing Celery workers or API routes.

### 3. Knowledge Graph Sync
- [ ] After modifying code files, update the AST graph using `graphify update .`.
- [ ] Verify god nodes and community boundaries in `graphify-out/GRAPH_REPORT.md`.
