# ettametta: Expansion Blueprint

> **Last Updated**: 2026-02-22  
> **Version**: 1.0 - Production Expansion Roadmap

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
│      Render Node (GPU Server)            │
│  - FastAPI + Diffusers                  │
│  - Veo 3 / Wan2.2 / LTX-2              │
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

## Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| P0 | Stripe Integration | 2 days | Revenue |
| P0 | GPU Node Setup | 3 days | Core Feature |
| P1 | API Key Documentation | 1 day | DX |
| P2 | Load Testing | 2 days | Reliability |

---

## Next Steps

1. **Week 1:** Implement Stripe billing endpoints
2. **Week 2:** Set up GPU render node
3. **Week 3:** Document API key configuration
4. **Week 4:** Run load tests and optimize

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
