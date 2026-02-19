# ViralForge: Implementation Plan (Current & Future)

> **Last Updated**: 2026-02-19  
> **Version**: 2.1 — Production-Hardened Autonomous Platform

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

### Component 5: Analytics & Intelligence
- **Real-time**: WebSocket telemetry streaming
- **Retention**: Average view duration from YouTube Analytics API
- **Visualization**: D3.js (Geomap, NetworkMesh), Three.js Globe, Recharts
- **Export**: PDF/CSV report generation

### Component 6: Authentication & Security
- **JWT**: `python-jose` with role-based access control
- **Roles**: ADMIN, CREATOR, VIEWER
- **Data Isolation**: All jobs/history linked to `user_id`
- **Admin**: Hardcoded root access for `psalmprax`

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
| 92 | DNS & HTTPS final binding | HIGH |
| 93 | Mobile App (React Native) | MEDIUM |
| 94 | Marketplace for Skills/Templates | LOW |
