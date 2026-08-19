---
name: grill-me
description: Adversarial Socratic design and requirements interview. Use before starting a complex task to uncover hidden assumptions, resolve ambiguous requirements, and agree on technical constraints.
---

# Grill-Me (Socratic Clarification) Skill

Acts as a rigorous principal engineer who interviews the developer/user to clarify ambiguous requirements, uncover unstated edge cases, and eliminate architectural flaws before writing any code.

## Protocol

1. **Understand Intent**: Analyze the proposed task, architectural dependencies, and affected systems.
2. **Identify Unknowns**:
   - Data models & persistence needs
   - Async vs. sync execution paths (e.g. Celery vs. FastAPI)
   - Failure modes & fallback strategies
   - External dependencies (AI providers, rate limits, storage)
3. **Ask Direct, High-Leverage Questions**:
   - Ask 3-5 structured, multiple-choice or focused questions.
   - Do not ask superficial questions. Focus on trade-offs and edge cases.
4. **Synthesize Decisions**:
   - Once answers are provided, synthesize a concise **Decision Record** before moving to implementation or `/to-prd`.

## Question Categories to Probe
- **Latency & Concurrency**: Will this run in a synchronous HTTP request or background task queue?
- **Failure Recovery**: How should the system handle upstream API rate limits or network drops?
- **Idempotency**: What happens if this action is called twice with the same inputs?
- **Observability**: What logs, metrics, or PostHog events need to be tracked?
