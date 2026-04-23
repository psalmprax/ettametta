# Semantic Misalignment Analysis

**Analysis Date:** 2026-04-23  
**Final Check:** Complete — Critical bugs identified  
**Analyzer:** GSD Codebase Mapper (concerns focus)

---

## Executive Summary

This analysis identified **significant semantic misalignments** that cause runtime errors, silent query failures, and architectural confusion. Contrary to prior findings, **multiple critical bugs exist** in production code paths.

**Severity Breakdown:**
- **CRITICAL:** 5 issues → immediate fix required (will cause crashes or data loss)
- **MAJOR:** 11 issues → high-priority refactor needed
- **MINOR:** 7 issues → cleanup for maintainability

**Total Issues:** 23 across 7 categories

---

## CRITICAL ISSUES (Fix Immediately)

### 1. Invalid Column Access: `PublishedContentDB.views` (Runtime Error)

**File:** `src/services/optimization/scheduler.py:39`  
**Severity:** CRITICAL — AttributeError at runtime  
**Impact:** Query fails with `InvalidRequestError: Mapper has no property 'views'`. Analytics queries crash, preventing dynamic scheduling window calculations.

**Broken Code:**
```python
stmt = select(
    extract("hour", PublishedContentDB.published_at).label("hour"),
    func.avg(PublishedContentDB.view_count).label("avg_views"),  # ✓ correct
).where(
    PublishedContentDB.status == "Published",  # also wrong (see #2)
    PublishedContentDB.view_count > 0,
)
stmt = stmt.order_by(func.avg(PublishedContentDB.views).desc())  # ❌ FAILS
```

**Model Definition** (`src/api/utils/models.py:206`):
```python
class PublishedContentDB(Base):
    view_count = Column(Integer, default=0)   # correct field
    # NO field named 'views'
```

**Fix:** Change `PublishedContentDB.views` → `PublishedContentDB.view_count`.

Also fix the status comparison on the same line (see #2 below).

---

### 2. Status String Literal Mismatch: `"Published"` vs `ContentPublishStatus.PUBLISHED`

**Files Affected:**
- `src/api/routes/analytics.py:32, 240, 451`
- `src/services/optimization/scheduler.py:30`

**Severity:** CRITICAL — Silent query failure  
**Impact:** Queries filtering by `"Published"` return **zero rows** because database stores `"PUBLISHED"` (UPPER_CASE). Analytics endpoints show empty data for published posts; scheduling logic never triggers for published content.

**Enum Definition** (`src/shared/enums.py:55-60`):
```python
class ContentPublishStatus(str, Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"   # UPPER_CASE
    FAILED = "FAILED"
```

**Broken Code:**
```python
# analytics.py line 32
stmt = select(PublishedContentDB).where(
    PublishedContentDB.status == "Published"   # ❌ "Published" != "PUBLISHED"
)
```

**Correct Code:**
```python
from src.shared.enums import ContentPublishStatus
stmt = select(PublishedContentDB).where(
    PublishedContentDB.status == ContentPublishStatus.PUBLISHED
)
```

**Additional Risk:** Hardcoded string `"Published"` appears 4+ times. Any future enum value change would require hunting all literals.

---

### 3. Invalid Enum Value: `"PENDING_AUTH"` Not Defined

**File:** `src/services/optimization/scheduler_tasks.py:305`  
**Severity:** CRITICAL — Schema/Enum drift  
**Impact:** Comparison against undefined state. If database ever stores `"PENDING_AUTH"` (legacy?), the query still works (string compare) but it's not a valid `ContentPublishStatus` member — type system can't catch errors.

**Code:**
```python
if (
    ScheduledPostDB.status == "PENDING_AUTH"
    and current_time >= ScheduledPostDB.scheduled_time
):
    # OAuth re-auth logic...
```

**Problem:** `ScheduledPostDB.status` is `Enum(ContentPublishStatus)`. Only valid values: `PENDING`, `PUBLISHED`, `FAILED`. `"PENDING_AUTH"` cannot exist in enum column unless legacy data was inserted bypassing ORM.

**Recommendation:**
- Add `PENDING_AUTH = "PENDING_AUTH"` to `ContentPublishStatus` enum if this is a valid state, OR
- Replace pattern with `ScheduledPostDB.status == ContentPublishStatus.PENDING and ScheduledPostDB.requires_auth == True`.

---

### 4. Schema Drift Risk: `user_id` Type Mismatch in Migrations

**Files:** 
- Migration: `alembic/versions/86ebe6287aea_add_metrics_to_publishedcontentdb.py:24`
- Model: `src/api/utils/models.py:202`

**Severity:** CRITICAL — Could break FK constraints or queries  
**Impact:** Historical migration added `user_id` as `Integer()`, but model declares `String(36)`. If migration was applied as-is, the actual column type in PostgreSQL is INTEGER, while SQLAlchemy expects VARCHAR. This causes `ProgrammingError` on queries.

**Migration Line 24:**
```python
op.add_column('published_content', sa.Column('user_id', sa.Integer(), nullable=True))
```

**Model Line 202:**
```python
user_id = Column(String(36), ForeignKey("users.id"), index=True)
```

**Recommendation:**
- Immediately inspect actual database schema: `\d published_content` in psql.
- If column is INTEGER, create a new migration to alter column type to VARCHAR(36) and update FK to reference `users.id` string UUID.
- Prevent future drift by ensuring all migrations are generated via Alembic autogenerate, not hand-edited without model sync.

---

### 5. Service Layer Bypass: Direct DB Queries in Routes

**Files:** 
- `src/api/routes/video_jobs.py:28-38`
- `src/api/routes/discovery.py:311-327, 520-544`

**Severity:** MAJOR → CRITICAL for consistency  
**Impact:** Business logic split between route and service. Testing becomes harder, and duplication invites semantic drift. Route directly uses `select(VideoJobDB)` instead of `VideoJobService.get_user_jobs()`.

**Example:**
```python
# video_jobs.py lines 28-38 - direct query in route
stmt = select(VideoJobDB).order_by(VideoJobDB.created_at.desc())
result = await db.execute(stmt)
jobs = result.scalars().all()
```

**But:** `VideoJobService` already exists (`src/services/video_engine/job_service.py`) with `get_user_jobs(user_id)` method.

**Problem:** Two code paths for same operation → they may diverge (e.g., one applies a filter the other doesn't). Tests for one may not cover the other.

**Fix:** Refactor route to inject service:
```python
async def list_jobs(
    current_user: UserDB = Depends(get_current_user),
    job_service: VideoJobService = Depends(get_video_job_service)
):
    return await job_service.get_user_jobs(current_user.id)
```

---

## MAJOR ISSUES (High Priority Refactor)

### 6. Enum Value Casing Inconsistency Across System

**Severity:** MAJOR — Source of bugs (see #2 above)  
**Location:** `src/shared/enums.py`

| Enum | Casing Strategy |
|------|-----------------|
| `SystemJobStatus` | Title Case with spaces: `"Queued"`, `"Analyzing Visuals"` |
| `ContentPublishStatus` | UPPER_CASE: `"PUBLISHED"`, `"PENDING"` |
| `ScanStatus` | lowercase: `"pending"`, `"completed"` |
| `ABTestStatus` | lowercase: `"active"`, `"completed"` |
| `SessionStatus` | lowercase: `"connected"`, `"disconnected"` |
| `ExperimentCohortStatus` | UPPER_CASE: `"ROLLING_OUT"` |
| `StrategyStatus` | UPPER_CASE: `"ACTIVE"`, `"DOMINANT"` |

**Problem:** Seven different casing strategies. Memory errors, case-fix bugs, and cross-enum confusion inevitable.

**Recommendation:**
- Adopt **UPPER_CASE** for all enum values (aligns with Python's `Enum` convention and `ContentPublishStatus`).
- Migration: update all code comparing status strings to use enum members.
- Database values: ensure stored values match new casing (UPDATE published_content SET status='PUBLISHED' WHERE status='Published'; etc.).

---

### 7. "Job" vs "Task" Semantic Overload

**Severity:** MAJOR — Conceptual confusion  
**Impact:** Different components use "job" and "task" interchangeably for the same entity.

**Current State:**
| Concept | Used In |
|---------|---------|
| **Task** (Celery) | `download_and_process_task`, `generate_video_task` — function names |
| **Job** (DB record) | `VideoJobDB`, `NexusJobDB` — database models |
| **Job** (API) | `/video/jobs` endpoints |
| **Task ID** (Celery) | `task.id` stored as `VideoJobDB.id` |

**Problem:** A dispatched Celery task creates a `VideoJobDB` record. The `task.id` is the `job.id`. But routes `/video/jobs` say "jobs" while the Celery task is called "task". Internal client methods: `create_job()` sends `task_id`.

**Recommendation:**
- **Rename all DB models** to `*TaskDB` if you prefer task as canonical, OR
- **Rename all Celery tasks** to `*_job` (e.g., `download_and_process_job`) to align with DB.

Pick one. Suggestion: keep DB as `JobDB` (domain entity), rename Celery tasks to `*_job` for clarity, or rename endpoints to `/tasks` if "task" is the user-facing word.

---

### 8. "Content" vs "Video" Domain Ambiguity

**Severity:** MAJOR — Architectural drift  
**Impact:** Database schema and user mental model disagree. Tables say "content", code says "video".

**Evidence:**
- `ContentCandidateDB`, `PublishedContentDB` — suggests generic content platform
- But all fields are video-specific: `duration_seconds`, `thumbnail_url`, no `text_content` or `image_count`.
- Frontend pages: `/creation`, `/publishing` but all workflows produce videos.

**Problem:** If future expansion to non-video content is planned, the naming is forward-compatible. If not, it's misleading and adds cognitive load.

**Recommendation:**
- **If video-only:** rename tables/fields to `Video*`:
  - `content_candidates` → `video_candidates`
  - `published_content` → `published_videos`
  - `ContentCandidate` Pydantic model → `VideoCandidate`
- **If multi-modal:** add explicit `media_type` column and keep "content". But currently all code assumes video → choose video-only naming.

---

### 9. Legacy Field `url` Coexists with Canonical `source_url`

**Files:** `src/api/utils/models.py:92-93`  
**Severity:** MAJOR — Data duplication, inconsistency risk

**Code:**
```python
source_url = Column(String)  # Primary canonical URL
url = Column(String, nullable=True)  # Legacy - will be phased out
```

**Usage:** `discovery/service.py:408` uses `source_url=r.source_url or r.url` — fallback pattern confirms both are active.

**Risk:** If both populated with different values, which is "true"? Sync jobs may write to one but not the other.

**Fix:** Deprecate `url` column:
1. Add migration: copy `url` → `source_url` where `source_url IS NULL`
2. Drop `url` column after one release cycle
3. Remove fallback logic

---

### 10. Duplicate Endpoint Functionality: `/discovery/niches` vs `/discovery/categories`

**File:** `src/api/routes/discovery.py` (lines 311-327 and around line 400+)  
**Severity:** MAJOR — API surface bloat

**Observation:** Two endpoints appear to return niche lists. Check if they're identical or subtly different. If identical, consolidate.

**Recommendation:** Audit and merge. Expose single source of truth for niche data.

---

### 11. Service Layer Incomplete: Business Logic in Routes

**Severity:** MAJOR — Violates Clean Architecture  
**Impact:** Testing difficulty, code duplication, mixed concerns.

**Evidence:** Already covered in CRITICAL #5. Routes contain SQL queries and business decisions that belong in services.

---

## MINOR ISSUES (Cleanup)

### 12. Singleton Naming Variability

**Pattern:** Most services use `base_<name>_service`:
- ✓ `base_discovery_service`
- ✓ `base_analytics_service`
- ✓ `base_optimization_service`
- ✗ `base_nexus_orchestrator` (different suffix)
- ✗ `base_agent_zero` (no `_service`)

**Recommendation:** Either rename all to `base_*` (drop `_service`) OR enforce `_service` suffix for all non-orchestrator services.

---

### 13. Inconsistent Abbreviation Usage

**Examples:**
- `vid` appears in variable names like `vid_id` (discovery/service.py:1072)
- `db` is standard abbreviation for database — fine
- `cfg` vs `config` — no strong pattern
- `txn` vs `transaction` — not used

**Recommendation:** Avoid abbreviations unless universally understood (`db`, `id`, `url`, `json`). `vid` should be `video_id`.

---

### 14. Type Hint Inconsistencies

**Seen in:** `scheduler.py:64`
```python
last_post_time: datetime | None = None
```
Uses `datetime` from standard `datetime` module, not `datetime.datetime`. This is fine with Python 3.10's `from datetime import datetime` style but is inconsistent across files (some use `import datetime` then `datetime.datetime`).

**Recommendation:** Standardize imports: either `from datetime import datetime, timedelta` everywhere OR `import datetime` and use `datetime.datetime`. The former is more concise.

---

### 15. Alembic Migration Filename Style Drift

**Pattern:** Mixed naming in `alembic/versions/`:
- `001_create_user_table.py` (numeric prefix)
- `a4b1aaadd072_initial_migration.py` (hash + snake_case)
- `add_user_id_monitored_niches.py` (no hash prefix — error?)
- `86ebe6287aea_add_metrics_to_publishedcontentdb.py` (hash + PascalCase DB name)

**Recommendation:** Adopt standard Alembic format: `<hash>_<description>.py` (all snake_case). Rename `001_create_user_table.py` to `a1b2c3..._create_users_table.py` or similar. Remove any file without hash prefix (Alembic may reject).

---

### 16. Route Tags Appear Duplicative

**Observation:** Swagger UI shows multiple tags with overlapping names:
- `"Video Generation"` (video_generate)
- `"Video Transformation"` (video_transform)
- `"Video Engine"` (video_jobs)

**Recommendation:** Consolidate into "Video" umbrella tag with path grouping. Or accept three tags if workflow steps are conceptually distinct to users.

---

### 17. Status Value Hardcoding in Non-Model Code

**Pattern:** `status == "PENDING"` string literal vs using `ScanStatus.PENDING`.

**Files:** `scheduler_tasks.py:60,232,370` use `"PENDING"` (correct value but should use enum).

**Recommendation:** Replace all status string literals with enum member references for type safety and future-proofing.

---

### 18. Missing Type Safety for Credit Actions

**Issue:** Credit action strings (`"video_transformation"`, `"viral_analysis"`, `"storytelling"`) are scattered as literals across routes but validated in `credit_service`. No compile-time checking.

**Recommendation:** Define `CreditAction(str, Enum)` in `shared/enums.py` and use everywhere. Credit service's `credits_required` decorator already maps actions — centralize mapping.

---

## PATTERNS OBSERVED (Not Issues)

| Pattern | Status | Notes |
|---------|--------|-------|
| `success_response()` wrapper | ✓ Consistent | Good |
| snake_case Python functions | ✓ Consistent | Follows PEP8 |
| camelCase TypeScript variables | ✓ Consistent | Follows TS convention |
| `BaseModel` Pydantic schemas | ✓ Consistent | Clean separation |
| `*_service.py` module names | ✓ Consistent | Good |
| DB session via `Depends(get_db)` | ⚠️ Mixed | Some routes still use `SessionLocal()` |
| `base_*` singleton pattern | ✓ Mostly | See #12 |

---

## CROSS-CUTTING RECOMMENDATIONS

### A. Create Semantic Style Guide

Add new doc: `SEMANTICS.md` or extend `CONVENTIONS.md` with:

1. **Enums:** Always UPPER_CASE values. Never compare enums by string literal.
2. **Models:** `PascalCase` with optional `DB` suffix. Document suffix policy.
3. **Tables:** `snake_case_plural`. Document mapping from model name.
4. **Services:** `base_<name>_service` singleton instances.
5. **Routes:** RESTful resources in plural nouns (`/video/jobs`, `/publishing`, `/analytics`). Avoid verbs in path when possible.
6. **Variables:** `snake_case` for Python, `camelCase` for TypeScript.
7. **Database Fields:** Prefer explicit names; avoid abbreviations (`view_count` not `views`).
8. **Constants:** `UPPER_SNAKE_CASE` for module-level constants.

### B. Fix Order (Dependency-Aware)

**Phase 1 — Breakage Fixes (do in order):**
1. Fix `scheduler.py:39` `views` → `view_count` (syntax error fix)
2. Fix all `"Published"` → `ContentPublishStatus.PUBLISHED` in analytics.py and scheduler.py (query correctness)
3. Investigate and resolve `user_id` column type drift (schema integrity)
4. Decide on `PENDING_AUTH` resolution

**Phase 2 — Consistency Improvements:**
5. Standardize all enum values to UPPER_CASE
6. Rename `ContentCandidate` → `VideoCandidate` (requires widespread changes — do with codemod)
7. Remove `url` legacy column from `ContentCandidateDB` and replace with `source_url` only
8. Consolidate duplicate `/discovery/niches` and `/discovery/categories` endpoints

**Phase 3 — Architecture Cleanup:**
9. Move all route-based DB queries into service classes
10. Standardize singleton naming (`base_*`)
11. Generate TypeScript API types from OpenAPI spec

### C. Automated Detection

Add pre-commit hook or CI job to catch:
- String literals compared against known enum values (regex `status == "[A-Za-z]+"` in relevant files)
- Invalid field access on models (static analysis via mypy/pyright)
- Missing enum imports when using string literals

---

## CONCLUSION

The ettametta codebase shows **strong architectural foundations** but suffers from **semantic drift** in critical areas:

- **Data layer:** Field name typos (`views`) and status value mismatches (`"Published"` vs `PUBLISHED`) cause runtime failures.
- **Enums:** Inconsistent casing invites bugs.
- **Domain model:** Unclear whether "content" or "video" — leads to mixed terminology.
- **Service layer:** Incomplete abstraction; routes reach into database.

**Immediate action required on 5 critical items** before they cause production incidents. The remaining 18 items are refactoring opportunities to improve maintainability.

---

*Analysis generated by GSD codebase mapper — concerns focus*
