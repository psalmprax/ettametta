# ettametta: Expansion Blueprint

> **Last Updated**: 2026-02-27  
> **Version**: 1.1 - Production Expansion Roadmap (Updated)

---

## Phase 1: External API Integrations (Points 1-2)

### 1. External API Keys Configuration

Required API keys for full functionality:

| Service | Key | Purpose | Status |
|---------|-----|---------|--------|
| YouTube Data API | `YOUTUBE_API_KEY` | Discovery + Publishing | Required |
| Google Gemini | `GEMINI_API_KEY` | VLM Visual Cortex | Required |
| TikTok API | `TIKTOK_API_KEY` | Discovery + Publishing | Required |
| Shopify | `SHOPIFY_*` | Commerce/Merch | Required |
| Stripe | `STRIPE_*` | Payments | Required |
| Pexels | `PEXELS_API_KEY` | Stock Media | Optional |
| OpenAI | `OPENAI_API_KEY` | Fallback AI | Optional |

**Configuration:**
```bash
# Add to .env
YOUTUBE_API_KEY="AIza..."
TIKTOK_API_KEY="..."
SHOPIFY_SHOP_URL="..."
STRIPE_SECRET_KEY="sk_..."
```

### 2. GPU Node Setup for Video Generation

**Current State:** Video synthesis returns errors when APIs unavailable  
**Goal:** Self-hosted GPU rendering for generative video

**Architecture:**
```
┌─────────────────────────────────────────┐
│         Main API (Python)               │
│  ┌───────────────────────────────────┐  │
│  │  SynthesisService                 │  │
│  │  - Check RENDER_NODE_URL          │  │
│  │  - Proxy to GPU Node              │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│      Render Node (GPU Server)           │
│  - FastAPI + Diffusers                  │
│  - Veo 3 / Wan2.2 / LTX-2            │
│  - Webhook callback on completion       │
└─────────────────────────────────────────┘
```

**Implementation:**
- [ ] Deploy separate GPU container with `services/video_engine/`
- [ ] Configure `RENDER_NODE_URL` in environment
- [ ] Implement async job queue with Celery
- [ ] Add webhook endpoints for job completion
- [ ] Test with sample prompts

---

## Phase 2: Payment Integration (Point 3)

### 3. Real Payment Processor Integration

**Current State:** No payment processing  
**Goal:** Stripe integration for subscriptions

**Required Files:**
- [`api/routes/billing.py`](api/routes/billing.py) - New billing endpoints
- [`services/payment/stripe_service.py`](services/payment/stripe_service.py) - Stripe integration

**Implementation:**
```python
# services/payment/stripe_service.py
import stripe
from api.config import settings

class PaymentService:
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
    
    async def create_subscription(self, user_id: str, price_id: str):
        # Create Stripe customer
        # Create subscription
        # Store Stripe customer ID in DB
        pass
    
    async def get_subscription_status(self, stripe_customer_id: str):
        # Check subscription status
        pass
    
    async def cancel_subscription(self, subscription_id: str):
        # Cancel at period end
        pass
```

**Subscription Tiers:**
| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | Basic discovery, 5 videos/month |
| Creator | $29/mo | Full pipeline, 50 videos/mo |
| Empire | $99/mo | Unlimited, priority GPU |

---

## Phase 3: Performance & Scale (Point 4)

### 4. Load Testing & Performance Tuning

**Current State:** Single OCI ARM instance  
**Goal:** Production-grade performance

**Testing Strategy:**
```bash
# Install k6 for load testing
brew install k6  # macOS
sudo apt-get install k6  # Linux

# Run load test
k6 run scripts/load_test.js
```

**Key Metrics to Test:**
- [ ] API response time (p95 < 500ms)
- [ ] Concurrent user capacity
- [ ] Database connection pool efficiency
- [ ] Redis cache hit rates
- [ ] Video processing queue throughput

**Optimization Checklist:**
- [ ] Add database connection pooling (PgBouncer)
- [ ] Implement Redis caching for frequent queries
- [ ] Add CDN for static assets
- [ ] Configure horizontal pod autoscaling
- [ ] Set up Prometheus + Grafana monitoring

---

## Phase 4: Credential & OAuth Configuration (Points 5-7)

### 5. Production OAuth Credentials

**Current State:** OAuth credentials missing for production deployment
**Goal:** Configure real OAuth credentials for YouTube and TikTok publishing

| Credential | Location | Status |
|------------|---------|--------|
| `GOOGLE_CLIENT_ID` | api/config.py:40 | ❌ Missing |
| `GOOGLE_CLIENT_SECRET` | api/config.py:41 | ❌ Missing |
| `TIKTOK_CLIENT_KEY` | api/config.py:45 | ❌ Missing |
| `TIKTOK_CLIENT_SECRET` | api/config.py:46 | ❌ Missing |

**Required Actions:**
- [ ] Register application in Google Cloud Console
- [ ] Register application in TikTok Developer Portal
- [ ] Configure production redirect URIs
- [ ] Set `PRODUCTION_DOMAIN` environment variable
- [ ] Implement OAuth token refresh webhooks

### 6. Cloud Storage Configuration

**Current State:** AWS S3 credentials not configured
**Goal:** Enable cloud storage for processed videos

| Service | Keys Required | Status |
|---------|---------------|--------|
| AWS S3 | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` | ❌ Missing |

**Required Actions:**
- [ ] Configure AWS credentials in .env
- [ ] Set up S3 bucket for video storage
- [ ] Configure storage lifecycle policies

### 7. External AI Services

**Current State:** Missing API keys for premium services
**Goal:** Enable premium voice and stock media

| Service | Key | Status |
|---------|-----|--------|
| ElevenLabs | `ELEVENLABS_API_KEY` | ❌ Missing |
| Pexels | `PEXELS_API_KEY` | ❌ Missing |
| OpenAI | `OPENAI_API_KEY` | ❌ Missing |

**Required Actions:**
- [ ] Add ElevenLabs API key for premium voice generation
- [ ] Add Pexels API key for stock media access
- [ ] Add OpenAI API key as Groq fallback

---

## Phase 5: Commerce Integration (Point 8)

### 8. Shopify Commerce Setup

**Current State:** Commerce service coded but not configured
**Goal:** Enable product monetization and affiliate links

| Config | Key | Status |
|--------|-----|--------|
| Shopify Store | `SHOPIFY_SHOP_URL` | ❌ Missing |
| Shopify Token | `SHOPIFY_ACCESS_TOKEN` | ❌ Missing |

**Required Actions:**
- [ ] Configure Shopify Admin API credentials
- [ ] Add affiliate link management UI
- [ ] Implement product-to-niche matching

---

## Phase 6: Monetization Enhancement (NEW - Priority P0)

### 9. Monetization Full Implementation

**Current State:** 75% Complete - Revenue tracking exists, but external integrations missing
**Goal:** Complete monetization pipeline with real payments and analytics

#### 9.1 Shopify Integration
| Config | Key | Status | Priority |
|--------|-----|--------|----------|
| Shopify Store | `SHOPIFY_SHOP_URL` | ❌ Missing | P0 |
| Shopify Token | `SHOPIFY_ACCESS_TOKEN` | ❌ Missing | P0 |
| Admin API | `SHOPIFY_ADMIN_KEY` | ❌ Missing | P0 |

**Implementation:**
- [ ] Configure Shopify Admin API credentials in SystemSettings
- [ ] Implement product catalog sync
- [ ] Add order tracking webhooks
- [ ] Create product-to-niche matching algorithm

#### 9.2 AWS S3 Cloud Storage for Revenue
| Config | Key | Status | Priority |
|--------|-----|--------|----------|
| AWS Access Key | `AWS_ACCESS_KEY_ID` | ❌ Missing | P0 |
| AWS Secret Key | `AWS_SECRET_ACCESS_KEY` | ❌ Missing | P0 |
| S3 Bucket | `AWS_STORAGE_BUCKET_NAME` | ❌ Missing | P0 |
| AWS Region | `AWS_REGION` | ❌ Missing | P0 |

**Required Actions:**
- [ ] Configure AWS credentials
- [ ] Set up S3 bucket with lifecycle policies
- [ ] Implement video upload to S3
- [ ] Configure CloudFront CDN for video delivery

#### 9.3 Premium AI Services
| Service | Key | Status | Priority |
|---------|-----|--------|----------|
| ElevenLabs | `ELEVENLABS_API_KEY` | ❌ Missing | P1 |
| Pexels | `PEXELS_API_KEY` | ❌ Missing | P1 |

**Required Actions:**
- [ ] Add ElevenLabs for premium voice generation (tier 2-3)
- [ ] Add Pexels for stock media access
- [ ] Implement usage-based billing tracking

#### 9.4 Revenue Analytics
**Required Actions:**
- [ ] Connect Empire page to A/B test API
- [ ] Implement real revenue dashboard
- [ ] Add affiliate link click tracking
- [ ] Create revenue forecasting models

---

## Phase 7: E2E Testing Framework (NEW - Priority P0)

### 10. Comprehensive Testing Suite

**Current State:** 15% Complete - Only unit tests exist
**Goal:** Production-grade testing with integration and E2E coverage

#### 10.1 Integration Tests for API Routes

**Required Actions:**
- [ ] Create `api/tests/test_routes/` directory
- [ ] Add integration tests for all 16 API routes:
  - [ ] `test_auth.py` - Authentication flows
  - [ ] `test_discovery.py` - Discovery endpoints
  - [ ] `test_video.py` - Video processing
  - [ ] `test_publish.py` - Publishing workflows
  - [ ] `test_analytics.py` - Analytics data
  - [ ] `test_monetization.py` - Revenue tracking
  - [ ] `test_nexus.py` - Nexus orchestration

**Test Structure:**
```python
# api/tests/test_routes/test_auth.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_login_success(client):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpass"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_credentials(client):
    response = client.post("/auth/login", json={
        "email": "invalid@example.com",
        "password": "wrongpass"
    })
    assert response.status_code == 401
```

#### 10.2 OAuth Flow E2E Tests

**Required Actions:**
- [ ] Create OAuth mock service for testing
- [ ] Implement YouTube OAuth flow tests
- [ ] Implement TikTok OAuth flow tests
- [ ] Add token refresh webhook tests
- [ ] Test OAuth error handling

**Test Coverage:**
- [ ] OAuth redirect URL generation
- [ ] Callback URL handling
- [ ] Token storage and retrieval
- [ ] Token refresh automation
- [ ] Error scenarios (expired, revoked tokens)

#### 10.3 Video Pipeline Tests

**Required Actions:**
- [ ] Create video processing test fixtures
- [ ] Test video upload endpoints
- [ ] Test transformation pipeline (filters, overlays)
- [ ] Test face detection/removal
- [ ] Test voiceover integration
- [ ] Test render completion webhooks

**Test Fixtures:**
```python
# api/tests/fixtures/video.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_video_path():
    return Path("tests/fixtures/sample_video.mp4")

@pytest.fixture
def video_processing_result():
    return {
        "job_id": "test-123",
        "status": "completed",
        "output_path": "/output/test-output.mp4"
    }
```

#### 10.4 Discovery Scanner Tests

**Required Actions:**
- [ ] Create scanner mock responses
- [ ] Test YouTube discovery scanner
- [ ] Test TikTok discovery scanner
- [ ] Test cross-platform aggregation
- [ ] Test trend detection algorithms
- [ ] Test Redis caching for discoveries

#### 10.5 E2E Framework Setup (Playwright/Cypress)

**Framework Selection:** Playwright (recommended for Python/FastAPI)

**Required Actions:**
- [ ] Install Playwright: `pip install pytest-playwright`
- [ ] Create `e2e/` directory
- [ ] Configure playwright.config.ts
- [ ] Implement E2E test suites:

```
e2e/
├── conftest.py           # Playwright configuration
├── playwright.config.ts  # Browser settings
├── tests/
│   ├── auth/
│   │   ├── login.spec.ts
│   │   └── register.spec.ts
│   ├── discovery/
│   │   └── trend_discovery.spec.ts
│   ├── creation/
│   │   └── video_creation.spec.ts
│   ├── publishing/
│   │   └── publish_workflow.spec.ts
│   └── monetization/
│       └── revenue_tracking.spec.ts
└── fixtures/
    ├── videos/
    └── images/
```

**E2E Test Examples:**
```typescript
// e2e/tests/auth/login.spec.ts
import { test, expect } from '@playwright/test';

test('user can login with valid credentials', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'testpass');
  await page.click('[data-testid="login-button"]');
  
  // Should redirect to dashboard
  await expect(page).toHaveURL('/');
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
});
```

---

## Phase 8: Quality Assurance (NEW - Priority P1)

### 11. Production Quality Gates

**Current State:** 70% Complete - Basic linting and security scanning exists
**Goal:** Enterprise-grade quality with validation, rate limiting, and versioning

#### 11.1 Environment Validation on Startup

**Required Actions:**
- [ ] Implement fail-fast environment validation in [`api/config.py`](api/config.py)
- [ ] Add required field validation
- [ ] Add credential presence checks
- [ ] Add warning system for optional services
- [ ] Create startup health report

**Implementation:**
```python
# api/config.py - Add to Settings class
def validate_critical_config(self) -> List[str]:
    warnings = []
    
    # Check required credentials
    if self.ENV == "production":
        if not self.GOOGLE_CLIENT_ID:
            warnings.append("GOOGLE_CLIENT_ID required for YouTube OAuth")
        if not self.TIKTOK_CLIENT_KEY:
            warnings.append("TIKTOK_CLIENT_KEY required for TikTok OAuth")
        if not self.GROQ_API_KEY:
            warnings.append("GROQ_API_KEY required for AI processing")
        
        # Check production settings
        if "localhost" in self.PRODUCTION_DOMAIN:
            warnings.append("PRODUCTION_DOMAIN cannot be localhost in production")
    
    return warnings
```

#### 11.2 Consistent Error Handling

**Required Actions:**
- [ ] Create centralized error response schemas
- [ ] Replace dict errors with HTTPException
- [ ] Add error logging middleware
- [ ] Implement error code system
- [ ] Add error response validation

**Error Schema:**
```python
# api/schemas/error.py
from pydantic import BaseModel
from typing import Optional, List

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime
    
class ValidationErrorResponse(ErrorResponse):
    field_errors: List[dict]
```

#### 11.3 Rate Limiting Middleware

**Required Actions:**
- [ ] Install slowapi: `pip install slowapi`
- [ ] Implement rate limiter for API routes
- [ ] Configure rate limits by tier:
  - Free: 100 req/hour
  - Creator: 1000 req/hour
  - Empire: unlimited
- [ ] Add rate limit headers
- [ ] Create rate limit exceeded responses

**Implementation:**
```python
# api/utils/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to routes
@router.post("/video/process")
@limiter.limit("100/hour")
async def process_video(request: Request):
    ...
```

#### 11.4 API Versioning

**Required Actions:**
- [ ] Implement URL-based versioning (/v1/, /v2/)
- [ ] Create version deprecation policy
- [ ] Add version headers to responses
- [ ] Create migration guide documentation
- [ ] Implement backwards compatibility layer

**Version Strategy:**
```
/api/v1/auth/login      → Original
/api/v2/auth/login      → Enhanced with OAuth
/api/v1/video/process   → Original
/api/v2/video/process   → Faster processing
```

---

## Implementation Priority (Updated)

| Priority | Task | Phase | Effort | Impact |
|----------|------|-------|--------|--------|
| **P0** | OAuth Credentials Configuration | 4 | 1 day | Blocking |
| **P0** | Production Domain Setup | 4 | 1 day | Blocking |
| **P0** | Shopify Commerce Setup | 5 | 2 days | Monetization |
| **P0** | AWS S3 Cloud Storage | 6 | 1 day | Storage/Revenue |
| **P0** | E2E Test Framework | 7 | 5 days | Quality |
| **P0** | API Route Integration Tests | 7 | 3 days | Quality |
| **P0** | OAuth Flow E2E Tests | 7 | 2 days | Quality |
| P1 | Stripe Integration | 2 | 2 days | Revenue |
| P1 | GPU Node Setup | 1 | 3 days | Core Feature |
| P1 | ElevenLabs/Pexels Integration | 6 | 2 days | Quality |
| P1 | Rate Limiting Middleware | 8 | 2 days | Security |
| P1 | Environment Validation | 8 | 1 day | DX |
| P1 | Video Pipeline Tests | 7 | 3 days | Quality |
| P2 | Load Testing | 3 | 2 days | Reliability |
| P2 | API Versioning | 8 | 3 days | Extensibility |
| P2 | Error Handling Standardization | 8 | 2 days | DX |

---

## Next Steps (Updated Roadmap)

### Week 1-2: Critical Infrastructure
1. Configure OAuth credentials and production domain
2. Implement Shopify commerce integration
3. Set up AWS S3 cloud storage

### Week 3-4: Testing Foundation
1. Build E2E testing framework (Playwright)
2. Create API integration tests
3. Implement OAuth flow E2E tests

### Week 5-6: Quality Gates
1. Add environment validation on startup
2. Implement rate limiting
3. Standardize error handling

### Week 7-8: Advanced Features
1. Implement API versioning
2. Complete video pipeline tests
3. Run load tests and optimize

---

## Transformation Pipeline Reference

### Transformation Filters (VideoProcessor)

| Filter | Effect |
|--------|--------|
| Originality | Mirror, zoom (1.02x-1.08x), color shift |
| Speed Ramping | Variable speed (0.95x-1.05x) |
| Dynamic Jitter | Frame-level scale jitter |
| Cinematic Overlays | Letterbox, vignette |
| Film Grain | Retro film texture |
| Grayscale | Black & white |
| Glitch Effect | Digital distortion |
| B-Roll Injection | Pexels stock footage |

### Generative Synthesis Engines

| Engine | Use Case |
|--------|----------|
| Veo 3 | High-quality Google AI generation |
| Wan2.2 | Open-source via SiliconFlow |
| LTX-2 | Local GPU rendering |
| Cinematic Motion | Static image → video |

### Output Formats

| Aspect Ratio | Platform |
|--------------|----------|
| 9:16 | TikTok, Reels, Shorts |
| 16:9 | YouTube, Twitter |
| 1:1 | Instagram Feed |
