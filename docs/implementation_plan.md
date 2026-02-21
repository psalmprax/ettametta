# ViralForge: Implementation Plan (Current & Future)

> **Last Updated**: 2026-02-21  
> **Version**: 2.3 — Multimodal AI Director (VLM Integrated)

---

## System Overview

ViralForge is a fully autonomous viral content engine for solo creators. It uses a hybrid Go+Python architecture for discovery, Groq AI for intelligence, FFmpeg for video transformation, and a Next.js dashboard for control. The system is deployed on Oracle Cloud Infrastructure (OCI) Always-Free ARM instances.

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
// Before
export const ModelApiSchema = z.union([
  z.literal("openai-completions"),
  z.literal("openai-responses"),
  // ... other types
]);

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

### Component 9: Scraper Resiliency & Bypass (Phase 18)
- **Cookie-Based Proof**: Implementation of authenticated session cookies for `yt-dlp` to bypass "Confirm you're not a bot" screens.
- **Persistence**: Hybrid CI/CD logic to exclude session data from being scrubbed during Jenkins deployments.
- **Signature Decryption (Phase 18.5)**: Integration of `nodejs` runtime into the API container to solve YouTube "n-challenge" signature decryption, ensuring full access to video streams on cloud infrastructure.

### Component 10: High-Artistry & VLM Intuition (Phase 19 & 20)
- **OCR Awareness**: Implementation of [**`OCRService`**](file:///home/psalmprax/viral_forge/services/video_engine/ocr_service.py) for text-region detection, preventing caption overlap.
- **Semantic Trimming**: AI-driven "hook" detection to keep only high-energy segments.
- **Visual Cortex**: Integration of **Gemini 1.5 Flash** via [**`VLMService`**](file:///home/psalmprax/viral_forge/services/video_engine/vlm_service.py) for true visual intuition (mood, lighting, subject analysis).
- **Dynamic Aesthetics**: Automated caption color and grading selection based on visual mood.
- **Stock Injection**: Pexels API integration for automated cinematic B-roll insertion.
- **Infrastructural Scale**: Scaled `celery_worker` to 3 replicas for high-concurrency production.

### Component 11: Universal Niche & Style Expansion (Phase 21)
- **Niche Persistence**: Automated registration of custom dashboard searches into the [**`MonitoredNiche`**](file:///home/psalmprax/viral_forge/api/utils/models.py) registry.
- **High-Art Suite**: Implementation of 12+ creative filters including Glitch, Noir, Atmospheric Glow, and Film Grain.
- **Aesthetic Direction**: Expanded `DecisionEngine` prompts for style-specific intensity and color harmony logic.

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
