# ettametta - Testing & Validation Guide

This document outlines the testing infrastructure, locations, and execution procedures for the **ettametta** (ettametta) platform.

---

## 1. Production Smoke Tests

Run the canonical remote-server test ladder from the repository root:

```bash
python3 scripts/production_smoke_test.py \
  --api-url http://localhost:7201 \
  --dashboard-url http://localhost:7200 \
  --docker
```

Add `--e2e` for Playwright and `--video-scenario 0` for a controlled render smoke. Full details live in `docs/production_smoke_testing.md`.

---

## 2. Backend & Unit Tests (Python)

Backend tests are located in `src/api/tests/` and use the `pytest` framework.

### 📂 Directory Structure
- `src/api/tests/test_config.py`: Hardened environment and startup validation.
- `src/api/tests/test_routes/`: FastAPI endpoint coverage (`auth`, `video`, `discovery`, `health`).
- `src/api/tests/test_integration_discovery.py`: Integration bridge to discovery scanners.
- `src/api/tests/test_integration_video.py`: Virtualized MoviePy/FFmpeg pipeline.
- `src/api/tests/test_automation.py`: E2E autonomous "Search -> Download -> Process" loop.

### 🚀 Execution
Run backend tests from the repository root:
```bash
pytest src/api/tests -v --tb=short
```

---

## 3. Frontend & User Flow Tests (Playwright)

End-to-end (E2E) browser tests are located in `src/tests/e2e/`.

### 📂 Directory Structure
- `src/tests/e2e/tests/auth/`: Login and OAuth redirection flows.
- `src/tests/e2e/tests/creation/`: Content generation and dashboard interaction.
- `src/tests/e2e/playwright.config.ts`: Playwright configuration and fixtures.

### 🚀 Execution
Run the E2E suite against the remote dashboard:
```bash
cd src/tests/e2e
npm install
SKIP_WEB_SERVER=1 BASE_URL=http://localhost:7200 npm test
```

---

## 4. CI/CD Integration

The testing suite is fully integrated into the **Jenkins CI/CD Pipeline**.

- **Automatic Execution**: Every commit to `master` triggers the "Integration Tests" stage.
- **Reporting**: Results are aggregated and displayed in the Jenkins dashboard via JUnit XML reports.
- **Fail-Fast**: The deployment is automatically aborted if any P0/P1 configuration or core integration tests fail.

---

## 5. Manual / Scripted Stubs

For rapid local iteration, specialized scripts are available in the `scripts/` folder:
- `scripts/test_discovery_search.py`: CLI-based scanner testing.
- `scripts/load_test.js`: Performance benchmarking for API endpoints.
- `scripts/check_server.py`: Connectivity and environment health check.

---
*Maintained by: Antigravity AI Engine*
