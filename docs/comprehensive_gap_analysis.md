# Viral Forge - Comprehensive UI/Buttons/Clickables & Use Case Gap Analysis

**Date:** 2026-04-04  
**Version:** 2.0 (Combined)
**Priority:** Real Implementation First, Fallback as Safety Net

---

## Executive Summary

This document combines two analyses:
1. **UI/Buttons/Clickables/Menus Gap Analysis** - Complete mapping of all frontend interactions
2. **Missing Use Case Links** - Gaps between documented use cases and actual implementation

**Philosophy:** Implement real solutions first. Use dummies/simulations/placeholders ONLY as fallback when real implementation fails - not as a waiting point for the user to implement.

---

## PART A: UI/Buttons/Clickables - Complete Coverage Map

### A.1 Sidebar Navigation (COMPLETE ✅)

| Menu Item | Route | Implementation | Status |
|-----------|-------|----------------|--------|
| Dashboard | `/` | ✅ Real API | COMPLETE |
| Discovery | `/discovery` | ✅ Real API + fallback | COMPLETE |
| Creation | `/creation` | ✅ Real API | COMPLETE |
| Nexus Flow | `/nexus` | ✅ Real API | COMPLETE |
| Autonomous | `/autonomous` | ⚠️ Verify | VERIFY |
| Transformation | `/transformation` | ✅ Real API | COMPLETE |
| Publishing | `/publishing` | ✅ Real API | COMPLETE |
| Analytics | `/analytics` | ✅ Real API + fallback | COMPLETE |
| Empire | `/empire` | ✅ Real API | COMPLETE |
| Credits | `/credits` | ⚠️ Verify | VERIFY |
| Trading | `/trading` | ⚠️ Verify | VERIFY |
| Settings | `/settings` | ⚠️ Verify | VERIFY |

---

## PART B: Use Case Gap Analysis - Covered vs Uncovered

### B.1 CONTENT DISCOVERY (UC-1)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| Search Trending | ✅ `/discovery/search` | ✅ | COVERED | - |
| Browse By Niche | ✅ Niches list | ✅ `/discovery/niches` | COVERED | - |
| Analyze with AI | ✅ Analyze button | ✅ `/discovery/analyze` | COVERED | HIGH |
| Monitor Niches | ⚠️ Display only | ❌ No continuous monitoring | **UNCOVERED** | HIGH |
| Deep Scan | ✅ Deep Scan button | ✅ `/discovery/scan` | COVERED | - |

**Gap:** No continuous niche monitoring backend - only manual trigger

---

### B.2 VIDEO GENERATION (UC-2)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| Transform Existing | ✅ `/transformation` page | ✅ `/video/transform` | COVERED | - |
| AI Generate from Text | ✅ `/discovery` generative mode | ⚠️ Stub implementations | **PARTIAL** | HIGH |
| Story Generate | ✅ Story mode toggle | ❌ Stub | **UNCOVERED** | HIGH |
| Test Drive Quick Preview | ✅ Test Drive button | ✅ `/video/test-drive` | COVERED | - |

**Gap:** Most AI generation engines are stubs (veo3, wan2.2, hunyuan, etc. not really implemented)

---

### B.3 VIDEO ENHANCEMENT (UC-3)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| Voice Overdub (TTS) | ✅ Per-segment buttons | ✅ `/no-face/generate-voiceover` | COVERED | - |
| Face Animation (No-Face) | ✅ Nexus cinema mode | ⚠️ Stub | **PARTIAL** | HIGH |
| Background Removal | ✅ Filter toggles | ❌ Not implemented | **UNCOVERED** | MEDIUM |
| Sound Design | ✅ Toggle in transformation | ❌ Disabled | **UNCOVERED** | MEDIUM |
| Music Addition | ⚠️ Toggle exists | ❌ Not implemented | **UNCOVERED** | MEDIUM |
| Subtitle Generation | ❌ No UI | ❌ Not implemented | **UNCOVERED** | MEDIUM |
| Thumbnail Generation | ✅ Toggle in transformation | ⚠️ Partial | PARTIAL | LOW |
| Quality Upscaling | ❌ No UI | ❌ Not implemented | **UNCOVERED** | LOW |

---

### B.4 NEXUS COMPOSITION (UC-4)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| Assemble from Segments | ✅ Nexus pipeline | ⚠️ Partial | PARTIAL | - |
| Cinema Mode Autonomous | ✅ Cinema toggle | ❌ Stub (base_auto_creator) | **UNCOVERED** | HIGH |
| Story Factory | ✅ Blueprint selection | ❌ Stub | **UNCOVERED** | HIGH |
| Blueprint Templates | ✅ Blueprint dropdown | ✅ `/nexus/blueprints` | COVERED | - |

**Gap:** Cinema mode and story factory call stub implementations that don't actually generate content

---

### B.5 PUBLISHING (UC-5)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| YouTube Upload OAuth | ✅ Platform modal | ✅ OAuth flow | COVERED | - |
| YouTube Upload | ✅ Deploy modal | ✅ `/publish/post` | COVERED | - |
| TikTok Upload OAuth | ✅ Platform modal | ⚠️ Partial | PARTIAL | HIGH |
| TikTok Upload | ✅ Deploy modal | ⚠️ May be incomplete | PARTIAL | HIGH |
| Schedule Posts | ✅ Toggle + datetime | ⚠️ No worker | **PARTIAL** | HIGH |
| A/B Testing Variants | ✅ Variant B input | ⚠️ Partial | PARTIAL | MEDIUM |

**Gaps:** 
- TikTok publisher may be incomplete
- No cron worker to execute scheduled posts
- A/B variant tracking not working properly

---

### B.6 MONETIZATION (UC-6)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| Affiliate Links CRUD | ✅ Empire page | ✅ `/monetization/links` | COVERED | - |
| Revenue Tracking | ✅ Empire metrics | ✅ `/monetization/report` | COVERED | - |
| Empire Building/Cloning | ✅ Clone button | ✅ `/monetization/empire/clone` | COVERED | - |
| Auto-Merch Generation | ✅ Auto-Merch section | ❌ Stub (commerce stub) | **UNCOVERED** | HIGH |
| Product Recommendations | ✅ AI Recommender | ✅ `/monetization/recommend-links` | COVERED | - |
| Promo Script Generation | ✅ Promo section | ✅ `/monetization/promo/generate` | COVERED | - |
| Shopify Commerce Sync | ✅ Sync button | ⚠️ Stub | **PARTIAL** | HIGH |

**Gaps:**
- Auto-merch calls stub commerce service
- Shopify integration is stub only

---

### B.7 ANALYTICS (UC-7)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| Performance Reports | ✅ Metrics grid | ✅ `/analytics/report/{id}` | COVERED | - |
| Insights Generation | ✅ Insights section | ✅ `/analytics/insights/{id}` | COVERED | - |
| Monetization Suggestions | ✅ "Execute Injection" | ⚠️ Returns but not applied | PARTIAL | MEDIUM |
| Storage Stats | ⚠️ Display only | ❌ Not implemented | **UNCOVERED** | LOW |

**Gap:** Monetization suggestions returned but not connected to apply to content generation

---

### B.8 SUBSCRIPTION & BILLING (UC-8)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| Subscribe Plan | ✅ Settings billing tab | ✅ Stripe checkout | COVERED | - |
| View Subscription | ✅ Settings | ✅ `/billing/subscription` | COVERED | - |
| Cancel Subscription | ⚠️ No UI | ⚠️ Partial | **UNCOVERED** | MEDIUM |
| Webhook Handling | ❌ No UI | ✅ Stripe webhook | COVERED | - |

---

### B.9 USER MANAGEMENT (UC-9)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| Register | ✅ `/register` page | ✅ `/auth/register` | COVERED | - |
| Login | ✅ `/login` page | ✅ `/auth/login` | COVERED | - |
| OAuth (Google) | ✅ Login page | ✅ OAuth flow | COVERED | - |
| Settings Management | ✅ `/settings` page | ⚠️ Partial | PARTIAL | - |

---

### B.10 ADMIN OPERATIONS (UC-10)

| Sub-Use Case | Frontend | Backend | Status | Priority |
|--------------|-----------|---------|--------|----------|
| User Management | ✅ Admin page | ⚠️ Partial | PARTIAL | - |
| System Monitoring | ⚠️ Limited | ✅ Prometheus metrics | PARTIAL | - |
| Audit Logs | ❌ No UI | ✅ `/admin/logs` (maybe) | **UNCOVERED** | LOW |
| Content Moderation | ❌ No UI | ❌ Not implemented | **UNCOVERED** | MEDIUM |

---

## PART C: Critical Gaps - Priority Order

### 🔴 CRITICAL (Must Fix Before Production)

| Gap ID | Use Case | Issue | Solution | Owner |
|--------|----------|-------|----------|-------|
| C1 | Publishing - Scheduling | No worker executes scheduled posts | Implement scheduler worker in `services/optimization/scheduler_tasks.py` | Backend |
| C2 | Video Gen - AI Engines | Most engines are stubs | Either implement real integration or remove from UI | Backend |
| C3 | Nexus - Cinema Mode | base_auto_creator is stub | Implement real composition logic | Backend |
| C4 | Discovery - Monitor | No continuous monitoring | Implement Celery periodic task | Backend |
| C5 | TikTok - Publishing | May be incomplete | Verify and complete tiktok_publisher.py | Backend |

### 🟠 HIGH Priority

| Gap ID | Use Case | Issue | Solution | Owner |
|--------|----------|-------|----------|-------|
| H1 | Monetization - Auto-Merch | commerce_service is stub | Implement real Shopify API integration | Backend |
| H2 | Analytics - Apply Suggestions | Not connected to generation | Wire up apply button to generation | Frontend |
| H3 | A/B Testing - Variant Tracking | Not working properly | Fix variant tracking endpoints | Backend |
| H4 | Video Enhancement - Sound Design | Toggle exists but disabled | Enable and implement service | Backend |
| H5 | Story Generation | Stub implementation | Implement or hide from UI | Backend |

### 🟡 MEDIUM Priority

| Gap ID | Use Case | Issue | Solution | Owner |
|--------|----------|-------|----------|-------|
| M1 | Settings - Neural Config | Changes don't persist | Add API to save/load config | Fullstack |
| M2 | Publishing - Toggles | Monetization/Scheduling don't persist | Add persistence for toggles | Frontend |
| M3 | Billing - Cancel | No cancel UI | Add cancel subscription flow | Frontend |
| M4 | Admin - Content Moderation | Not implemented | Implement moderation UI | Frontend |
| M5 | Video - Subtitles | Not implemented | Add subtitle generation | Backend |

### 🟢 LOW Priority

| Gap ID | Use Case | Issue | Solution | Owner |
|--------|----------|-----|----------|-------|
| L1 | Analytics - Storage Stats | Not implemented | Add storage stats endpoint | Backend |
| L2 | Admin - Audit Logs | No UI | Add audit log viewer | Frontend |
| L3 | Video - Thumbnail | Partial only | Complete thumbnail generation | Backend |

---

## PART D: Real-First Implementation Status

### Current Pattern (Already Good)

The codebase already uses `real_first_utils.ts`:
```typescript
// Tries real API first, falls back to deterministic data only if it fails
await withRealFallback(
    fetch(`${API_BASE}/some/endpoint`),
    { fallback: { deterministic: "data" } }
);
```

### Areas Needing Improvement

| Page | Current Behavior | Should Be |
|------|------------------|-----------|
| Discovery - Neural Config | Local state only | Save to backend |
| Publishing - Toggles | Local state only | Save to backend |
| Analytics - Export | Client-side only | Backend export endpoint |
| Empire - Clone | Returns success but may not work | Verify actual cloning |

---

## PART E: What NOT to Do (No More Placeholders)

Based on your feedback, here are things to STOP doing:

### ❌ DON'T create more dummies/simulations/placeholders
Instead: 
- If feature is needed, implement it for real
- If can't implement now, mark as "NOT_IMPLEMENTED" and hide UI
- Don't leave stub buttons that pretend to work

### ❌ DON'T wait for user to implement
Instead:
- If you identify a gap, either fix it yourself or clearly document what needs to be done
- Don't write "TODO: implement this" and leave it for someone else

### ❌ DON'T add fallback without real attempt first
Instead:
- Always try real API call first
- Fallback should be emergency safety net, not standard flow

---

## Summary Table: All Use Cases

| Use Case | Covered | Partial | Uncovered | Priority |
|----------|---------|---------|-----------|----------|
| Content Discovery | ✅ | | | - |
| Video Generation | | ⚠️ | | HIGH |
| Video Enhancement | | | ❌ | HIGH |
| Nexus Composition | | ⚠️ | | HIGH |
| Publishing | | ⚠️ | | HIGH |
| Monetization | | ⚠️ | | HIGH |
| Analytics | ✅ | | | - |
| Subscription/Billing | | ⚠️ | | MEDIUM |
| User Management | ✅ | | | - |
| Admin Operations | | | ❌ | MEDIUM |

**Legend:**
- ✅ Covered: Fully implemented with real backend
- ⚠️ Partial: Some parts work, some are stubs
- ❌ Uncovered: Not implemented or placeholder only

---

## Files Referenced

- Frontend Pages: `apps/dashboard/src/app/*/page.tsx`
- Components: `apps/dashboard/src/components/`
- Backend Routes: `api/routes/*.py`
- Services: `services/**/*.py`
- Real-First Utils: `apps/dashboard/src/lib/real_first_utils.ts`

---

*End of Comprehensive Gap Analysis*