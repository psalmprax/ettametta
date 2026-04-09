# Roadmap

## Phases

- [ ] **Phase 1: User Authentication and Settings** - Secure account access and configuration
- [ ] **Phase 2: Content Discovery** - Access to trending content across platforms
- [ ] **Phase 3: Basic Video Generation** - AI-powered video creation and transformation
- [ ] **Phase 4: Advanced Video Generation** - Multi-scene storytelling video creation
- [ ] **Phase 5: Multi-Platform Publishing** - Social media content distribution
- [ ] **Phase 6: Automated Scheduling Publishing** - Campaign automation for publishing
- [ ] **Phase 7: Monetization** - Revenue generation and credit management
- [ ] **Phase 8: Analytics** - Performance metrics and insights

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
**Plans**: 4 plans
- [x] 01-01-PLAN.md — Implement core user authentication system
- [x] 01-02-PLAN.md — Implement user settings and notifications
- [x] 01-03-PLAN.md — Fix authentication gaps (logout and OAuth)
- [x] 01-04-PLAN.md — Implement bot integration for notifications

### Phase 2: Content Discovery
**Goal**: Users can discover and analyze trending content
**Depends on**: Phase 1
**Requirements**: DISC-01, DISC-02, DISC-03
**Success Criteria** (what must be TRUE):
  1. User can view trending content from YouTube, TikTok, and other platforms via automated scanners
  2. User can search for content with filters and sort by viral score
  3. User can analyze content for viral patterns and insights
**Plans**: 3 plans
- [ ] 02-01-PLAN.md — Implement automated trending content collection from YouTube
- [ ] 02-02-PLAN.md — Implement content search API with filters and viral score sorting
- [ ] 02-03-PLAN.md — Implement AI-powered content analysis for viral patterns and insights

### Phase 3: Basic Video Generation
**Goal**: Users can generate and enhance videos using AI
**Depends on**: Phase 2
**Requirements**: VIDEO-01, VIDEO-02, VIDEO-04
**Success Criteria** (what must be TRUE):
  1. User can transform existing videos with AI enhancements like sound design and quality tiers
  2. User can generate new videos from scratch using multiple AI engines (Veo3, LTX-Video, etc.)
  3. User can preview generated videos and retry failed jobs
**Plans**: TBD

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
**Plans**: TBD

### Phase 6: Automated Scheduling Publishing
**Goal**: Users can automate publishing campaigns
**Depends on**: Phase 5
**Requirements**: PUBLISH-02
**Success Criteria** (what must be TRUE):
  1. User can schedule automated content publishing campaigns
**Plans**: TBD

### Phase 7: Monetization
**Goal**: Users can monetize content and manage credits
**Depends on**: Phase 6
**Requirements**: MONET-01, MONET-02, MONET-03
**Success Criteria** (what must be TRUE):
  1. User can automatically insert affiliate links into video content
  2. User can track affiliate revenue and manage referral programs
  3. User can purchase and consume credits for AI services and features
**Plans**: TBD

### Phase 8: Analytics
**Goal**: Users can view content performance metrics
**Depends on**: Phase 7
**Requirements**: ANALYTICS-01
**Success Criteria** (what must be TRUE):
  1. User can view performance analytics and content metrics
**Plans**: TBD
**UI hint**: yes

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. User Authentication and Settings | 1/4 | Verifying | - |
| 2. Content Discovery | 0/0 | Not started | - |
| 3. Basic Video Generation | 0/0 | Not started | - |
| 4. Advanced Video Generation | 0/0 | Not started | - |
| 5. Multi-Platform Publishing | 0/0 | Not started | - |
| 6. Automated Scheduling Publishing | 0/0 | Not started | - |
| 7. Monetization | 0/0 | Not started | - |
| 8. Analytics | 0/0 | Not started | - |

---
*Roadmap created: 2026-04-08*</content>
<parameter name="filePath">.planning/ROADMAP.md