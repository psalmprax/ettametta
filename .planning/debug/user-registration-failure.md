---
status: investigating
trigger: "**Issue:** POST /auth/register with valid email/password creates new user account. Returns 201 status with user data (excluding password).

**Expected:** POST /auth/register with valid email/password creates new user account. Returns 201 status with user data (excluding password).

**Actual:** describe

**Errors:** None reported

**Reproduction:** Test 1 in UAT

**Timeline:** Discovered during UAT

**Goal:** find_root_cause_only"
created: 2026-04-08T22:11:27+02:00
updated: 2026-04-08T22:11:27+02:00
---

## Current Focus

hypothesis: Conflicting UserDB model definitions causing database column mismatch during registration
test: Verify the database schema and column names used in registration
expecting: Find that table has 'hashed_password' but code sets 'password_hash'
next_action: Check database schema or run registration test

## Symptoms

expected: POST /auth/register with valid email/password creates new user account. Returns 201 status with user data (excluding password).
actual: describe
errors: None reported
reproduction: Test 1 in UAT
started: Discovered during UAT

## Eliminated

## Evidence

- timestamp: 2026-04-08T22:11:27+02:00
  checked: UserDB model definitions
  found: Two conflicting UserDB classes: one in user_models.py with hashed_password/Integer ID, one in models.py with password_hash/UUID ID
  implication: Database tables created with user_models schema, but auth code uses models schema

- timestamp: 2026-04-08T22:11:27+02:00
  checked: Auth route imports
  found: auth.py imports UserDB from models.py (password_hash field)
  implication: Registration code expects password_hash column

- timestamp: 2026-04-08T22:11:27+02:00
  checked: Main.py table creation
  found: Imports UserDB from user_models.py and calls Base.metadata.create_all
  implication: Users table created with hashed_password column, not password_hash

- timestamp: 2026-04-08T22:11:27+02:00
  checked: Field usage in codebase
  found: password_hash used in auth.py, hashed_password used in user_models.py and security.py
  implication: Inconsistent naming convention causing mismatch

## Resolution

root_cause: Conflicting UserDB model definitions with different password field names (password_hash vs hashed_password) and ID types, causing SQL column errors during user registration
fix: 
verification: 
files_changed: []