# ettametta: Architecture Design

> **Version**: 2.6 — Tiered Monetization & Production Hardening

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      ettametta PLATFORM                         │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  Discovery   │    │  AI Brain    │    │  Video Engine    │  │
│  │  (Go + Py)   │───▶│ (AIWorker)   │───▶│  (FFmpeg+MoviePy)│  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                  │                     │              │
│         ▼                  ▼                     ▼              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │  PostgreSQL  │◀───│ Security     │───▶│  Publishing Hub  │  │
│  │  + Redis     │    │ Sentinel     │    │  (YT + TikTok)   │  │
│  └──────────────┘    └──────────────┘    └──────────────────┘  │
│         │                                        │              │
│         ▼                                        ▼              │
│  ┌──────────────┐                      ┌──────────────────┐    │
│  │  Analytics   │                      │  Monetization    │    │
│  │  Service     │                      │  Engine          │    │
│  └──────────────┘                      └──────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Next.js 14 Dashboard (Port 3000)           │   │
│  │  Discovery | Analytics | Empire | Transformation | Pub  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   OCI ARM Server   │
                    │  (Always-Free)     │
                    │  4 OCPU / 24GB RAM │
                    │  200GB Storage     │
                    └────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌──────────┐   ┌──────────────┐  ┌──────────┐
       │ OpenClaw │   │   Jenkins    │  │  GitHub  │
       │  Agent   │   │   CI/CD      │  │  Actions │
       └──────────┘   └──────────────┘  └──────────┘
              │
       ┌──────▼──────┐
       │  Telegram   │
       │ @Psalmpraxbot│
       └─────────────┘
```

---

## Service Architecture

### Backend Services (Docker Compose)

| Service | Port | Technology | Purpose |
|---|---|---|---|
| `api` | 8000 | FastAPI (Python) + Node.js | Main REST API + Signature Solving |
| `VLMService` | — | Gemini 1.5 Flash | Visual intuition & aesthetic reasoning |
| `dashboard` | 3000 | Next.js 14 | Frontend SPA |
| `db` | 5432 | PostgreSQL 15 | Primary database |
| `redis` | 6379 | Redis 7 | Cache + Celery broker |
| `celery` | — | Celery 5 (Scaled x3) | High-concurrency background task workers |
| `celery-beat` | — | Celery Beat | Scheduled task scheduler |
| `discovery-go` | 8080 | Go 1.21 | High-speed trend scanner |
| `voiceover` | 8080 | FastAPI (Python) | Local neural voice synthesis (Fish Speech) |
| `jenkins` | 8080 | Java (Dockerized) | Idempotent CI/CD Lifecycle Automation |

### API Layer (FastAPI)

```
api/
├── main.py                    # App factory, CORS, WebSocket
├── auth.py                    # JWT middleware
├── config.py                  # Env-based configuration
└── routes/
    ├── auth.py                # /auth/login, /auth/register
    ├── discovery.py           # /discovery/search, /discovery/scan
    ├── video.py               # /video/transform, /video/jobs
    ├── analytics.py           # /analytics/summary, /analytics/retention
    ├── publishing.py          # /publish/youtube, /publish/tiktok
    ├── optimization.py        # /optimization/monetize
    ├── empire.py              # /empire/clone, /empire/network
    └── settings.py            # /settings/get, /settings/save
```

### Database Schema (PostgreSQL)

```sql
-- Core Tables
UserDB          (id, username, email, role, subscription, telegram_chat_id, created_at)
  -- subscription: free, creator, empire, sovereign, studio
ContentCandidate (id, title, platform, views, engagement_score, thumbnail_url, ...)
VideoJob        (id, user_id, status, input_url, output_path, created_at)
PublishedContent (id, user_id, job_id, platform, views, likes, revenue, ...)
SocialAccount   (id, user_id, platform, access_token, open_id, ...)
NicheTrendDB    (id, niche, trend_data, score, created_at)
MonitoredNiche  (id, niche, is_active, last_scanned_at)
ABTestDB        (id, user_id, content_id, variant_a_title, variant_b_title, ...)
NexusJobDB      (id, user_id, status, blueprint_id, node_data, created_at)
```

---

## Discovery Architecture

### Platform Coverage

```
Discovery Core (service.py)
├── YouTube Scanner          → YouTube Data API v3
├── TikTok Scanner           → Web scraping + search
├── Reddit Scanner           → Reddit JSON API
├── X (Twitter) Scanner      → Nitter scraping
├── Instagram Scanner        → Web scraping
├── Facebook Scanner         → Web scraping
├── Twitch Scanner           → Twitch API
├── Snapchat Scanner         → Spotlight scraping
├── Pinterest Scanner        → Pinterest API
├── LinkedIn Scanner         → Web scraping
├── Bilibili Scanner         → Bilibili API
├── Rumble Scanner           → Web scraping
├── DuckDuckGo Scanner       → Metasearch
├── Archive.org Scanner      → Internet Archive API
└── Pexels Scanner           → Pexels API
```

### Neural Ranking Pipeline

```
Raw Candidates
    │
    ▼
Groq Llama-3.3-70b
    │ Prompt: "Analyze viral potential of these trends..."
    ▼
Scored & Ranked Candidates
    │
    ▼
PostgreSQL (ContentCandidate table)
    │
    ▼
Dashboard Discovery Grid
```

---

## Video Transformation Pipeline

```
Input URL
    │
    ▼
yt-dlp Download
    │
    ▼
FFmpeg Analysis (duration, resolution, codec)
    │
    ▼
VLM Visual Intuition (Gemini 1.5 Flash)
    │   - Detect Mood, Lighting, Subjects
    │   - Suggest aesthetic strategy
    ▼
MoviePy Transformation:
  ├── Mirror (horizontal flip)
  ├── Zoom (1.02x–1.08x random)
  ├── Color shift (hue rotation)
  └── Pattern interrupts (every 3s)
    │
    ▼
Fast-Whisper Transcription
    │
    ▼
Subtitle Overlay (word-level timestamps)
    │
    ▼
NVENC GPU Encode (fallback: CPU x264)
    │
    ▼
S3/MinIO Storage
    │
    ▼
Publishing Queue (Celery)
```

---

## Infrastructure Architecture (OCI Terraform)

```
OCI Frankfurt Region
├── VCN (10.0.0.0/16)
│   └── Public Subnet (10.0.1.0/24)
│       ├── Internet Gateway
│       └── Security List
│           ├── Ingress: 22 (SSH), 80, 443, 3000, 8000
│           └── Egress: All
├── Compute Instance (VM.Standard.A1.Flex)
│   ├── 4 OCPUs (ARM Ampere)
│   ├── 24GB RAM
│   ├── Boot Volume: 200GB
│   └── Cloud-init: Docker + Git + Docker Compose
└── Object Storage
    └── Private Bucket (video assets)
```

---

## OpenClaw Agent Architecture (Multi-Bot)

```
Telegram (User-Provided Tokens via @BotFather)
    │
    ▼
OpenClaw Gateway (Port 3001)
    │
    ├── BotManager: Concurrent bot application lifecycle orchestration
    ├── Identity: API-driven chat_id verification (/auth/verify-telegram)
    ├── LLM: Groq llama-3.3-70b-versatile
    └── Skills:
        ├── discovery_skill  → /discovery/search API
        ├── system_skill     → Health & Storage telemetry
        ├── content_skill    → /video/transform synthesis
        └── publishing_skill → /publish action orchestration
```

### OpenClaw Config (`~/.openclaw/config.yaml`)
```yaml
models:
  - name: groq/llama-3.3-70b-versatile
    api: groq
    apiKey: ${GROQ_API_KEY}

gateway:
  port: 3001
  telegram:
    token: ${TELEGRAM_BOT_TOKEN}
```

---

## CI/CD Architecture

```
Developer Push
    │
    ▼
GitHub (master branch)
    │
    ├── GitHub Actions (.github/workflows/deploy.yml)
    │   ├── Lint + Type Check
    │   ├── Docker Build Test
    │   └── SSH Deploy to OCI
    │
    └── Jenkins (OCI Server, Port 8080)
        ├── Dockerized Runtime (jenkins/jenkins:lts)
        ├── Configuration as Code (JCasC)
        ├── Groovy-based Credential Automation
        ├── Docker-out-of-Docker (DooD) build logic
        └── docker-compose up -d (Stable Node Deployment)
```

---

## Security Architecture

| Layer | Mechanism |
|---|---|
| API Auth | JWT (HS256, 30min expiry) |
| Role-Based Access | ADMIN > CREATOR > VIEWER |
| Data Isolation | `user_id` FK on all user data |
| OAuth Tokens | Encrypted in PostgreSQL |
| SSH Access | PEM key authentication |
| CORS | Configured per environment (Dynamic Origins) |
| Secrets | `.env` file (never committed) |
| WS Verification | `isMounted` hook guards + 101 Handshake validation |
| Edge Stability | Standardized Nginx `Upgrade` mapping |
| Internal Services | Configurable `INTERNAL_API_TOKEN` for service-to-service auth |
| Infrastructure | JCasC (Jenkins Configuration as Code) for idempotent secrets |
| Bot Bypass | Synchronized `youtube_cookies.txt` with Docker-aware path resolution |
| Branding | `et_token` standardized across all dashboard feature sets |
| Monetization | Tiered Gating (Free, Creator, Empire, Sovereign, Studio) |

## Unified Subscription Gating (Phase 59/60)

The platform enforces a multi-tier subscription model to monetize high-end generative compute:

| Tier | Daily/Monthly Limit | Engine Access | Features |
|---|---|---|---|
| **FREE** | 1 Video/Day | - | Basic Discovery |
| **CREATOR** | 3 Videos/Day | - | Transformation Pipeline |
| **EMPIRE** | 90 Videos/Month | `lite4k` | Viral Growth Nodes |
| **SOVEREIGN**| 120 Videos/Month | `ltx-2`, `lite4k` | LTX-Video Access |
| **STUDIO** | 200 Videos/Month | `veo3`, `wan2.2`, `runway`, `pika` | Full Generative Suite |

### Gating Logic (`api/utils/subscription.py`)
- **Engine Gating**: Backend decorators verify if the requested synthesis engine (e.g., `veo3`) is allowed for the user's current tier.
- **Quota Management**: Real-time tracking of daily/monthly video generations against tier limits.
- **Frontend Sync**: The Dashboard UI (`settings`, `discovery`) dynamically enables features and displays "Tier Req" badges based on `userProfile.subscription`.

## Data Integrity & Production Readiness

All system components follow strict data integrity principles:

| Component | Behavior When Unconfigured |
|---|---|
| Discovery Scanners | Return empty list `[]` |
| Video Synthesis | Raise `ValueError` / `NotImplementedError` |
| Monetization CTAs | Return empty string `""` |
| Thumbnail Generation | Raise `RuntimeError` |
| Publish Package | Use proper UUID generation |

This ensures no fake data is ever displayed to end users.

---

## Competitive Advantage (The Moat)

ettametta is architected to outperform 2026's "Clipper" SaaS apps by focusing on **Autonomy** and **Intuition**:

1.  **Discovery Moat**: Multi-platform `discovery-go` engine scans the "Trend Mesh" before content goes viral locally.
2.  **Creative Moat**: `VLMService` (Visual Cortex) performs scene/mood reasoning that transcript-only tools miss.
3.  **Owner Moat**: 100% private ownership on OCI ARM ensures no platform taxes or content censorship.

---

## V2.0 Migration Path (Future)

The current monolithic Docker Compose architecture can evolve to:

1. **Kubernetes (K8s)**: Extract each service into a K8s Deployment with HPA
2. **Service Mesh**: Istio for inter-service communication and observability
3. **Event Streaming**: Replace Celery with Apache Kafka for real-time event processing
4. **Multi-Region**: OCI Frankfurt + US East for global low-latency
5. **Mobile**: React Native app consuming the existing FastAPI backend
### 3.4. Remote Synthesis Node Pattern (LTX-2)
To handle the heavy VRAM requirements (28GB+), the system utilizes a **Remote Synthesis Node** pattern:
- **Local API**: Orchestrates requests and manages job state.
- **Secure Tunneling**: Utilizes `ngrok` or `RunPod` exposed ports to bridge environments.
- **GPU Node**: A specialized environment (OCI, Colab Pro, or RunPod) that handles the heavy diffusion inference.
- **Asynchronous Retrieval**: Results are pulled back to the local OCI instance via the same secure tunnel.

### 3.5. Multi-Node (Hybrid) Strategy
The system is designed to support multiple GPU providers simultaneously or as failovers:
- **Tier 1 (Prototyping)**: Google Colab Pro (High-RAM) for cost-effective interactive development.
- **Tier 2 (Production)**: RunPod/Vast.ai for "Always-On" stability and automated scaling via Agent Zero.
- **Monitoring**: The `Sentinel` agent monitors `RENDER_NODE_URL` and triggers recovery (Telegram alerts or RunPod API restarts) upon detection of downtime.
6. **SaaS**: Multi-tenant with per-user resource quotas and billing
