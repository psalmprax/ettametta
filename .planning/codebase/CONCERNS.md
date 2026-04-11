# Codebase Concerns

**Analysis Date:** 2026-04-10

## Tech Debt

**[Large Files]:**
- Issue: Several source files exceed recommended size limits, indicating potential complexity and maintenance issues
- Files: `api/routes/publish.py` (1741 lines), `services/video_engine/synthesis_service.py` (1140 lines), `api/routes/settings.py` (939 lines), `services/video_engine/processor.py` (901 lines)
- Impact: Difficult to maintain, test, and understand; increased risk of bugs
- Fix approach: Refactor into smaller, focused modules with single responsibilities

**[Stub Implementations]:**
- Issue: Multiple functions return None or empty collections, indicating incomplete implementations
- Files: `services/video_engine/stock_service.py` (multiple return None), `services/video_engine/ai_generator.py` (multiple return None), `services/video_engine/motion_graphics.py` (multiple return None)
- Impact: Silent failures, unpredictable behavior in production
- Fix approach: Implement proper error handling or complete the functionality

**[TODO Comments]:**
- Issue: Unfinished API integrations marked with TODO
- Files: `services/video_engine/synthesis_service.py` (lines 353, 365)
- Impact: Features not working as expected
- Fix approach: Complete the API integrations or remove dead code

## Known Bugs

**[Configuration Validation]:**
- Issue: Config validation runs on startup but errors are not fatal in development
- Files: `api/config.py` (validation method prints but doesn't exit)
- Impact: Invalid config may cause runtime failures
- Workaround: Manually check logs on startup

## Security Considerations

**[Secret Management]:**
- Issue: API keys stored in environment variables without rotation policies
- Files: `api/config.py` (multiple *_API_KEY fields)
- Current mitigation: Validation checks for production secrets
- Recommendations: Implement secret rotation, consider using secret management services

**[JWT Token Handling]:**
- Issue: Long token expiry (24 hours) without refresh mechanism
- Files: `api/utils/security.py`, `api/utils/auth.py`
- Current mitigation: Token blacklist in Redis
- Recommendations: Implement token refresh, shorter expiry times

**[CORS Configuration]:**
- Issue: CORS allows all origins in development
- Files: `api/main.py` (CORS middleware)
- Current mitigation: Production-only security headers
- Recommendations: Restrict CORS origins even in development

## Performance Bottlenecks

**[Synchronous Operations]:**
- Issue: Some routes may perform synchronous I/O operations
- Files: Various route files without explicit async/await patterns
- Cause: Blocking operations in async context
- Improvement path: Audit all routes for synchronous calls, convert to async

**[GPU Queue Management]:**
- Issue: GPU slot calculation depends on hardware detection
- Files: `api/config.py` (EFFECTIVE_GPU_QUEUE_SLOTS property)
- Cause: Hardware detection may fail or be inaccurate
- Improvement path: Add fallback mechanisms, better error handling for GPU operations

## Fragile Areas

**[External API Dependencies]:**
- Issue: Heavy reliance on external AI/video APIs without circuit breakers
- Files: `services/video_engine/synthesis_service.py`, `services/video_engine/processor.py`
- Why fragile: API rate limits, downtime, or changes break functionality
- Safe modification: Implement retry logic, fallback providers, caching

**[Database Migrations]:**
- Issue: Alembic migrations may fail if schema changes are not backward compatible
- Files: `alembic/versions/` (migration scripts)
- Why fragile: Production data integrity at risk
- Test coverage: Add migration tests

## Scaling Limits

**[Redis Dependency]:**
- Issue: Single Redis instance used for cache, broker, and session storage
- Files: `api/config.py` (REDIS_URL), `api/main.py` (cache setup)
- Current capacity: Single instance configuration
- Limit: Redis becomes bottleneck under high load
- Scaling path: Implement Redis cluster, separate instances for different purposes

**[GPU Resource Management]:**
- Issue: GPU queue slots calculated per server, not distributed
- Files: `api/utils/hardware_detector.py`, `api/config.py`
- Current capacity: Local GPU only
- Limit: Cannot scale video generation across multiple machines
- Scaling path: Distributed GPU orchestration, cloud GPU integration

## Dependencies at Risk

**[Third-party AI APIs]:**
- Issue: No fallback when primary AI providers are unavailable
- Files: `api/config.py` (multiple AI provider keys), `services/video_engine/synthesis_service.py`
- Impact: Core video generation features fail
- Migration plan: Implement provider failover, circuit breaker pattern

**[Font Dependencies]:**
- Issue: Hardcoded font path may not exist on all systems
- Files: `api/config.py` (FONT_PATH)
- Impact: Video rendering fails
- Migration plan: Fallback font detection, embed fonts

## Missing Critical Features

**[Error Monitoring]:**
- Issue: No centralized error tracking beyond logging
- Files: `api/main.py` (exception handlers)
- Problem: Hard to monitor production errors
- Blocks: Proactive issue resolution

**[API Rate Limiting]:**
- Issue: Rate limiting implemented but may not handle distributed attacks
- Files: `api/utils/limiter.py`, `api/main.py`
- Problem: Single-instance rate limiting doesn't scale
- Blocks: Protection against abuse in multi-instance deployments

## Test Coverage Gaps

**[Integration Tests]:**
- Issue: Limited end-to-end testing for critical paths
- Files: `api/tests/` (mostly unit tests)
- Risk: Integration issues in production
- Priority: High - implement comprehensive E2E tests

**[Error Scenario Testing]:**
- Issue: Exception handlers tested but edge cases not covered
- Files: `api/main.py` (exception handlers), `api/tests/test_routes/`
- Risk: Unhandled exceptions cause 500 errors
- Priority: Medium - add chaos testing

---

*Concerns audit: 2026-04-10*</content>
<parameter name="filePath">.planning/codebase/CONCERNS.md