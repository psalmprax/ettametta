# Viral Forge — UI/Backend Gap Analysis (March 2026)

**Scope:** Every button, clickable, menu, form input, and use case scenario across 14 frontend pages cross-referenced with 87 API endpoints and 31 backend services.

**Principle Applied:** Real implementations first. Dummies/simulations/placeholders only as fallback when the real solution fails — never as the primary path.

---

## EXECUTIVE SUMMARY

| Metric | Value |
|---|---|
| Frontend pages analyzed | 14 |
| UI interactive elements found | ~200+ |
| API endpoints mapped | 87 |
| Backend services audited | 31 |
| **Fully wired (UI → real backend)** | ~75% |
| **Backend endpoints with NO UI** | 21 |
| **Broken connections (UI → missing/wrong endpoint)** | 3 |
| **Settings silently discarded** | 42 fields (non-admin) |
| **Stub/placeholder services** | 3 |
| **Services with NotImplementedError** | 2 |

---

## SECTION 1: CRITICAL GAPS (Must Fix Immediately)

### 1.1 Non-Admin Settings Save Is a No-Op — `settings/page.tsx:207`

**Severity:** CRITICAL  
**Impact:** 42 settings fields show "Saved!" but are silently discarded for non-admin users.

The `handleSave` function only calls `POST /settings/bulk` when `userProfile.role === "admin"`. Non-admin users get a success toast after only `telegram_chat_id` and `telegram_token` are saved via `PATCH /auth/me`. All other fields (API keys, monetization config, engine toggles, storage config) are lost.

**Fix Required:**
- Backend: Create `POST /settings/user` endpoint that saves user-scoped settings to `UserSetting` table
- Frontend: Route non-admin saves to the new user-settings endpoint instead of skipping entirely

---

### 1.2 Global Error Reporting Hits Non-Existent Endpoint — `GlobalErrorBoundary.tsx:44`

**Severity:** CRITICAL  
**Impact:** Application errors are never reported to the backend.

`GlobalErrorBoundary` calls `POST /api/errors` (no `/v1` prefix). No such route exists in any route file.

**Fix Required:**
- Backend: Add `POST /api/v1/errors` endpoint that logs to `AuditLogDB`
- Frontend: Update the call URL to `/api/v1/errors`

---

### 1.3 Affiliate Link Listing Returns 405 — `empire/page.tsx:122`

**Severity:** HIGH  
**Impact:** Empire page's affiliate links section likely shows empty or errors.

Frontend calls `GET /monetization/links` to list links. Backend only defines `POST /monetization/links` (create). No GET handler exists.

**Fix Required:**
- Backend: Add `GET /monetization/links` that queries `AffiliateLinkDB` for the current user

---

## SECTION 2: BACKEND ENDPOINTS WITH NO FRONTEND UI (21 Orphaned)

### 2.1 Security Module — 3 endpoints, zero UI

| Endpoint | Method | What It Does | Missing UI Element |
|---|---|---|---|
| `/security/status` | GET | Security health score + threats | Admin dashboard security panel |
| `/security/scan` | POST | Trigger manual integrity audit | "Run Security Audit" button |
| `/security/events` | GET | List security events | Security events log table |

**Scenario Coverage:** Admin needs to monitor security posture, trigger audits, review events. None of this is possible from the UI.

---

### 2.2 Persona Module — 2 endpoints, zero UI

| Endpoint | Method | What It Does | Missing UI Element |
|---|---|---|---|
| `/persona/create` | POST | Create AI avatar (image + audio) | Persona creation form |
| `/persona/generate` | POST | Generate deepfake video | "Generate Video" button on persona |

**Scenario Coverage:** Users creating faceless content need to create personas for consistent branding. The feature exists in the backend but is completely inaccessible.

---

### 2.3 Trading Module — 5 endpoints, zero UI

| Endpoint | Method | What It Does | Missing UI Element |
|---|---|---|---|
| `/trading/market/{symbol}` | GET | Stock market data | Market data search/input |
| `/trading/crypto/{coin_id}` | GET | Crypto price lookup | Crypto price card |
| `/trading/crypto/trending` | GET | Trending cryptos | Trending crypto list |
| `/trading/screener` | GET | Market screener | Screener dashboard |
| `/trading/analysis/{symbol}` | GET | AI stock analysis | Analysis results panel |

**Scenario Coverage:** Content creators covering finance/crypto niches need market data for content ideas. All 5 endpoints are fully implemented with real Alpha Vantage + CoinGecko APIs but have zero UI exposure.

---

### 2.4 AI Agent Module — 4 endpoints, zero UI

| Endpoint | Method | What It Does | Missing UI Element |
|---|---|---|---|
| `/agent/chat` | POST | Chat with AI agent | Chat interface |
| `/agent/crew` | POST | Multi-agent task execution | Task orchestration UI |
| `/agent/code-executor` | POST | Code analysis/execution | Code execution panel |
| `/agent/capabilities` | GET | Available capabilities | Agent capabilities display |

---

### 2.5 Publishing Gaps — Missing controls

| Endpoint | Method | Missing UI Element |
|---|---|---|
| `/publish/post-multi` | POST | Multi-platform publish button (current UI only does single platform) |
| `/publish/platforms` | GET | Platform listing (hardcoded in frontend instead) |
| `/publish/package` | POST | SEO package generation button |
| `/publish/retry/{content_id}` | POST | Retry button for failed publishes |
| `/publish/account/{account_id}` | DELETE | Unlink/disconnect account button |

---

### 2.6 Monetization Gaps — Missing triggers

| Endpoint | Method | Missing UI Element |
|---|---|---|
| `/monetization/commerce/sync` | POST | Shopify sync button |
| `/monetization/auto-merch` | POST | Auto-merch trigger (toggle exists but never calls endpoint) |
| `/monetization/recommend-links` | POST | AI link recommendation (never called from any flow) |

---

### 2.7 Other Orphaned Endpoints

| Endpoint | Method | Missing UI Element |
|---|---|---|
| `/remotion/render` | POST | Custom Remotion render form |
| `/settings/monetization/strategies` | GET | Strategy status display |
| `/no-face/empire/clone` | POST | Clone button (empire page uses different endpoint) |
| `/credits/referral/stats` | GET | Referral statistics display |
| `/ab/record-view/{content_id}` | POST | View recording (should be automatic) |
| `/ab/test/{id}/recommend-variant` | GET | Variant recommendation display |

---

## SECTION 3: STUB/PLACEHOLDER SERVICES THAT NEED REAL IMPLEMENTATIONS

### 3.1 `_synthesize_veo3` — `services/video_engine/synthesis_service.py:354`

**Current:** Raises `NotImplementedError`  
**Impact:** Users selecting "Veo3" engine get an error  
**Fix:** Implement Veo3 API integration or remove from UI engine selector

---

### 3.2 `_synthesize_wan` — `services/video_engine/synthesis_service.py:366`

**Current:** Raises `NotImplementedError`  
**Impact:** Users selecting "Wan" synthesis path get an error  
**Fix:** Wire to existing `wan_inference.py` or remove the stub

---

### 3.3 Motion Graphics Overlay — `services/video_engine/motion_graphics.py:134`

**Current:** `add_animated_overlay` explicitly logs "not implemented" and returns `None`  
**Impact:** Motion graphics toggle in transformation modal does nothing for overlays  
**Fix:** Implement using Remotion or remove the toggle from UI

---

### 3.4 Persona TTS — `services/video_engine/persona_service.py:26`

**Current:** TTS generation is "mocked here for MVP"  
**Impact:** Persona video generation produces silent or placeholder audio  
**Fix:** Wire to ElevenLabs or Fish Speech TTS service

---

### 3.5 `ModelManager.acquire_model` — `services/video_engine/synthesis_service.py:40`

**Current:** Uses `asyncio.sleep(2)` to simulate model download  
**Impact:** Model acquisition appears instant but nothing actually downloads  
**Fix:** Implement real model download from HuggingFace or remove the simulation

---

### 3.6 `start_time` Undefined — `wan_inference.py:109,153` and `mochi_inference.py:86`

**Current:** `start_time` variable referenced but never defined — causes `NameError` at runtime  
**Impact:** Wan and Mochi video generation crashes  
**Fix:** Add `start_time = time.time()` at function entry

---

### 3.7 Digital Product Strategy — `services/monetization/strategies/digital_product.py`

**Current:** Returns empty list and generic CTA — no actual product data source  
**Impact:** Digital product monetization strategy produces no recommendations  
**Fix:** Query `AffiliateLinkDB` filtered by `digital_product` niche or integrate with Gumroad/Teachable API

---

## SECTION 4: USE CASE SCENARIO COVERAGE MATRIX

### 4.1 Content Discovery

| Scenario | UI Element | Backend Endpoint | Status |
|---|---|---|---|
| Browse trending by niche | Niche buttons + candidate list | `GET /discovery/trends` | ✅ COVERED |
| Search by keyword | Search input + "Deep Scan" | `GET /discovery/search` + `POST /discovery/scan` | ✅ COVERED |
| Filter by platform | Platform cycle button | Client-side filter | ✅ COVERED |
| Filter by viral score | Range slider | Query param | ✅ COVERED |
| Filter by time horizon | 24h/7d/30d buttons | Query param | ✅ COVERED |
| Exclude shorts | Toggle | Query param | ✅ COVERED |
| Open candidate URL | Row click | `window.open(url)` | ✅ COVERED |
| Deep analyze candidate | "Deconstruct" button | `POST /discovery/analyze` | ✅ COVERED |
| Poll analysis status | Automatic polling | `GET /discovery/analyze/{taskId}` | ✅ COVERED |
| Create video from analysis | **MISSING** | `POST /discovery/analyze/{taskId}/create-video` | ❌ NO UI |
| Monitor niches continuously | **MISSING** | N/A | ❌ NO UI |
| View niche trend history | N/A | `GET /discovery/niche-trends/{niche}` | ⚠️ WIRED but no dedicated view |

### 4.2 Video Generation

| Scenario | UI Element | Backend Endpoint | Status |
|---|---|---|---|
| Transform existing video | "Start Engine" in modal | `POST /video/transform` | ✅ COVERED |
| AI generate from prompt | "Synthesize Video" | `POST /video/generate` | ✅ COVERED |
| Story mode generation | "Synthesize Video" (story toggle) | `POST /video/generate-story` | ⚠️ WIRED but story task is stub |
| Test drive (quick preview) | "Test Drive" button | `POST /video/test-drive` | ✅ COVERED |
| Abort running job | "Abort" button | `POST /video/jobs/{id}/abort` | ✅ COVERED |
| View job status | Job cards + WebSocket | `GET /video/jobs` + WS | ✅ COVERED |
| Select AI engine | Engine buttons (8 options) | Client state → API | ⚠️ PARTIAL — Veo3, Runway, Pika are stubs |
| Nexus compose | "Initiate Cinema Mode" | `POST /nexus/compose` | ✅ COVERED |
| Nexus cinema mode | Cinema mode toggle | `POST /nexus/compose` | ⚠️ Calls auto_creator (real) but limited blueprints |

### 4.3 Creation (No-Face)

| Scenario | UI Element | Backend Endpoint | Status |
|---|---|---|---|
| Generate script | "Generate Script" | `POST /no-face/generate-script` | ✅ COVERED |
| Validate hook | "Analyze Retention" | `POST /no-face/validate-hook` | ✅ COVERED |
| Generate voiceover | Audio button per segment | `POST /no-face/generate-voiceover` | ✅ COVERED |
| Search stock media | Stock button per segment | `GET /no-face/search-stock` | ✅ COVERED |
| Generate image | Image button per segment | `POST /no-face/generate-image` | ✅ COVERED |
| Localize script | "ES"/"DE" buttons | `POST /no-face/localize` | ✅ COVERED |
| Export assets | "Export Assets" | Client-side JSON download | ✅ COVERED |
| Launch production | "Launch Production" | `POST /nexus/compose` | ✅ COVERED |

### 4.4 Publishing

| Scenario | UI Element | Backend Endpoint | Status |
|---|---|---|---|
| Connect platform (OAuth) | "Inject Node" → platform select | `GET /publish/auth/{platform}` | ✅ COVERED (YouTube, TikTok, Instagram, X, LinkedIn) |
| View connected accounts | Account cards | `GET /publish/accounts` | ✅ COVERED |
| Publish single platform | "Initialize Transmission" | `POST /publish/post` | ✅ COVERED |
| Publish multi-platform | **MISSING** | `POST /publish/post-multi` | ❌ NO UI |
| Schedule post | Schedule toggle + time input | `POST /publish/schedule` | ✅ COVERED |
| View publish history | History list | `GET /publish/history` | ✅ COVERED |
| Sync metrics | "Sync" button per item | `POST /publish/sync/{postId}` | ✅ COVERED |
| View live post | "View Live" link | External URL | ✅ COVERED |
| Re-authenticate account | "Re-Authenticate Node" | `GET /publish/auth/{platform}` | ✅ COVERED |
| Delete/disconnect account | **MISSING** | `DELETE /publish/account/{id}` | ❌ NO UI |
| Retry failed publish | **MISSING** | `POST /publish/retry/{content_id}` | ❌ NO UI |
| Generate SEO package | **MISSING** | `POST /publish/package` | ❌ NO UI |

### 4.5 Analytics

| Scenario | UI Element | Backend Endpoint | Status |
|---|---|---|---|
| View published posts | Posts table | `GET /analytics/posts` | ✅ COVERED |
| View performance report | Charts on post select | `GET /analytics/report/{postId}` | ✅ COVERED |
| View insights | Insights panel | `GET /analytics/insights/{postId}` | ✅ COVERED |
| Get monetization suggestions | "Execute Inversion" | `GET /analytics/monetization/{postId}` | ✅ COVERED |
| Export CSV | "Global Export" | Client-side generation | ✅ COVERED |
| View A/B results | A/B panel | `GET /analytics/ab/results/{postId}` | ✅ COVERED |
| Start A/B test | "+ New Test" → "Start Test" | `POST /ab/test/start` | ✅ COVERED |
| Determine A/B winner | "Determine Winner" | `POST /ab/test/{id}/determine-winner` | ✅ COVERED |
| View dashboard stats | Stats cards | `GET /analytics/stats/summary` | ✅ COVERED |
| View storage stats | Storage card | `GET /analytics/stats/storage` | ✅ COVERED |
| Record variant view | **AUTOMATIC** | `POST /ab/record-view/{content_id}` | ❌ NO UI (should be server-side) |
| Get variant recommendation | **MISSING** | `GET /ab/test/{id}/recommend-variant` | ❌ NO UI |

### 4.6 Monetization (Empire)

| Scenario | UI Element | Backend Endpoint | Status |
|---|---|---|---|
| View revenue report | Revenue panel | `GET /monetization/report` | ✅ COVERED |
| View empire metrics | Metrics cards | `GET /monetization/empire/metrics` | ✅ COVERED |
| View blueprints | Blueprint cards | `GET /monetization/empire/blueprints` | ✅ COVERED |
| View network graph | Network visualization | `GET /monetization/empire/network` | ✅ COVERED |
| Clone strategy | "Launch Empire Mode" | `POST /monetization/empire/clone` | ✅ COVERED |
| Add affiliate link | "Add Affiliate Link" | `POST /monetization/links` | ✅ COVERED |
| Generate promo | "Generate High-ROI Promo" | `POST /monetization/promo/generate` | ✅ COVERED |
| List affiliate links | Links list | `GET /monetization/links` | ❌ BROKEN — 405 (no GET handler) |
| Trigger auto-merch | **MISSING** | `POST /monetization/auto-merch` | ❌ NO UI (toggle saves setting only) |
| Sync Shopify | **MISSING** | `POST /monetization/commerce/sync` | ❌ NO UI |
| Get AI link recommendations | **MISSING** | `POST /monetization/recommend-links` | ❌ NO UI |

### 4.7 Credits & Billing

| Scenario | UI Element | Backend Endpoint | Status |
|---|---|---|---|
| View balance | Balance display | `GET /credits/balance` | ✅ COVERED |
| View costs | Costs table | `GET /credits/costs` | ✅ COVERED |
| View transactions | Transactions table | `GET /credits/transactions` | ✅ COVERED |
| Purchase credits | "Purchase" buttons | `POST /credits/purchase` | ✅ COVERED |
| View referral code | Referral display | `GET /credits/referral/code` | ✅ COVERED |
| Copy referral link | Copy button | `navigator.clipboard` | ✅ COVERED |
| Apply referral code | "Apply Code" | `POST /credits/referral/apply` | ✅ COVERED |
| View referrals | Referrals list | `GET /credits/referrals` | ✅ COVERED |
| View subscription | Billing tab display | `GET /billing/subscription` | ✅ COVERED |
| Upgrade plan | Upgrade buttons | `POST /billing/create-checkout-session` | ✅ COVERED |
| Cancel subscription | "Cancel Subscription" | `POST /billing/cancel` | ✅ COVERED |
| View referral stats | **MISSING** | `GET /credits/referral/stats` | ❌ NO UI |
| View available packages | **MISSING** | `GET /credits/packages` | ❌ NO UI |

### 4.8 Autonomous (Agent Zero)

| Scenario | UI Element | Backend Endpoint | Status |
|---|---|---|---|
| View Agent Zero status | Status cards | `GET /zero/status` | ✅ COVERED |
| Start autonomous mode | "Launch Director" | `POST /zero/start` | ✅ COVERED |
| Stop autonomous mode | "Halt Operations" | `POST /zero/stop` | ✅ COVERED |
| View insights | Insight oracle | `GET /zero/insights` | ✅ COVERED |

### 4.9 Settings & Admin

| Scenario | UI Element | Backend Endpoint | Status |
|---|---|---|---|
| View profile | Identity tab | `GET /auth/me` | ✅ COVERED |
| Change password | Password form | `POST /auth/me/change-password` | ✅ COVERED |
| Save settings (admin) | "Synchronize" | `POST /settings/bulk` | ✅ COVERED |
| Save settings (non-admin) | "Synchronize" | **SKIPPED** | ❌ CRITICAL — saves nothing |
| View system settings (admin) | Admin tabs | `GET /settings/system` | ✅ COVERED |
| Update system settings | "Commit Changes" | `POST /settings/system` | ✅ COVERED |
| Toggle filters | Filter toggles | `POST /settings/filters/{id}/toggle` | ✅ COVERED |
| View security status | **MISSING** | `GET /security/status` | ❌ NO UI |
| Trigger security scan | **MISSING** | `POST /security/scan` | ❌ NO UI |
| View security events | **MISSING** | `GET /security/events` | ❌ NO UI |

---

## SECTION 5: ERROR HANDLING GAPS

### 5.1 Silent Error Failures (Console-Only)

| Page | Count | Impact |
|---|---|---|
| Dashboard | 2 | Stats show zeros, scan fails silently |
| Empire | 6 | All data fetches fail silently |
| Settings | 1 | Profile fetch fails silently |
| Publishing | 1 | Initial load fails silently |
| Creation | 4 | Script/voiceover/image/stock failures invisible |
| Autonomous | 1 | Status fetch fails silently |
| Nexus | 2 | Job listing/compose fails silently |

**Total:** ~17 catch blocks that only `console.error` with no user-facing feedback.

### 5.2 False Positive Feedback

- **Settings save (non-admin):** Shows "Saved!" when nothing was saved
- **Settings save (admin, partial failure):** If bulk save fails but telegram PATCH succeeds, shows "Saved!" masking the real failure

### 5.3 Missing Error Boundaries

Only `GlobalErrorBoundary` and `ErrorBoundary` (in sidebar) exist. Individual pages have no error boundaries — a crash in one section takes down the page.

---

## SECTION 6: SERVICES CLASSIFICATION SUMMARY

### FULLY REAL (24 services)
`agent_zero`, `trading`, `auto_merch`, `commerce_service`, `ltx_inference`, `hunyuan_inference`, `cogvideo_inference`, `animatediff_inference`, `remotion_service`, `vlm_service`, `stock_service`, `storyboard_service`, `thumbnail_service`, `audio_mixer`, `scheduler`, `scheduler_tasks`, `viral_loop`, `empire_mode`, `security`, `analytics`, `stripe_service`, `credit_service`, `auto_creator`, `orchestrator`

### PARTIAL (4 services)
| Service | Real Parts | Stub Parts |
|---|---|---|
| `langchain` | Chat chains when enabled | Disabled by default |
| `persona_service` | Render node call | TTS is mocked |
| `synthesis_service` | LTX, Hunyuan, CogVideo, Lite4K dispatch | Veo3: NotImplementedError, Wan: NotImplementedError, ModelManager: simulated download |
| `wan_inference` / `mochi_inference` | Real diffusers pipeline | `start_time` undefined causes NameError |

### STUB/PLACEHOLDER (3 items)
| Item | Location | Issue |
|---|---|---|
| Motion graphics overlay | `motion_graphics.py:134` | Returns None, logs "not implemented" |
| Digital product strategy | `strategies/digital_product.py` | Returns empty list |
| Veo3 synthesis | `synthesis_service.py:354` | Raises NotImplementedError |

---

## SECTION 7: ACTIONABLE FIX LIST (Priority Order)

### P0 — Fix Today (Broken Core Flows)

1. **Non-admin settings save** — Add `POST /settings/user` endpoint, wire frontend to it
2. **Global error endpoint** — Add `POST /api/v1/errors`, fix URL in `GlobalErrorBoundary.tsx`
3. **`GET /monetization/links`** — Add GET handler to list affiliate links
4. **`start_time` NameError** — Add `start_time = time.time()` in `wan_inference.py` and `mochi_inference.py`

### P1 — This Week (Orphaned Backend → UI Wiring)

5. **Security dashboard** — Add security panel to admin page (3 endpoints)
6. **Multi-platform publish** — Add "Publish Everywhere" button calling `/publish/post-multi`
7. **Retry failed publish** — Add retry button per failed history item
8. **Disconnect account** — Add delete button per connected account
9. **Auto-merch trigger** — Wire existing toggle to actually call `/monetization/auto-merch`
10. **AI link recommendations** — Wire "Recommend Links" button in publishing flow

### P2 — Next Sprint (Missing Features)

11. **Trading dashboard** — Create `/trading` page with market data, crypto, screener
12. **AI Agent chat** — Create agent chat interface on Nexus page
13. **Persona management** — Create persona CRUD UI
14. **Remotion render form** — Add custom render UI
15. **SEO package generator** — Add button in publishing flow
16. **Referral stats** — Add referral stats display on credits page

### P3 — Technical Debt

17. **Replace NotImplementedError stubs** — Either implement Veo3/Wan synthesis or remove from engine selector
18. **Implement motion graphics overlay** — Or remove toggle from UI
19. **Wire persona TTS** — Connect to ElevenLabs/Fish Speech
20. **Implement digital product strategy** — Or remove from monetization options
21. **Add error handling to all pages** — Replace 17+ console.error-only catch blocks with toast notifications
22. **Add page-level error boundaries** — Prevent full-page crashes

---

## SECTION 8: COMPLETE ENDPOINT-TO-UI MAP

### Auth (`/auth`) — 10 endpoints

| Endpoint | UI Page | Button/Element | Status |
|---|---|---|---|
| POST `/register` | `/register` | "INITIALIZE ACCOUNT" | ✅ |
| POST `/login` | `/login` | "AUTHENTICATE" | ✅ |
| GET `/me` | Multiple | Auth context on mount | ✅ |
| PATCH `/me` | `/settings` | "Synchronize" (telegram fields) | ✅ |
| POST `/me/change-password` | `/settings` | "Change Password" | ✅ |
| POST `/me/upgrade-subscription` | — | — | ⚠️ Unused (billing handles this) |
| GET `/verify-telegram/{id}` | — | — | ❌ NO UI |
| GET `/verify-whatsapp/{id}` | — | — | ❌ NO UI |
| GET `/verify-telegram-internal/{id}` | — | — | ❌ Internal only |
| GET `/internal/users-with-bots` | — | — | ❌ Internal only |

### Discovery (`/discovery`) — 8 endpoints

| Endpoint | UI Page | Button/Element | Status |
|---|---|---|---|
| GET `/trends` | `/discovery` | Auto-fetch on niche select | ✅ |
| GET `/search` | `/discovery` | Search input | ✅ |
| POST `/scan` | `/discovery` | "Deep Scan" | ✅ |
| POST `/analyze` | `/discovery` | "Deconstruct" | ✅ |
| GET `/niche-trends/{niche}` | `/discovery` | Auto-fetch | ✅ |
| GET `/niches` | Multiple | Niche selectors | ✅ |
| GET `/analyze/{task_id}` | `/discovery` | Polling | ✅ |
| POST `/analyze/{task_id}/create-video` | — | — | ❌ NO UI |

### Video (`/video`) — 6 endpoints

| Endpoint | UI Page | Button/Element | Status |
|---|---|---|---|
| POST `/transform` | `/transformation`, `/discovery` | "Start Engine", "Transform" | ✅ |
| GET `/jobs` | `/transformation`, `/publishing` | Job list | ✅ |
| POST `/jobs/{id}/abort` | `/transformation`, `/discovery` | "Abort" | ✅ |
| POST `/test-drive` | `/discovery` | "Test Drive" | ✅ |
| POST `/generate` | `/discovery` | "Synthesize Video" | ✅ |
| POST `/generate-story` | `/discovery` | "Synthesize Video" (story mode) | ✅ |

### Publishing (`/publish`) — 16 endpoints

| Endpoint | Status |
|---|---|
| GET `/platforms` | ❌ NO UI |
| GET `/auth/youtube` | ✅ |
| GET `/auth/youtube/callback` | ✅ |
| GET `/accounts` | ✅ |
| DELETE `/account/{id}` | ❌ NO UI |
| POST `/retry/{content_id}` | ❌ NO UI |
| GET `/auth/tiktok` | ✅ |
| GET `/auth/tiktok/callback` | ✅ |
| GET `/auth/instagram` | ✅ |
| GET `/auth/instagram/callback` | ✅ |
| GET `/auth/x` | ✅ |
| GET `/auth/x/callback` | ✅ |
| GET `/auth/linkedin` | ✅ |
| GET `/auth/linkedin/callback` | ✅ |
| POST `/package` | ❌ NO UI |
| POST `/sync/{content_id}` | ✅ |
| GET `/history` | ✅ |
| POST `/schedule` | ✅ |
| POST `/post` | ✅ |
| POST `/post-multi` | ❌ NO UI |

### Monetization (`/monetization`) — 10 endpoints

| Endpoint | Status |
|---|---|
| POST `/recommend-links` | ❌ NO UI |
| POST `/auto-merch` | ❌ NO UI (toggle exists but doesn't call) |
| GET `/report` | ✅ |
| GET `/empire/metrics` | ✅ |
| GET `/empire/blueprints` | ✅ |
| GET `/empire/network` | ✅ |
| POST `/commerce/sync` | ❌ NO UI |
| POST `/empire/clone` | ✅ |
| POST `/links` | ✅ |
| GET `/links` | ❌ BROKEN (405) |

### Credits (`/credits`) — 9 endpoints

| Endpoint | Status |
|---|---|
| GET `/balance` | ✅ |
| GET `/transactions` | ✅ |
| GET `/packages` | ❌ NO UI |
| POST `/purchase` | ✅ |
| GET `/costs` | ✅ |
| GET `/referral/code` | ✅ |
| POST `/referral/apply` | ✅ |
| GET `/referrals` | ✅ |
| GET `/referral/stats` | ❌ NO UI |

### Other Modules — Summary

| Module | Total Endpoints | With UI | Without UI |
|---|---|---|---|
| Billing | 4 | 4 | 0 |
| Settings | 8 | 7 | 1 (`/monetization/strategies`) |
| Nexus | 3 | 3 | 0 |
| Security | 3 | 0 | 3 |
| Persona | 2 | 0 | 2 |
| Webhooks | 4 | 0 (server-side) | 0 |
| Admin | 2 | 2 | 0 |
| No-Face | 8 | 6 | 2 |
| A/B Testing | 6 | 4 | 2 |
| Remotion | 1 | 0 | 1 |
| Trading | 5 | 0 | 5 |
| Agent | 4 | 0 | 4 |
| Zero | 4 | 4 | 0 |
| WebSocket | 2 | 2 | 0 |

---

## SECTION 9: MISSING USE CASE SCENARIOS (Not Covered By Any Page)

1. **Security Monitoring** — No page exists for security status, scans, or event logs
2. **Market Intelligence** — No page for trading/market data (finance niche content creators)
3. **AI Agent Interaction** — No page for chatting with AI agents or running multi-agent tasks
4. **Persona Management** — No page for creating/managing AI avatars
5. **Multi-Platform Deploy** — Publishing page only does single platform at a time
6. **Content Analysis → Video Pipeline** — "Create Video from Analysis" button missing
7. **Scheduled Post Monitoring** — No view of pending scheduled posts or their execution status
8. **Affiliate Performance** — No tracking of which affiliate links generate revenue
9. **A/B Test Auto-Optimization** — Tests created but no automatic variant serving
10. **Notification Center** — No central place to see all system notifications/events

---

*Generated: 2026-03-29 | Viral Forge Project | Comprehensive UI/Backend Gap Analysis*
