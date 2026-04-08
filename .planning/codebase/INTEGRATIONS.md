# External Integrations

**Analysis Date:** 2026-04-08

## APIs & External Services

**AI/ML Providers:**
- Groq API - Primary LLM provider (`GROQ_API_KEY`)
  - SDK/Client: groq Python library
  - Auth: API key via environment
- OpenAI API - Fallback LLM (`OPENAI_API_KEY`)
  - SDK/Client: openai library
  - Auth: API key
- Anthropic Claude - LLM provider (`ANTHROPIC_API_KEY`)
  - SDK/Client: anthropic library
  - Auth: API key
- Google Gemini - Vision and text (`GOOGLE_API_KEY`)
  - SDK/Client: google-generativeai
  - Auth: API key
- Multiple other LLM providers (DeepSeek, Cohere, Mistral, etc.)

**Video Generation:**
- Runway ML - Video generation (`RUNWAY_API_KEY`)
- Pika Labs - Video creation (`PIKA_API_KEY`)
- Stability AI - Video models (`STABILITY_API_KEY`)
- ZSky AI - Video generation (`ZSKY_API_KEY`)

**Social Media Platforms:**
- YouTube API - Publishing and analytics (`YOUTUBE_API_KEY`)
  - SDK/Client: google-api-python-client
  - Auth: OAuth 2.0 + API key
- TikTok API - Publishing (`TIKTOK_API_KEY`)
  - SDK/Client: Custom HTTP client
  - Auth: OAuth 2.0

**Voice & Audio:**
- ElevenLabs - Text-to-speech (`ELEVENLABS_API_KEY`)
- Fish Speech - Local voice synthesis (endpoint: `FISH_SPEECH_ENDPOINT`)

**Media & Content:**
- Pexels API - Stock images/videos (`PEXELS_API_KEY`)
- Google Search API - Content discovery (`GOOGLE_API_KEY`, `GOOGLE_SEARCH_CX`)

**Authentication:**
- Google OAuth - YouTube integration (`GOOGLE_CLIENT_ID/SECRET`)
- TikTok OAuth - TikTok integration (`TIKTOK_CLIENT_KEY/SECRET`)

## Data Storage

**Databases:**
- PostgreSQL 15 - Primary relational database
  - Connection: `DATABASE_URL` environment variable
  - Client: SQLAlchemy ORM

**File Storage:**
- Multi-cloud storage with provider abstraction
  - AWS S3 (`STORAGE_PROVIDER=AWS`)
  - OCI, GCP, Azure support configured
  - Local filesystem fallback

**Caching:**
- Redis - In-memory caching and session storage
  - Connection: `REDIS_URL`
  - Client: redis-py library

## Authentication & Identity

**Auth Provider:**
- JWT-based custom authentication
  - Implementation: FastAPI security with PyJWT
- OAuth 2.0 for social platforms (Google, TikTok)
  - Google OAuth: `GOOGLE_CLIENT_ID/SECRET`
  - TikTok OAuth: `TIKTOK_CLIENT_KEY/SECRET`

## Monitoring & Observability

**Error Tracking:**
- Custom logging with structured error reporting
- Frontend error reporting endpoint (`/api/v1/errors`)

**Logs:**
- Python logging with multiple handlers
- Loki for log aggregation
- Promtail for log shipping

## CI/CD & Deployment

**Hosting:**
- Docker containerized deployment
- Traefik for load balancing and SSL termination
- Nginx for static file serving

**CI Pipeline:**
- Jenkins (Jenkinsfile detected)
- Docker-based builds

## Environment Configuration

**Required env vars:**
- Database: `DATABASE_URL`
- Redis: `REDIS_URL`
- Secrets: `SECRET_KEY`, `INTERNAL_API_TOKEN`
- AI APIs: Various provider keys
- OAuth: Social platform credentials

**Secrets location:**
- Environment variables (from .env file)
- Docker secrets for production
- Vault integration for sensitive data

## Webhooks & Callbacks

**Incoming:**
- Stripe webhooks: Payment events (`STRIPE_WEBHOOK_SECRET`)
- YouTube webhooks: Content updates (`YOUTUBE_WEBHOOK_SECRET`)
- TikTok webhooks: Publishing notifications (`TIKTOK_WEBHOOK_SECRET`)
- Social media webhooks for engagement tracking

**Outgoing:**
- Not explicitly detected in codebase

---

*Integration audit: 2026-04-08*