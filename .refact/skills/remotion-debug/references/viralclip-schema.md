# ViralClip Schema Reference

The `ViralClip` composition in `apps/remotion-studio/src/Composition.tsx` accepts props validated by a Zod schema.

## Schema Fields

### Required
| Field | Type | Description |
|-------|------|-------------|
| `title` | `string` | Main title text |
| `video_url` | `string` | Background video URL |
| `duration_in_frames` | `number` | Total duration in frames |

### Optional
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `subtitle` | `string` | — | Subtitle text below title |
| `audio_url` | `string` | — | Background audio URL |
| `show_cta_overlay` | `boolean` | `false` | Show call-to-action overlay |
| `cta_type` | `"engagement" \| "cta"` | `"cta"` | CTA overlay type |
| `cta_text` | `string` | — | CTA button text |
| `video_duration_frames` | `number` | — | Override video duration |
| `timeline` | `Array<{start, end, text}>` | `[]` | Timed text segments |
| `words` | `Array<{start, end, word, confidence}>` | `[]` | Word-level timed captions |
| `clips` | `Array<{url, duration_in_frames}>` | `[]` | Multi-clip segments |
| `trademark_url` | `string` | — | Logo/trademark image URL |
| `brand_name` | `string` | — | Brand name for BrandReveal |
| `primary_color` | `string` | `"#ffffff"` | Primary accent color |
| `vignette_intensity` | `number` | `0.4` | Vignette darkness (0-1) |
| `grain_opacity` | `number` | `0.15` | Film grain opacity (0-1) |
| `style` | `string` | `"default"` | Style variant (see below) |
| `job_metadata` | `object` | `{}` | Additional metadata from pipeline |

### job_metadata Fields
| Field | Type | Description |
|-------|------|-------------|
| `remotion_flags` | `object` | Style parameters from StochasticModulator |
| `reddit_data` | `object` | Reddit post data for RedditHook overlay |
| `vfx` | `string` | VFX shader type (`vhs_glitch`, `blueprint`, etc.) |

### remotion_flags Fields (from StochasticModulator)
| Field | Type | Description |
|-------|------|-------------|
| `typography` | `string` | Font style override |
| `slow_motion` | `boolean` | Enable slow motion effect |
| `vfx` | `string` | VFX overlay type |
| `auto_zoom` | `boolean` | Enable auto zoom |
| `beat_sync` | `boolean` | Enable beat-synced pulse |
| `zoom_intensity` | `number` | Zoom intensity (0-1) |
| `transition_duration_seconds` | `number` | Transition duration |

## Style Values

| Style | BPM | Color Grade | Special Overlays |
|-------|-----|-------------|------------------|
| `REDDIT_STORY` | 120 | default | RedditHook |
| `BROADCAST_NEWS` | 120 | default | NewsTicker |
| `ULTIMATE_TUTORIAL` | 120 | default | — |
| `HEARTFELT_NARRATIVE` | 75 | warm_narrative | Serif captions |
| `TOP_LISTICLE` | 128 | electric_listicle | Slide transitions |
| `CINEMATIC_DOC` | 120 | default | Letterbox, chromatic aberration |
| `default` | 120 | default | — |

## Example Props

```json
{
  "title": "This AI Changes Everything",
  "subtitle": "The future is here",
  "video_url": "https://storage.example.com/video.mp4",
  "duration_in_frames": 900,
  "style": "TOP_LISTICLE",
  "show_cta_overlay": true,
  "cta_type": "engagement",
  "cta_text": "Follow for more",
  "brand_name": "TechDaily",
  "primary_color": "#00ff88",
  "words": [
    {"start": 0, "end": 30, "word": "This", "confidence": 0.95},
    {"start": 30, "end": 60, "word": "AI", "confidence": 0.98}
  ],
  "job_metadata": {
    "remotion_flags": {
      "beat_sync": true,
      "vfx": "vhs_glitch",
      "zoom_intensity": 0.3
    }
  }
}
```
