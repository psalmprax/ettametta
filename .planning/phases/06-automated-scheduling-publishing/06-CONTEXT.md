# Phase 6: Automated Scheduling Publishing - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can schedule automated content publishing campaigns with smart timing optimization. Phase delivers PUBLISH-02 requirement.

**Goal from ROADMAP:** Users can schedule automated content publishing campaigns

**Dependency:** Phase 5 (Multi-Platform Publishing)

</domain>

<decisions>
## Implementation Decisions

### Timing (D-01): Smart Windows
- **Smart scheduling:** AI analyzes historic engagement to suggest optimal posting windows
- Uses existing `SmartScheduler` class which calculates peak windows from views data
- Extends `calculate_next_posting_time()` to return N optimal windows for multi-post days

### Queuing (D-02): Smart Parallel
- **Sequential by default:** Posts go out in scheduled order
- **Smart parallel allowed:**
  - If posts are spaced 4+ hours apart → parallel allowed
  - If user explicitly enables same-window → parallel allowed
  - Otherwise, sequential respects timing preferences
- Supports 2+ posts per day through multiple optimal windows

### Time Zone (D-03): UTC Storage
- Store all times in UTC internally
- Convert to user's local timezone on display
- SmartScheduler uses UTC internally (no change needed)

### Interface (D-04): AI-Suggested Times
- Show AI-suggested optimal posting times
- Include engagement prediction for each suggested time
- Clean, minimal UI focused on the suggestion

### Recurrence (D-05): One-Time Only
- Each scheduled post is independent
- No recurring series or templates in v1
- User can create multiple one-time schedules for recurring content
- Keeps implementation scope manageable

### Missed Schedule (D-06): Retry Immediately
- When scheduled post misses window due to downtime:
  - Post immediately when system recovers
  - Simple logic, ensures content publishes

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Code
- `src/services/optimization/scheduler.py` — SmartScheduler class to extend
- `src/api/routes/publish.py` — `/schedule` and `/scheduled` endpoints
- `src/api/utils/models.py` — ScheduledPostDB model

### No external specs required — all requirements captured in decisions above

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SmartScheduler` class — calculates peak engagement windows from historic views
- Existing `/api/v1/publish/schedule` POST endpoint
- Existing `/api/v1/publish/scheduled` GET endpoint
- `ScheduledPostDB` model already defined

### Established Patterns
- Uses datetime.utcnow() for scheduling
- Celery beat_schedule for periodic tasks
- JWT authentication for user-specific scheduling

### Integration Points
- Extend SmartScheduler to return N optimal windows
- Add "parallel" flag to ScheduledPostDB
- UI calls existing schedule endpoints with new parameters

</code_context>

<specifics>
## Specific Ideas

- AI suggests "Best time: Monday 9am (87% predicted engagement)"
- SmartScheduler analyzes top 3 performing hours, extends for multi-post days
- User sees "Suggested times" with confidence percentages
- No calendar UI in v1 — focused on AI suggestion flow

</specifics>

<deferred>
## Deferred Ideas

- Calendar view scheduling (v2)
- Recurring series patterns (v2)
- Template-based scheduling (v2)
- Full parallel posting without spacing rules (v2)

</deferred>

---

*Phase: 06-automated-scheduling-publishing*
*Context gathered: 2026-04-17*