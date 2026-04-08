# External Integrations

**Analysis Date:** 2026-04-08

## APIs & External Services

**[AI/ML Providers]:**
- Groq - Primary LLM provider
  - SDK/Client: groq Python library
  - Auth: GROQ_API_KEY environment variable
- OpenAI - LLM and image generation
  - SDK/Client: openai Python library
  - Auth: OPENAI_API_KEY
- Google Generative AI - Vision and text
  - SDK/Client: google-generativeai
  - Auth: GOOGLE_API_KEY (inferred)
- YouTube API - Publishing and analytics
  - SDK/Client: google-api-python-client
  - Auth: YOUTUBE_API_KEY, OAuth with GOOGLE_CLIENT_ID/SECRET

**[Social Media Platforms]:**
- TikTok API - Publishing
  - SDK/Client: Custom HTTP client
  - Auth: TIKTOK_API_KEY, OAuth with TIKTOK_CLIENT_KEY/SECRET

**[Voice & Audio]:**
- ElevenLabs - Text-to-speech
  - SDK/Client: Not detected in code
  - Auth: ELEVENLABS_API_KEY

**[Media & Content]:**
- Pexels API - Stock images/videos
  - SDK/Client: Not detected in code
  - Auth: PEXELS_API_KEY

**[Payment Processing]:**
- Stripe - Subscription and payment handling
  - SDK/Client: stripe Python library
  - Auth: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

**[Cloud Storage]:**
- AWS S3 - File storage
  - SDK/Client: boto3
  - Auth: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_STORAGE_BUCKET_NAME

## Data Storage

**Databases:**
- PostgreSQL 15-alpine
  - Connection: DATABASE_URL environment variable
  - Client: SQLAlchemy ORM

**File Storage:**
- AWS S3
  - Connection: boto3 client with AWS credentials
  - Client: Custom storage service

**Caching:**
- Redis - In-memory caching and session storage
  - Connection: REDIS_URL
  - Client: redis-py library

## Authentication & Identity

**Auth Provider:**
- JWT-based custom authentication
  - Implementation: python-jose[cryptography]
- OAuth 2.0 for social platforms
  - Google OAuth: GOOGLE_CLIENT_ID/SECRET
  - TikTok OAuth: TIKTOK_CLIENT_KEY/SECRET

## Monitoring & Observability

**Error Tracking:**
- Custom logging with structured error reporting

**Logs:**
- Python logging with multiple handlers
- Loki for log aggregation
- Promtail for log shipping

## CI/CD & Deployment

**Hosting:**
- Docker containerized deployment
- Traefik v3.0 for load balancing and SSL termination
- Nginx alpine for static file serving

**CI Pipeline:**
- Jenkins (jenkins-docker-compose.yml detected)
- Docker-based builds

## Environment Configuration

**Required env vars:**
- Database: DATABASE_URL
- Redis: REDIS_URL
- Secrets: SECRET_KEY, INTERNAL_API_TOKEN
- AI APIs: GROQ_API_KEY, OPENAI_API_KEY, etc.
- OAuth: GOOGLE_CLIENT_ID/SECRET, TIKTOK_CLIENT_KEY/SECRET
- Payment: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
- Cloud: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_STORAGE_BUCKET_NAME

**Secrets location:**
- Environment variables (from .env file)
- Docker secrets for production

## Webhooks & Callbacks

**Incoming:**
- Stripe webhooks: Payment events
  - Endpoint: /webhooks/monetization/stripe
  - Auth: STRIPE_WEBHOOK_SECRET

**Outgoing:**
- Not detected

---

*Integration audit: 2026-04-08*