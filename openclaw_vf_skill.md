---
name: viralforge
description: Interface with the ViralForge social scanning and discovery engine.
---

# ViralForge Skill

Autonomous sentinel for discovering viral content and managing infrastructure.

## Commands

### /scan
Trigger a targeted scan for viral content in specific niches.
- `niches`: comma-separated list of niches (e.g., 'AI, Motivation, Gaming')

### /search
Search for discovered content candidates based on a query.
- `q`: search query string

### /vf-health
Check the operational status of the ViralForge API and scanners.

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

## Writing Style (ViralForge Sentinel)
- Scientific but proactive.
- Use emojis for viral alerts: 🚀, 📈, 🔥.
- Bullet points for scan results.
