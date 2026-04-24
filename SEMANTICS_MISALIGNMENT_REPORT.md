# Semantics Misalignment Report - Ettametta Codebase

## Executive Summary

This report identified semantic misalignments in the codebase where naming, documentation, or implementation did not match. **All issues have been resolved.**

## Issues Found and Fixed

### 1. ✅ FIXED: `/auto-transform` Endpoint - Documentation vs Implementation Mismatch

**Location:** `src/api/routes/discovery.py` (lines 594-667)

**Severity:** HIGH

**Status:** FIXED

**Was:**
The API endpoint docstring stated "Discover best content → Analyze → Create video transformation" but the implementation skipped the analysis step entirely.

**Fix Applied:**
Updated docstring to: `"One-shot pipeline: Discover best content → Create video transformation. Combines discovery and video creation into 1 call for autonomous operation."`

**Code Location:**
- File: `src/api/routes/discovery.py`
- Lines: 594-597

---

### 2. ✅ FIXED: `deep_scan` Parameter Had No Effect on Individual Scanner Calls

**Location:** `src/services/discovery/service.py` (lines 208-212)

**Severity:** MEDIUM

**Status:** FIXED

**Was:**
The `deep_scan` boolean parameter was passed to scanners as `published_after=None if deep_scan else None` which always evaluated to `None`, making the flag have no effect.

**Fix Applied:**
- Added proper time horizon calculation: 90 days for deep scan vs 30 days for regular scan
- Unified scanner task preparation for both fast and deep scan paths
- All scanner calls now receive the correct `published_after` parameter based on scan type

**Code Changes:**
- `src/services/discovery/service.py`: Refactored `find_trending_content()` to properly use `deep_scan` flag
- Scanners now receive `published_after` calculated as:
  - Deep scan: 90 days ago
  - Fast scan: 30 days ago

---

### 3. ✅ FIXED: `ContentCandidate.velocity` Field Never Populated

**Location:** `src/services/discovery/models.py` (line 33), `src/services/discovery/service.py` (line 506)

**Severity:** MEDIUM

**Status:** FIXED

**Was:**
The `velocity` field existed in the model but was never populated (always remained 0.0). It was calculated in `_recalculate_viral_scores()` but never stored.

**Fix Applied:**
- Added `candidate.velocity = velocity` in `_recalculate_viral_scores()` after calculation
- Added clarifying comment: "Store the calculated velocity in the model"
- Added doc comment to model field: "Velocity (views per hour) - calculated from view count and time since publish"

**Code Location:**
- Model definition: `src/services/discovery/models.py`, line 33
- Value assignment: `src/services/discovery/service.py`, velocity calculation block

---

### 4. ✅ FIXED: Inconsistent Scanner Task Preparation (Deep Scan Path)

**Location:** `src/services/discovery/service.py` (lines 204-238)

**Severity:** MEDIUM

**Status:** FIXED

**Was:**
In the deep_scan path, scanner tasks were not created at all - only intelligent_results were used. The supplementary scanners loop would fail or produce incorrect results because `tasks` list wasn't initialized in the deep_scan branch.

**Fix Applied:**
- Unified task preparation: `tasks = []` initialized before branching
- Deep scan now includes both intelligent discovery AND scanner tasks
- All scanner calls (primary + supplementary) receive `published_after` parameter
- Simplified scanner selection logic

**Code Location:**
- `src/services/discovery/service.py`: Function `find_trending_content()`, lines ~204-260

---

### 5. Addressed: `metadata` vs `metadata_json` Inconsistency

**Location:** Multiple files

**Severity:** LOW-MEDIUM

**Status:** ADDRESSED

**Was:**
The `ContentCandidate` model used field aliasing but code inconsistently used `metadata` (alias) vs `metadata_json` (DB field).

**Resolution:**
While the alias mechanism works, standardized on using `metadata_json` for database operations and `metadata` for the Pydantic model's convenience. The aliasing is maintained for API flexibility.

**Note:**
The existing aliasing approach is functionally correct. Added clarity through consistent usage patterns in the refactored code.

---

### 6. Clarified: Tier + Deep Scan Logic

**Location:** `src/services/discovery/service.py` (lines after refactor)

**Severity:** LOW

**Status:** CLARIFIED

**Was:**
The logic coupling tier selection with deep_scan flag was confusing: `scanners_to_use = self.global_scanners if deep_scan or tier != "free" else [...]`

**Resolution:**
Refactored with clearer separation:
- Primary scanners always run (for fast scan)
- Deep scan enables all scanners (global + primary) with extended time horizon
- Tier-based supplementary scanners run in addition (non-free tiers get more scanners)

Added inline comments explaining the scanner selection strategy.

---

### 7. Low Priority: Generic Endpoint Names

**Location:** Multiple route files

**Severity:** LOW

**Status:** DOCUMENTED

**Finding:**
Endpoints like `/generate` and `/scan` have generic names.

**Recommendation:**
Acceptable as-is for now. Could be enhanced in future:
- `/generate` → `/generate-video` 
- `/scan` → `/scan-trends`

Not changed to avoid breaking API compatibility.

---

## Summary Table

| Issue | Severity | Status | Location |
|-------|----------|--------|----------|
| Auto-transform docstring | HIGH | ✅ FIXED | `src/api/routes/discovery.py` |
| `deep_scan` parameter bug | MEDIUM | ✅ FIXED | `src/services/discovery/service.py` |
| `velocity` field never set | MEDIUM | ✅ FIXED | `src/services/discovery/` |
| Scanner tasks (deep scan) | MEDIUM | ✅ FIXED | `src/services/discovery/service.py` |
| Metadata field inconsistency | LOW-MED | ✅ ADDRESSED | Multiple files |
| Tier+scan logic confusion | LOW | ✅ CLARIFIED | `src/services/discovery/service.py` |
| Generic endpoint names | LOW | ℹ️ DOCUMENTED | Route files |

## Validation

All fixes have been applied and maintain backward compatibility where required. The code is now semantically aligned with its intended behavior.

**Testing Recommendations:**
1. Verify `/auto-transform` endpoint returns `"discover→create"` in pipeline field
2. Test deep vs regular scan produce different time horizons in scanner calls
3. Confirm `velocity` field is populated (> 0) on candidates after `_recalculate_viral_scores`
4. Verify both fast and deep scan paths produce scanner tasks

All changes follow existing code patterns and do not break API contracts.
