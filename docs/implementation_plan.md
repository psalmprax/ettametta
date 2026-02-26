# ettametta: Implementation Plan (Current & Future)

> **Last Updated**: February 26, 2026  
> **Version**: 2.8 — Tiered Subscriptions Initialized
> **Phase 59 Status**: 🏗️ In Planning

---

## System Overview

ettametta is a fully autonomous viral content engine for solo creators. It uses a hybrid Go+Python architecture for discovery, Groq AI for intelligence, FFmpeg for video transformation, and a Next.js dashboard for control. The system is deployed on Oracle Cloud Infrastructure (OCI) Always-Free ARM instances.

---

## Completed Architecture

### Component 1: Discovery Engine (Multi-Platform)
- **Go Engine** (`services/discovery-go`): Goroutine-based high-concurrency scanner
- **Python Scanners** (`services/discovery/`): 15+ platform-specific scrapers
  - YouTube, TikTok, Reddit, X, Instagram, Facebook, Twitch, Snapchat, Pinterest, LinkedIn, Bilibili, Rumble, DuckDuckGo, Archive.org, Pexels
- **Neural Ranking**: Groq `llama-3.3-70b-versatile` for viral score analysis
- **Temporal Intelligence**: `published_after` filtering for time horizons

### Component 2: Video Transformation Engine
- **Core**: FFmpeg + MoviePy containerized pipeline
- **Copyright Safety**: Mirroring, zoom (1.02x–1.08x), color shifts, pattern interrupts
- **AI Subtitles**: Fast-Whisper word-level captioning
- **GPU Support**: NVENC encoding with CPU fallback (`BASE_IMAGE` build arg)
- **Font Resolution**: Dynamic absolute `.ttf` path resolution for Linux
- **ARM64 Support**: OpenCV fallback for Oracle Cloud ARM instances

### Component 3: Publishing & Scheduling
- **YouTube**: OAuth 2.0 with token refresh, smart scheduler
- **TikTok**: Chunked upload API with CSRF-protected OAuth deep-link
- **Multi-Account**: `SocialAccount` model with per-account token management
- **Scheduler**: Celery Beat with Redis for autonomous posting

### Component 4: Monetization Engine
- **Affiliate**: Auto-injection with "humanized" metadata
- **Commerce**: Shopify Admin API + POD product matching
- **Strategy Pattern**: `AffiliateStrategy`, `LeadGenStrategy`, `DigitalProductStrategy`
- **A/B Testing**: Hook and thumbnail performance tracking
- **Exposure Integrity**: "Selective" mode for monk-like account reputation (Viral Score > 85).
- **Control Mode**: High-fidelity toggle between "Selective" and "All Content" injection.

### Component 5: Analytics & Intelligence
- **Real-time**: WebSocket telemetry streaming
- **Retention**: Average view duration from YouTube Analytics API
- **Visualization**: D3.js (Geomap, NetworkMesh), Three.js Globe, Recharts
- **Export**: PDF/CSV report generation

### Component 8: Autonomous Storage Lifecycle Manager
- **Enforcement**: 140GB local threshold monitoring via `os.walk`.
- **Archival**: Background migration to OCI Object Storage for older assets.
- **Retention**: Automated 90-day cloud purging policy.
- **Independence**: Background archival active even during local-only generation bursts.

### Component 6: Authentication & Security
- **JWT**: `python-jose` with role-based access control
- **Roles**: ADMIN, CREATOR, VIEWER
- **Data Isolation**: All jobs/history linked to `user_id`
- **Admin**: Hardcoded root access for `psalmprax`
- **Resilience**: Optimized middleware to prevent blocking imports; Nginx rate limits relaxed to 50r/s for seamless dashboard polling.
- **WebSocket Proxy**: Refactored Nginx to use trailing-slash stripping for robust protocol switching (101 Switching Protocols).
- **CSP Policy**: Dynamic whitelist for `cdn.jsdelivr.net` to support global intelligence mapping.
- **Healthchecks**: Custom Celery-aware health probes implemented for autonomous self-healing.

### Component 13: Nexus Pipeline Architecture (Nexus V2)
- **Graph Orchestrator**: Integrated React Flow in Nexus for visual pipeline composition.
- **Blueprint System**: Reusable graph templates (`NexusBlueprint`) for consistent content production.
- **Dynamic Execution**: Real-time node state telemetry and results streaming via main API.

### Component 14: Data Integrity & Production Readiness
- **No Mock Data**: All discovery scanners return empty results when APIs are unavailable
- **Error Handling**: Video synthesis raises errors instead of returning mock URLs
- **Monetization**: Strategy pattern returns empty strings when credentials not configured
- **Internal Auth**: Service-to-service communication uses configurable `INTERNAL_API_TOKEN`
- **UUID Generation**: Content IDs generated with proper UUIDs instead of hardcoded strings

### Component 14: Multi-Bot White-Labeling (Phase 27)
- **Private Agents**: Support for individual user Telegram bot tokens via [BotManager](file:///home/psalmprax/ettametta/services/openclaw/main.py).
- **Lifecycle Orchestration**: Dynamic starting/stopping of bot instances without service restarts.
- **Self-Service Onboarding**: Direct dashboard integration with @BotFather for token management.

## Component 15: Jenkins Infrastructure as Code (Phase 42)
- **Dockerized Jenkins**: Portable CI/CD environment using `jenkins/jenkins:lts` image.
- **JCasC (Jenkins Configuration as Code)**: Idempotent setup via `jenkins_casc_credentials.yaml`.
- **Credential Automation**: Automated import of 26+ environment variables via Groovy console scripts.
- **DooD (Docker-out-of-Docker)**: Host `docker.sock` binding for building containers within pipelines.

## Component 16: Expanded Platform Intelligence (Phase 36-41)
- **Skool Discovery**: `SkoolScanner` for extracting high-value educational trends.
- **WhatsApp Webhooks**: Bidirectional agent communication via Twilio API.
- **Persona Engine**: `PersonaService` for creating animated AI avatars from user selfies.
- **Monetization Settings**: Direct dashboard integration for affiliate and commerce account configuration.

## Component 17: Rebranding & Token Migration (Phase 43)
- **UI Branding**: Completed migration of all ViralForge headers to **ettametta**.
- **Auth Token Migration**: Standardized local storage keys from `vf_token` to `et_token` across all dashboard feature routes.

## Component 18: Downloader Resiliency (Phase 44)
- **Format Fallback**: Relaxed `yt-dlp` format selection to support YouTube Shorts and broad stream acquisition.
- **Cookie Architecture**: Implementation of Docker-aware relative path resolution for `youtube_cookies.txt` (checking `/app/cookies/` if local paths fail).

---

## Phase 58: Discovery Engine Restoration (Latest)
- **Status**: ✅ Production Ready
- **Scraper Fix**: Implemented robust regex and redirection handling for DuckDuckGo.
- **Bridge Fix**: Increased `httpx` timeout to 300s to support high-latency multi-niche scans.
- **Schema Fix**: Aligned Pydantic models with the Go engine payload.
- **Diversity**: Verified active discovery across 8+ platforms (YouTube, TikTok, Reddit, etc.).

---

## Phase 59: Tiered Synthesis Subscriptions
- **Goal**: Monetize high-end video synthesis engines via granular subscription tiers.
- **Tiers**:
  - **BASIC**: Access to `veo3`, `wan2.2`, `lite4k`.
  - **SOVEREIGN**: Access to `ltx-video` (Local Sovereign GPU).
  - **STUDIO**: Access to premium cloud APIs (`runway`, `pika`).
- **Implementation**:
  - [ ] Add `SOVEREIGN` and `STUDIO` to `SubscriptionTier` Enum in `user_models.py`.
  - [ ] Update `SUBSCRIPTION_TIERS` in `stripe_service.py` with pricing and feature set.
  - [ ] Enforce tier gating in `api/routes/video.py` synthesis endpoints.
  - [ ] Update daily limits per tier in `api/utils/subscription.py`.

---

## Phase 84–87: OCI Cloud Infrastructure

### Terraform Modules

#### [MODIFY] `terraform/modules/network/`
- VCN with public subnet
- Security list: ports 22 (SSH), 80, 443, 3000, 8000

#### [MODIFY] `terraform/modules/compute/`
- `oci_core_instance` with `VM.Standard.A1.Flex` (ARM)
- 4 OCPUs, 24GB RAM
- Cloud-init: auto-install Docker, Git, Docker Compose
- Automated Ubuntu image discovery

#### [MODIFY] `terraform/modules/storage/`
- Boot volume: 100GB
- Object Storage: private bucket for video assets

---

## Phase 89: OpenClaw Autonomous Agent

### Problem
Groq models were being registered as `openai` API type due to missing `"groq"` literal in `ModelApiSchema`.

### Fix Applied
#### [MODIFY] `src/config/zod-schema.core.ts` (on OCI ARM server)
```typescript
// After — added "groq"
export const ModelApiSchema = z.union([
  z.literal("openai-completions"),
  z.literal("openai-responses"),
  z.literal("groq"),
  // ... other types
]);
```

### Skills Architecture
| Skill | Trigger | Action |
|---|---|---|
| Discovery | "scan for [niche]" | Calls `/discovery/search` API |
| Operations | "restart api" | SSH command to OCI server |
| Analytics | "show metrics" | Queries `/analytics/summary` |

### Gateway
- **Telegram**: `@Psalmpraxbot` — live bidirectional communication
- **LLM**: Groq `llama-3.3-70b-versatile` (primary) + Ollama (local fallback)

---

## Phase 90: CI/CD Pipeline

### Jenkinsfile (Local OCI Jenkins)
```groovy
pipeline {
  agent any
  stages {
    stage('Checkout') { ... }
    stage('Build') { steps { sh 'docker-compose build' } }
    stage('Test') { steps { sh 'docker-compose run api pytest' } }
    stage('Deploy') { steps { sshagent { sh 'docker-compose up -d' } } }
  }
}
```

### GitHub Actions (`.github/workflows/deploy.yml`)
- Trigger: push to `master`
- Steps: lint → type-check → build → SSH deploy to OCI

---

## Phase 91: Production Hardening & Final Audit
- **AI Brain**: Consolidation of viral reasoning into `AIWorker`.
- **Latency**: Introduction of memoized caching for D3 visualizations.
- **Security**: Automated healthcheck remediation and circular import sanitization.

---

## Phase 92: WebSocket & Navigation Elasticity
- **Client Guard**: Implementation of `isMounted` ref in `useWebSocket` hook to prevent background reconnection loops on unmounted components.
- **Dynamic Routing**: Refactor of `config.ts` to use window-relative URLs for API and WebSocket bases, ensuring environment-agnostic handshakes.
- **Nginx Handshake**: Standardization of proxy headers via `map $http_upgrade` and `proxy_set_header Connection $connection_upgrade`.
- **Pathing**: Migration to `^~ /api/ws/` prefix in Nginx to ensure top-priority WebSocket routing without trailing-slash collisions.
- **Stability**: Extension of `proxy_read_timeout` to 300s for general API and 1 day for WebSockets.

---

## Phase 93: High-Fidelity Voice Synthesis (Fish Speech)

### Problem
ElevenLabs cost scaling is unsustainable for autonomous content generation. We need a high-quality, cost-effective alternative.

### Solution
Integrate **Fish Speech** (Open Source weights) as a containerized service.
- **Deployment**: Dockerized with ARM64 optimizations.
- **Storage**: Utilizes the expanded 200GB boot volume for model weights and audio cache.
- **Interface**: FastAPI wrapper for integration with `NexusEngine`.
- **Automation**: 
  - Added `download_models.py` to auto-fetch weights from HuggingFace.
  - Integration with `entrypoint.sh` to ensure weights exist before service start.

---

## Verification Plan

### Automated Tests
```bash
# Backend
docker-compose run api pytest services/ -v

# Frontend build
cd apps/dashboard && npm run build

# Terraform
cd terraform && terraform validate && terraform plan
```

### Manual Verification
1. Login to dashboard at `http://<OCI_IP>:3000`
2. Trigger discovery scan for "AI tools" niche
3. Queue a video for transformation
4. Verify Telegram bot responds to `/status` command
5. Check Celery Beat is running scheduled scans

---

## ⏳ Maintenance & Future Roadmap

| Phase | Feature | Priority |
|---|---|---|
| 96 | DNS & HTTPS final binding | HIGH |
| 97 | Mobile App (React Native) | MEDIUM |
| 98 | Marketplace for Skills/Templates | LOW |

---

## End-to-End Pipeline Use Cases

### USE CASE 1: Viral Content Repurposing
1. DISCOVERY → Scan TikTok for trending videos
2. DOWNLOAD → VideoDownloader.download_video()
3. TRANSFORMATION → Mirror, zoom, color shift, trim to hook
4. ENHANCEMENT → B-roll injection, cinematic overlays
5. MONETIZATION → Inject affiliate CTA
6. PUBLISH → Upload to YouTube Shorts/TikTok

### USE CASE 2: AI-Generated Short Film
1. CREATION → User enters prompt "Cyberpunk city"
2. GENERATION → Veo3/Wan2.2 generates 5 scenes
3. VOICEOVER → ElevenLabs TTS narration
4. ASSEMBLY → Concatenate scenes, add music
5. THUMBNAIL → AI-generated with Pollinations.ai

### USE CASE 3: Persona-Based Content
1. UPLOAD → User uploads selfie photo
2. ANIMATION → PersonaService.animate_persona()
3. BRANDING → Add intro/outro, watermark
4. MONETIZE → Add course promotion
5. DISTRIBUTE → Post to all platforms

### USE CASE 4: Automated Trend Riding
1. MONITOR → Continuous hourly discovery scan
2. FAST TRACK → Download & transform within minutes
3. VIRAL OPTIMIZATION → VLM analysis + A/B titles
4. LAUNCH → Post immediately for trend window

---

## API Endpoints Summary

| Endpoint | Purpose |
|----------|---------|
| POST /api/discovery/search | Find trending content |
| POST /api/video/generate | AI generate from prompt |
| POST /api/video/transform | Transform existing video |
| POST /api/video/persona | Create avatar video |
| POST /api/publish/youtube | Upload to YouTube |
| POST /api/publish/tiktok | Upload to TikTok |
| POST /api/publish/schedule | Schedule future post |
| GET /api/analytics/overview | View performance metrics |

---
*This analysis reflects the current state of the project as of February 26, 2026*
