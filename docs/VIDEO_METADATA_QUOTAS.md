# Video Metadata & Provider Quota Documentation

## Overview
Viral Forge tracks comprehensive metadata for every video generated, including which AI model/provider was used, quotas, and generation costs. This document details the metadata schema and quota management.

## Video Metadata Schema

### Database Model (`VideoJobDB`)
```python
class VideoJobDB(Base):
    id: str  # Task ID (primary key)
    title: str
    status: str  # Queued, Synthesizing, Completed, Failed
    progress: int  # 0-100
    input_url: str  # Original prompt or source URL
    output_path: str  # Generated video file path
    user_id: int
    created_at: datetime
    updated_at: datetime
    # Note: Model/provider info is tracked in audit logs
```

### Provider-Specific Metadata
Each provider returns standardized metadata:

```json
{
  "video_url": "https://cdn.example.com/video.mp4",
  "metadata": {
    "model": "zsky-wan",  // Provider model identifier
    "provider": "zsky",   // Provider name
    "cost": 0.02,         // Cost per video (if paid)
    "duration": 5,        // Generated duration in seconds
    "resolution": "720p", // Video resolution
    "aspect_ratio": "9:16" // Video aspect ratio
  }
}
```

## Video Provider Quotas

### Free Daily Providers (0 Credits)

| Provider | Model | Daily Quota | Resolution | Max Duration | Cost/Video |
|----------|-------|-------------|------------|--------------|------------|
| **ZSky AI** | zsky-wan | ~50 videos | 1080p | 10s | **$0.00** |
| **Kling AI** | kling | ~100 videos | 1080p | 10s | **$0.00** |
| **PixVerse** | pixverse | ~20 videos | 1080p | 8s | **$0.00** |
| **Replicate** | minimax/mimi-alpha-01 | Trial credits | 720p | 10s | **$0.00** |

### Paid Replicate Models (5 Credits = ~$0.50)

| Provider | Model | Daily Quota | Resolution | Max Duration | Cost/Video |
|----------|-------|-------------|------------|--------------|------------|
| **Wan 2.2 Fast** | wan-video/wan-2.2-5b-fast | Unlimited | 720p | 5s | **$0.02** |
| **Seedance Lite** | bytedance/seedance-1-lite | Unlimited | 1080p | 10s | **$0.40** |
| **Hailuo Fast** | minimax/hailuo-02-fast | Unlimited | 720p | 6s | **$0.15** |

### Premium Local GPU Models (10-30 Credits = $1-3)

| Model | Credits/Video | Resolution | Max Duration | GPU Requirements |
|-------|---------------|------------|--------------|------------------|
| **LTX-Video** | 10 | 720p | 10s | 10GB VRAM |
| **Hunyuan** | 15 | 1080p | 5s | 16GB VRAM |
| **Mochi** | 15 | 1080p | 5s | 16GB VRAM |
| **Wan 2.2** | 15 | 720p | 5s | 12GB VRAM |
| **CogVideo** | 15 | 1080p | 5s | 20GB VRAM |

### Enterprise Cloud Models (25-30 Credits = $2.50-3)

| Model | Credits/Video | Resolution | Max Duration | Provider |
|-------|---------------|------------|--------------|----------|
| **Veo3** | 25 | 1080p | 8s | Google |
| **Runway** | 30 | 720p | 10s | Runway ML |
| **Pika** | 30 | 720p | 8s | Pika Labs |

### OpenCLAW Browser-Based Skills (Free, No API Required)

Viral Forge includes OpenCLAW skills that automate browser UIs for platforms without public APIs. These use Playwright for browser automation.

#### Image Generation Providers

| Provider | Type | Features | Resolution | Use Cases |
|----------|------|----------|------------|-----------|
| **Perchance** | Image | negative prompts, seed control, batch generation | 512-1024px | social media, anime, product, artwork |
| **Leonardo** | Image | image-to-video, controlnet, inpainting | 512-1024px | concept art, game assets, characters |

#### Video Generation Providers

| Provider | Type | Features | Max Duration | Resolution | Use Cases |
|----------|------|----------|-------------|------------|-----------|
| **PixVerse** | Video | image-to-video, text-to-video | 10s | 540-1080p | short_form, social_media |
| **Kling** | Video | text-to-video, image-to-video, extend | 20s | 720-1080p | cinematic, professional |
| **Haiper** | Video | text-to-video, image-to-video | 8s | 720-1080p | animated_content |
| **Luma** | Video | image-to-video, camera motion | 10s | 720-1080p | product_shots, cinematic |
| **Runway** | Video | image-to-video, video-to-video | 10s | 720-1080p | professional, film |
| **Pika** | Video | text-to-video, image-to-video | 10s | 720-1080p | short_form, quick |
| **LTX Video** | Video | text-to-video, cartoon | 16s | 512-1024px | cartoon, animation |
| **VidU** | Video | image-to-video, character consistency | 10s | 720-1080p | characters, portraits |
| **Hailuo** | Video | text-to-video, image-to-video | 10s | 720-1080p | short_clips, social_media |
| **Seedance** | Video | text-to-video, image-to-video | 10s | 720-1080p | advertising, promos |
| **LeiaPix** | Video | image-to-video, motion effects | 8s | 720-1080p | image_to_video, cinemagraphs |
| **Fliki** | Video | text-to-video, voiceover | 30s | 720-1080p | video_with_audio |
| **InVideo** | Video | text-to-video, templates | 30s | 720-1080p | social_media, marketing |
| **Kaiber** | Video | image-to-video, style transfer | 30s | 720-1080p | artistic, music_videos |
| **Morph** | Video | text-to-video, image-to-video | 10s | 720-1080p | animation, short_clips |
| **Genmo** | Video | text-to-video, creative | 10s | 512-1024px | creative, artistic |
| **HeyGen** | Video | avatar, talking_head | 60s | 720-1080p | avatars, presentations |
| **FrameLoop** | Video | text-to-video, image-to-video | 10s | 720-1080p | motion_design |
| **WaveSpeed** | Video | text-to-video, image-to-video | 10s | 720-1080p | short_form |

#### Using OpenCLAW Skills

```python
from services.openclaw.skills import (
    perchance_skill,
    get_model_settings,
    get_recommended_settings,
    list_providers,
)

# Get recommended settings for a use case
settings = get_recommended_settings("pixverse", use_case="short_form")
# Returns: {"aspect_ratio": "9:16", "resolution": "720"}

# List all providers with a feature
video_providers = list_providers(type="video", feature="image_to_video")

# Generate image with Perchance
result = await perchance_skill.generate(
    prompt="cyberpunk city",
    generator="default",
    resolution="portrait_hd",
    aspect_ratio="9:16",
    negative_prompt="blurry, deformed",
    seed=42,
    batch_size=4
)
```

#### API Usage

```bash
# Auto-detect use case from message
POST /agent/chat
{"message": "generate video tiktok using pixverse", "context": {}}

# With custom settings
POST /agent/chat
{
  "message": "generate anime portrait",
  "context": {
    "provider": "perchance",
    "generator": "anime",
    "resolution": "portrait_hd",
    "aspect_ratio": "9:16"
  }
}
```

## Quota Management

### Daily Limits by Subscription Tier

| Tier | Free Videos/Day | Paid Videos/Day | Total Credits/Month |
|------|-----------------|-----------------|-------------------|
| **Free** | 5 | 0 | 0 |
| **Creator** | 20 | 5 | 50 |
| **Empire** | Unlimited | Unlimited | 200 |
| **Sovereign** | Unlimited | Unlimited | 500 |
| **Studio** | Unlimited | Unlimited | 1000 |

### Cost Calculation

```python
# Credits required per video generation
credit_costs = {
    "free_providers": 0,      # ZSky, Kling, PixVerse, free Replicate
    "replicate_paid": 5,      # Wan, Seedance, Hailuo
    "local_gpu": 10-15,       # LTX, Hunyuan, Mochi, etc.
    "cloud_premium": 25-30,   # Veo3, Runway, Pika
}

# Example: 5 videos/day with Wan 2.2
daily_cost = 5 * 5 = 25 credits = ~$2.50/day
monthly_cost = 25 * 30 = 750 credits = ~$75/month
```

## Metadata Tracking Implementation

### Audit Logging
Every video generation is logged with full metadata:

```python
audit_service.log(
    action="VIDEO_GENERATE_START",
    user_id=user_id,
    resource_type="VIDEO",
    resource_id=task_id,
    details={
        "engine": engine,        # zsky, kling, wan, veo3, etc.
        "style": style,          # Cinematic, Viral, etc.
        "aspect_ratio": aspect_ratio,
        "custom_image": bool(custom_image_url),
        "provider": provider,    # From FreeVideoProvider result
        "model": model,          # From provider metadata
        "cost": cost             # Actual cost incurred
    }
)
```

### Provider Fallback Chain
```python
# Configurable priority order
AI_VIDEO_PROVIDER=zsky              # Primary
AI_VIDEO_FALLBACKS=kling,pixverse,replicate_wan,replicate_seedance

# Automatic failover with cost optimization
providers = ["zsky", "kling", "pixverse", "replicate_wan", "replicate_seedance"]
for provider in providers:
    if has_api_key(provider) and within_quota(provider):
        result = await generate_with_provider(provider, ...)
        if result:
            # Log which provider succeeded
            audit_service.log_provider_success(provider, result["metadata"])
            return result
```

## Usage Examples

### Check Available Quotas
```bash
# Get current user's daily video quota status
GET /api/user/quota/video

Response:
{
  "free_used": 3,
  "free_limit": 20,
  "paid_used": 1,
  "paid_limit": 5,
  "credits_remaining": 47,
  "reset_time": "2026-04-07T00:00:00Z"
}
```

### Generate Video with Metadata Tracking
```bash
POST /video/generate
{
  "prompt": "A cat playing piano",
  "engine": "zsky",
  "style": "Cinematic"
}

Response:
{
  "task_id": "video_123456",
  "status": "queued",
  "estimated_cost": 0,
  "provider": "zsky",
  "model": "zsky-wan"
}
```

### Query Generation History
```bash
GET /video/history?user_id=123

Response: [
  {
    "id": "video_123456",
    "title": "A cat playing piano",
    "status": "completed",
    "provider": "zsky",
    "model": "zsky-wan",
    "cost": 0,
    "created_at": "2026-04-06T10:30:00Z",
    "output_url": "https://cdn.example.com/video.mp4"
  }
]
```

## Cost Optimization Strategy

### Automatic Provider Selection
```python
def select_optimal_provider():
    """
    Choose provider based on:
    1. Free quota availability
    2. Quality requirements
    3. Cost efficiency
    4. API reliability
    """
    # Priority: Free → Cheap → Quality → Fallback
    free_providers = ["zsky", "kling", "pixverse"]
    cheap_providers = ["replicate_wan", "replicate_hailuo"]
    quality_providers = ["replicate_seedance", "veo3", "runway"]

    for provider in free_providers + cheap_providers + quality_providers:
        if can_use_provider(provider):
            return provider

    return "lite4k"  # Local GPU fallback
```

This ensures maximum free usage while maintaining quality and reliability.