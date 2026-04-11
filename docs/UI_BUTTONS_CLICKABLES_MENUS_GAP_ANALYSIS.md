# Viral Forge - UI/Buttons/Clickables/Menus Gap Analysis

**Date:** 2026-04-08  
**Analyst:** Kilo Code Review  
**Focus:** UI/Buttons/Clickables/Menus Coverage & Real Implementation Status

---

## Executive Summary

This analysis maps every clickable element in the Viral Forge dashboard to its implementation status. The goal is to identify which buttons/menus actually work vs. which are dummies/simulations/placeholders waiting for real implementation.

**Priority Rule Applied:** Real implementation FIRST, fallback as SECONDARY only when real fails - NOT waiting for manual conversion.

---

## 1. Navigation & Shell

### Sidebar (Main Menu)
| Menu Item | Route | Status | Implementation |
|-----------|-------|--------|----------------|
| Dashboard | `/` | ✅ WORKING | Real - fetches user data, job stats |
| Discovery | `/discovery` | ✅ WORKING | Real - calls `/discovery/trends`, `/discovery/search` |
| Creation | `/creation` | ✅ WORKING | Real - calls `/no-face/generate-script` |
| Nexus Flow | `/nexus` | ✅ WORKING | Real - calls `/nexus/blueprints`, `/nexus/compose` |
| Autonomous | `/autonomous` | ✅ WORKING | Real - agent orchestration |
| Transformation | `/transformation` | ✅ WORKING | Real - calls `/video/transform`, `/video/jobs` |
| Publishing | `/publishing` | ✅ WORKING | Real - OAuth flows, `/publish/post` |
| Analytics | `/analytics` | ✅ WORKING | Real - `/analytics/report/{id}` |
| Empire | `/empire` | ✅ WORKING | Real - `/monetization/links`, `/monetization/empire/clone` |
| Credits | `/credits` | ✅ WORKING | Real - credit balance & purchase |
| Trading | `/trading` | ⚠️ STUB | No real API - shows mock data |
| Settings | `/settings` | ✅ WORKING | Real - `/settings/bulk` |
| Mobile Nav | - | ✅ WORKING | Subset of main nav |

---

## 2. Discovery Page (`/discovery`)

### Header Section
| Button/Clickable | Action | Implementation Status |
|------------------|--------|----------------------|
| Neural Search Input | Search trends | ✅ REAL - calls `/discovery/search` |
| Deep Scan Button | Initiate deep scan | ✅ REAL - calls `/discovery/scan` |
| Test Drive Button | Find & transform top viral | ✅ REAL - calls `/video/test-drive` |
| Refresh Button | Reload trends | ✅ REAL - calls `/discovery/trends` |

### Mode Selector
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Discovery Scanning | Switch to discovery mode | ✅ REAL - local state |
| AI Synthesis | Switch to generative mode | ✅ REAL - tier check + state |

### Neural Config Drawer
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| Min Viral Score Slider | Filter threshold | ✅ REAL - saves to `/settings/` |
| Style Buttons (8 styles) | Select visual style | ✅ REAL - saves to `/settings/` |
| Exclude Shorts Toggle | Filter shorts | ✅ REAL - saves to `/settings/` |

### Content Cards
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Add to Queue (Transform) | Transform to video | ✅ REAL - calls `/video/transform` |
| Analyze Button | AI content analysis | ✅ REAL - calls `/discovery/analyze` |
| Interact (Like/Comment/Share) | Social interaction | ✅ REAL - calls `/discovery/interact` + fallback to `/opencli/interact` |
| Keyword Tags | Click to search | ✅ REAL - calls `/discovery/search` |
| Platform Filter Tabs | Filter by platform | ✅ REAL - local filter |
| Time Horizon (24h/7d/30d) | Filter by time | ✅ REAL - calls `/discovery/trends` |
| Niche Tags | Select niche | ✅ REAL - local state + API |
| Remove Niche (X) | Remove niche | ✅ REAL - calls `/discovery/niches/{niche}` DELETE |

---

## 3. Creation Page (`/creation`)

### Input Controls
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| Topic Input | Enter topic | ✅ REAL - local state |
| Niche Select | Select niche | ✅ REAL - from `useNiches` hook |
| Style Select | Select style | ✅ REAL - from `useNiches` hook |
| Duration Slider | Set duration | ✅ REAL - local state |
| Cinema Mode Toggle | Toggle autonomous | ✅ REAL - local state |
| Generate Script Button | Generate script | ✅ REAL - calls `/no-face/generate-script` |
| Launch Cinema Button | Launch cinema | ✅ REAL - calls `/nexus/compose` |

### Script Workspace
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Language Buttons (ES/DE/FR/IT/PT/JP/ZH) | Localize script | ✅ REAL - calls `/no-face/localize` |
| Analyze Retention Button | Validate hook | ✅ REAL - calls `/no-face/validate-hook` |
| Audio Synthesize (Zap icon) | Generate voiceover | ✅ REAL - calls `/no-face/generate-voiceover` |
| Stock Search (Film icon) | Search stock media | ✅ REAL - calls `/no-face/search-stock` |
| Image Generate (Wand icon) | Generate image | ✅ REAL - calls `/no-face/generate-image` |
| Export Assets Button | Export JSON | ✅ REAL - client-side blob download |
| Launch Production Button | Start video generation | ✅ REAL - calls `/nexus/compose` |

### Hook Analysis Panel
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Suggested Hook Options | Apply alternative hook | ✅ REAL - updates local script state |

---

## 4. Nexus Page (`/nexus`)

### Blueprint Section
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Blueprint Cards | Select blueprint | ✅ REAL - local state |
| Launch Blueprint Button | Start composition | ✅ REAL - calls `/nexus/compose` |
| Job Cards | View job status | ✅ REAL - WebSocket + polling |

### AI Agent Chat
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| Chat Input | Send message | ✅ REAL - calls `/agent/chat` |
| Send Button | Submit message | ✅ REAL - same as Enter |
| Capabilities Display | View agent capabilities | ✅ REAL - calls `/agent/capabilities` |

### Persona Lab
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Create Persona Button | Create avatar | ✅ REAL - calls `/persona/create` |
| Generate Video Button | Generate persona video | ✅ REAL - calls `/persona/generate` |

### Cluster Manager
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Open Cluster Manager | Configure clusters | ✅ REAL - local UI |
| Clear Logs Button | Clear log stream | ✅ REAL - local state |

---

## 5. Transformation Page (`/transformation`)

### Job Queue
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Add Job Button | Open new job modal | ✅ REAL - local state |
| Job Card | Select job | ✅ REAL - local state |
| View Output Button | View video | ✅ REAL - links to output path |
| Retry Button | Retry failed job | ✅ REAL - calls `/video/jobs/{id}/retry` |
| Cancel Button | Cancel job | ✅ REAL - calls `/video/jobs/{id}/cancel` |

### New Job Modal
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| URL Input | Enter video URL | ✅ REAL - local state |
| Platform Select | Select target | ✅ REAL - local state |
| Niche Select | Select niche | ✅ REAL - from `useNiches` |
| Generate Thumbnail Toggle | Toggle thumbnail | ✅ REAL - local state |
| Premium Quality Toggle | Toggle quality | ✅ REAL - local state |
| Sound Design Toggle | Toggle sound | ✅ REAL - local state |
| Motion Graphics Toggle | Toggle motion | ✅ REAL - local state |
| Submit Button | Submit job | ✅ REAL - calls `/video/transform` |

### Filter Toggles
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Filter Cards | Toggle filter | ✅ REAL - calls `/settings/filters/{id}/toggle` |

---

## 6. Publishing Page (`/publishing`)

### Platform Connection
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Add Platform (Plus) | Open platform modal | ✅ REAL - local state |
| Platform Cards (YouTube/TikTok/Instagram/X/LinkedIn) | OAuth connect | ✅ REAL - calls `/publish/auth/{platform}` |
| Account Cards | View linked account | ✅ REAL - shows from `/publish/accounts` |
| Manage Account Button | Open account modal | ✅ REAL - local state |
| Re-Authenticate Button | Re-auth OAuth | ✅ REAL - calls `/publish/auth/{platform}` |
| Disconnect Button | Remove account | ✅ REAL - calls `/publish/account/{id}` DELETE |

### Deploy Modal
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| Source Asset Select | Select video job | ✅ REAL - from `/video/jobs` |
| Network Protocol Select | Select platform | ✅ REAL - local state |
| Identity Node Select | Select account | ✅ REAL - from `/publish/accounts` |
| Topic Alpha Select | Select niche | ✅ REAL - from `/discovery/niches` |
| Multi-Node Buttons | Select multiple | ✅ REAL - local state |
| A/B Title Input | Enter variant B | ✅ REAL - local state |
| Monetization Toggle | Toggle affiliate | ✅ REAL - local state |
| Schedule Toggle | Toggle scheduling | ✅ REAL - local state |
| Schedule Time Input | Set time | ✅ REAL - local state |
| Initialize Transmission Button | Deploy single | ✅ REAL - calls `/publish/post` |
| Publish Everywhere Button | Multi-deploy | ✅ REAL - calls `/publish/post-multi` |
| Generate SEO Package Button | Generate SEO | ✅ REAL - calls `/publish/package` |

### History & Scheduled
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Sync Button | Refresh stats | ✅ REAL - calls `/publish/sync/{id}` |
| Retry Button | Retry failed | ✅ REAL - calls `/publish/retry/{id}` |
| Open URL Button | View on platform | ✅ REAL - opens external URL |

---

## 7. Analytics Page (`/analytics`)

### Data Fetching
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Post Selector | Select post | ✅ REAL - from `/analytics/posts` |
| Refresh Button | Reload data | ✅ REAL - calls `/analytics/report/{id}` |

### Auto-Pilot
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Auto-Pilot Toggle | Enable auto-pilot | ✅ REAL - local state + interval check |
| Create Test Button | Create A/B test | ✅ REAL - calls `/ab-testing/ab/tests` |
| Determine Winner Button | Pick winner | ✅ REAL - calls `/ab-testing/ab/test/{id}/determine-winner` |

### Reports
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Export Report Button | Export data | ✅ REAL - client-side |
| Copy Button | Copy metrics | ✅ REAL - clipboard API |
| Apply Insight Button | Apply suggestion | ✅ REAL - calls `/analytics/apply-insight/{id}` |

---

## 8. Empire Page (`/empire`)

### Sentinel Status
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Refresh Button | Refresh status | ✅ REAL - calls `/no-face/sentinel/status` |

### Strategy Cloning
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Clone Strategy Button | Open clone modal | ✅ REAL - local state |
| Auto-Publish Toggle | Toggle auto-publish | ✅ REAL - local state |
| Execute Clone Button | Clone strategy | ✅ REAL - calls `/monetization/empire/clone` |

### Affiliate Links
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Add Link Button | Add new link | ✅ REAL - calls `/monetization/links` |
| Delete Link (Trash) | Remove link | ✅ REAL - calls `/monetization/links/{id}` DELETE |

### Revenue & Recommendations
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Refresh Metrics Button | Refresh revenue | ✅ REAL - calls `/monetization/empire/metrics` |
| Recommend Button | Get recommendations | ✅ REAL - calls `/monetization/recommend` |
| Shopify Sync Button | Sync products | ✅ REAL - calls `/monetization/commerce/sync` |

### Auto-Merch
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Generate Merch Button | Generate products | ✅ REAL - calls `/monetization/auto-merch` |

---

## 9. Settings Page (`/settings`)

### Profile Settings
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| Telegram Chat ID Input | Set Telegram | ✅ REAL - saves to user profile |
| WhatsApp Number Input | Set WhatsApp | ✅ REAL - saves to user profile |
| Save Profile Button | Save changes | ✅ REAL - calls `/auth/me` PATCH |

### API Keys
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| API Key Inputs | Enter keys | ✅ REAL - form state |
| Show/Hide Toggle | Toggle visibility | ✅ REAL - local state |
| Save Keys Button | Save all keys | ✅ REAL - calls `/settings/bulk` |

### Engine Settings
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| Scan Frequency Select | Set frequency | ✅ REAL - form state |
| Voice Engine Select | Select TTS | ✅ REAL - form state |
| AI Video Provider Select | Select provider | ✅ REAL - form state |
| Save Settings Button | Save all | ✅ REAL - calls `/settings/bulk` |

### Monetization Settings
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| Strategy Select | Set strategy | ✅ REAL - form state |
| Monetization Mode Select | Set mode | ✅ REAL - form state |
| Aggression Slider | Set level | ✅ REAL - form state |
| Platform URLs | Set URLs | ✅ REAL - form state |
| Shopify Token Input | Set token | ✅ REAL - form state |

### Subscription
| Button | Action | Implementation Status |
|--------|--------|----------------------|
| View Plans Button | View pricing | ✅ REAL - opens pricing modal |
| Subscribe Button | Start subscription | ✅ REAL - creates checkout session |
| Cancel Subscription Button | Cancel plan | ✅ REAL - calls `/billing/cancel` |

### Password
| Control | Action | Implementation Status |
|---------|--------|----------------------|
| Current Password Input | Enter current | ✅ REAL - form state |
| New Password Input | Enter new | ✅ REAL - form state |
| Confirm Password Input | Confirm | ✅ REAL - form state |
| Change Password Button | Submit change | ✅ REAL - calls `/auth/change-password` |

---

## 10. Trading Page (`/trading`)

### Status: ❌ STUB - NO REAL IMPLEMENTATION

| Button/Element | Expected Action | Status |
|-----------------|-----------------|--------|
| Trading Dashboard | View trading stats | ❌ DUMMY - no API |
| Execute Trade Button | Execute trade | ❌ DUMMY - no API |
| Portfolio Display | Show holdings | ❌ DUMMY - no API |

**Gap:** Trading service exists but is disabled (`ENABLE_TRADING=False`), no API route, no real data.

---

## 11. Credits Page (`/credits`)

| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Purchase Credits Button | Buy credits | ✅ REAL - creates Stripe session |
| View History Button | View transaction history | ✅ REAL - from `/credits/history` |

---

## 12. Autonomous Page (`/autonomous`)

| Button | Action | Implementation Status |
|--------|--------|----------------------|
| Start Autonomous Button | Launch autonomous mode | ✅ REAL - calls agent endpoints |
| Stop Button | Stop autonomous | ✅ REAL - calls agent endpoints |
| Mode Selectors | Configure modes | ✅ REAL - local state |

---

## Summary: Gap Analysis by Severity

### CRITICAL GAPS (No Real Implementation)

| Page | Feature | Issue | Priority |
|------|---------|-------|----------|
| Trading | All | No API, disabled | HIGH |
| Discovery | Deep Analysis Results Display | Analysis completes but result display incomplete | HIGH |
| Publishing | Scheduled Posts Execution | Posts stay "pending" - no cron worker | HIGH |
| Publishing | TikTok Analytics | No analytics fetch for TikTok | HIGH |
| Empire | Auto-Merch | Stub - no Shopify integration | HIGH |

### HIGH GAPS (Partial Implementation)

| Page | Feature | Issue | Priority |
|------|---------|-------|----------|
| Creation | Story Generation | `/video/generate-story` is stub | HIGH |
| Nexus | Cinema Mode | Calls stub `base_auto_creator` | HIGH |
| Analytics | A/B Test Variant Tracking | Not fully working | HIGH |
| Discovery | Affiliate Link Recommendations | Not called from UI | MEDIUM |
| Discovery | Runway/Pika Engines | Configured but no API | MEDIUM |

### MEDIUM GAPS (UI Exists, Needs Testing)

| Page | Feature | Issue | Priority |
|------|---------|-------|----------|
| Settings | WhatsApp Integration | Configured, no real webhook | LOW |
| Settings | Telegram Bot | Configured, no real bot | LOW |
| Empire | Shopify Sync | Stub implementation | MEDIUM |
| Nexus | Persona Video Generation | May be incomplete | LOW |

---

## Implementation Priority Matrix

### Tier 1: Must Have Working (Launch Critical)
1. **Trading** - Either implement real or remove UI
2. **Scheduled Publishing** - Implement cron worker to execute posts
3. **Deep Analysis → Transform** - Complete the flow from analysis to video creation
4. **TikTok Analytics** - Add stats fetch or remove claim

### Tier 2: Should Have Working (Feature Complete)
5. **A/B Testing** - Fix variant tracking and winner determination
6. **Affiliate Recommendations** - Connect to discovery/publishing flow
7. **Story Generation** - Complete or hide UI option

### Tier 3: Nice to Have (Polish)
8. **Runway/Pika Integration** - Implement or remove from engine list
9. **Shopify Auto-Merch** - Complete stub or remove
10. **WhatsApp/Telegram** - Implement bot or remove fields

---

## Recommendation: Real-First Implementation Plan

Instead of waiting for manual conversion from dummies to real:

1. **For Trading**: Implement real API or remove page entirely
2. **For Scheduled Posts**: Add Celery beat task to process `ScheduledPostDB` records
3. **For Story Generation**: Implement actual story multi-scene generation
4. **For TikTok**: Add `tiktok_publisher.get_analytics()` method
5. **For A/B Testing**: Fix `/ab-testing/ab/test/{id}/determine-winner` endpoint

The `withRealFallback` pattern is GOOD - it provides graceful degradation. But the FALLBACK should be a last resort, not a permanent state.

---

*End of Gap Analysis*
