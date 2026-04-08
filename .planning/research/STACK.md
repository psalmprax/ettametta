# Technology Stack

**Project:** ettametta
**Researched:** 2026-04-08
**Confidence:** HIGH

## Recommended Stack

### Core Framework
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Next.js | 15.x | Frontend framework for content management UI and publishing interfaces | Industry standard for modern web apps with SSR/SSG, enabling fast content previews and real-time publishing controls; dominant in 2026 content platforms per multiple sources |
| FastAPI | 0.115.x | Backend API for AI processing, content discovery, and multi-platform publishing | Async Python framework optimized for AI workloads with automatic OpenAPI docs; proven in high-throughput content platforms with built-in rate limiting for API costs |

### Database
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PostgreSQL | 16.x | Primary data store for user accounts, content metadata, analytics, and credit tracking | ACID-compliant with JSON support for flexible content schemas; industry leader for transactional data in 2026 AI platforms |
| pgvector | 0.7.x | Vector extension for content similarity search and AI embeddings | Native PostgreSQL integration avoids data duplication; recommended for cost-effective RAG in content discovery features |

### Infrastructure
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Vercel | Latest | Frontend hosting with edge functions for global content delivery | Optimized for Next.js with automatic scaling; standard for viral content platforms needing instant global reach |
| Railway | Latest | Backend hosting with managed PostgreSQL and Redis | Developer-friendly PaaS reducing DevOps overhead; popular in 2026 for AI startups needing rapid scaling without cloud complexity |

### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai | 1.50.x | Text generation and content optimization | For AI-powered storytelling and viral copy enhancement |
| replicate | 0.32.x | Runway Gen-4.5 and other AI video models | When generating high-quality videos from text prompts or existing content |
| lumalabs | Latest | Luma AI video generation API | For cinematic video creation with motion control |
| xai | Latest | xAI video generation | Cost-effective alternative for multi-scene narratives |
| google-api-python-client | 2.140.x | YouTube and Google OAuth integration | For content discovery and publishing to YouTube |
| TikTokApi | 6.3.x | TikTok content scraping and publishing | For trend discovery and automated uploads |
| facebook-sdk | 4.0.x | Facebook/Instagram Graph API | Multi-platform publishing with analytics |
| redis | 5.0.x | Caching for API responses and session management | High-throughput content processing and user sessions |
| stripe | 10.x | Payment processing for credits and monetization | Secure handling of affiliate revenue and subscriptions |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Frontend | Next.js | React + Vite | Next.js provides better SEO and performance for content-heavy apps |
| Backend | FastAPI | Express.js | Python ecosystem stronger for AI integrations in 2026 |
| Database | PostgreSQL + pgvector | Pinecone standalone | pgvector reduces complexity and costs for moderate-scale content platforms |
| Hosting | Vercel + Railway | AWS full stack | Managed services accelerate development for viral content features |

## Installation

```bash
# Frontend (Next.js)
npm install next@15 react@18 react-dom@18

# Backend (FastAPI)
pip install fastapi==0.115 uvicorn[standard] sqlalchemy psycopg2-binary pgvector redis openai replicate lumalabs xai google-api-python-client TikTokApi facebook-sdk stripe

# Dev dependencies
npm install -D typescript @types/react @types/node eslint prettier
```

## Sources

- Medium article "The 2026 Marketing Stack" — Comprehensive tool recommendations for AI marketing platforms
- Pragmatic Digital "2026 AI Marketing Tech Stack" — Verified stack patterns for revenue operations
- Zapier "Best AI Video Generators 2026" — Current leading video APIs and models
- PingCap "Best Database for AI Agents 2026" — Vector database recommendations for content similarity
- Marketing Agent Blog "AI Content Creation Tools 2026" — Practitioner guide to AI stack components
</content>
<parameter name="filePath">.planning/research/STACK.md