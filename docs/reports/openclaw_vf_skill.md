---
name: ettametta
description: Interface with the ettametta social scanning and discovery engine.
---

# ettametta Skill

Autonomous sentinel for discovering viral content and managing infrastructure.

## Commands

### /scan
Trigger a targeted scan for viral content in specific niches.
- `niches`: comma-separated list of niches (e.g., 'AI, Motivation, Gaming')

### /intelligent-scan
Perform a deep, multi-platform resilient scan with LLM query expansion.
- `niche`: single niche/topic to explore deeply.

### /narrative-fusion
Trigger an autonomous multi-clip narrative video production task.
- `niche`: topic for the narrative.
- `duration`: video duration in seconds.

### /search
Search for discovered content candidates based on a query.
- `q`: search query string

### /vf-health
Check the operational status of the ettametta API and scanners.

### /storage
Check the local video storage usage and cloud migration status.

### /ltx
Check status of the remote LTX-2 video synthesis node.

## Actions

### Scan
```json
{
  "action": "scan",
  "niches": ["AI"]
}
```

### Search
```json
{
  "action": "search",
  "q": "funny cat videos"
}
```

### Health
```json
{
  "action": "health"
}
```

### Storage
```json
{
  "action": "storage"
}
```

### LTX Status
```json
{
  "action": "ltx_status"
}
```

### Intelligent Scan
```json
{
  "action": "intelligent_scan",
  "niche": "AI Productivity Tools"
}
```

### Narrative Fusion
```json
{
  "action": "autonomous_fusion",
  "niche": "Future of Robotics",
  "duration": 60
}
```

## Writing Style (ettametta Sentinel)
- Scientific but proactive.
- Use emojis for viral alerts: 🚀, 📈, 🔥.
- Bullet points for scan results.
