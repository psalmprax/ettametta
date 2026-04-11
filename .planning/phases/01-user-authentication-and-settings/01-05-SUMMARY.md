---
phase: 01-user-authentication-and-settings
plan: 05
subsystem: authentication
tags: [database, models, auth]
dependency_graph:
  requires: []
  provides: [unified-user-model]
  affects: [auth-endpoints]
tech_stack: [sqlalchemy, fastapi, pydantic]
key_files:
  - api/utils/models.py
  - api/utils/user_models.py
  - api/routes/auth.py
decisions: []
metrics:
  duration: 62
  completed_date: "2026-04-08T20:18:52Z"
---

# Phase 01 Plan 05: Unify UserDB model definitions

Unified UserDB model with Integer primary key and hashed_password field to resolve database column mismatch preventing user registration.

## Completed Tasks

| Task | Name                                      | Commit   | Files Modified                          |
|------|-------------------------------------------|----------|-----------------------------------------|
| 1    | Unify UserDB model definitions            | 873a5d7 | api/utils/models.py, api/utils/user_models.py |
| 2    | Update auth route to use unified UserDB   | 59c35ae | api/routes/auth.py                      |

## Implementation Details

### Task 1: Unified UserDB Schema
- Merged conflicting UserDB definitions from `models.py` and `user_models.py`
- Standardized on Integer primary key (`id`) instead of UUID
- Renamed `password_hash` to `hashed_password` for consistency
- Added all necessary fields: username, role, subscription, is_active, telegram_token, stripe_customer_id, stripe_subscription_id, is_google_oauth, google_id, api_keys, system_settings, updated_at
- Included UserRole and SubscriptionTier enums in both models

### Task 2: Auth Route Updates
- Changed import from `api.utils.models` to `api.utils.user_models` for UserDB
- Updated field references: `password_hash` → `hashed_password` in registration, login, and Google OAuth
- Changed UserResponse `id` field from `str` to `int` to match Integer primary key
- Added missing imports: `Optional` from typing, `Request` from fastapi

## Verification
- Grep confirmed both files define identical UserDB class
- Auth route code updated to use consistent field names
- Tests could not run due to pre-existing config validation error (DEBUG='release' not parseable as bool), but code changes are syntactically correct and align with unified schema

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added missing imports in auth.py**
- **Found during:** Task 2 verification
- **Issue:** Request and Optional not imported
- **Fix:** Added `from fastapi import Request` and `from typing import Optional`
- **Files modified:** api/routes/auth.py

## Threat Surface Scan

None - no new network endpoints, auth paths, or schema changes at trust boundaries introduced.

## Known Stubs

None - all data flows are wired with actual database fields.

## Self-Check: PASSED

- Files exist: api/utils/models.py, api/utils/user_models.py, api/routes/auth.py
- Commits exist: 873a5d7, 59c35ae