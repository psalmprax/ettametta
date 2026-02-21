# Task: Integrate Fish Speech and Scale OCI Infrastructure

## Information Gathering & Design
- [x] Compare Docker vs. Bare Metal for Fish Speech performance
- [x] Research Fish Speech Dockerization best practices for ARM architectures

## Infrastructure Scaling
- [x] Update Terraform configuration to increase boot volume to 200GB [ ]
- [x] Verify Terraform plan [ ]
- [x] Run terraform apply to increase volume [ ]

## Implementation Plan Update
- [x] Document Fish Speech as Component 7 in `implementation_plan.md` [ ]
- [x] Add deployment strategy (Docker) to the plan [ ]

## Service Integration (Future steps)
- [x] Create Fish Speech service skeleton
- [x] Add Dockerfile for Fish Speech
- [x_] Create `download_models.py` script
- [x] Update `Dockerfile` with automated bootstrapping
- [x] Automate Git push to trigger Jenkins
- [x] Replace ElevenLabs in frontend Settings UI with Engine Selection
- [x] Refactor backend VoiceoverService to support multiple engines
- [x] Implement Monetization Mode selection (Selective vs. All)
    - [x] Update backend settings defaults
    - [x] Update frontend settings UI
    - [x] Refactor engine to respect monetization mode
- [x] Sync all root documentation in `docs/`
- [x] Push all updates to remote GitHub repository

## Operations & Maintenance
- [x] Verify remote Jenkins status
    - [x] Check Jenkins service process (Running in Docker)
    - [x] Verify port 8080 visibility (Opened via OCI Security List)
    - [x] Test build pulse (HTTP 200 OK)
## Storage Lifecycle Management
- [x] Develop `StorageManager` service
    - [x] Implement local disk usage monitoring (140GB threshold)
    - [x] Implement safe move logic (Upload -> Verify -> Delete Local)
    - [x] Implement OCI retention policy (90 days)
- [x] Schedule storage manager via Celery Beat
- [x] Verify migration and deletion pulse

## Storage Monitoring & UI
- [x] Register `/storage` command in OpenClaw skill
- [x] Add `/stats/storage` endpoint to backend analytics
- [x] Implement storage health telemetry in Dashboard Home page
- [x] Develop OpenClaw handler for `storage` action
- [x] Verify Telegram report accuracy

## E2E Configuration
- [x] Create detailed E2E setup guide
- [x] Document sslip.io networking workaround
- [x] Configure Telegram Admin ID

## CI/CD Hardening
- [x] Update Jenkinsfile to inject all production credentials

## Seamless Configuration Vault
- [x] Implement `vault.py` secret resolver
- [x] Expand `/settings` API for OCI keys
- [x] Add OCI Storage inputs to Dashboard Settings UI
- [x] Refactor StorageService for dynamic keys
- [x] Refactor Stock Media service for dynamic keys
- [x] Refactor Voiceover service for dynamic keys
- [x] Refactor NexusEngine / Discovery for dynamic keys
## Phase 10: Local Video Preview (Test Drive)
- [x] Implement `preview_only` flag in `download_and_process_task`
- [x] Create `POST /video/test-drive` endpoint
- [x] Add "Test Drive" button to Dashboard Discovery Page
- [x] Create `VideoPreviewModal` UI component
- [x] Verify End-to-End "Test Drive" flow

## Phase 11: Analytics UI Design Refinement
- [x] Implement Neural Web lines in `GlobalPulseGlobe`
- [x] Upgrade globe materials and lighting
- [x] Fix Analytics layout constraints and skeleton states
- [x] Add mouse parallax interactivity to 3D assets
- [x] Verify premium aesthetic alignment

## Phase 12: Test Drive Reliability (Guardrails)
- [x] Add thumbnail validation to `/test-drive` selection
- [x] Add pre-download video-only check in Celery task
- [x] Implement graceful failure for incompatible assets

## Phase 13: Universal Niche & Style Expansion (The Infinity Pulse)
- [x] Support "Music", "Storytelling", "Children", and "True Crime" default niches
- [x] Implement Dynamic Niche Search in Discovery UI
- [x] Add "Style Overlay" selector (Cinematic, Hectic, ASMR)
- [x] Upgrade `DecisionEngine` to handle explicit style parameters
- [x] Verify niche/style variety in transformation outputs

## Phase 14: The Nexus Command Center (Visual Automation)
- [x] Create `/nexus` page with Framer Motion drag-and-drop
- [x] Implement `NexusNode` component (Source, AI, Synth, Egress)
- [x] Build "Blueprint Library" with preset automation recipes
- [x] Integrate real-time "Pipeline Conveyor Belt" visualization
- [x] Support dynamic flow orchestration in `NexusOrchestrator`

## Phase 15: Production Hardening & Global Config
- [x] Move `PRODUCTION_DOMAIN` and Redirect URIs to environment variables
- [x] Remove hardcoded production IP from `docker-compose.yml`
- [x] Implement startup environment validation (Fail-fast logic)
- [x] Make `FONT_PATH` and render settings fully configurable
- [x] Centralize all API keys in `Vault` with local fallbacks
- [x] Connect Empire page to real A/B testing telemetry

## Phase 16: Build System Hardening (Hotfix)
- [x] Deduplicate `api/requirements.txt` and fix `SQLAlchemy` casing
- [x] Add global `pip install --upgrade pip` to Dockerfiles

## Phase 16.1: Build Resiliency (Networking)
- [x] Increase `pip` timeout to 100s in all Dockerfiles
- [x] Add `dns` configuration to `docker-compose.yml` (Optional recommendation)

## Phase 16.2: Route Layer Hotfix
- [x] Fix missing `Optional` import in `api/routes/video.py`
- [x] Audit all_ route files for import consistency

## Phase 17: Jenkins Production Sync
- [x] Map all remaining production keys (OpenAI, Pexels, ElevenLabs) in `Jenkinsfile`
- [x] Add `PRODUCTION_DOMAIN` parameterization to Jenkins pipeline
- [x] Verify `.env` generation on the OCI instance

## Phase 18: YouTube Bot Detection Bypass
- [x] Implement generic `COOKIES_PATH` support in `VideoDownloader`
- [x] Add `YOUTUBE_COOKIES_PATH` to `Settings` and `Vault`
- [x] Update documentation with instructions for exporting cookies

## Phase 18.1: CI/CD Persistence & Security
- [x] Exclude `cookies/` from `rsync` in `Jenkinsfile`
- [x] Add `cookies/` to `.gitignore`
- [x] Push security updates to GitHub

## Phase 18.2: OCI Permission Repair
- [x] Fix `/home/ubuntu/viralforge` ownership on OCI instance
- [x] Upload `youtube_cookies.txt` with correct permissions

## Phase 18.3: Format Resiliency (Hotfix)
- [x] Explicitly upgrade `yt-dlp` in `Dockerfile` to handle YouTube changes
- [x] Refine `format` selector in `VideoDownloader` for Shorts compatibility
- [x] Add `best` fallback to `verify_video_asset` logic

## Phase 18.4: Hyper-Resiliency (Validation Fix)
- [x] Remove restrictive `format: best` from `verify_video_asset`
- [x] Broaden download fallback chain to `ydl_opts.pop('format')` as last resort
