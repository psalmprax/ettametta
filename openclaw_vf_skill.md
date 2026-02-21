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

### /search
Search for discovered content candidates based on a query.
- `q`: search query string

### /vf-health
Check the operational status of the ettametta API and scanners.

### /storage
Check the local video storage usage and cloud migration status.

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

## Writing Style (ettametta Sentinel)
- Scientific but proactive.
- Use emojis for viral alerts: 🚀, 📈, 🔥.
- Bullet points for scan results.
