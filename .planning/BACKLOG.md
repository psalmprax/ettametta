# ettametta — Prioritized Missing-Feature Backlog

> **Status:** Active tracking
> **Last updated:** 2026-05-29
> **Numbering convention:** `999.x` per GSD backlog standard
> **Priorities:** P0 = blocks production, P1 = high value, P2 = nice to have, P3 = future

This backlog consolidates every known gap from:
- `.planning/PROJECT.md` (active requirements not yet validated)
- `.planning/ROADMAP.md` (in-progress phases)
- `docs/comprehensive_gap_analysis.md`
- `docs/gap_analysis_april_2026.md`
- `docs/gap_analysis_viral_forge_comprehensive.md`
- `docs/expansion_blueprint.md`
- Direct code investigation (Discovery pipeline + AI video engines)

Promote an item from this list into a new numbered phase in `ROADMAP.md` when it is ready for planning. Use `/gsd-add-phase` or `/gsd-insert-phase` to convert.

---

## P0 — Critical (Blocks Production / User-Visible Broken)

### ~~999.1 — Fix Discovery → Analysis → Video Pipeline~~ ⮕ **PROMOTED → Phase 10 (2026-05-29)**
**Source:** `docs/comprehensive_gap_analysis.md` §1.1, code investigation
**Impact:** Core user journey is broken end-to-end
**Root cause:** Frontend sends fake URL `https://ettametta.ai/discovery/${id}` to `/analyze`; analysis result lives only in Celery in-memory backend; "Create Video" never passes analysis insights (hooks/pacing) into the transform job
**Files:**
- `apps/dashboard/src/app/discovery/page.tsx` (handleAnalyze, handleCreateFromAnalysis)
- `src/services/discovery/tasks.py` (analyze_viral_pattern_task)
- `src/services/discovery/analysis_service.py` (extract_content_patterns)
- `src/services/discovery/video_content_pipeline.py`
- `src/api/routes/discovery.py` (get_analysis_status, create_video_from_analysis)
- `src/api/utils/models.py` (ContentCandidateDB)
- `src/api/routes/video_jobs.py` (download_and_process_task signature)

**Tasks:**
- [ ] Add `analysis_task_id`, `analysis_status`, `analysis_payload` (JSONB), `analysis_persisted_at`, `recommended_style`, `viral_score_velocity` to `ContentCandidateDB` (Alembic migration)
- [ ] Define stable `AnalysisReport` Pydantic contract in `src/services/discovery/schemas.py`
- [ ] Refactor `analyze_viral_pattern_task` to persist payload to DB and return normalized shape
- [ ] Make `extract_content_patterns` defer to persisted analysis when present (unify the two parallel systems)
- [ ] Rewrite `get_analysis_status` to read from DB first, Celery fallback
- [ ] Add `GET /discovery/analysis/{content_id}` for direct lookup
- [ ] Extend `download_and_process_task` with `analysis_id`, `analysis_hook`, `analysis_pacing`, `analysis_structure`, `analysis_recommended_style` kwargs
- [ ] Rewrite `create_video_from_analysis` to thread insights into the dispatched video job and snapshot report into `job_metadata.analysis_snapshot`
- [ ] Frontend: stop sending fake URL, send real `source_uri` + full `candidate`
- [ ] Frontend: persist `analysisTasks` state to `sessionStorage`; render `AnalysisReport` in new `AnalysisResultsCard.tsx`
- [ ] Frontend: replace 3s polling with WebSocket push (`analysis_complete` event); add "My Analyses" page
- [ ] Backend: add `notify_analysis_update_sync` helper, fire from Celery task
- [ ] Add `ENABLE_PERSISTED_ANALYSIS` feature flag for safe rollout
- [ ] Add `tests/discovery/test_analysis_persistence.py` (unit + integration) and `apps/dashboard/src/__tests__/discovery/` (component + E2E)
- [ ] Write `scripts/e2e/discovery_to_video.py` smoke test

**Acceptance:** Scan → Analyze → click "Create Video" → real video render, with no page refresh; analysis survives reload; `VideoJobDB.job_metadata.analysis_snapshot.hook` equals `AnalysisReport.hook`.
**Status:** Promoted to Phase 10 in ROADMAP.md. Execution plan: `.planning/phases/10-pipeline-fixes/10-01-PLAN.md`.

---

### 999.2 — Remove Veo3 Stub (Credit-Scam)
**Source:** Code investigation, `docs/gap_analysis_april_2026.md` (claims "fixed" but isn't)
**Impact:** Users pay 25 credits for a fake Veo3 — they actually get a Pollinations.ai image with parallax
**Root cause:** `_synthesize_veo3` in `src/services/video_engine/synthesis_service.py:880` calls `gemini-1.5-pro` with `generate_content` (returns text, not video), logs it, and falls through to Lite4K
**Files:**
- `src/services/video_engine/synthesis_service.py:880-940` (delete `_synthesize_veo3`)
- `src/services/video_engine/engine_config.py:12` (remove `"veo3": "video_generation_veo3"`)
- `src/api/routes/content_editor.py:119` (remove from engine list endpoint)
- `apps/dashboard/src/app/creation/page.tsx:290` (remove from engine selector)
- `src/api/utils/subscription.py:118,228` (remove tier mapping + engine metadata)
- `src/services/payment/credit_service.py:34` (remove `video_generation_veo3` cost entry)
- `src/services/payment/stripe_service.py:48` (update STUDIO tier features list)
- `src/api/routes/video_jobs.py:140` (remove from engine cost map)
- `src/api/tests/test_routes/test_video.py:136` (remove or update `test_generate_veo3`)
- `src/api/tests/test_api_comprehensive.py:38,115` (remove veo3 references)
- `src/tests/test_video_generation.py:26-205` (remove veo3 tests)
- `src/services/video_engine/tests/test_generative_service.py:173` (remove veo3 test)
- `src/services/openclaw/skills/content.py:19,42` (change default from "veo3")
- `src/services/video_engine/synthesis_service.py:33,43,381,394,474,504,829,1060` (change defaults from "veo3")
- `src/api/routes/video_generate.py:33,43,381,394` (change defaults from "veo3")
- `src/api/routes/video_jobs.py:235` (change default)
- `scratch/trigger_test_job.py:34,45` (remove)

**Tasks:**
- [ ] Delete `_synthesize_veo3` and all dispatch arms pointing to it
- [ ] Remove from `ENGINE_ACTION_MAP`, `PREMIUM_ENGINES`, tier gating, cost tables, settings
- [ ] Replace default-engine in all schemas/route signatures with `"ltx-video"`
- [ ] Update tests + scratch + docs to remove veo3 references
- [ ] Update `docs/comprehensive_gap_analysis.md` and `docs/100_percent_complete.md` to reflect removal

**Acceptance:** `grep -ri "veo3" src/ apps/ scripts/` returns no engine references; engine selector in UI no longer shows Veo3; user cannot pay 25 credits for a fake Veo3.

---

### ~~999.3 — Wire Up Runway + Pika API Keys~~ ⮕ **PROMOTED → Phase 12 (2026-05-29)**
**Source:** Code investigation
**Impact:** Real, production-quality API integration code exists but is dormant because env vars are never set
**Root cause:** `AIVideoGeneratorService` gates itself on `AI_VIDEO_PROVIDER` and `_get_api_key()` returns empty string by default
**Files:**
- `src/services/video_engine/ai_generator.py:22-51` (PROVIDER_CONFIGS + key resolution)
- `src/api/config/settings.py:195-198, 291-295` (RUNWAY_API_KEY, PIKA_API_KEY settings)
- `src/services/video_engine/settings.py:181-184, 269-273`
- `.env.example`, `.env.production.template`
- `src/api/routes/settings.py:130-131` (expose keys in user settings)

**Tasks:**
- [ ] Add `RUNWAY_API_KEY`, `PIKA_API_KEY` to `Settings` and `VideoSettings` (with `Optional[str] = None`)
- [ ] Update `AIVideoGeneratorService._get_api_key()` to use `settings.RUNWAY_API_KEY` and `settings.PIKA_API_KEY` instead of `os.getenv`
- [ ] Add keys to `.env.example` and `.env.production.template` with comments
- [ ] Update `src/api/routes/settings.py` GET /settings to include these (masked) so users can verify presence
- [ ] Add `/engines/availability` endpoint that reports per-engine status (key set, circuit closed, last successful call)
- [ ] Update `apps/dashboard/src/components/...` engine selector to use availability endpoint to hide non-working engines
- [ ] Add tests verifying the service correctly uses settings-based keys

**Acceptance:** With valid `RUNWAY_API_KEY` set, `POST /video/generate {engine: "runway"}` returns a real Runway video URI (not None).
**Status:** Promoted to Phase 12 in ROADMAP.md. Execution plan: `.planning/phases/12-wire-runway-pika/12-01-PLAN.md`.

---

### ~~999.4 — Rewrite Luma API to Ray (Current API is Dead)~~ ⮕ **PROMOTED → Phase 13 (2026-05-29)**
**Source:** Code investigation
**Impact:** `_generate_luma` calls `https://api.lumalabs.ai/dream-machine/v1/generations` which was deprecated in 2024; always 404s and falls back to Playwright (which needs auth)
**Files:**
- `src/services/video_engine/free_video_providers.py:695-760` (`_generate_luma`)
- `src/services/video_engine/free_video_providers.py:151-160` (PROVIDER_CONFIGS["luma"])

**Tasks:**
- [ ] Update endpoint to `https://api.lumalabs.ai/v1/generations` (Luma Ray API)
- [ ] Update payload schema per Luma Ray docs (request `model` parameter, `aspect_ratio` format)
- [ ] Update poll endpoint
- [ ] Add `LUMA_API_KEY` to settings
- [ ] Test with real key

**Acceptance:** With valid `LUMA_API_KEY`, Luma engine returns a real video URI without falling back to Playwright.
**Status:** Promoted to Phase 13 in ROADMAP.md. Execution plan: `.planning/phases/13-luma-ray-rewrite/13-01-PLAN.md`.

---

## P1 — High Value (Core User Journeys)

### ~~999.5 — Auto-Insert Affiliate Links into Videos~~ ✅ **COMPLETE — Phase 14 shipped (2026-06-13)**
**Source:** `docs/comprehensive_gap_analysis.md` §1.2, current `transformation/page.tsx` shows button but it doesn't work
**Impact:** Monetization is broken end-to-end
**Files:**
- `src/api/routes/video_transform.py` (`POST /auto-insert-links` endpoint exists)
- `src/services/monetization/service.py` (`plan_monetization_strategy`, `_plan_link_insertion`, `process_video_with_links`)
- `src/services/video_engine/ffmpeg_utils.py` (`draw_text_overlay`)
- `apps/dashboard/src/app/transformation/page.tsx` (`handleAutoLinks` wired to correct endpoint)

**Tasks:**
- [x] Implement `POST /video/auto-insert-links` that takes a `job_id` + calls `MonetizationEngine.plan_monetization_strategy()`
- [x] Use FFmpeg drawtext overlay to burn links into video (start/mid/end card overlay)
- [x] Track per-link impression count on `AffiliateLinkDB.impression_count`
- [x] Wire up `transformation/page.tsx` `handleAutoLinks` to the real endpoint
- [x] Tests for overlay positioning + persistence (14 tests)

**Acceptance:** User clicks "Auto-Inject Affiliate Nodes" in transformation page → links appear on rendered video → impression count increments per view.
**Status:** ✅ **Complete.** Implemented in `.planning/phases/14-affiliate-auto-insert/14-01-PLAN.md`. All acceptance criteria met.

---

### 999.6 — Auto-Merch (Shopify Integration)
**Source:** `docs/comprehensive_gap_analysis.md` §1.2, `docs/expansion_blueprint.md` §8
**Impact:** `commerce_service` is a placeholder, "Auto-Merch" button on Empire page does nothing real
**Files:**
- `src/services/monetization/commerce_service.py` (new or existing)
- `src/api/routes/monetization.py` (auto-merch endpoint)
- `src/services/payment/stripe_service.py:48` (lists shopify in features — verify)

**Tasks:**
- [ ] Implement real Shopify Admin API integration
- [ ] Add `SHOPIFY_SHOP_URL`, `SHOPIFY_ACCESS_TOKEN`, `SHOPIFY_ADMIN_KEY` to settings
- [ ] Product catalog sync (background task)
- [ ] Order webhook handler
- [ ] Product-to-niche matching algorithm
- [ ] Wire up "Auto-Merch" UI on Empire page

**Acceptance:** With valid Shopify creds, "Auto-Merch" button on Empire page successfully creates a real product in Shopify tied to the niche.

---

### 999.7 — AB-TESTING-01 (A/B Testing for Content Variants)
**Source:** `.planning/PROJECT.md` (Active requirements)
**Impact:** Currently no way to A/B test video variants
**Files:**
- New: `src/services/ab_testing/` (service + models)
- `src/api/routes/video_generate.py` (variant generation already exists per multi-variant endpoint)
- `src/services/analytics/` (variant tracking)
- `apps/dashboard/src/app/empire/` or similar (results viewer)

**Tasks:**
- [ ] Add `ABTestDB` (variant A, B, share %, engagement metrics)
- [ ] Endpoint: `POST /ab-test/create` from a base job_id
- [ ] Endpoint: `POST /ab-test/{id}/track` to record impressions/clicks
- [ ] Dashboard view showing winner with statistical significance
- [ ] Wire up publishing to randomly assign variant per impression

**Acceptance:** User creates an A/B test → publishes both variants → dashboard shows engagement deltas with p-value.

---

### 999.8 — WEBHOOKS-01 (Affiliate Network Webhooks for Revenue)
**Source:** `.planning/PROJECT.md` (Active requirements)
**Impact:** Revenue is not actually tracked from real affiliate networks
**Files:**
- `src/api/routes/webhooks.py` (YouTube webhook exists; add generic affiliate webhook)
- `src/services/monetization/revenue_tracker.py` (new)
- `src/api/utils/models.py` (RevenueLogDB — verify it exists)

**Tasks:**
- [ ] Add `POST /webhooks/affiliate/{network}` generic handler
- [ ] HMAC signature validation per network
- [ ] Idempotency dedupe (by event_id)
- [ ] Persist to `RevenueLogDB`
- [ ] Update Empire page revenue dashboard in real-time

**Acceptance:** Amazon Associates webhook → revenue entry appears in user's Empire dashboard within 5s.

---

### 999.9 — Complete Phase 1 — UserDB Unification (01-06-PLAN.md)
**Source:** `.planning/ROADMAP.md` (Phase 1, 5/6 complete)
**Files:**
- `src/api/utils/user_models.py`
- `src/api/utils/models.py`
- `alembic/versions/`

**Tasks:**
- [ ] Unify all user references to single `UserDB`
- [ ] Alembic migration to drop legacy columns/tables
- [ ] Update all routes to import from `user_models`
- [ ] Tests for unified model

---

### 999.10 — Complete Phase 4 — Multi-Scene Storytelling Verification (04-01-PLAN.md)
**Source:** `.planning/ROADMAP.md` (Phase 4, 0/1 complete)
**Files:**
- `src/services/nexus_engine/auto_creator.py`
- `src/services/nexus_engine/orchestrator.py`
- `tests/nexus/` (new)

**Tasks:**
- [ ] End-to-end test of `create_cinema_video_task` with multi-scene input
- [ ] Verify scene beat detection from analysis
- [ ] Verify final compilation produces a single video
- [ ] Document supported blueprints

---

### 999.11 — Complete Phase 5 — Multi-Platform Publishing Verification (05-02-PLAN.md)
**Source:** `.planning/ROADMAP.md` (Phase 5, 1/2 complete)
**Files:**
- `src/services/publishing/` (all platforms)
- `tests/publishing/`

**Tasks:**
- [ ] Verify TikTok upload actually works end-to-end
- [ ] Verify Instagram upload (currently stub)
- [ ] Verify all 8 platforms with real OAuth + real upload
- [ ] Document platform-specific quirks

---

### 999.12 — Complete Phase 7 — Monetization & Credit System Verification (07-02-PLAN.md)
**Source:** `.planning/ROADMAP.md` (Phase 7, 1/2 complete)
**Files:**
- `src/services/payment/credit_service.py`
- `src/services/monetization/`

**Tasks:**
- [ ] Verify credit consumption across all actions
- [ ] Test tier upgrade/downgrade flows
- [ ] Test credit refund on failed jobs
- [ ] Load test concurrent credit consumption

---

### 999.13 — Complete Phase 8 — Analytics Verification (08-02-PLAN.md)
**Source:** `.planning/ROADMAP.md` (Phase 8, 1/2 complete)
**Files:**
- `src/services/analytics/`
- `tests/analytics/`

**Tasks:**
- [ ] Verify cross-platform metrics aggregation
- [ ] Verify time-series data is correct
- [ ] Verify report generation

---

### 999.14 — Complete Phase 9 Plan 02 — Verify Enterprise Infrastructure (09-02-PLAN.md)
**Source:** `.planning/ROADMAP.md` (Phase 9, 1/2 complete), `HARDENING_ROADMAP.md`
**Files:**
- All Phase 9 hardening work

**Tasks:**
- [ ] Verify tracing across all services
- [ ] Verify Grafana dashboards show real metrics
- [ ] Verify alert rules fire on real failures
- [ ] Run chaos_utility.py in staging
- [ ] Document SLOs

---

## P2 — Nice to Have (Quality of Life)

### 999.15 — Background Removal in Video Transform
**Source:** `docs/comprehensive_gap_analysis.md` §B.3
**Files:** `src/services/video_engine/processor.py`, new `background_remover.py`

**Tasks:**
- [ ] Integrate `rembg` or `mediapipe` for video background removal
- [ ] UI toggle in `transformation/page.tsx`
- [ ] Tests

### 999.16 — Sound Design + Music Addition
**Source:** `docs/comprehensive_gap_analysis.md` §B.3
**Files:** `src/services/audio/sound_design.py`, `src/services/audio/music_library.py`

**Tasks:**
- [ ] Implement sound design service (mix background music, SFX)
- [ ] Implement music library integration (royalty-free)
- [ ] UI toggles in `transformation/page.tsx`

### 999.17 — Subtitle Generation
**Source:** `docs/comprehensive_gap_analysis.md` §B.3
**Files:** `src/services/video_engine/captioner.py`

**Tasks:**
- [ ] Integrate Whisper for transcription
- [ ] Burn subtitles into video with FFmpeg
- [ ] UI: subtitle style picker

### 999.18 — Quality Upscaling (4K)
**Source:** `docs/comprehensive_gap_analysis.md` §B.3
**Files:** `src/services/video_engine/upscaler.py`

**Tasks:**
- [ ] Implement Real-ESRGAN (already in synthesis_service.py:1183)
- [ ] Extract into a standalone service
- [ ] UI button (already exists in `transformation/page.tsx` "Neural Upscale" — currently disabled)

### 999.19 — Dynamic Watermarking (Branding Burn-in)
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §6
**Files:** `src/services/video_engine/watermarker.py`

**Tasks:**
- [ ] Accept user logo upload
- [ ] Position picker (corners, center, lower-third)
- [ ] Apply during transformation pipeline

### 999.20 — Cancel Subscription UI Flow
**Source:** `docs/comprehensive_gap_analysis.md` §B.8
**Files:** `src/api/routes/billing.py`, `apps/dashboard/src/app/settings/page.tsx`

**Tasks:**
- [ ] Add cancel-subscription endpoint (already partial)
- [ ] Add UI flow with confirmation modal
- [ ] Test refund/credit logic

### 999.21 — Audit Logs UI for Admins
**Source:** `docs/comprehensive_gap_analysis.md` §B.10
**Files:** `src/api/routes/admin.py`, `apps/dashboard/src/app/admin/`

**Tasks:**
- [ ] Add `AuditLogDB` if missing
- [ ] Wire up logging across sensitive routes
- [ ] Add admin viewer page

### 999.22 — Content Moderation (Admin)
**Source:** `docs/comprehensive_gap_analysis.md` §B.10
**Files:** `src/services/moderation/`, admin UI

**Tasks:**
- [ ] Implement content classifier (toxicity, NSFW)
- [ ] Admin queue to approve/reject
- [ ] Auto-flag for high-risk niches

### 999.23 — Global Error Boundary (Frontend)
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §1
**Files:** `apps/dashboard/src/app/error.tsx`, `apps/dashboard/src/app/global-error.tsx`

**Tasks:**
- [ ] Add `app/error.tsx` and `app/global-error.tsx`
- [ ] Sentry integration (`@sentry/nextjs`)
- [ ] Fall back to existing `POST /api/v1/errors`

### 999.24 — PWA / Offline Manifest
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §1
**Files:** `apps/dashboard/public/manifest.json`, `apps/dashboard/next.config.js`

**Tasks:**
- [ ] Add manifest, service worker, icons
- [ ] Cache static assets + read-only API responses

### 999.25 — Continuous Niche Monitoring Backend
**Source:** `docs/comprehensive_gap_analysis.md` §B.1
**Files:** `src/services/discovery/tasks.py` (sentinel_watcher exists but is manual)

**Tasks:**
- [ ] Add Celery Beat schedule for periodic niche monitoring
- [ ] Trigger alerts when viral velocity crosses threshold
- [ ] Persist monitoring state

### 999.26 — Multi-Gateway Payments (PayPal, Razorpay)
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §4
**Files:** `src/services/payment/`

**Tasks:**
- [ ] Abstract payment gateway behind interface
- [ ] Implement PayPal + Razorpay adapters
- [ ] UI: gateway selector at checkout

### 999.27 — Credits / Usage-Based Billing
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §4
**Files:** `src/services/payment/credit_service.py`

**Tasks:**
- [ ] One-off credit pack purchases
- [ ] Pricing tier per engine
- [ ] UI: credits page already exists at `/credits`

### 999.28 — GPU Task Batching / Accumulator
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §6
**Files:** `src/services/video_engine/synthesis_service.py` (GpuQueueManager exists at :148)

**Tasks:**
- [ ] Add 10-15s buffer to group similar jobs
- [ ] Track batch hit rate

---

## P3 — Future / Infrastructure

### 999.29 — Distributed Tracing (Jaeger)
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §2
**Files:** `src/api/utils/tracing.py`

**Tasks:**
- [ ] Add Jaeger exporter to OpenTelemetry
- [ ] Trace all HTTP + Celery spans

### 999.30 — Circuit Breaker Pattern for External APIs
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §2
**Files:** `src/api/utils/resilience.py` (CircuitBreaker already exists)

**Tasks:**
- [ ] Audit which external API calls lack circuit breakers
- [ ] Apply `CircuitBreaker` to YouTube, Stripe, all video providers
- [ ] Tests for open/half-open/closed states

### 999.31 — PostgreSQL Master-Slave (HA)
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §3
**Files:** `docker-compose.yml`, `src/api/utils/database.py`

**Tasks:**
- [ ] Add replica to docker-compose
- [ ] Configure read-replica routing
- [ ] Document failover procedure

### 999.32 — WAF (Web Application Firewall)
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §3

**Tasks:**
- [ ] Add Traefik plugins (CrowdSec, ModSecurity)
- [ ] Rules for L7 attacks (SQLi, XSS)

### 999.33 — Service Discovery (Consul)
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §3

**Tasks:**
- [ ] Add Consul to docker-compose
- [ ] Refactor static service URLs to use Consul DNS

### 999.34 — Storybook / Component Testing
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §1
**Files:** `apps/dashboard/.storybook/`

**Tasks:**
- [ ] Add Storybook 8
- [ ] Story for each component in `components/ui/`

### 999.35 — Visual Regression Testing
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §5

**Tasks:**
- [ ] Add Playwright visual diffs
- [ ] Run in CI

### 999.36 — Performance Budget (k6 Load Tests)
**Source:** `docs/gap_analysis_viral_forge_comprehensive.md` §5
**Files:** `scripts/load_test.js` (exists)

**Tasks:**
- [ ] Define SLOs (p95 < 500ms, 100 concurrent users)
- [ ] Wire k6 into CI
- [ ] Track regressions

### 999.37 — Visual Regression for Skill Audit (2 stale + 7 new)
**Source:** `.planning/STATE.md` (Pending Todos)

**Tasks:**
- [ ] Fix 2 stale skills
- [ ] Complete 7 in-progress skills
- [ ] Skill audit automation

---

## Summary by Priority

| Priority | Count | Status |
|----------|-------|--------|
| P0 | 4 | All have clear root cause + acceptance criteria |
| P1 | 10 | Mix of feature completion + active requirements |
| P2 | 14 | Quality-of-life + content moderation |
| P3 | 9 | Infrastructure + future scale |
| **Total** | **37** | |

## Promotion Criteria

Promote a backlog item to a numbered phase in `ROADMAP.md` when:
1. It has a clear acceptance criterion (this file does)
2. Required dependencies (services, env vars, infrastructure) are in place
3. Effort estimate is ≤ 5 days of work, or it can be split into sub-plans

Use `/gsd-add-phase` or `/gsd-insert-phase <between>` to convert.

## Related Documents

- `.planning/ROADMAP.md` — Active phase tracking
- `.planning/PROJECT.md` — Validated + active requirements
- `.planning/STATE.md` — Current state
- `.planning/HARDENING_ROADMAP.md` — Phase 9 enterprise hardening
- `docs/comprehensive_gap_analysis.md` — Original gap analysis
- `docs/gap_analysis_april_2026.md` — April 2026 status

---

*Generated: 2026-05-29*
