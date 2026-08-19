---
name: to-issues
description: Decompose a PRD or feature specification into vertical, testable, independently shippable task tickets. Use after /to-prd to prepare execution phases.
---

# To-Issues (Task Slicing) Skill

Decomposes architectural specifications and PRDs into atomic, vertical slices of work.

## Ticket Breakdown Rules

1. **Vertical Slices**: Each ticket should touch the minimum layers needed to be testable end-to-end (e.g. Model -> Service -> API Route -> Test).
2. **Strict Independence**: Tickets should minimize blocking dependencies.
3. **Built-in Verification**: Every ticket must have an automated test verification command (`pytest tests/test_xyz.py`).

## Ticket Template

```markdown
### Task [N]: [Action-Oriented Title]
- **Goal**: Concise description of what this task implements.
- **Files to Modify/Create**:
  - `src/...`
  - `tests/...`
- **Dependencies**: Prerequisites if any.
- **Verification**: `pytest tests/test_xyz.py` or equivalent check.
```
