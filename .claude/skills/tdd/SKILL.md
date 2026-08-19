---
name: tdd
description: Enforce Test-Driven Development (TDD) red-green-refactor cycle. Use when creating new features, fixing bugs, or implementing services to ensure code is verified by automated tests.
---

# Test-Driven Development (TDD) Skill

Enforces the classic Red-Green-Refactor discipline to ensure high code quality, zero regressions, and robust verification.

## Core Rules

1. **Never write implementation code without a failing test first (RED).**
2. **Write the minimal code necessary to make the test pass (GREEN).**
3. **Refactor for clarity, architecture, and performance while keeping tests green (REFACTOR).**

---

## The 3-Phase Workflow

### 1. Phase RED — Write the Failing Test
- Identify the target behavior, edge cases, and interfaces.
- Create or update the test file in `api/tests/` or `tests/`.
- Run the test suite:
  ```bash
  pytest tests/test_<target>.py -v
  # OR for frontend:
  npm --prefix apps/dashboard run test
  ```
- **Verify that the test fails for the expected reason** (e.g. `ImportError`, `AttributeError`, assertion failure) rather than a syntax error.

### 2. Phase GREEN — Implement Minimum Code
- Write the simplest code that makes the failing test pass.
- Do not over-engineer or add speculative functionality not covered by tests.
- Re-run the test to confirm it passes:
  ```bash
  pytest tests/test_<target>.py -v
  ```

### 3. Phase REFACTOR — Clean Up & Adhere to Architecture
- Refactor according to ettametta conventions:
  - Ensure service singletons follow `base_[service_name]_service`.
  - Maintain type annotations and error handling.
  - Remove dead code or debugging artifacts.
- Verify all unit and integration tests still pass.

---

## Checklist Before Finishing
- [ ] Failing test written before code.
- [ ] Test fails with meaningful assertion output.
- [ ] Code passes test cleanly.
- [ ] Edge cases (null values, timeouts, network failures) tested.
- [ ] Tests run quickly and do not depend on unmocked external APIs.
