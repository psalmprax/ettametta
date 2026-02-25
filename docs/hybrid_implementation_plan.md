# Hybrid Tier 2 + Tier 3 Implementation Plan

**Date:** February 24, 2026  
**Goal:** Add Tier 3 features as optional enhancements without disrupting existing Tier 2 pipeline

---

## Architecture: Parallel Processing Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONTENT REQUEST                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     QUALITY TIER SELECTOR                        │
│  (User/Dashboard selects: Standard, Enhanced, or Premium)        │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   ┌─────────┐           ┌─────────┐           ┌─────────┐
   │ TIER 2  │           │ TIER 2  │           │ TIER 3  │
   │ STANDARD│           │ENHANCED │           │PREMIUM  │
   └─────────┘           └─────────┘           └─────────┘
        │                     │                     │
   Current Pipeline      Add Optional          Full Hybrid
   (No changes)         Enhancements         Processing
```

---

## Implementation Strategy

### Phase 1: Add Sound Design Service (Non-Breaking)

**New Service:** `services/audio/sound_design.py`

```python
class SoundDesignService:
    """Optional enhancement - adds background music and SFX"""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_SOUND_DESIGN", "false").lower() == "true"
    
    async def add_background_music(self, video_path: str, mood: str) -> str:
        """Add royalty-free background music based on mood"""
        # Returns enhanced video path
        pass
    
    async def add_sfx(self, video_path: str, sfx_type: str) -> str:
        """Add sound effects"""
        pass
```

**Integration:** Add as optional step in video pipeline, only if enabled

---

### Phase 2: Add Motion Graphics Service (Non-Breaking)

**New Service:** `services/video_engine/motion_graphics.py`

```python
class MotionGraphicsService:
    """Optional enhancement - adds text animations and overlays"""
    
    def __init__(self):
        self.enabled = os.getenv("ENABLE_MOTION_GRAPHICS", "false").lower() == "true"
    
    async def add_title_sequence(self, video_path: str, title: str) -> str:
        """Add animated title sequence"""
        pass
    
    async def add_animated_overlay(self, video_path: str, text: str) -> str:
        """Add animated text overlay"""
        pass
```

---

### Phase 3: Add AI Video Generation Integration (Non-Breaking)

**New Service:** `services/video_engine/ai_generator.py`

```python
class AIVideoGeneratorService:
    """Optional enhancement - AI video generation (Runway/Pika)"""
    
    def __init__(self):
        self.provider = os.getenv("AI_VIDEO_PROVIDER", "none")  # runway, pika, none
    
    async def generate_clip(self, prompt: str, duration: int = 5) -> str:
        """Generate AI video clip from prompt"""
        if self.provider == "none":
            return None  # Graceful fallback
        pass
```

---

## Modified Video Pipeline

### Current (Tier 2 Standard)
```python
async def process_video_standard(input_url, niche, filters):
    # 1. Download
    video = await download_video(input_url)
    # 2. Transform
    video = await apply_filters(video, filters)
    # 3. Voiceover
    video = await add_voiceover(video, niche)
    # 4. Upload
    return await upload(video)
```

### Enhanced (Tier 2 + Sound)
```python
async def process_video_enhanced(input_url, niche, filters, enable_sound=False):
    # 1. Download
    video = await download_video(input_url)
    # 2. Transform
    video = await apply_filters(video, filters)
    # 3. Voiceover
    video = await add_voiceover(video, niche)
    # 4. [NEW] Sound Design (optional)
    if enable_sound:
        video = await add_background_music(video, niche)
    # 5. Upload
    return await upload(video)
```

### Premium (Tier 3 Full)
```python
async def process_video_premium(input_url, niche, filters):
    # 1. Download
    video = await download_video(input_url)
    # 2. AI Video Generation (optional clips)
    ai_clips = await generate_ai_clips(niche)
    video = await merge_ai_clips(video, ai_clips)
    # 3. Transform
    video = await apply_filters(video, filters)
    # 4. Voiceover
    video = await add_voiceover(video, niche)
    # 5. Sound Design
    video = await add_background_music(video, niche)
    # 6. Motion Graphics
    video = await add_title_sequence(video, niche)
    # 7. Upload
    return await upload(video)
```

---

## Environment Configuration

```bash
# .env additions for Tier 3 features

# Sound Design
ENABLE_SOUND_DESIGN=false
SOUND_DESIGN_LIBRARY=epidemic  # or free alternative

# Motion Graphics  
ENABLE_MOTION_GRAPHICS=false
MOTION_GRAPHICS_ENGINE=local  # or render farm

# AI Video Generation
AI_VIDEO_PROVIDER=none  # runway, pika, none
RUNWAY_API_KEY=
PIKA_API_KEY=
```

---

## Dashboard Integration

Add tier selection in transformation page:

```tsx
const [qualityTier, setQualityTier] = useState('standard'); // standard | enhanced | premium

<select onChange={(e) => setQualityTier(e.target.value)}>
  <option value="standard">Standard (Tier 2)</option>
  <option value="enhanced">Enhanced + Sound</option>
  <option value="premium">Premium (Tier 3)</option>
</select>
```

---

## Celery Task Routing

```python
@celery.task
def process_video_tier(request):
    tier = request.get('tier', 'standard')
    
    if tier == 'standard':
        return process_video_standard(request)
    elif tier == 'enhanced':
        return process_video_enhanced(request)
    elif tier == 'premium':
        return process_video_premium(request)
```

---

## Implementation Order

| Phase | Feature | Disruption Risk | Effort |
|-------|---------|-----------------|--------|
| 1 | Sound Design Service | None (off by default) | 2 days |
| 2 | Motion Graphics Service | None (off by default) | 3 days |
| 3 | AI Video Integration | None (optional provider) | 5 days |
| 4 | Dashboard UI | Low | 1 day |
| 5 | Full Testing | Medium | 2 days |

**Total:** ~13 days

---

## Backward Compatibility

- All new features are **disabled by default**
- Existing pipeline unchanged
- Environment variables control activation
- No breaking changes to existing API endpoints
- Gradual rollout possible (enable per-user or per-niche)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| New services break existing pipeline | All new code isolated, existing functions unchanged |
| AI generation is slow | Async processing, queue-based |
| Cost increase | Tier 3 disabled by default, user pays for premium |
| API rate limits | Add rate limiting, fallback to standard |

---

*Hybrid implementation plan - adds Tier 3 features without disrupting current process*
