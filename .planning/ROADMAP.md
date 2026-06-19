# Roadmap

## Phases

- [x] **Phase 1: User Authentication and Settings** - Secure account access and configuration
- [x] **Phase 2: Content Discovery** - Access to trending content across platforms
- [x] **Phase 3: Basic Video Generation** - AI-powered video creation and transformation
- [x] **Phase 4: Advanced Video Generation** - Multi-scene storytelling video creation
- [x] **Phase 5: Multi-Platform Publishing** - Social media content distribution
- [x] **Phase 6: Automated Scheduling Publishing** - Campaign automation for publishing
- [x] **Phase 7: Monetization** - Revenue generation and credit management
- [x] **Phase 8: Analytics** - Performance metrics and insights
- [ ] **Phase 9: Enterprise Hardening** - Strategic scaling and technical resilience
    - [x] 09-01-PLAN.md — Unified Observability and Request Tracing
- [ ] **Phase 10: Discovery → Analysis → Video Pipeline Fix** - Repair the broken core user journey end-to-end
    - Promoted from `.planning/BACKLOG.md` item 999.1 (P0)
    - [x] 10-01-PLAN.md — Foundation: DB schema + AnalysisReport contract
- [ ] **Phase 11: Remove Veo3 Stub (Credit-Scam Fix)** - Stop the fake-Veo3 from charging 25 credits for a Pollinations.ai image
    - Promoted from `.planning/BACKLOG.md` item 999.2 (P0)
    - [x] 11-01-PLAN.md — Engine removal + route signature defaults + test fixture updates
- [ ] **Phase 12: Wire Up Runway + Pika API Keys** - Activate the dormant Runway/Pika API integration by reading keys from settings and exposing /engines/availability
    - Promoted from `.planning/BACKLOG.md` item 999.3 (P0)
    - [ ] 12-01-PLAN.md — Settings-based key resolution + /engines/availability endpoint + tests
- [ ] **Phase 13: Rewrite Luma API to Luma Ray** - Replace the deprecated `dream-machine` endpoint with the current Luma Ray API (`https://api.lumalabs.ai/v1/generations`) and add `LUMA_API_KEY` to settings
    - Promoted from `.planning/BACKLOG.md` item 999.4 (P0)
    - [ ] 13-01-PLAN.md — Luma Ray endpoint + payload + poll + settings key + tests

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
**Plans**: 1 plans
- [ ] 04-01-PLAN.md — Verify multi-scene storytelling video generation

### Phase 5: Multi-Platform Publishing
**Goal**: Users can publish content to social media platforms
**Depends on**: Phase 4
**Requirements**: PUBLISH-01
**Success Criteria** (what must be TRUE):
  1. User can publish videos to YouTube, TikTok, Facebook, and Instagram
**Plans**: 2 plans
- [x] 05-01-PLAN.md — Implement multi-platform publishing drivers
- [ ] 05-02-PLAN.md — Verify multi-platform publishing capabilities

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
**Plans**: 2 plans
- [x] 07-01-PLAN.md — Implement affiliate links and revenue tracking
- [ ] 07-02-PLAN.md — Verify monetization and credit system

### Phase 8: Analytics
**Goal**: Users can view content performance metrics
**Depends on**: Phase 7
**Requirements**: ANALYTICS-01
**Success Criteria** (what must be TRUE):
  1. User can view performance analytics and content metrics
**Plans**: 2 plans
- [x] 08-01-PLAN.md — Implement performance analytics and content metrics
- [ ] 08-02-PLAN.md — Verify analytics and reporting capabilities

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
**Plans**: 2 plans
- [x] 09-01-PLAN.md — Unified Observability and Request Tracing
- [ ] 09-02-PLAN.md — Verify enterprise infrastructure capabilities

### Phase 10: Discovery → Analysis → Video Pipeline Fix
**Goal**: Repair the broken core user journey end-to-end (Discovery → Analysis → Video)
**Depends on**: Phase 2 (Content Discovery), Phase 3 (Basic Video Generation)
**Requirements**: DISC-03, VIDEO-01
**Success Criteria** (what must be TRUE):
  1. User can click "Analyze" on a real candidate and receive a structured, persisted report
  2. Analysis survives a page refresh and can be looked up by `content_id` directly from the DB
  3. "Create Video" button uses the analysis insights (hook, pacing, structure, style) to inform the video job
  4. The video job record carries a snapshot of the originating analysis in `job_metadata.analysis_snapshot`
  5. Old behavior (in-memory Celery results) still works behind a feature flag (`ENABLE_PERSISTED_ANALYSIS`)
**Plans**: 1 plans (this phase ships in a single plan; sub-plans split if scope grows)
- [x] 10-01-PLAN.md — Foundation: DB schema + AnalysisReport contract

### Phase 12: Wire Up Runway + Pika API Keys
**Goal**: Activate the dormant Runway/Pika API integration by reading keys from `settings` (not `os.getenv`) and expose a `/engines/availability` endpoint so the UI can hide non-working engines
**Depends on**: Phase 3 (Basic Video Generation)
**Requirements**: VIDEO-01
**Success Criteria** (what must be TRUE):
  1. `AIVideoGeneratorService._get_api_key()` reads from `settings.RUNWAY_API_KEY` and `settings.PIKA_API_KEY` (not `os.getenv`)
  2. With `AI_VIDEO_PROVIDER=runway` + `RUNWAY_API_KEY` set in env, the service is `enabled=True` and `_get_api_key()` returns a non-empty string
  3. `GET /engines/availability` returns per-engine status: `key_set`, `circuit_closed`, `enabled`, `provider` (for Runway, Pika, and the existing engines)
  4. `RUNWAY_API_KEY` and `PIKA_API_KEY` are documented in `.env.example`
  5. Unit tests verify settings-based key resolution and the availability endpoint
**Plans**: 1 plans (single commit)
- [ ] 12-01-PLAN.md — Settings-based key resolution + /engines/availability endpoint + tests

### Phase 13: Rewrite Luma API to Luma Ray
**Goal**: Replace the deprecated Luma Dream Machine endpoint with the current Luma Ray API so the Luma engine actually works end-to-end (no more silent 404 → Playwright fallback)
**Depends on**: Phase 3 (Basic Video Generation)
**Requirements**: VIDEO-01
**Success Criteria** (what must be TRUE):
  1. `PROVIDER_CONFIGS["luma"]["api_url"]` is `https://api.lumalabs.ai/v1` (Luma Ray, not the deprecated `dream-machine/v1`)
  2. `_generate_luma` posts to `/generations` with the Ray payload schema: `{"prompt": ..., "model": "ray-2", "aspect_ratio": "16:9", "loop": false, "duration": "5s"}` and an `Authorization: Bearer luma-...` header
  3. `_poll_luma_job` polls `/generations/{id}` and reads the new response shape (`state`: `queued`|`dreaming`|`completed`|`failed`; `assets.video`: URL on completion)
  4. `LUMA_API_KEY` is defined on `src.api.config.settings.Settings` AND `src.services.video_engine.settings.Settings` (so both the API service and the worker process see it)
  5. `_get_api_key("luma")` in `free_video_providers.py` returns `settings.LUMA_API_KEY` (replacing the old browser-automation-only path)
  6. `LUMA_API_KEY` is documented in `.env.example`
  7. Unit tests cover: key-missing skip, Ray-format POST payload, immediate `video` field, async poll loop, failed-state handling
**Plans**: 1 plans (single commit)
- [ ] 13-01-PLAN.md — Luma Ray endpoint + payload + poll + settings key + tests

### Phase 11: Remove Veo3 Stub (Credit-Scam Fix)
**Goal**: Stop users from being charged 25 credits for a fake Veo3 (the synthesis path silently falls through to a Pollinations.ai image+parallax)
**Depends on**: Phase 3 (Basic Video Generation)
**Requirements**: VIDEO-01
**Success Criteria** (what must be TRUE):
  1. `grep -ri "veo3" src/ apps/ scripts/` returns no engine references
  2. Engine selector in `apps/dashboard/src/app/creation/page.tsx` no longer shows "Veo3"
  3. `ENGINE_ACTION_MAP` and `PREMIUM_ENGINES` in `engine_config.py` no longer mention `veo3`
  4. Default `engine` field in Pydantic schemas and route signatures is `"ltx-video"` (not `"veo3"`)
  5. User cannot trigger a video job with `engine="veo3"` (endpoint returns 400)
  6. No documentation still claims Veo3 is supported
**Plans**: 1 plans (single-commit removal)
- [x] 11-01-PLAN.md — Engine removal + route signature defaults + test fixture updates

**Recent Hardening Work (2026-04-17 to 2026-05-29):**
- 14+ operational/debugging skills created (ai-provider-debug, celery-monitor, cloakbrowser, content-discovery, db-performance, dep-audit, docker-compose, fastapi-debug, nexus-engine, redis-debug, remotion-debug, security-sentinel, social-api, storage-lifecycle, video-pipeline, voiceover-tts)
- OpenClaw hardened: asyncio offload, PEP 8 compliance, type safety, GC management
- AI Gateway: cognitive complexity reduced, temp file hardening
- CloakBrowser: multi-platform stealth scraping (Instagram, Facebook, X, LinkedIn)
- Semantic hardening: global type normalization, placeholder code elimination
- System-wide skill audit completed

**UI hint**: yes

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. User Authentication and Settings | 5/6 | In Progress | - |
| 2. Content Discovery | 3/3 | Complete    | 2026-04-17 |
| 3. Basic Video Generation | 5/5 | Complete | 2026-04-15 |
| 4. Advanced Video Generation | 0/1 | In Progress | - |
| 5. Multi-Platform Publishing | 1/2 | In Progress | - |
| 6. Automated Scheduling Publishing | 3/3 | Complete | 2026-04-17 |
| 7. Monetization | 1/2 | In Progress | - |
| 8. Analytics | 1/2 | In Progress | - |
| 9. Enterprise Hardening | 1/2 | In Progress | 2026-05-29 (skills + hardening) |
| 10. Discovery → Analysis → Video Pipeline Fix | 1/1 | In Progress | 2026-05-29 (10-01 Foundation complete) |
| 11. Remove Veo3 Stub | 1/1 | Complete | 2026-05-29 (6a790f10) |
| 12. Wire Up Runway + Pika | 0/1 | Not Started | - |
| 13. Rewrite Luma API to Luma Ray | 0/1 | Not Started | - |

---
## Related Documents

| Document | Purpose | When to use |
|----------|---------|-------------|
| [`.planning/ROADMAP.md`](./ROADMAP.md) | Active phase tracker with plan pointers (this file) | "What's being worked on right now?" |
| [`.planning/BACKLOG.md`](./BACKLOG.md) | Prioritized missing-feature list (37 items, `999.x` numbering) | "What's still TODO and unprioritized?" — check here BEFORE planning a new phase |
| [`.planning/STATE.md`](./STATE.md) | Current position, progress %, pending todos | "Where are we, what was I doing?" |
| [`.planning/PROJECT.md`](./PROJECT.md) | Validated + active requirements, key decisions | "What does this project do and why?" |
| [`.planning/REQUIREMENTS.md`](./REQUIREMENTS.md) | Requirement-level tracking | "Has requirement X been validated?" |
| [`.planning/HARDENING_ROADMAP.md`](./HARDENING_ROADMAP.md) | Phase 9 enterprise-hardening work | "What hardening is done / pending?" |
| `.planning/phases/<NN>-*/<NN>-*-PLAN.md` | Per-plan execution contract (YAML frontmatter + tasks) | "How do I execute plan X?" |
| `.planning/phases/<NN>-*/<NN>-*-SUMMARY.md` | Per-plan completion record | "What shipped in plan X?" |

### Planning-cycle workflow

1. **Before** drafting a new phase plan, skim `.planning/BACKLOG.md` for any
   `999.x` item that already covers the work — promote it (don't duplicate).
2. After a phase ships, add any newly-discovered work to `.planning/BACKLOG.md`
   under the appropriate priority tier (P0–P3) and assign the next free
   `999.x` number.
3. Use `/gsd-add-phase` to promote a `999.x` item into a real numbered phase
   here, or `/gsd-insert-phase` to slip urgent work between existing phases.

---

*Roadmap created: 2026-04-08 — Last updated: 2026-05-29 (Phase 10/11/12/13 promoted from BACKLOG.md 999.1/999.2/999.3/999.4; Related Documents section added)*
