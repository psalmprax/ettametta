# ViralForge: Architecture Design

> **Last Updated**: 2026-02-20  
> **Version**: 2.2 — Production-Hardened Autonomous Platform

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    VIRALFORGE PLATFORM                          │
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
| `dashboard` | 3000 | Next.js 14 | Frontend SPA |
| `db` | 5432 | PostgreSQL 15 | Primary database |
| `redis` | 6379 | Redis 7 | Cache + Celery broker |
| `celery` | — | Celery 5 | Background task workers |
| `celery-beat` | — | Celery Beat | Scheduled task scheduler |
| `discovery-go` | 8080 | Go 1.21 | High-speed trend scanner |
| `voiceover` | 8080 | FastAPI (Python) | Local neural voice synthesis (Fish Speech) |

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
UserDB          (id, username, email, role, subscription_tier, created_at)
ContentCandidate (id, title, platform, views, engagement_score, thumbnail_url, ...)
VideoJob        (id, user_id, status, input_url, output_path, created_at)
PublishedContent (id, user_id, job_id, platform, views, likes, revenue, ...)
SocialAccount   (id, user_id, platform, access_token, open_id, ...)
NicheTrendDB    (id, niche, trend_data, score, created_at)
MonitoredNiche  (id, niche, is_active, last_scanned_at)
ABTest          (id, user_id, variant_a, variant_b, winner, ...)
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

## OpenClaw Agent Architecture

```
Telegram (@Psalmpraxbot)
    │
    ▼
OpenClaw Gateway (Port 3001)
    │
    ├── Memory: Persistent session context
    ├── LLM: Groq llama-3.3-70b-versatile
    └── Skills:
        ├── vf_discovery_skill → /discovery/search API
        ├── vf_ops_skill       → SSH commands to OCI
        └── vf_analytics_skill → /analytics/summary API
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
        ├── Checkout
        ├── Docker Compose Build
        ├── pytest Suite
        └── docker-compose up -d
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
| CORS | Configured per environment |
| Secrets | `.env` file (never committed) |
| WS Verification | `isMounted` hook guards + 101 Handshake validation |
| Edge Stability | Standardized Nginx `Upgrade` mapping |

---

## V2.0 Migration Path (Future)

The current monolithic Docker Compose architecture can evolve to:

1. **Kubernetes (K8s)**: Extract each service into a K8s Deployment with HPA
2. **Service Mesh**: Istio for inter-service communication and observability
3. **Event Streaming**: Replace Celery with Apache Kafka for real-time event processing
4. **Multi-Region**: OCI Frankfurt + US East for global low-latency
5. **Mobile**: React Native app consuming the existing FastAPI backend
6. **SaaS**: Multi-tenant with per-user resource quotas and billing
