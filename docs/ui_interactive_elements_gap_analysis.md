# UI/Buttons/Clickables/Menus Gap Analysis - Use Case Coverage

**Date:** 2026-04-08  
**Focus:** Frontend Interactive Elements Coverage & Gap Analysis  
**Priority:** Real Implementation First, Dummies/Simulations as Fallback Only

---

## Executive Summary

This document maps ALL interactive elements (buttons, clickables, menus) across the 13 main pages of the Viral Forge dashboard, identifies which use cases are covered vs NOT covered, and highlights where real implementation exists vs where only stubs/simulations exist.

**Key Finding:** The project follows a "Real-First" philosophy with `withRealFallback()` pattern, meaning real API calls are attempted first, and deterministic fallbacks only activate when the backend fails. However, many features still lack complete end-to-end coverage.

---

## Page-by-Page Interactive Element Analysis

### 1. DISCOVERY PAGE (`/discovery`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Search Input + Submit | Search trends | Content Discovery | ✅ `/discovery/search` | COVERED |
| Deep Scan Button | Trigger niche scan | Deep Discovery | ✅ `/discovery/scan` | COVERED |
| Test Drive Button | Auto-find viral content | Quick Transformation | ✅ `/video/test-drive` | COVERED |
| Mode Toggle (Discovery/Generative) | Switch modes | Mode Selection | ✅ State change only | COVERED |
| Refresh Trends Button | Refresh data | Refresh Data | ✅ `/discovery/trends` | COVERED |
| Niche Pills/Buttons | Select niche | Niche Selection | ✅ URL param | COVERED |
| Neural Config Toggle | Show config drawer | Settings | ✅ `/settings/` POST | COVERED |
| Min Viral Score Slider | Filter threshold | Filter Configuration | ✅ Saves to settings | COVERED |
| Style Selection Buttons | Select style | Style Configuration | ✅ Saves to settings | COVERED |
| Exclude Shorts Toggle | Filter shorts | Filter Configuration | ✅ Saves to settings | COVERED |
| Category Tabs (All/Video/Blog/Social/News) | Filter category | Content Filtering | ✅ State change | COVERED |
| Keyword Neural Cloud Tags | Click to search | Quick Search | ✅ State change | COVERED |
| Content Card "Add to Queue" | Transform content | Discovery→Creation | ✅ `/video/transform` | COVERED |
| Content Card "Analyze" Button | AI Analysis | Deep Analysis | ✅ `/discovery/analyze` | COVERED |
| Content Card "Open Original" | Open source URL | View Original | ✅ External link | COVERED |
| Content Card Interact (Like/Comment/Subscribe) | Social interaction | Discovery Interaction | ✅ `/discovery/interact` | COVERED |
| "Create Video from Analysis" Action | Transform with insights | Analysis→Creation | ✅ `/discovery/analyze/{task}/create-video` | COVERED |
| Generative Mode: Prompt Input | Enter text | AI Generation | ✅ `/video/generate` | COVERED |
| Generative Mode: Engine Selector | Select AI engine | Engine Selection | ✅ State change | COVERED |
| Generative Mode: Generate Button | Start generation | Video Generation | ✅ `/video/generate` or `/video/generate-story` | COVERED |
| Generative Mode: Story Toggle | Enable story mode | Mode Selection | ✅ State change | COVERED |

**GAPS - Discovery Page:**
1. ❌ **Analysis Polling Endpoint** - `/discovery/analyze/{taskId}` returns status, but no robust retry logic in UI
2. ❌ **Runway/Pika Engine Selection** - UI shows these options but backend returns stubs (Gap from docs)
3. ❌ **Generative Mode: Story Generation** - `/video/generate-story` exists but backend has stub implementation
4. ❌ **Niche Add Button** - No clear "Add New Niche" button, only search adds implicitly

---

### 2. CREATION PAGE (`/creation`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Topic Input + Generate Button | Generate script | Script Generation | ✅ `/no-face/generate-script` | COVERED |
| Cinema Mode Toggle | Enable autonomous | Mode Selection | ✅ State change | COVERED |
| Launch Cinema Button | Start autonomous | Full Automation | ✅ `/nexus/compose` | COVERED |
| Niche Dropdown | Select niche | Niche Selection | ✅ State change | COVERED |
| Style Dropdown | Select style | Style Selection | ✅ State change | COVERED |
| Duration Slider | Set duration | Configuration | ✅ State change | COVERED |
| Validate Hook Button | Analyze hook | Hook Validation | ✅ `/no-face/validate-hook` | COVERED |
| Alternative Hook Buttons | Apply suggestion | Content Modification | ✅ State change | COVERED |
| Segment Audio Generate | Synthesize voice | Audio Generation | ✅ `/no-face/generate-voiceover` | COVERED |
| Segment Stock Search | Search stock media | Asset Search | ✅ `/no-face/search-stock` | COVERED |
| Segment Image Generate | AI generate image | Image Generation | ✅ `/no-face/generate-image` | COVERED |
| Localization Buttons (ES/DE/FR/IT/etc) | Translate script | Localization | ✅ `/no-face/localize` | COVERED |
| Export Assets Button | Download JSON | Export | ✅ Client-side generation | COVERED |
| Launch Production Button | Start rendering | Video Creation | ✅ `/nexus/compose` | COVERED |

**GAPS - Creation Page:**
1. ❌ **Script Editing** - No inline editing of generated script segments
2. ❌ **Audio Preview** - Generated audio not playable in UI
3. ❌ **Stock Media Preview** - No video preview for stock clips
4. ❌ **Production Progress** - No job tracking after launch (redirects to transformation but no job ID passed)

---

### 3. TRANSFORMATION PAGE (`/transformation`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Add Job Button (+) | Open modal | Add Job | ✅ Opens modal | COVERED |
| Job URL Input | Enter source URL | Input Source | ✅ `/video/transform` POST | COVERED |
| Platform Dropdown | Select target | Platform Selection | ✅ State change | COVERED |
| Niche Dropdown | Select niche | Niche Selection | ✅ State change | COVERED |
| Generate Thumbnail Toggle | Enable thumbnail | Configuration | ✅ State change | COVERED |
| Premium Quality Toggle | Select quality | Quality Selection | ✅ State change | COVERED |
| Sound Design Toggle | Enable sound | Configuration | ✅ State change | COVERED |
| Motion Graphics Toggle | Enable motion | Configuration | ✅ State change | COVERED |
| Submit Job Button | Start transformation | Job Submission | ✅ `/video/transform` | COVERED |
| Filter Toggle Buttons | Enable/disable filters | Filter Management | ✅ `/settings/filters/{id}/toggle` | COVERED |
| Job Card Click | Select job | Job Selection | ✅ State change | COVERED |
| Job Card Preview Button | View output | Preview | ✅ Opens preview modal | COVERED |
| Job Card Abort Button | Cancel job | Job Control | ✅ `/video/jobs/{id}/abort` | COVERED |
| Job Card Retry Button | Retry failed job | Job Control | ❌ NO ENDPOINT | **GAP** |

**GAPS - Transformation Page:**
1. ❌ **Job Retry** - No `/video/jobs/{id}/retry` endpoint exists
2. ❌ **Thumbnail Preview** - Generated thumbnail not viewable in UI
3. ❌ **Job Output Download** - No direct download button for completed videos
4. ❌ **Filter Settings** - No full filter management UI (only toggle)

---

### 4. PUBLISHING PAGE (`/publishing`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Manual Transmission Button | Open deploy modal | Manual Publish | ✅ Opens modal | COVERED |
| Add Platform (+) Button | Open OAuth modal | Connect Account | ✅ Opens modal | COVERED |
| Platform Select (YouTube/TikTok/Instagram/X/LinkedIn) | Start OAuth | OAuth Flow | ✅ `/publish/auth/{platform}` | COVERED |
| Account Card Click | Manage account | Account Management | ✅ Opens modal | COVERED |
| Re-Authenticate Button | Refresh OAuth | OAuth Refresh | ✅ `/publish/auth/{platform}` | COVERED |
| Disconnect Button | Remove account | Account Removal | ✅ `/publish/account/{id}` | COVERED |
| Deploy Modal: Job Select | Choose video | Video Selection | ✅ State change | COVERED |
| Deploy Modal: Platform Select | Choose platform | Platform Selection | ✅ State change | COVERED |
| Deploy Modal: Account Select | Choose account | Account Selection | ✅ State change | COVERED |
| Deploy Modal: Niche Select | Choose niche | Niche Selection | ✅ State change | COVERED |
| Deploy Modal: Multi-Platform Toggles | Select targets | Multi-Publish | ✅ State change | COVERED |
| Deploy Modal: A/B Title Input | Set variant B | A/B Testing Setup | ✅ State change | COVERED |
| Monetization Toggle | Enable affiliate | Monetization Setup | ✅ State change | COVERED |
| Schedule Toggle | Enable scheduling | Scheduling | ✅ Shows datetime input | COVERED |
| Schedule Time Picker | Set publish time | Time Selection | ✅ State change | COVERED |
| Initialize Transmission Button | Publish video | Publish | ✅ `/publish/post` or `/publish/schedule` | COVERED |
| Publish Everywhere Button | Multi-platform | Bulk Publish | ✅ `/publish/post-multi` | COVERED |
| Generate SEO Package Button | Generate metadata | SEO Generation | ✅ `/publish/package` | COVERED |
| Monetization Protocol Card Click | Toggle affiliate | Quick Toggle | ✅ State change | COVERED |
| Deployment Timing Card Click | Toggle schedule | Quick Toggle | ✅ State change | COVERED |
| A/B Testing Card Input | Set variant B | Quick Config | ✅ State change | COVERED |
| Sync Button (on post) | Refresh stats | Telemetry Sync | ✅ `/publish/sync/{postId}` | COVERED |
| Retry Button (on failed) | Retry publish | Publish Retry | ✅ `/publish/retry/{postId}` | COVERED |

**GAPS - Publishing Page:**
1. ❌ **TikTok Analytics** - No `/publish/tiktok/analytics` endpoint
2. ❌ **TikTok Comment Retrieval** - No endpoint to fetch comments
3. ❌ **Scheduled Post Execution** - No worker actually runs scheduled posts (from docs)
4. ❌ **A/B Test Results Display** - No variant view tracking in results
5. ❌ **Instagram Reels** - Platform in dropdown but may not be fully implemented

---

### 5. ANALYTICS PAGE (`/analytics`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Global Export Button | Download CSV | Data Export | ✅ `/analytics/export` | COVERED |
| Post Selection | Select post | Post Selection | ✅ State change | COVERED |
| Apply Insights Button | Inject optimization | Optimization | ✅ `/analytics/inject-pattern/{postId}` | COVERED |
| Copy Insights Button | Copy to clipboard | Copy | ✅ Client-side | COVERED |
| Table Row Click | Select post | Post Selection | ✅ State change | COVERED |
| Table Search Input | Filter posts | Search | ✅ TanStack table filter | COVERED |
| Chart Click | View data point | Detail View | ✅ Sets global filter | COVERED |
| A/B Test Tab Toggle | Switch tabs | View Selection | ✅ State change | COVERED |
| Create Test Button | Start new test | A/B Test Creation | ✅ Opens modal | COVERED |
| Auto-Pilot Toggle | Enable auto-winner | Automation | ✅ State change | COVERED |
| Winner Modal Confirm | Apply winner | Winner Application | ✅ Calls determine-winner | COVERED |

**GAPS - Analytics Page:**
1. ❌ **Post Selection Without Data** - When no posts, shows error but no way to create/test
2. ❌ **A/B Test Creation Flow** - Modal not fully visible in code snippet (cut off)
3. ❌ **Monetization Data** - No monetization insights shown
4. ❌ **Real-Time Views** - Telemetry shows mock data when backend unavailable

---

### 6. EMPIRE PAGE (`/empire`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Refresh Sentinel Button | Refresh status | Status Refresh | ✅ `/no-face/sentinel/status` | COVERED |
| Clone Strategy Button | Open clone modal | Strategy Clone | ✅ Opens modal | COVERED |
| Clone Modal: Source Niche Select | Select source | Source Selection | ✅ State change | COVERED |
| Clone Modal: Target Niche Input | Enter target | Target Input | ✅ State change | COVERED |
| Clone Modal: Auto-Publish Toggle | Enable auto-publish | Automation | ✅ State change | COVERED |
| Execute Clone Button | Clone strategy | Empire Building | ✅ `/monetization/empire/clone` | COVERED |
| Add Affiliate Link Button | Add link | Link Management | ✅ Opens form | COVERED |
| Affiliate Link Form: Product Name | Enter product | Input | ✅ State change | COVERED |
| Affiliate Link Form: Niche Select | Select niche | Input | ✅ State change | COVERED |
| Affiliate Link Form: URL Input | Enter link | Input | ✅ State change | COVERED |
| Affiliate Link Form: CTA Text | Enter CTA | Input | ✅ State change | COVERED |
| Save Link Button | Save link | Link Save | ✅ `/monetization/links` POST | COVERED |
| Delete Link Button | Remove link | Link Delete | ✅ `/monetization/links/{id}` DELETE | COVERED |
| Generate Promo Button | Generate script | Promo Generation | ✅ `/monetization/promo/generate` | COVERED |
| Auto-Merch Button | Generate merch | Merch Creation | ✅ `/monetization/auto-merch` | COVERED |
| Recommend Links Button | Get recommendations | Link Recommendation | ✅ `/monetization/recommend-links` | COVERED |
| Shopify Sync Button | Sync commerce | Commerce Sync | ✅ `/monetization/commerce/sync` | COVERED |

**GAPS - Empire Page:**
1. ❌ **Shopify Integration** - Stub implementation (from docs)
2. ❌ **Auto-Merch** - Stub implementation, no actual product generation
3. ❌ **Recommendation Link Usage** - Links recommended but not connected to video publishing flow
4. ❌ **Empire Network Visualization** - Network mesh shows but data may be empty
5. ❌ **Timeline Events** - Not visible in first 400 lines, likely limited

---

### 7. SETTINGS PAGE (`/settings`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Tab Navigation | Switch sections | Navigation | ✅ State change | COVERED |
| API Key Visibility Toggle | Show/hide keys | Security | ✅ State change | COVERED |
| Input Fields (all settings) | Configure values | Configuration | ✅ State change | COVERED |
| Save Button | Save all settings | Save | ✅ `/settings/bulk` or `/settings/user` | COVERED |
| Verify Service Button | Test connection | Verification | ✅ `/settings/verify/{serviceId}` | COVERED |
| Comms Verify (Telegram/WhatsApp) | Send verification | Verification | ✅ `/auth/verify-comms` | COVERED |
| Cancel Subscription Button | Cancel plan | Subscription | ✅ `/billing/cancel` | COVERED |
| Change Password Button | Update password | Security | ✅ `/auth/me/change-password` | COVERED |

**GAPS - Settings Page:**
1. ❌ **Telegram Bot Integration** - Verification endpoint exists but no actual bot
2. ❌ **WhatsApp Integration** - Number field exists but no backend integration
3. ❌ **Sound Design Settings** - Toggle exists but service disabled by default
4. ❌ **Motion Graphics Settings** - Toggle exists but service disabled by default
5. ❌ **AI Video Provider Settings** - Dropdown exists but Runway/Pika are stubs

---

### 8. CREDITS PAGE (`/credits`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Refresh Button | Refresh all data | Data Refresh | ✅ Calls all endpoints | COVERED |
| Package Purchase Button | Buy credits | Purchase | ✅ `/credits/purchase` | COVERED |
| Apply Referral Code Input | Enter code | Code Input | ✅ State change | COVERED |
| Apply Button | Submit code | Code Apply | ✅ `/credits/referral/apply` | COVERED |
| Copy Code Button | Copy referral | Share | ✅ Client-side | COVERED |

**GAPS - Credits Page:**
1. ❌ **Credit Package Display** - Limited packages shown
2. ❌ **Transaction History** - Displayed but may lack detail
3. ❌ **Referral Program Details** - UI shows stats but referral system may be limited

---

### 9. NEXUS PAGE (`/nexus`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Blueprint Selection | Select blueprint | Template Selection | ✅ State change | COVERED |
| Launch Blueprint Button | Start job | Job Launch | ✅ `/nexus/compose` | COVERED |
| Niche Selection | Select niche | Niche Selection | ✅ State change | COVERED |
| Cluster Manager Button | Manage clusters | Cluster Management | ✅ Opens modal | COVERED |
| Blueprint Builder Button | Create blueprint | Blueprint Creation | ✅ Opens modal | COVERED |
| AI Agent Chat Input | Send message | Agent Interaction | ✅ `/agent/chat` | COVERED |
| Persona Create Button | Create avatar | Avatar Creation | ✅ `/persona/create` | COVERED |
| Persona Generate Video Button | Generate video | Video Generation | ✅ `/persona/generate` | COVERED |
| Clear Jobs Button | Clear all | Job Management | ✅ Opens confirmation | COVERED |

**GAPS - Nexus Page:**
1. ❌ **Cinema Mode** - `base_auto_creator` is a stub (from docs)
2. ❌ **Story Factory** - `base_auto_creator` is a stub (from docs)
3. ❌ **Only "viral-reskin" blueprint works** - Others are stubs (from docs)
4. ❌ **Persona Generation** - Backend exists but may be limited

---

### 10. AUTONOMOUS PAGE (`/autonomous`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Launch Director Button | Start/stop | Agent Control | ✅ `/zero/start` or `/zero/stop` | COVERED |

**GAPS - Autonomous Page:**
1. ❌ **Agent Zero** - Stub implementation (from docs)
2. ❌ **No detailed step control** - Only start/stop, no granular control

---

### 11. TRADING PAGE (`/trading`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| (All elements) | Trading features | Trading | ❌ NO BACKEND | **GAP** |

**GAPS - Trading Page:**
1. ❌ **Entire Page** - Trading service disabled (`ENABLE_TRADING=False`), no backend

---

### 12. ADMIN PAGE (`/admin`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Environment Manager | View/edit env vars | Configuration | ✅ `/admin/env` | COVERED |
| (Other elements) | Admin features | Admin | Limited | LIKELY GAP |

---

### 13. CREDITS PAGE (`/credits`)

| Interactive Element | Action | Use Case | Backend Status | Gap? |
|---------------------|--------|----------|----------------|------|
| Balance Display | View balance | Credits Display | ✅ `/credits/balance` | COVERED |
| Cost List | View pricing | Pricing Display | ✅ `/credits/costs` | COVERED |
| Transaction History | View transactions | History | ✅ `/credits/transactions` | COVERED |
| Referral Code Display | View code | Referral | ✅ `/credits/referral/code` | COVERED |
| Referral Stats | View stats | Stats | ✅ `/credits/referral/stats` | COVERED |
| Package Purchase | Buy credits | Purchase | ✅ `/credits/purchase` | COVERED |
| Apply Referral | Apply code | Code Apply | ✅ `/credits/referral/apply` | COVERED |

---

## Summary: Covered vs Uncovered Use Cases

### FULLY COVERED (Real Implementation Exists)
✅ Content Discovery & Search  
✅ Video Transformation (basic)  
✅ Script Generation  
✅ Voice Synthesis  
✅ Platform Publishing (YouTube)  
✅ Account Management  
✅ Scheduling  
✅ A/B Testing (basic)  
✅ Analytics Display  
✅ Affiliate Link Management  
✅ Credits System  
✅ Settings Management  

### PARTIALLY COVERED (Stubs/Simulations Exist)
⚠️ TikTok Publishing - partial  
⚠️ Instagram Publishing - partial  
⚠️ LinkedIn Publishing - partial  
⚠️ AI Video Generation - Runway/Pika are stubs  
⚠️ Story Generation - stub  
⚠️ Nexus Cinema Mode - stub  
⚠️ Auto-Merch - stub  
⚠️ Shopify Sync - stub  
⚠️ A/B Testing Results - incomplete  

### NOT COVERED (No Implementation)
❌ Trading Features - disabled  
❌ LangChain - disabled  
❌ CrewAI - disabled  
❌ Interpreter - disabled  
❌ Agent Zero - stub  
❌ TikTok Analytics  
❌ TikTok Comments  
❌ Job Retry  
❌ Scheduled Post Execution Worker  

---

## Recommendations

### Priority 1: Fix Broken Flows (Real Implementation)
1. **Discovery → Creation Pipeline** - Ensure "Create Video from Analysis" works end-to-end
2. **Scheduled Publishing** - Implement actual Celery worker to execute scheduled posts
3. **Job Retry** - Add `/video/jobs/{id}/retry` endpoint or remove retry UI
4. **TikTok Integration** - Complete upload and add analytics fetching

### Priority 2: Complete Partial Implementations
5. **Runway/Pika Integration** - Either implement real API or remove from UI
6. **Story Generation** - Either complete or hide
7. **Auto-Merch** - Either complete or remove feature
8. **A/B Testing** - Fix variant tracking and winner selection

### Priority 3: Enable Disabled Services
9. **Trading** - Enable or remove page
10. **LangChain/CrewAI** - Enable or remove from codebase

---

## Fallback Strategy (When Real Implementation Fails)

Per your "Real-First" mandate, the current `withRealFallback()` pattern correctly handles failures:
- **Primary:** Real API call is attempted
- **Fallback:** Only activates when API fails
- **Pattern:** Deterministic data, NOT random simulations

**Exception:** The `getVelocityPoints()` function provides deterministic fallback curves when no historical data exists - this is acceptable as it's not a simulation but a reasonable projection.

---

*End of Analysis - 2026-04-08*