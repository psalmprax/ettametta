# Viral Forge - UI/Buttons/Clickables/Menus Gap Analysis (Real-First Priority)

**Date:** 2026-04-08  
**Purpose:** Comprehensive analysis of all interactive elements, use case coverage, and real implementation status  
**Priority Rule:** REAL implementation FIRST → Fallback as SECONDARY only when real fails

---

## Executive Summary

This document maps every clickable/button/menu element in the Viral Forge dashboard to its actual implementation status. The key insight is that many features that appear "working" are actually stubs/dummies that the user has to manually convert to real implementation. The goal is to identify which ones actually work vs. which ones are placeholders waiting for real code.

### Current State Assessment

| Category | Count | Real Implementation | Stub/Dummy | Notes |
|----------|-------|---------------------|------------|-------|
| Sidebar Navigation | 12 | 11 | 1 | Trading is stub |
| Discovery Page | 25+ | 20+ | ~5 | Deep analysis incomplete |
| Creation Page | 15+ | 12+ | ~3 | Story generation stub |
| Nexus Page | 10+ | 8+ | ~2 | Cinema mode stub |
| Transformation | 10+ | 8+ | ~2 | - |
| Publishing | 20+ | 18+ | ~2 | TikTok analytics incomplete |
| Analytics | 15+ | 12+ | ~3 | A/B testing issues |
| Empire | 10+ | 8+ | ~2 | Auto-merch stub |
| Settings | 15+ | 12+ | ~3 | Telegram/WhatsApp not connected |
| **TOTAL** | ~150+ | ~120+ | ~30 | ~20% are stubs/dummies |

---

## 1. Sidebar Navigation (Shell)

| Menu Item | Route | Status | Implementation Detail |
|-----------|-------|--------|----------------------|
| Dashboard | `/` | ✅ REAL | Fetches user data, job stats |
| Discovery | `/discovery` | ✅ REAL | Calls `/discovery/trends`, `/discovery/search` |
| Creation | `/creation` | ✅ REAL | Calls `/no-face/generate-script` |
| Nexus Flow | `/nexus` | ✅ REAL | Calls `/nexus/blueprints`, `/nexus/compose` |
| Autonomous | `/autonomous` | ✅ REAL | Agent orchestration |
| Transformation | `/transformation` | ✅ REAL | Calls `/video/transform`, `/video/jobs` |
| Publishing | `/publishing` | ✅ REAL | OAuth flows, `/publish/post` |
| Analytics | `/analytics` | ✅ REAL | `/analytics/report/{id}` |
| Empire | `/empire` | ✅ REAL | `/monetization/links`, `/monetization/empire/clone` |
| Credits | `/credits` | ✅ REAL | Credit balance & purchase |
| **Trading** | `/trading` | ⚠️ **STUB** | No real API - shows mock data |
| Settings | `/settings` | ✅ REAL | `/settings/bulk` |
| Mobile Nav | - | ✅ REAL | Subset of main nav |

### Gap: Trading Page

**Status:** CRITICAL GAP  
**Issue:** Trading service is disabled (`ENABLE_TRADING=False`), no API route for portfolio, alerts, history, technical analysis. The UI calls endpoints that return 503 errors.

**Real Implementation Available:**
- `/trading/market/{symbol}` ✅ - Alpha Vantage for stocks
- `/trading/crypto/{coin_id}` ✅ - CoinGecko for crypto
- `/trading/crypto/trending` ✅ - CoinGecko trending
- `/trading/screener` ✅ - Alpha Vantage + CoinGecko fallback
- `/trading/analysis/{symbol}` ✅ - GROQ LLM analysis

**NOT Available (return 503):**
- `/trading/portfolio` ❌ - Needs trading service enabled
- `/trading/portfolio/position` ❌ - Needs trading service
- `/trading/alerts` ❌ - Needs trading service
- `/trading/history/{symbol}` ❌ - Needs trading service
- `/trading/technical/{symbol}` ❌ - Needs trading service

**Recommendation:** Either enable trading service OR remove the UI elements that depend on it.

---

## 2. Discovery Page (`/discovery`)

### Header Controls

| Button/Input | Action | Status | Implementation |
|--------------|--------|--------|----------------|
| Neural Search Input | Search trends | ✅ REAL | `/discovery/search` |
| Deep Scan Button | Initiate deep scan | ✅ REAL | `/discovery/scan` |
| Test Drive Button | Find & transform top viral | ✅ REAL | `/video/test-drive` |
| Refresh Button | Reload trends | ✅ REAL | `/discovery/trends` |

### Mode Selector

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Discovery Scanning | Switch to discovery mode | ✅ REAL | Local state |
| AI Synthesis | Switch to generative mode | ✅ REAL | Tier check + state |

### Neural Config Drawer

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| Min Viral Score Slider | Filter threshold | ✅ REAL | Saves to `/settings/` |
| Style Buttons (8 styles) | Select visual style | ✅ REAL | Saves to `/settings/` |
| Exclude Shorts Toggle | Filter shorts | ✅ REAL | Saves to `/settings/` |

### Content Cards Actions

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Add to Queue (Transform) | Transform to video | ✅ REAL | `/video/transform` |
| Analyze Button | AI content analysis | ✅ REAL | `/discovery/analyze` |
| Interact (Like/Comment/Share) | Social interaction | ✅ REAL | `/discovery/interact` + fallback to `/opencli/interact` |
| Keyword Tags | Click to search | ✅ REAL | `/discovery/search` |
| Platform Filter Tabs | Filter by platform | ✅ REAL | Local filter |
| Time Horizon (24h/7d/30d) | Filter by time | ✅ REAL | `/discovery/trends` |
| Niche Tags | Select niche | ✅ REAL | Local state + API |
| Remove Niche (X) | Remove niche | ✅ REAL | `/discovery/niches/{niche}` DELETE |

### Discovery Gaps

| Feature | Status | Issue | Real Implementation |
|---------|--------|-------|---------------------|
| **Deep Analysis Results Display** | ⚠️ PARTIAL | Analysis completes but result display incomplete | `/discovery/analyze` dispatches Celery task but no polling endpoint for status |
| **Transform from Analysis** | ❌ MISSING | No "Create Video" button from analysis results | Should call `/video/transform` with analysis data |
| **Affiliate Link Recommendations** | ❌ NOT CONNECTED | `/monetization/recommend-links` exists but NOT called from Discovery UI | Needs integration |

---

## 3. Creation Page (`/creation`)

### Input Controls

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| Topic Input | Enter topic | ✅ REAL | Local state |
| Niche Select | Select niche | ✅ REAL | From `useNiches` hook |
| Style Select | Select style | ✅ REAL | From `useNiches` hook |
| Duration Slider | Set duration | ✅ REAL | Local state |
| Cinema Mode Toggle | Toggle autonomous | ✅ REAL | Local state |
| Generate Script Button | Generate script | ✅ REAL | `/no-face/generate-script` |
| Launch Cinema Button | Launch cinema | ✅ REAL | `/nexus/compose` |

### Script Workspace

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Language Buttons (7) | Localize script | ✅ REAL | `/no-face/localize` |
| Analyze Retention Button | Validate hook | ✅ REAL | `/no-face/validate-hook` |
| Audio Synthesize (Zap) | Generate voiceover | ✅ REAL | `/no-face/generate-voiceover` |
| Stock Search (Film) | Search stock media | ✅ REAL | `/no-face/search-stock` |
| Image Generate (Wand) | Generate image | ✅ REAL | `/no-face/generate-image` |
| Export Assets Button | Export JSON | ✅ REAL | Client-side blob download |
| Launch Production Button | Start video generation | ✅ REAL | `/nexus/compose` |

### Hook Analysis Panel

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Suggested Hook Options | Apply alternative hook | ✅ REAL | Updates local script state |

### Creation Gaps

| Feature | Status | Issue | Real Implementation |
|---------|--------|-------|---------------------|
| **Story Generation** | ❌ STUB | `/video/generate-story` is stub - no multi-scene generation | Needs actual implementation |
| **Runway/Pika Engines** | ❌ STUB | Configured but no API | Either implement or remove from UI |

---

## 4. Nexus Page (`/nexus`)

### Blueprint Section

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Blueprint Cards | Select blueprint | ✅ REAL | Local state |
| Launch Blueprint Button | Start composition | ✅ REAL | `/nexus/compose` |
| Job Cards | View job status | ✅ REAL | WebSocket + polling |

### AI Agent Chat

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| Chat Input | Send message | ✅ REAL | `/agent/chat` |
| Send Button | Submit message | ✅ REAL | Same as Enter |
| Capabilities Display | View agent capabilities | ✅ REAL | `/agent/capabilities` |

### Persona Lab

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Create Persona Button | Create avatar | ✅ REAL | `/persona/create` |
| Generate Video Button | Generate persona video | ✅ REAL | `/persona/generate` |

### Cluster Manager

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Open Cluster Manager | Configure clusters | ✅ REAL | Local UI |
| Clear Logs Button | Clear log stream | ✅ REAL | Local state |

### Nexus Gaps

| Feature | Status | Issue | Real Implementation |
|---------|--------|-------|---------------------|
| **Cinema Mode** | ⚠️ STUB | Calls `base_auto_creator` - stub implementation | Needs real implementation |
| **Story Factory** | ⚠️ STUB | Calls `base_auto_creator` - stub implementation | Needs real implementation |
| **Persona Video Generation** | ⚠️ PARTIAL | May be incomplete | Needs testing |

---

## 5. Transformation Page (`/transformation`)

### Job Queue

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Add Job Button | Open new job modal | ✅ REAL | Local state |
| Job Card | Select job | ✅ REAL | Local state |
| View Output Button | View video | ✅ REAL | Links to output path |
| Retry Button | Retry failed job | ✅ REAL | `/video/jobs/{id}/retry` |
| Cancel Button | Cancel job | ✅ REAL | `/video/jobs/{id}/cancel` |

### New Job Modal

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| URL Input | Enter video URL | ✅ REAL | Local state |
| Platform Select | Select target | ✅ REAL | Local state |
| Niche Select | Select niche | ✅ REAL | From `useNiches` |
| Generate Thumbnail Toggle | Toggle thumbnail | ✅ REAL | Local state |
| Premium Quality Toggle | Toggle quality | ✅ REAL | Local state |
| Sound Design Toggle | Toggle sound | ✅ REAL | Local state |
| Motion Graphics Toggle | Toggle motion | ✅ REAL | Local state |
| Submit Button | Submit job | ✅ REAL | `/video/transform` |

### Filter Toggles

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Filter Cards | Toggle filter | ✅ REAL | `/settings/filters/{id}/toggle` |

---

## 6. Publishing Page (`/publishing`)

### Platform Connection

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Add Platform (Plus) | Open platform modal | ✅ REAL | Local state |
| Platform Cards (5) | OAuth connect | ✅ REAL | `/publish/auth/{platform}` |
| Account Cards | View linked account | ✅ REAL | From `/publish/accounts` |
| Manage Account Button | Open account modal | ✅ REAL | Local state |
| Re-Authenticate Button | Re-auth OAuth | ✅ REAL | `/publish/auth/{platform}` |
| Disconnect Button | Remove account | ✅ REAL | `/publish/account/{id}` DELETE |

### Deploy Modal

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| Source Asset Select | Select video job | ✅ REAL | From `/video/jobs` |
| Network Protocol Select | Select platform | ✅ REAL | Local state |
| Identity Node Select | Select account | ✅ REAL | From `/publish/accounts` |
| Topic Alpha Select | Select niche | ✅ REAL | From `/discovery/niches` |
| Multi-Node Buttons | Select multiple | ✅ REAL | Local state |
| A/B Title Input | Enter variant B | ✅ REAL | Local state |
| Monetization Toggle | Toggle affiliate | ✅ REAL | Local state |
| Schedule Toggle | Toggle scheduling | ✅ REAL | Local state |
| Schedule Time Input | Set time | ✅ REAL | Local state |
| Initialize Transmission Button | Deploy single | ✅ REAL | `/publish/post` |
| Publish Everywhere Button | Multi-deploy | ✅ REAL | `/publish/post-multi` |
| Generate SEO Package Button | Generate SEO | ✅ REAL | `/publish/package` |

### History & Scheduled

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Sync Button | Refresh stats | ✅ REAL | `/publish/sync/{id}` |
| Retry Button | Retry failed | ✅ REAL | `/publish/retry/{id}` |
| Open URL Button | View on platform | ✅ REAL | Opens external URL |

### Publishing Gaps

| Feature | Status | Issue | Real Implementation |
|---------|--------|-------|---------------------|
| **Scheduled Posts Execution** | ✅ REAL (Backend) | Posts stay "pending" - BUT Celery beat IS configured to process | `check_and_post_scheduled` runs every 5 minutes |
| **TikTok Analytics** | ⚠️ PARTIAL | Method exists but may not work properly | `tiktok_publisher._get_metrics_impl()` exists |
| **TikTok Comments** | ⚠️ PARTIAL | Method exists but may not work properly | `tiktok_publisher._get_comments_impl()` exists |

**Note on Scheduling:** The scheduler IS implemented (`services/optimization/scheduler_tasks.py`):
- `check_and_post_scheduled` task runs every 5 minutes (Celery beat configured)
- Processes `ScheduledPostDB` with status "PENDING" and past `scheduled_time`
- Uses platform publishers to actually upload videos
- **This is NOT a gap - it works!**

---

## 7. Analytics Page (`/analytics`)

### Data Fetching

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Post Selector | Select post | ✅ REAL | From `/analytics/posts` |
| Refresh Button | Reload data | ✅ REAL | `/analytics/report/{id}` |

### Auto-Pilot

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Auto-Pilot Toggle | Enable auto-pilot | ✅ REAL | Local state + interval check |
| Create Test Button | Create A/B test | ✅ REAL | `/ab-testing/ab/tests` |
| Determine Winner Button | Pick winner | ✅ REAL | `/ab-testing/ab/test/{id}/determine-winner` |

### Reports

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Export Report Button | Export data | ✅ REAL | Client-side |
| Copy Button | Copy metrics | ✅ REAL | Clipboard API |
| Apply Insight Button | Apply suggestion | ✅ REAL | `/analytics/apply-insight/{id}` |

### Analytics Gaps

| Feature | Status | Issue | Real Implementation |
|---------|--------|-------|---------------------|
| **A/B Testing** | ⚠️ PARTIAL | Endpoint works BUT has bugs in UI integration | `/ab-testing/*` endpoints exist and are functional |
| **Apply Insight** | ⚠️ PARTIAL | Endpoint exists but may not be fully connected | `/analytics/apply-insight/{id}` exists |

**A/B Testing Status:**
- `/ab-testing/test/start` ✅ - Creates test
- `/ab-testing/test/{test_id}` ✅ - Gets results
- `/ab-testing/record/{test_id}/event` ✅ - Records events
- `/ab-testing/test/{test_id}/determine-winner` ✅ - Determines winner with proper statistical significance (z-test, p-value)
- **This is NOT a gap - it works!**

---

## 8. Empire Page (`/empire`)

### Sentinel Status

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Refresh Button | Refresh status | ✅ REAL | `/no-face/sentinel/status` |

### Strategy Cloning

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Clone Strategy Button | Open clone modal | ✅ REAL | Local state |
| Auto-Publish Toggle | Toggle auto-publish | ✅ REAL | Local state |
| Execute Clone Button | Clone strategy | ✅ REAL | `/monetization/empire/clone` |

### Affiliate Links

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Add Link Button | Add new link | ✅ REAL | `/monetization/links` |
| Delete Link (Trash) | Remove link | ✅ REAL | `/monetization/links/{id}` DELETE |

### Revenue & Recommendations

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Refresh Metrics Button | Refresh revenue | ✅ REAL | `/monetization/empire/metrics` |
| Recommend Button | Get recommendations | ✅ REAL | `/monetization/recommend` |
| Shopify Sync Button | Sync products | ✅ REAL | `/monetization/commerce/sync` |

### Auto-Merch

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Generate Merch Button | Generate products | ✅ REAL | `/monetization/auto-merch` |

### Empire Gaps

| Feature | Status | Issue | Real Implementation |
|---------|--------|-------|---------------------|
| **Shopify Sync** | ⚠️ STUB | Stub implementation | `/monetization/commerce/sync` exists but may not fully work |
| **Auto-Merch** | ⚠️ STUB | Stub - no Shopify integration | `/monetization/auto-merch` exists but may be stub |

---

## 9. Settings Page (`/settings`)

### Profile Settings

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| Telegram Chat ID Input | Set Telegram | ✅ REAL | Saves to user profile |
| WhatsApp Number Input | Set WhatsApp | ✅ REAL | Saves to user profile |
| Save Profile Button | Save changes | ✅ REAL | `/auth/me` PATCH |

### API Keys

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| API Key Inputs | Enter keys | ✅ REAL | Form state |
| Show/Hide Toggle | Toggle visibility | ✅ REAL | Local state |
| Save Keys Button | Save all keys | ✅ REAL | `/settings/bulk` |

### Engine Settings

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| Scan Frequency Select | Set frequency | ✅ REAL | Form state |
| Voice Engine Select | Select TTS | ✅ REAL | Form state |
| AI Video Provider Select | Select provider | ✅ REAL | Form state |
| Save Settings Button | Save all | ✅ REAL | `/settings/bulk` |

### Monetization Settings

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| Strategy Select | Set strategy | ✅ REAL | Form state |
| Monetization Mode Select | Set mode | ✅ REAL | Form state |
| Aggression Slider | Set level | ✅ REAL | Form state |
| Platform URLs | Set URLs | ✅ REAL | Form state |
| Shopify Token Input | Set token | ✅ REAL | Form state |

### Subscription

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| View Plans Button | View pricing | ✅ REAL | Opens pricing modal |
| Subscribe Button | Start subscription | ✅ REAL | Creates checkout session |
| Cancel Subscription Button | Cancel plan | ✅ REAL | `/billing/cancel` |

### Password

| Control | Action | Status | Implementation |
|---------|--------|--------|----------------|
| Current Password Input | Enter current | ✅ REAL | Form state |
| New Password Input | Enter new | ✅ REAL | Form state |
| Confirm Password Input | Confirm | ✅ REAL | Form state |
| Change Password Button | Submit change | ✅ REAL | `/auth/change-password` |

### Settings Gaps

| Feature | Status | Issue | Real Implementation |
|---------|--------|-------|---------------------|
| **WhatsApp Integration** | ⚠️ STUB | Configured but no real webhook handler | Field exists but no backend implementation |
| **Telegram Bot** | ⚠️ STUB | Configured but no real bot | Field exists but no backend implementation |

---

## 10. Credits Page (`/credits`)

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Purchase Credits Button | Buy credits | ✅ REAL | Creates Stripe session |
| View History Button | View transaction history | ✅ REAL | From `/credits/history` |

**Status:** ✅ FULLY IMPLEMENTED

---

## 11. Autonomous Page (`/autonomous`)

| Button | Action | Status | Implementation |
|--------|--------|--------|----------------|
| Start Autonomous Button | Launch autonomous mode | ✅ REAL | Calls agent endpoints |
| Stop Button | Stop autonomous | ✅ REAL | Calls agent endpoints |
| Mode Selectors | Configure modes | ✅ REAL | Local state |

**Status:** ✅ FULLY IMPLEMENTED

---

## 12. Use Case Scenario Coverage

### Content Discovery Pipeline

| Scenario | Status | Implementation |
|----------|--------|----------------|
| Search trends by keyword | ✅ REAL | `/discovery/search` |
| Browse by niche | ✅ REAL | `/discovery/niches` |
| Analyze content with AI | ✅ REAL | `/discovery/analyze` |
| Monitor niches continuously | ✅ REAL | Sentinel + Celery beat |
| Transform from discovery | ✅ REAL | `/video/transform` |
| Test drive top viral | ✅ REAL | `/video/test-drive` |
| **Recommend affiliate links** | ❌ NOT CONNECTED | Endpoint exists but not called |

### Video Generation Pipeline

| Scenario | Status | Implementation |
|----------|--------|----------------|
| Transform existing video | ✅ REAL | `/video/transform` |
| Generate from text (veo3) | ✅ REAL | `/video/generate` |
| Generate from text (wan2.2) | ⚠️ STUB | Engine stub |
| Story generation | ⚠️ STUB | Stub implementation |
| Add voiceover | ✅ REAL | `/no-face/generate-voiceover` |
| Add subtitles | ✅ REAL | `/video/add-subtitles` |
| Quality upscaling | ✅ REAL | `/video/upscale` |

### Publishing Pipeline

| Scenario | Status | Implementation |
|----------|--------|----------------|
| OAuth connect YouTube | ✅ REAL | `/publish/auth/youtube` |
| OAuth connect TikTok | ✅ REAL | `/publish/auth/tiktok` |
| OAuth connect Instagram | ✅ REAL | `/publish/auth/instagram` |
| OAuth connect LinkedIn | ✅ REAL | `/publish/auth/linkedin` |
| OAuth connect X | ✅ REAL | `/publish/auth/x` |
| Upload to YouTube | ✅ REAL | YouTube API |
| Upload to TikTok | ✅ REAL | TikTok API |
| Schedule post | ✅ REAL | `/publish/schedule` |
| **Execute scheduled post** | ✅ REAL | Celery beat (every 5 min) |
| Retry failed post | ✅ REAL | `/publish/retry/{id}` |
| Get YouTube analytics | ✅ REAL | YouTube API |
| **Get TikTok analytics** | ⚠️ PARTIAL | Method exists but may fail |
| **Get TikTok comments** | ⚠️ PARTIAL | Method exists but may fail |

### Monetization Pipeline

| Scenario | Status | Implementation |
|----------|--------|----------------|
| Add affiliate link | ✅ REAL | `/monetization/links` |
| Track revenue | ✅ REAL | `/monetization/empire/metrics` |
| Clone strategy | ✅ REAL | `/monetization/empire/clone` |
| Get recommendations | ✅ REAL | `/monetization/recommend` |
| Shopify sync | ⚠️ STUB | Stub implementation |
| Auto-merch generate | ⚠️ STUB | Stub implementation |

---

## 13. Critical Gaps Summary (Real-First Priority)

### Tier 1: MUST HAVE (Launch Critical)

| # | Feature | Gap | Solution |
|---|---------|-----|----------|
| 1 | **Trading Page** | UI depends on disabled service | Either enable `ENABLE_TRADING=True` or remove dependent UI elements |
| 2 | **Affiliate Link Recommendations** | Not called from Discovery UI | Connect `/monetization/recommend-links` to Discovery/Publishing flow |
| 3 | **Story Generation** | Stub implementation | Implement actual multi-scene story generation |
| 4 | **Runway/Pika Engines** | Stub + no UI toggle | Either implement or remove from engine selection |

### Tier 2: SHOULD HAVE (Feature Complete)

| # | Feature | Gap | Solution |
|---|---------|-----|----------|
| 5 | **TikTok Analytics** | Method exists but may fail | Test and fix `_get_metrics_impl()` |
| 6 | **TikTok Comments** | Method exists but may fail | Test and fix `_get_comments_impl()` |
| 7 | **Cinema Mode** | Stub implementation | Implement `base_auto_creator` or remove |
| 8 | **Story Factory** | Stub implementation | Implement `base_auto_creator` or remove |

### Tier 3: NICE TO HAVE (Polish)

| # | Feature | Gap | Solution |
|---|---------|-----|----------|
| 9 | **Shopify Auto-Merch** | Stub implementation | Complete or remove |
| 10 | **WhatsApp Integration** | No webhook handler | Implement bot or remove field |
| 11 | **Telegram Bot** | No webhook handler | Implement bot or remove field |
| 12 | **Deep Analysis Display** | Incomplete result display | Add polling + better UI |

---

## 14. Implementation Recommendation

### Priority: Real First, Fallback Second

The current codebase uses `withRealFallback` pattern correctly - it provides graceful degradation. BUT the issue is many fallbacks are permanent states rather than temporary failures.

**Action Items:**

1. **Trading:** Either implement real trading service or remove portfolio/alerts/history/technical UI
2. **Discovery → Affiliate:** Call `/monetization/recommend-links` from Discovery UI
3. **Story Generation:** Implement real multi-scene generation or hide UI option
4. **Runway/Pika:** Implement real API integration or remove from dropdown
5. **TikTok Analytics:** Test and fix metrics fetching
6. **Cinema/Story Factory:** Implement or remove from blueprints

**The key insight:** Don't leave stubs as "placeholders" - either implement real solution or remove the UI entirely. Waiting for manual conversion creates technical debt.

---

*End of Gap Analysis - Real-First Priority*