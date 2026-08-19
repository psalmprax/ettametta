---
name: to-prd
description: Convert conversational ideas and requirements into a structured, production-grade Product Requirements Document (PRD). Use when scoping new features or services.
---

# To-PRD (Product Requirements Document) Skill

Transforms unstructured feature ideas into a structured, engineer-ready PRD.

## PRD Structure

Every PRD generated must follow this format:

```markdown
# PRD: [Feature / Service Name]

## 1. Problem Statement & User Value
- What exact user problem or bottleneck does this solve?
- What is the expected business or operational impact?

## 2. Scope & Core Requirements
- **In-Scope**: Bulleted list of non-negotiable features.
- **Out-of-Scope**: Explicit boundaries to prevent scope creep.

## 3. Architecture & Data Flow
- Component interactions (FastAPI, Celery, Redis, PostgreSQL, Frontend).
- Data models & schema alterations.
- Service singletons following `base_[service_name]_service`.

## 4. Edge Cases & Resilience
- Network timeouts, AI provider rate limits, invalid input recovery.
- Fallback strategies (e.g. circuit breakers, mock providers).

## 5. Acceptance Criteria
- [ ] Explicit verifiable criteria #1
- [ ] Explicit verifiable criteria #2
```
