---
phase: 17-revenue-txid-backfill-idempotency
plan: 01
title: "Verify NOT IN subquery + add 3-pass integration test + structural regression test"
status: complete
depends_on: [Phase 7 (Monetization)]
created: 2026-06-19
completed: 2026-06-19
gsd_version: 1.1
---

# Phase 17-01 — Summary

## What Shipped

Verification and hardening of the revenue transaction_id backfill idempotency. 80% of the work was already in place (SQL fix + xfail removal from prior deployment). This plan added structural regression tests and a 3-pass integration test.

## Task Results

### Task 1: Verify NOT IN subquery ✅
- Confirmed `(platform, metadata_json->>'transaction_id') NOT IN` present at line 112 of `alembic/versions/2026_06_16_backfill_txid.py`
- Inner subquery `SELECT platform, transaction_id FROM revenue_logs WHERE transaction_id IS NOT NULL` confirmed

### Task 2: Add 3-pass idempotency test ✅
- Added `test_backfill_is_idempotent_over_three_passes` to `TestBackfillFixturesOnPostgres`
- Asserts: pass-1 writes 2 winners, pass-2 writes 0, pass-3 writes 0
- Asserts: loser row a-002 stays NULL after all three passes
- Cleanly skips when DATABASE_URL is unset

### Task 3: Structural regression test ✅
- Added `test_candidates_not_in_subquery_prevents_unique_violation` to `TestBackfillStructure`
- AST-parses `_BACKFILL_SQL` and asserts NOT IN subquery is present
- Regression catcher: future cleanup that drops NOT IN will fail this test

### Task 4: Full test module verification ✅
- 20 passed, 8 skipped (DB-backed tests skip without DATABASE_URL)
- Zero xfail markers confirmed via grep

## Files Modified
- `tests/migrations/test_revenue_txid_migrations.py` — added 2 new test methods
- `.planning/ROADMAP.md` — Phase 17 entry added

## Test Results
```
tests/migrations/test_revenue_txid_migrations.py::TestBackfillStructure::test_candidates_not_in_subquery_prevents_unique_violation PASSED
tests/migrations/test_revenue_txid_migrations.py::TestBackfillFixturesOnPostgres::test_backfill_is_idempotent_over_three_passes SKIPPED (no DATABASE_URL)
20 passed, 8 skipped in 0.15s
```
