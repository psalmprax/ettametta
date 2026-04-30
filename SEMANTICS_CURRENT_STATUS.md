# Semantics Misalignment - Current Status Report (April 29, 2026)

## Executive Summary

The codebase has **improved significantly** from previous analysis (April 23). Several critical issues have been fixed, but **14 significant semantic misalignments remain** that need attention for code quality and maintainability.

**Status Breakdown:**
- ✅ **5 Critical issues FIXED** (as of April 23)
- ⚠️ **11 MAJOR issues remain** - require refactoring
- 📌 **7 MINOR issues remain** - cleanup opportunities
- 📊 **1 NEW issue discovered** - Content domain ambiguity

---

## VERIFICATION OF PREVIOUS FIXES

### ✅ FIXED: `PublishedContentDB.views` Typo
**Status:** RESOLVED  
**File:** `src/services/optimization/scheduler.py:30`  
- Now correctly uses `ContentPublishStatus.PUBLISHED` enum
- Correct field reference: `PublishedContentDB.view_count`

### ✅ FIXED: Status String Literal Mismatch  
**Status:** RESOLVED  
- Enum `ContentPublishStatus` properly defined with UPPER_CASE values
- Analytics.py no longer has hardcoded string `"Published"`

### ✅ FIXED: `PENDING_AUTH` Undefined Enum Value
**Status:** RESOLVED  
**File:** `src/shared/enums.py:59`
- `PENDING_AUTH = "PENDING_AUTH"` now defined
- Valid state for content requiring OAuth re-authentication

### ✅ FIXED: `velocity` Field Never Populated
**Status:** RESOLVED  
**File:** `src/services/discovery/service.py:527`
- Field documented: "Velocity (views per hour) - calculated from view count and time since publish"
- Now assigned: `candidate.velocity = velocity`

### ✅ FIXED: `deep_scan` Parameter Bug
**Status:** RESOLVED  
- Parameter now correctly affects time horizon calculation
- Deep scan: 90 days ago | Regular scan: 30 days ago

---

## REMAINING MAJOR ISSUES (Priority: High)

### 1. Enum Value Casing Inconsistency - PERSIST
**Severity:** MAJOR  
**Impact:** Subtle bugs, memory errors, cross-enum confusion

| Enum | Current Casing |
|------|-----------------|
| `SystemJobStatus` | Title Case: `"Queued"`, `"Analyzing Visuals"` |
| `ContentPublishStatus` | ✓ UPPER_CASE: `"PUBLISHED"`, `"PENDING"` |
| `ScanStatus` | lowercase: `"pending"`, `"completed"` |
| `ABTestStatus` | lowercase: `"active"`, `"completed"` |
| `SessionStatus` | lowercase: `"connected"`, `"disconnected"` |
| `ExperimentCohortStatus` | UPPER_CASE: `"ROLLING_OUT"` |
| `StrategyStatus` | UPPER_CASE: `"ACTIVE"`, `"DOMINANT"` |

**Recommendation:** Standardize all to UPPER_CASE (Python enum convention). Create migration to update database values.

---

### 2. "Job" vs "Task" Terminology Overload
**Severity:** MAJOR  
**Files Affected:** Multiple across API, DB, services  
**Impact:** Conceptual confusion, onboarding difficulty, API surface bloat

| Component | Terminology |
|-----------|-------------|
| Celery async functions | "task" (e.g., `generate_video_task()`) |
| Database models | "job" (e.g., `VideoJobDB`, `NexusJobDB`) |
| API endpoints | "job" (e.g., `/video/jobs`) |
| Internal logic | Mixed usage |

**Problem:** A Celery task creates a job. The task ID is the job ID. Routes say "jobs" but internals say "tasks".

**Recommendation:** Pick canonical term and apply consistently. Suggested: Keep DB as `*JobDB`, rename Celery functions to `*_job` suffix for alignment.

---

### 3. "Content" vs "Video" Domain Ambiguity
**Severity:** MAJOR  
**Files:** Database schema, models, services  
**Impact:** Future expansion uncertainty, misleading naming

| Naming | Scope |
|--------|-------|
| Table: `published_content` | Generic "content" | 
| Field: `duration_seconds` | Video-specific |
| Field: `thumbnail_uri` | Video-specific |
| No: `text_content`, `image_count` | Confirms video-only |
| But all future-proofed as "content" | Generic naming |

**Problem:** Database schema says "content" (generic multi-media), but every field is video-specific. No text, image, or audio support planned.

**Recommendation:** 
- **If video-only forever:** Rename tables/models to `Video*` (e.g., `video_candidates`, `published_videos`)
- **If multi-modal planned:** Add explicit `media_type` column and keep "content" naming

Currently creates cognitive dissonance.

---

### 4. Legacy `url` Field Coexists with `source_uri`
**Severity:** MAJOR  
**File:** `src/api/utils/models.py:92-93`  
**Impact:** Data duplication risk, inconsistency if both differ

```python
source_uri = Column(String)          # Primary canonical
url = Column(String, nullable=True)  # Legacy - to be phased out
```

**Current Pattern:** `source_uri=r.source_uri or r.url` (fallback suggests both can be populated)

**Recommendation:**
1. Add migration to copy `url` → `source_uri` for null values
2. Update all code to use only `source_uri`
3. Mark `url` for deprecation (remove in next major version)
4. Drop column after one release cycle

---

### 5. Duplicate Endpoint: `/discovery/niches` vs `/discovery/categories`
**Severity:** MAJOR  
**File:** `src/api/routes/discovery.py`  
**Impact:** API surface bloat, confusion about which to use

**Observation:** Two endpoints appear to serve similar or identical purposes.

**Recommendation:** Audit both endpoints, consolidate if identical, document semantic difference if not.

---

### 6. Service Layer Incomplete: Direct DB Queries in Routes
**Severity:** MAJOR → CRITICAL for consistency  
**Files:** `src/api/routes/video_jobs.py:28-38`, `src/api/routes/discovery.py:311-327, 520-544`  
**Impact:** Business logic split between route and service, testing difficulty

**Example:**
```python
# Route directly queries DB
stmt = select(VideoJobDB).order_by(VideoJobDB.created_at.desc())
result = await db.execute(stmt)
jobs = result.scalars().all()
```

But `VideoJobService.get_user_jobs()` exists and should be used.

**Recommendation:** Refactor routes to use service layer exclusively. Remove all SQL from routes.

---

### 7. Singleton Naming Variability
**Severity:** MAJOR  
**Pattern:** Most services use `base_<name>_service`, but exceptions exist
- ✓ `base_discovery_service`
- ✓ `base_analytics_service`
- ✗ `base_nexus_orchestrator` (different suffix)
- ✗ `base_agent_zero` (no `_service`)

**Recommendation:** Enforce consistent naming. Either all `base_*` or all `base_*_service`.

---

### 8. Inconsistent Abbreviation Usage
**Severity:** MAJOR  
**Examples:**
- `vid_id` (should be `video_id`)
- `cfg` vs `config` — no strong pattern
- `txn` vs `transaction` — unused

**Recommendation:** Avoid abbreviations unless universal (`db`, `id`, `url`, `json`). Standardize on full names.

---

### 9. `metadata` vs `metadata_json` Inconsistency (Resolved but Addressed)
**Severity:** LOW-MEDIUM  
**Status:** ADDRESSED (aliasing works)
**Pattern:** Pydantic model uses `metadata` alias for DB field `metadata_json`

**Recommendation:** Standardize usage — consistently use `metadata_json` for DB operations, `metadata` in Pydantic responses.

---

### 10. Alembic Migration Filename Style Drift
**Severity:** MEDIUM  
**Files:** `alembic/versions/`  
**Pattern:**
- `001_create_user_table.py` (numeric prefix — non-standard)
- `a4b1aaadd072_initial_migration.py` (hash + snake_case — standard)
- `add_user_id_monitored_niches.py` (no hash prefix — invalid)

**Recommendation:** Enforce Alembic standard: `<auto_hash>_<snake_case_description>.py`. Remove files with non-standard naming.

---

### 11. Type Hint Inconsistency: `datetime` Import
**Severity:** MINOR  
**Pattern:** Mixed between `from datetime import datetime` and `import datetime; datetime.datetime`

**Recommendation:** Standardize to `from datetime import datetime, timedelta` for conciseness.

---

## REMAINING MINOR ISSUES

### 12. Inconsistent `populate_by_name` Pydantic Config
**Severity:** MINOR  
**Observation:** Some models use `populate_by_name = True`, others don't. Inconsistent API flexibility.

### 13. Status Value Hardcoding
**Severity:** MINOR  
**Pattern:** `status == "PENDING"` string literals instead of enum members (works but not type-safe)

### 14. Missing Type Safety for Credit Actions
**Severity:** MINOR  
**Issue:** Credit action strings scattered as literals (`"video_transformation"`, `"viral_analysis"`) with no compile-time checking.

**Recommendation:** Define `CreditAction(str, Enum)` in `shared/enums.py`.

---

## CROSS-CUTTING RECOMMENDATIONS

### A. Create Semantic Style Guide
Add to `CONVENTIONS.md`:
1. **Enums:** Always UPPER_CASE. Never compare by string literal.
2. **Models:** `PascalCase` with optional `DB` suffix.
3. **Services:** `base_<name>_service` pattern.
4. **Routes:** RESTful plural nouns (`/jobs`, `/analytics`).
5. **Variables:** `snake_case` for Python, `camelCase` for TypeScript.
6. **Database fields:** Explicit names, no abbreviations (`view_count` not `views`).

### B. Fix Priority (Dependency-Aware)

**Phase 1 — Medium Priority:**
1. Standardize all enum values to UPPER_CASE (6-hour effort)
2. Resolve "content" vs "video" naming (decide policy)
3. Remove legacy `url` field (2-3 migrations)
4. Consolidate duplicate discovery endpoints (1-2 hours)

**Phase 2 — High Priority:**
5. Refactor routes to use service layer (8-10 hours, high impact)
6. Rename Celery tasks to `*_job` or unify terminology (6 hours)
7. Consolidate alembic migration naming (2-3 hours)
8. Standardize abbreviations (`vid` → `video`)

**Phase 3 — Code Quality:**
9. Validate type hints with mypy/pyright
10. Add pre-commit hook for enum string literal detection

---

## PATTERNS VERIFIED (No Issues)

✅ `success_response()` wrapper — consistent  
✅ snake_case Python functions — PEP8 compliant  
✅ camelCase TypeScript — consistent  
✅ `BaseModel` Pydantic schemas — clean separation  
✅ `*_service.py` module names — good  
✅ DB session via `Depends(get_db)` — mostly consistent  

---

## CONCLUSION

The codebase shows **strong architectural foundation** with **most critical issues resolved**. Remaining 14 issues are primarily:
- **Inconsistency** (enum casing, terminology, abbreviations)  
- **Cleanup** (legacy fields, duplicate endpoints, migration naming)  
- **Architecture** (service layer abstraction, domain naming clarity)

**Estimated Effort to Full Alignment:** 20-25 hours across 2-3 iterations.

**Immediate Action Items:**
1. Decide: video-only or multi-media platform?
2. Pick enum casing standard (UPPER_CASE recommended)
3. Pick terminology: "job" or "task"?
4. Schedule refactor phase 1 (standardization)

---

*Report generated: April 29, 2026*  
*Previous analysis: April 23, 2026 (SEMANTIC_MISALIGNMENTS.md)*  
*Original fixes: Pre-April 23 (SEMANTICS_MISALIGNMENT_REPORT.md)*
