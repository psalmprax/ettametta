# ettametta

## What This Is

ettametta is an autonomous multi-platform viral content discovery, transformation, optimization, and publishing engine — powered by AI. It provides a comprehensive platform for content creators to discover trending content across platforms, transform it using AI video generation, optimize for virality, and publish to multiple social media platforms.

## Core Value

**Empower content creators** with AI-driven automation to discover, create, and monetize viral content efficiently, removing the manual work of trend research and content optimization.

## Requirements

### Validated

- ✓ **DISC-01**: User can discover trending content across platforms (YouTube, TikTok, etc.) via automated scanners
- ✓ **VIDEO-01**: User can transform existing videos using AI enhancement (sound design, motion graphics, quality tiers)
- ✓ **VIDEO-02**: User can generate new videos from scratch using multiple AI engines (Veo3, LTX-Video, Hunyuan, etc.)
- ✓ **VIDEO-03**: User can create storytelling narratives with multi-scene AI video generation
- ✓ **PUBLISH-01**: User can publish content to YouTube, TikTok, Facebook, Instagram, and other platforms
- ✓ **AUTH-01**: User can register, login, and manage accounts with JWT authentication
- ✓ **AUTH-02**: User can integrate Google OAuth for seamless login
- ✓ **AUTH-03**: User can configure Telegram and WhatsApp notifications via OpenClaw bot
- ✓ **MONET-01**: User can insert affiliate links into video content automatically
- ✓ **MONET-02**: User can track affiliate revenue and manage referral programs
- ✓ **CREDITS-01**: User can purchase and consume credits for AI services and premium features
- ✓ **ANALYTICS-01**: User can view performance analytics and content metrics
- ✓ **SETTINGS-01**: User can configure system settings and manage API integrations

### Active

- [ ] **AB-TESTING-01**: User can run A/B tests on content variants to optimize engagement
- [ ] **SCHEDULING-01**: User can schedule automated content publishing campaigns
- [ ] **EMPIRE-01**: User can clone successful strategies and automate empire building
- [ ] **WEBHOOKS-01**: User can integrate with affiliate network webhooks for revenue tracking

### Out of Scope

- Real-time video streaming — Focus is on content creation and publishing, not live streaming
- Advanced video editing tools — Basic transformations only, not full video editor
- Multi-user collaboration — Single-user platform design
- White-label solutions — B2C focus, not B2B customization

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AI-First Architecture | Leverage AI for content discovery, generation, and optimization | Core competitive advantage |
| Multi-Platform Publishing | Support major social platforms for maximum reach | Broad distribution capability |
| Credit-Based Monetization | Freemium model with paid AI features | Sustainable revenue model |
| OpenClaw Integration | AI agent for notifications and user interaction | Enhanced user experience |
| FastAPI + Next.js Stack | Modern, scalable full-stack architecture | Development velocity and performance |

## Context

**Market**: Content creation tools market, specifically viral content optimization and AI video generation.

**Competition**: Manual content research tools, basic video editors, single-platform publishers.

**Differentiation**: End-to-end AI automation from discovery to publishing with monetization features.

**Timeline**: Ongoing development with regular feature releases and platform integrations.

**Constraints**: API rate limits, AI model costs, platform publishing restrictions.

**Success Metrics**:
- User engagement with automated discovery features
- Video generation quality and viral performance
- Platform publishing success rates
- Revenue from credit purchases and affiliate commissions

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Out of Scope audit — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-08 after project review*</content>
<parameter name="filePath">.planning/PROJECT.md