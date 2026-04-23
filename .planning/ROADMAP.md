# Roadmap

## Phases

- [x] **Phase 1: User Authentication and Settings** - Secure account access and configuration
- [x] **Phase 2: Content Discovery** - Access to trending content across platforms
- [x] **Phase 3: Basic Video Generation** - AI-powered video creation and transformation
- [x] **Phase 4: Advanced Video Generation** - Multi-scene storytelling video creation
- [x] **Phase 5: Multi-Platform Publishing** - Social media content distribution
- [ ] **Phase 6: Automated Scheduling Publishing** - Campaign automation for publishing
- [x] **Phase 7: Monetization** - Revenue generation and credit management
- [x] **Phase 8: Analytics** - Performance metrics and insights
- [ ] **Phase 9: Enterprise Hardening** - Strategic scaling and technical resilience

## Phase Details

### Phase 1: User Authentication and Settings
**Goal**: Users can securely access their accounts and manage personal settings
**Depends on**: Nothing
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, SETTINGS-01
**Success Criteria** (what must be TRUE):
  1. User can create an account with email and password
  2. User can log in with email/password or Google OAuth and remain logged in across sessions
  3. User can log out from any page
  4. User can configure Telegram and WhatsApp notifications via bots
  5. User can manage system settings and API integrations
**Plans**: 6 plans
- [x] 01-01-PLAN.md — Implement core user authentication system
- [x] 01-02-PLAN.md — Implement user settings and notifications
- [x] 01-03-PLAN.md — Fix authentication gaps (logout and OAuth)
- [x] 01-04-PLAN.md — Implement bot integration for notifications
- [x] 01-05-PLAN.md — Unify UserDB model definitions
- [ ] 01-06-PLAN.md — Fix UserDB unification and database schema

### Phase 2: Content Discovery
**Goal**: Users can discover and analyze trending content
**Depends on**: Phase 1
**Requirements**: DISC-01, DISC-02, DISC-03
**Success Criteria** (what must be TRUE):
  1. User can view trending content from YouTube, TikTok, and other platforms via automated scanners
  2. User can search for content with filters and sort by viral score
  3. User can analyze content for viral patterns and insights
**Plans**: 3 plans
- [x] 02-01-PLAN.md — Implement automated trending content collection from YouTube
- [x] 02-02-PLAN.md — Implement content search API with filters and viral score sorting
- [x] 02-03-PLAN.md — Implement AI-powered content analysis for viral patterns and insights

### Phase 3: Basic Video Generation
**Goal**: Users can generate and enhance videos using AI
**Depends on**: Phase 2
**Requirements**: VIDEO-01, VIDEO-02, VIDEO-04
**Success Criteria** (what must be TRUE):
  1. User can transform existing videos with AI enhancements like sound design and quality tiers
  2. User can generate new videos from scratch using multiple AI engines (Veo3, LTX-Video, etc.)
  3. User can preview generated videos and retry failed jobs
**Plans**: 5 plans
- [x] 03-01-PLAN.md — Install and verify video processing dependencies
- [x] 03-02-PLAN.md — Test video generation with multiple engines
- [x] 03-03-PLAN.md — Add error handling and retry logic
- [x] 03-04-PLAN.md — Optimize Docker builds for video processing
- [x] 03-05-PLAN.md — Implement video preview and storage upload

### Phase 4: Advanced Video Generation
**Goal**: Users can create complex storytelling videos
**Depends on**: Phase 3
**Requirements**: VIDEO-03
**Success Criteria** (what must be TRUE):
  1. User can generate videos with multi-scene narratives
**Plans**: TBD

### Phase 5: Multi-Platform Publishing
**Goal**: Users can publish content to social media platforms
**Depends on**: Phase 4
**Requirements**: PUBLISH-01
**Success Criteria** (what must be TRUE):
  1. User can publish videos to YouTube, TikTok, Facebook, and Instagram
**Plans**: 1 plans
- [x] 05-01-PLAN.md — Implement multi-platform publishing drivers

### Phase 6: Automated Scheduling Publishing
**Goal**: Users can automate publishing campaigns
**Depends on**: Phase 5
**Requirements**: PUBLISH-02
**Success Criteria** (what must be TRUE):
  1. User can schedule automated content publishing campaigns
**Plans**: 3 plans
- [x] 06-01-PLAN.md — Extend SmartScheduler and ScheduledPostDB for multi-window scheduling
- [x] 06-02-PLAN.md — Implement and verify scheduled posting routes
- [x] 06-03-PLAN.md — Verify end-to-end autonomous scheduling flow

### Phase 7: Monetization
**Goal**: Users can monetize content and manage credits
**Depends on**: Phase 6
**Requirements**: MONET-01, MONET-02, MONET-03
**Success Criteria** (what must be TRUE):
  1. User can automatically insert affiliate links into video content
  2. User can track affiliate revenue and manage referral programs
  3. User can purchase and consume credits for AI services and features
**Plans**: 1 plans
- [x] 07-01-PLAN.md — Implement affiliate links and revenue tracking

### Phase 8: Analytics
**Goal**: Users can view content performance metrics
**Depends on**: Phase 7
**Requirements**: ANALYTICS-01
**Success Criteria** (what must be TRUE):
  1. User can view performance analytics and content metrics
**Plans**: 1 plans
- [x] 08-01-PLAN.md — Implement performance analytics and content metrics

### Phase 9: Enterprise Hardening
**Goal**: Transition to an enterprise-grade, high-availability platform
**Depends on**: All previous phases
**Requirements**: Various (See HARDENING_ROADMAP.md)
**Success Criteria** (what must be TRUE):
  1. Decoupled Architecture (Go/Python DB separation)
  2. Zero-Crash technical stability (Remediation of nil-pointers/recursion)
  3. Unified Observability (Traces/Structured Logs)
  4. Unified LLM Proxy with Cost-Aware Routing
  5. EU AI Act compliant automated governance
**Plans**: See HARDENING_ROADMAP.md

**UI hint**: yes

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. User Authentication and Settings | 6/6 | Complete    | 2026-04-17 |
| 2. Content Discovery | 3/3 | Complete    | 2026-04-17 |
| 3. Basic Video Generation | 5/5 | Completed | 2026-04-15 |
| 4. Advanced Video Generation | 1/1 | Completed | 2026-04-17 |
| 5. Multi-Platform Publishing | 1/1 | Completed | 2026-04-17 |
| 6. Automated Scheduling Publishing | 3/3 | Completed | - |
| 7. Monetization | 1/1 | Completed | 2026-04-17 |
| 8. Analytics | 1/1 | Completed | 2026-04-17 |
| 9. Enterprise Hardening | 0/1 | In Progress | - |

---
*Roadmap created: 2026-04-08*