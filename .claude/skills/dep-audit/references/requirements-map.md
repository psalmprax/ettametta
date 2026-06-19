# Requirements File Map

## Python Requirements

### Root Level
- `requirements.txt` — Generated from `.venv` on 2026-05-21. Exact pins. **May not reflect deployed state.**

### API Service (`src/api/`)
- `requirements.in` — pip-compile input with loose constraints (52 deps)
- `requirements.txt` — Primary API deps, mixed pinning (76 deps)
- `requirements-locked.txt` — pip-compile output with hashes (most trustworthy)

### Other Services
- `requirements-agents.txt` — Agent framework: gpt-researcher, open-interpreter, browser-use, langchain
- `src/services/openclaw/requirements.txt` — OpenClaw service
- `src/engines/remote_ai_setup/requirements.txt` — Remote AI setup (heavy ML stack)

### Subproject
- `graphify/pyproject.toml` — Standalone `graphifyy` v0.5.5 with optional dependency groups

## Node.js Packages

### Root
- `package.json` — Workspace config: `apps/*`, `src/tests/e2e`

### Apps
- `apps/dashboard/` — Next.js dashboard
- `apps/remotion-studio/` — Remotion 4.0.454, React 19, Zod 4.3.6
- `apps/external-skills/` — External skills package

### Tests
- `src/tests/e2e/` — Playwright E2E tests

## Docker Base Images

- `infra/docker/api.Dockerfile` — Python 3.10-slim
- `apps/dashboard/Dockerfile` — Node.js 18-alpine

## Known Conflicts

| Package | Root pin | API pin | Resolution needed |
|---------|----------|---------|-------------------|
| `bcrypt` | `==5.0.0` | `==4.0.1` | Pick one |
| `langchain` | `==0.1.20` | `==0.1.20` | Intentional (breaking API changes in newer versions) |
