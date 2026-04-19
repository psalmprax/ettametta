---
status: testing
phase: 02-content-discovery
source: [.planning/phases/02-content-discovery/02-01-SUMMARY.md, .planning/phases/02-content-discovery/02-02-SUMMARY.md, .planning/phases/02-content-discovery/02-03-SUMMARY.md]
started: 2026-04-18T21:20:00Z
updated: 2026-04-18T21:20:00Z
---

## Current Test

number: 1
name: Cold Start Smoke Test
expected: |
  Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application using `docker compose up --build`. Server boots without errors, database migrations complete, and `GET /api/health` returns status "ok".
awaiting: user response

## Tests

### 1. Cold Start Smoke Test
expected: |
  Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application using `docker compose up --build`. Server boots without errors, database migrations complete, and `GET /api/health` returns status "ok".
result: [pending]

### 2. Automated Trending Content Collection
expected: |
  Access the database or logs. Verify that the YouTube scanner is triggered by Celery Beat (or manually via `POST /api/discovery/scan`). Verify that new records are inserted into `ContentCandidateDB` with complete metadata (title, platform, engagement metrics).
result: [pending]

### 3. Advanced Content Search API
expected: |
  Perform a search via `GET /api/discovery/search?platform=youtube&min_views=1000`. Verify that the response contains only YouTube results with at least 1000 views, correctly paginated.
result: [pending]

### 4. Semantic Normalization Check
expected: |
  Check the response from `GET /api/discovery/trending`. Verify that all results contain `source_url` and `creator_name` fields. Ensure legacy `url` and `author` fields are either absent from the Pydantic response or correctly mirrored for backward compatibility.
result: [pending]

### 5. Content Analysis API
expected: |
  Request analysis for a specific candidate via `GET /api/discovery/{content_id}/analysis`. Verify the response contains `topics`, `sentiment`, `keywords`, and a `viral_potential` score.
result: [pending]

### 6. Pipeline Propagation (Hardening)
expected: |
  Trigger a video transformation via `POST /api/video/transform` using a `candidate_id`. Verify that the backend correctly extracts the `source_url` from the candidate and initiates the synthesis task without field mismatch errors.
result: [pending]

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0

## Gaps

[none yet]
