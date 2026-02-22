# API Keys Configuration Guide

This document lists all required API keys and credentials to run the Viral Forge platform.

## Environment Variables Table

| Variable | Required | Where to Get | Purpose |
|----------|----------|--------------|---------|
| **App Core** ||||
| `SECRET_KEY` | ✅ Yes | Generate: `openssl rand -hex 32` | JWT signing |
| `PRODUCTION_DOMAIN` | ✅ Yes | Your domain or IP | URL generation |
| `ENV` | ✅ Yes | `production` | Environment mode |
| **Database** ||||
| `DATABASE_URL` | ✅ Yes | PostgreSQL connection string | Primary database |
| `REDIS_URL` | ✅ Yes | Redis connection string | Cache & message queue |
| **AI Intelligence** ||||
| `GROQ_API_KEY` | ✅ Yes | [groq.com](https://groq.com) | Fast LLM inference |
| `OPENAI_API_KEY` | Optional | [openai.com](https://openai.com) | GPT models backup |
| **Voice & Media** ||||
| `ELEVENLABS_API_KEY` | Optional | [elevenlabs.io](https://elevenlabs.io) | Voice cloning |
| `PEXELS_API_KEY` | Optional | [pexels.com/api](https://www.pexels.com/api/) | Stock footage |
| `PIXABAY_API_KEY` | Optional | [pixabay.com/api](https://pixabay.com/api/) | Stock media backup |
| **Social OAuth** ||||
| `GOOGLE_CLIENT_ID` | Optional | [console.cloud.google.com](https://console.cloud.google.com) | YouTube OAuth |
| `GOOGLE_CLIENT_SECRET` | Optional | Same as above | YouTube OAuth |
| `YOUTUBE_API_KEY` | ✅ Yes | [console.cloud.google.com](https://console.cloud.google.com) | Video discovery |
| `TIKTOK_CLIENT_KEY` | Optional | [developers.tiktok.com](https://developers.tiktok.com) | TikTok OAuth |
| `TIKTOK_CLIENT_SECRET` | Optional | Same as above | TikTok OAuth |
| `TIKTOK_API_KEY` | Optional | Same as above | TikTok data |
| **Payment** ||||
| `STRIPE_SECRET_KEY` | ✅ Yes | [dashboard.stripe.com](https://dashboard.stripe.com) | Payment processing |
| `STRIPE_WEBHOOK_SECRET` | ✅ Yes | Same as above | Webhook verification |
| **Storage (AWS S3)** ||||
| `AWS_ACCESS_KEY_ID` | Optional | [aws.amazon.com/iam](https://aws.amazon.com/iam) | S3 upload |
| `AWS_SECRET_ACCESS_KEY` | Optional | Same as above | S3 upload |
| `AWS_REGION` | Optional | AWS region | S3 region |
| `AWS_STORAGE_BUCKET_NAME` | Optional | [s3.console.aws.amazon.com](https://s3.console.aws.amazon.com) | S3 bucket |
| **Commerce** ||||
| `SHOPIFY_SHOP_URL` | Optional | Your Shopify store | E-commerce |
| `SHOPIFY_ACCESS_TOKEN` | Optional | Shopify admin | Product sync |
| **Internal** ||||
| `INTERNAL_API_TOKEN` | ✅ Yes | Generate: `openssl rand -hex 24` | Service communication |
| `JWT_SECRET_KEY` | ✅ Yes | Generate: `openssl rand -hex 32` | Token signing |
| **Telegram (Notifications)** ||||
| `TELEGRAM_BOT_TOKEN` | Optional | [@BotFather](https://t.me/BotFather) | Bot notifications |
| `TELEGRAM_ADMIN_ID` | Optional | @userinfobot | Admin alerts |

## Quick Start - Free Tier

For testing with minimal cost, fill these **minimum required** keys:

```bash
# Core (generate yourself)
SECRET_KEY="generate_a_secure_random_string_here"
INTERNAL_API_TOKEN="generate_a_secure_random_token"
PRODUCTION_DOMAIN="http://your-server-ip:8000"
ENV="production"

# Database (provided by your hosting)
DATABASE_URL="postgresql://user:password@host:5432/dbname"
REDIS_URL="redis://:password@host:6379/0"

# AI (free tier available)
GROQ_API_KEY="gsk_..."

# Video Discovery (critical for pipeline)
YOUTUBE_API_KEY="AIza..."
```

## Priority Order for Full Functionality

### Phase 1: Basic Pipeline (Start Here)
1. `GROQ_API_KEY` - AI analysis
2. `YOUTUBE_API_KEY` - Content discovery
3. `DATABASE_URL` - Data persistence
4. `REDIS_URL` - Queue processing

### Phase 2: Social Integration
5. `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - YouTube publishing
6. `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` - TikTok publishing

### Phase 3: Monetization
7. `STRIPE_SECRET_KEY` - Payments
8. `SHOPIFY_SHOP_URL` / `SHOPIFY_ACCESS_TOKEN` - Products
9. `AWS_*` - Asset storage

### Phase 4: Premium Features
10. `ELEVENLABS_API_KEY` - Voice cloning
11. `PEXELS_API_KEY` - Stock footage

## Adding to Jenkins

Add these as **Secret text** credentials with these exact IDs:

| Jenkins Credential ID | Environment Variable |
|---------------------|---------------------|
| `GROQ_API_KEY` | `GROQ_API_KEY` |
| `YOUTUBE_API_KEY` | `YOUTUBE_API_KEY` |
| `STRIPE_SECRET_KEY` | `STRIPE_SECRET_KEY` |
| `AWS_ACCESS_KEY_ID` | `AWS_ACCESS_KEY_ID` |
| `AWS_SECRET_ACCESS_KEY` | `AWS_SECRET_ACCESS_KEY` |
| `AWS_STORAGE_BUCKET_NAME` | `AWS_STORAGE_BUCKET_NAME` |
| `DATABASE_URL` | `DATABASE_URL` |
| `REDIS_URL` | `REDIS_URL` |

## Security Notes

- **Never commit actual keys** to GitHub
- Use Jenkins credentials or environment variables
- Rotate keys periodically
- Use separate keys for production vs development
- Stripe test keys start with `sk_test_`
- Stripe live keys start with `sk_live_`
