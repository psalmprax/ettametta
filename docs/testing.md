# ettametta - Testing & Validation Guide

This document outlines the testing infrastructure, locations, and execution procedures for the **ettametta** (viral_forge) platform.

---

## 1. Backend & Unit Tests (Python)

All backend tests are located in the `api/tests/` directory and use the `pytest` framework.

### 📂 Directory Structure
- `api/tests/test_config.py`: Hardened environment and "Startup Shield" validation.
- `api/tests/test_services.py`: Internal business logic (Agents, LangChain, etc.).
- `api/tests/test_routes/`: Comprehensive coverage for FastAPI endpoints (`auth`, `video`, `discovery`).
- `api/tests/test_integration_discovery.py`: **Integration** - Bridge to the high-speed Go scanner.
- `api/tests/test_integration_video.py`: **Integration** - Virtualized MoviePy/FFmpeg pipeline.
- `api/tests/test_automation.py`: **E2E** - The full autonomous "Search -> Download -> Process" loop.

### 🚀 Execution
Run all backend tests from the `api/` directory:
```bash
cd api
pytest tests/ -v
```

---

## 2. Frontend & User Flow Tests (Playwright)

End-to-end (E2E) browser tests are located in the `e2e/` directory.

### 📂 Directory Structure
- `e2e/tests/auth/`: Login and OAuth redirection flows.
- `e2e/tests/creation/`: Content generation and dashboard interaction.
- `e2e/conftest.ts`: Playwright global configuration and fixtures.

### 🚀 Execution
Run the E2E suite from the `e2e/` directory:
```bash
cd e2e
npm install
npm test
```

---

## 3. CI/CD Integration

The testing suite is fully integrated into the **Jenkins CI/CD Pipeline**.

- **Automatic Execution**: Every commit to `master` triggers the "Integration Tests" stage.
- **Reporting**: Results are aggregated and displayed in the Jenkins dashboard via JUnit XML reports.
- **Fail-Fast**: The deployment is automatically aborted if any P0/P1 configuration or core integration tests fail.

---

## 4. Manual / Scripted Stubs

For rapid local iteration, specialized scripts are available in the `scripts/` folder:
- `scripts/test_discovery_search.py`: CLI-based scanner testing.
- `scripts/load_test.js`: Performance benchmarking for API endpoints.
- `scripts/check_server.py`: Connectivity and environment health check.

---
*Maintained by: Antigravity AI Engine*
