# Missing Links in Use Case Flows

Based on the codebase analysis, here are the **missing links** between documented use cases and actual implementation:

---

## 1. Configuration vs Implementation Gaps

### Features Marked as "Enabled" but NOT Connected to API

| Config Flag | Status | API Route | Frontend | Issue |
|-------------|--------|-----------|----------|-------|
| `AI_VIDEO_PROVIDER=runway` | ⚠️ Configured | ❌ No route | ❌ No UI | Runway API not integrated |
| `AI_VIDEO_PROVIDER=pika` | ⚠️ Configured | ❌ No route | ❌ No UI | Pika API not integrated |
| `SHOPIFY_SHOP_URL` | ⚠️ Configured | ✅ `/monetization/commerce/sync` | ❌ No UI | Stub implementation |
| `ENABLE_SOUND_DESIGN` | ❌ Disabled | ✅ Service exists | ❌ No UI | Not connected |
| `ENABLE_MOTION_GRAPHICS` | ❌ Disabled | ✅ Service exists | ❌ No UI | Not connected |
| `TWILIO_WHATSAPP_NUMBER` | ⚠️ Configured | ❌ No route | ❌ No UI | WhatsApp not connected |

---

## 2. Services with No API Routes

| Service | Exists | API Route | Frontend | Status |
|---------|--------|-----------|----------|--------|
| **Trading** | ✅ | ❌ | ❌ | `ENABLE_TRADING=False` - No endpoint |
| **LangChain** | ✅ | ❌ | ❌ | `ENABLE_LANGCHAIN=False` - Disabled |
| **CrewAI** | ✅ | ❌ | ❌ | `ENABLE_CREWAI=False` - Disabled |
| **Interpreter** | ✅ | ❌ | ❌ | `ENABLE_INTERPRETER=False` - Disabled |
| **Agent Zero** | ✅ | ❌ | ❌ | No route - unused |
| **Visual Generator** | ✅ | ❌ | ❌ | No route - unused |

---

## 3. Routes Without Frontend Integration

| Route | Method | Backend | Frontend | Flow Broken |
|-------|--------|---------|----------|-------------|
| `/security/scan` | POST | ✅ | ❌ | Admin → Trigger scan |
| `/security/events` | GET | ✅ | ❌ | Admin → View events |
| `/remotion/render` | POST | ✅ | ❌ | No UI for custom renders |
| `/persona/create` | POST | ✅ | ❌ | Profile → Create avatar |
| `/persona/generate` | POST | ✅ | ❌ | Profile → Generate avatar video |
| `/settings/filters` | GET/POST | ✅ | ❌ | No filter management UI |
| `/auth/verify-telegram` | GET | ✅ | ❌ | No Telegram bot integration |
| `/auth/verify-whatsapp` | GET | ✅ | ❌ | No WhatsApp integration |
| `/auth/internal/users-with-bots` | GET | ✅ | ❌ | Internal only |

---

## 4. Monetization - Broken Links

### Affiliate Flow - INCOMPLETE
```
Documented: Discovery → AI Analysis → Recommend Links → Add to Video → Publish
                  ↓
Actual:     Discovery → AI Analysis → [MISSING: recommend_links not called]
                              ↓
                  [User must manually add links]
```

**Missing Link:** `/monetization/recommend-links` is NOT called from:
- Video generation flow
- Publishing flow  
- Analytics insights

### Empire Building - INCOMPLETE
```
Documented: Clone winning strategy → Auto-create content → Publish
                  ↓
Actual:     `/monetization/empire/clone` exists but:
- No frontend UI to select source/target
- No automation after cloning
- No monitoring of cloned strategies
```

### Auto-Merch - STUB
```
Documented: Trend detection → Auto-generate merch → Shopify sync → Publish
                  ↓
Actual:     `/monetization/auto-merch` exists but:
- commerce_service is a stub
- No Shopify API integration
- No product generation
```

---

## 5. Video Generation Flow - Missing Connections

### AI Generation Engines - NOT TIER-GATED PROPERLY
```
Documented: User selects engine → Check subscription → Generate
                  ↓
Actual:     API has tier checks in `/video/generate` but:
- Engines: lite4k, ltx-video, hunyuan, mochi, cogvideo, wan, veo3, runway, pika
- BUT only lite4k works (others are stubs or require external API keys)
- No way to test which engines actually work in UI
```

### Story Generation - DISCONNECTED
```
Documented: Prompt → Multi-scene story → Render
                  ↓
Actual:     `/video/generate-story` exists but:
- No UI for story creation
- generate_story_task is a stub
```

### Nexus Composition - PARTIAL
```
Documented: Segments + Voice + Music → Assemble → Render
                  ↓
Actual:     `/nexus/compose` works but:
- cinema_mode calls base_auto_creator (stub)
- story-factory calls base_auto_creator (stub)
- Only "viral-reskin" blueprint works
```

---

## 6. Discovery → Creation Pipeline - Broken

### Test Drive Flow - INCOMPLETE
```
Discovery → "Try This" → Test Drive → [MISSING]
                    ↓
        /video/test-drive works but:
        - No "Transform to Video" button in Discovery UI
        - Result not automatically sent to creation
```

### Deep Analysis - INCOMPLETE
```
Discovery → Analyze → [MISSING]
              ↓
  /discovery/analyze dispatches Celery task
  BUT:
  - No polling endpoint to check task status
  - No result display in UI
  - No "Create Video" from analysis
```

---

## 7. Publishing Flow - Missing Features

### TikTok - INCOMPLETE
```
Documented: OAuth → Upload → Track
              ↓
Actual:     OAuth works but:
- tiktok_publisher.py exists but may be incomplete
- No TikTok analytics fetch
- No TikTok comment retrieval
```

### Scheduling - DISCONNECTED
```
Documented: Schedule → Auto-publish at time
              ↓
Actual:     `/publish/schedule` works but:
- No cron job/worker to actually execute scheduled posts
- scheduler.py exists but may not be connected
- Posts stay "PENDING" forever
```

---

## 8. Analytics → Action Loop - Broken

### Monetization Suggestions - NOT USED
```
Analytics → Suggest monetization → [MISSING]
                    ↓
/analytics/monetization/{post_id} returns suggestions
BUT:
- No "Apply" button in UI
- Not connected to video generation
- Not connected to affiliate link system
```

### A/B Testing - INCOMPLETE
```
Publish with variants → Track views → [MISSING]
                          ↓
A/B test created but:
- No variant view tracking endpoint working properly
- No automatic winner selection
- Results not used for future content
```

---

## 9. Missing Webhooks & Callbacks

| Event | Missing Handler | Impact |
|-------|-----------------|--------|
| YouTube upload success | ❌ No webhook | Can't track video status |
| TikTok upload success | ❌ No webhook | Can't track video status |
| Stripe payment success | ✅ Has webhook | Works |
| Stripe subscription cancelled | ⚠️ Partial | May not downgrade user |
| Celery task completion | ⚠️ Partial | Only WebSocket notify |

---

## 10. Database Models Not Used

| Model | Created | Used in API | Used in UI |
|-------|---------|-------------|------------|
| `NicheTrendDB` | ✅ | ❌ Partially | ❌ No |
| `ViralPatternDB` | ✅ | ❌ Partially | ❌ No |
| `ABTestDB` | ✅ | ⚠️ Partial | ❌ No |
| `ScheduledPostDB` | ✅ | ⚠️ | ❌ No |
| `PersonaDB` | ✅ | ⚠️ Partial | ❌ No |
| `AuditLogDB` | ✅ | ❌ | ❌ Admin only |

---

## Summary: Critical Missing Links

### Must Fix Before Launch:

1. **Discovery → Creation** - Add "Create Video" button from analysis results
2. **Scheduled Publishing** - Implement actual scheduler worker  
3. **TikTok Integration** - Complete upload and add analytics
4. **A/B Testing** - Fix variant tracking and winner selection
5. **Affiliate Flow** - Connect recommendation to publishing
6. **Runway/Pika Integration** - Either implement or remove from UI

### Should Fix:

7. **Auto-Merch** - Complete or remove feature
8. **Story Generation** - Complete or hide
9. **Nexus Cinema Mode** - Complete stubs
10. **Trading/LangChain/CrewAI** - Either enable or remove

---

*End of Missing Links Analysis*
