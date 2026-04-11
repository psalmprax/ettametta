---
phase: "01"
fixed_at: 2026-04-10T18:15:21+02:00
review_path: .planning/phases/01-code-review/01-REVIEW.md
iteration: 1
findings_in_scope: 8
fixed: 8
skipped: 0
status: all_fixed
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-04-10T18:15:21+02:00
**Source review:** .planning/phases/01-code-review/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 8
- Fixed: 8
- Skipped: 0

## Fixed Issues

### CR-01: Schema Mismatch

**Files modified:** `alembic/versions/001_create_user_table.py`
**Commit:** 95b99f2
**Applied fix:** Updated migration to use String(36) UUID primary key and added all missing columns (username, role, subscription, is_active, telegram fields, stripe fields, etc.)

### WR-01: Redis connection not closed in api/utils/auth.py

**Files modified:** `api/utils/auth.py`
**Commit:** d3e5298
**Applied fix:** Added try/finally block to ensure Redis client is properly closed in decode_access_token function using await redis_client.aclose()

### IN-01: Move token expiry to settings configuration

**Files modified:** `api/config.py`, `api/utils/auth.py`
**Commit:** 78e08a9
**Applied fix:** Added ACCESS_TOKEN_EXPIRE_MINUTES setting (default 24 hours) to Settings class and updated auth.py to use getattr for backward compatibility

### WR-02: Redis connections not closed in api/routes/auth.py

**Files modified:** `api/routes/auth.py`
**Commit:** aa9653d
**Applied fix:** Added try/finally cleanup in /logout endpoint and removed redundant redis lookup in callback (using signed state instead)

### WR-03: Add password strength validation to UserCreate model

**Files modified:** `api/routes/auth.py`
**Commit:** aa9653d
**Applied fix:** Added field_validator to UserCreate model requiring 8+ characters, uppercase, lowercase, and digit

### WR-04: Add cryptographic signing for OAuth state parameter

**Files modified:** `api/utils/auth.py`, `api/routes/auth.py`
**Commit:** aa9653d
**Applied fix:** Added sign_oauth_state() and verify_oauth_state() functions using HMAC-SHA256, updated /google endpoint to sign state and /callback/google to verify signed state

### IN-02: Remove unused asyncio import

**Files modified:** `api/routes/auth.py`
**Commit:** aa9653d
**Applied fix:** Removed unused asyncio import from routes/auth.py (not needed after changes to callback)

### IN-03: Extract Google OAuth flow configuration to shared function

**Files modified:** `api/routes/auth.py`
**Commit:** aa9653d
**Applied fix:** Created create_google_flow() function and updated all endpoints (/google, /callback/google) to use the shared function

---

_Fixed: 2026-04-10T18:15:21+02:00_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 1_