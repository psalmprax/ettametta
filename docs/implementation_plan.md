## Switch to CPU-only ML Dependencies

This plan addresses the large (~2GB+) downloads of NVIDIA/CUDA libraries during Docker builds by switching to CPU-only versions of machine learning packages (Torch, etc.).

## User Review Required

> [!IMPORTANT]
> The `api` and `voiceover` services will no longer support GPU acceleration. All ML tasks (transcription, voice synthesis, OCR) will run on the CPU. This is recommended for your current server (no GPU available).

## Proposed Changes

### [API & Voiceover Services]

#### [MODIFY] [requirements.txt](file:///home/psalmprax/viral_forge/api/requirements.txt)
#### [MODIFY] [requirements.txt](file:///home/psalmprax/viral_forge/services/voiceover/requirements.txt)
Add `--extra-index-url https://download.pytorch.org/whl/cpu` to ensure `torch` dependencies use the CPU-only variant.

#### [MODIFY] [Dockerfile](file:///home/psalmprax/viral_forge/api/Dockerfile)
#### [MODIFY] [Dockerfile](file:///home/psalmprax/viral_forge/services/voiceover/Dockerfile)
- Modify the `pip install` command to prioritize the CPU wheel index.
- **[NEW]** Install Remotion dependencies in `api/Dockerfile`.

### [Remotion Engine]

#### [MODIFY] [Dockerfile](file:///home/psalmprax/viral_forge/api/Dockerfile)
Install Remotion and its dependencies to enable Tier 3 motion graphics:
```dockerfile
# Install Remotion dependencies
COPY apps/remotion-studio /app/apps/remotion-studio
WORKDIR /app/apps/remotion-studio
RUN npm install
WORKDIR /app
```

3.  **Image Size**: Verify the reduction in Docker image size (`docker images`).

---

## End-to-End System Review

This phase validates the functional integrity of the entire stack (Frontend, Backend, Middleware, Networking) on the remote production server.

## Proposed Changes

### [System-Wide Validation]
- **Networking**: Verify Nginx routing to FastAPI and WebSockets.
- **Automation**: Validate Celery `sentinel_watcher` and `viral_loop` heartbeats.
- **Video Pipeline**: Test `yt-dlp` and `FFmpeg` within the `api` container.
- **Auth**: Restore `INTERNAL_API_TOKEN` for cross-service connectivity.

## Verification Plan

### Manual Verification
1.  **Remote Logs**: Inspect `docker logs` for Celery and API to confirm task success.
2.  **Health Check**: Call `/api/health` from the host and inside the container.
3.  **E2E Loop**: Trigger a manual autonomous cycle to verify the full "Discovery -> Process -> Post" chain.

---

## Resource Optimization & OOM Fix

This plan addresses the OOM (Out of Memory) crashes that are causing the Jenkins pipeline to fail with `exit code -1`.

## User Review Required

> [!IMPORTANT]
> I will be reducing the Celery worker concurrency from 10 to 2 and the replica count from 3 to 1. This will significantly lower RAM usage but may slightly increase task processing time.
> I will also add a 4GB swap file to the server as a safety net.

## Proposed Changes

### [Infrastructure & Deployment]

#### [MODIFY] [docker-compose.yml](file:///home/psalmprax/viral_forge/docker-compose.yml)
- Reduce `celery_worker` concurrency and replicas.
- Add memory limits to core services.

```yaml
   celery_worker:
-    command: celery -A api.utils.celery worker --loglevel=info --concurrency=10
+    command: celery -A api.utils.celery worker --loglevel=info --concurrency=2
-    deploy:
-      replicas: 3
+    deploy:
+      replicas: 1
+      resources:
+        limits:
+          memory: 1G
```

#### [Remote Server: 38.54.12.83]
1.  **Create Swap File**:
    - Create and enable a 4GB swap file to prevent hard OOM kills during builds.
2.  **Apply Optimized Configuration**:
    - Deploy the updated `docker-compose.yml` and restart services.

## Verification Plan

### Manual Verification
1.  **Monitor RAM**: Run `free -m` while the Jenkins pipeline is building to ensure memory usage stays within safe limits.
2.  **Jenkins Pipeline**: Rerun the pipeline and verify it completes without crashing.
---

## Phase 62: Continuous E2E Validation

This phase formalizes the manual validation steps into a repeatable `pytest` suite to ensure the automation loop remains functional.

### [Test Suite]

#### [NEW] [test_automation.py](file:///home/psalmprax/viral_forge/api/tests/test_automation.py)
A new test suite that performs:
- **Discovery Scan Verification**: Real hit against the discovery bridge.
- **Video Pipeline Verification**: Submission of transformation jobs with fallback MP4s.
- **Synthesis Engine Check**: Verification of Lite4K and Remotion task routing.
- **Environment Parity**: Logic to skip real hits unless `REAL_WORLD_E2E=1` is set.

## Verification Plan

### Automated Tests
- Run `pytest api/tests/test_automation.py`.
- Run `REAL_WORLD_E2E=1 pytest api/tests/test_automation.py` on the remote server to verify live integrations.

---

## Phase 76: Critical Gap Resolution (P0/P1)

This phase addresses the critical security and configuration gaps identified in the March 1st analysis.

### [API Configuration]

#### [MODIFY] [config.py](file:///home/psalmprax/viral_forge/api/config.py)
- Add `CORS_ORIGINS` settings.
- Harden `validate_critical_config` to raise errors in production mode.
- Ensure all OAuth keys have proper env mapping.

#### [MODIFY] [main.py](file:///home/psalmprax/viral_forge/api/main.py)
- Replace hardcoded CORS origins with `settings.CORS_ORIGINS`.
- Implement dynamic regex for subdomains if provided.

### [Infrastructure]

#### [NEW] [.env.production.template](file:///home/psalmprax/viral_forge/.env.production.template)
- Create a comprehensive template with all P0/P1 keys marked as required.

## Verification Plan

### Automated Tests
- Run `pytest api/tests/test_config.py` to verify environment validation logic.
- Verify CORS headers via `curl -I -X OPTIONS` on the remote server.

---

## Phase 77: Expanded E2E & Integration Testing

This phase increases test coverage from 30% to 60%+ by implementing deep service-to-service integration tests.

### [Test Suites]

#### [NEW] [test_integration_discovery.py](file:///home/psalmprax/viral_forge/api/tests/test_integration_discovery.py)
- **Goal**: Verify the bridge between Python `DiscoveryService` and the Go-based `discovery-go` scanner.
- **Coverage**: HTTP request/response validation, schema mapping, and error handling for scanner timeouts.

#### [NEW] [test_integration_video.py](file:///home/psalmprax/viral_forge/api/tests/test_integration_video.py)
- **Goal**: Verify the `VideoProcessor` pipeline without requiring a GPU.
- **Coverage**: Mocked FFmpeg output generation, metadata extraction, and successful task state transitions in Celery.

## Verification Plan

### Automated Tests
- Run `pytest api/tests/test_integration_discovery.py`.
- Run `pytest api/tests/test_integration_video.py`.
- Final E2E Run: `REAL_WORLD_E2E=1 pytest api/tests/test_automation.py`.

---

## Phase 80: E2E Remediation & Validation

This phase resolves naming inconsistencies and dependency gaps in the Playwright E2E suite to ensure it is executable.

### [Fixes]

#### [RENAME] `e2e/conftest.ts` -> `e2e/playwright.config.ts`
- **Reason**: Playwright requires `playwright.config.ts` by default. `conftest.ts` is a Python/pytest naming convention that was mistakenly applied to the TypeScript suite.

#### [COMMAND] `npm install` in `e2e/`
- **Reason**: The `node_modules` directory is missing, preventing test execution.

## Verification Plan

### Automated Tests
- Run `npx playwright test --list` to verify configuration validity.
- Run a single test file: `npx playwright test tests/auth/login.spec.ts`.

---

## Phase 81: CI/CD E2E Integration & Sync

This phase formally integrates the Playwright browser-based tests into both Jenkins and GitHub Actions CI pipelines, ensuring a consistent testing bar across environments.

### [CI Configuration]

#### [MODIFY] [.github/workflows/ci.yml](file:///home/psalmprax/viral_forge/.github/workflows/ci.yml)
- **Action**: Update backend tests to run `pytest tests/` (full suite).
- **Action**: Add a new `e2e` job that installs Node.js, Playwright, and runs the browser tests.

#### [MODIFY] [Jenkinsfile](file:///home/psalmprax/viral_forge/Jenkinsfile)
- **Action**: Remove `|| true` from the `E2E Tests` stage to make test results meaningful.
- **Action**: Add structured JUnit/Allure reporting for Playwright results.

## Verification Plan

### Automated Tests
- Push to a feature branch and verify that GitHub Actions triggers both backend and Playwright jobs.
- Trigger a manual build in Jenkins and verify that the "E2E Tests" stage correctly reports success/failure.

---

## Phase 83: Remote AI API Deployment (VPS)

This phase handles the offloading of heavy AI inference (LTX-Video, SpeechT5, Moondream2) to a dedicated high-GPU VPS.

### [Setup Components]

#### [NEW] `remote_ai_setup/`
A standalone directory containing:
- `install.sh`: Dependency installer (Python, CUDA dev, PyTorch).
- `main.py`: The FastAPI inference engine.
- `requirements.txt`: Unified dependency list.

### [Inference Features]
- **Video**: LTX-Video (T4 safe with CPU offload).
- **TTS**: Microsoft SpeechT5 (Stable default speaker).
- **VLM**: Moondream2 (Image analysis).

## Verification Plan

### Automated Tests
- `curl -sf http://66.23.193.245:8000/health` (Direct VPS check).
- `post /voice` test with specific payload.

---

## Phase 84: Expanding Remote AI (Whisper + Llama)

Maximize the utility of the RTX A4000 by adding high-speed transcription and local analysis.

### [Setup Components]

#### [MODIFY] `remote_ai_setup/main.py`
- **Integration**: Add `faster-whisper` using GPU/float16.
- **Integration**: Add `Llama-3.1-8B-Instruct` (Quantized via `bitsandbytes` or `AutoGPTQ`).
- **Endpoint**: `/transcribe` for ASR with word-level timestamps.
- **Endpoint**: `/llm` for local text generation and analysis.

#### [MODIFY] `remote_ai_setup/requirements.txt`
- Add `faster-whisper`, `bitsandbytes`, `scipy`.

### [VRAM Optimization]
- Use `torch.cuda.empty_cache()` between model transitions.
- Implement strictly lazy loading with optional "Unloading" for the largest models.

## Verification Plan

### Automated Tests
- `curl -X POST http://.../transcribe` with a small test WAV.
- `curl -X POST http://.../llm` with a simple "Hello" prompt.

