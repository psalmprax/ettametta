# Service Layer Refactoring - Implementation Guide

**Objective:** Move database queries from routes to service layer  
**Impact:** Improves testability, code organization, and follows clean architecture  
**Estimated Time:** 8-11 hours across 3 service layers

---

## Phase 1: Analytics Service Extension (4-6 hours)

### Target: `src/services/analytics/service.py`

Add these methods to the `AnalyticsService` class (before `base_analytics_service = AnalyticsService()` singleton):

```python
async def list_published_posts(self, db, user_id: str, page: int = 1, size: int = 20, is_admin: bool = False):
    """
    List published content posts for a user with pagination.
    MIGRATION SOURCE: src/api/routes/analytics.py - GET /analytics/posts
    """
    from sqlalchemy import select, func
    from src.api.utils.models import PublishedContentDB
    from src.shared.enums import ContentPublishStatus
    from src.api.utils.api_responses import Paginator

    stmt = select(PublishedContentDB).where(
        PublishedContentDB.status == ContentPublishStatus.PUBLISHED
    )
    
    if not is_admin:
        stmt = stmt.where(PublishedContentDB.user_id == user_id)

    stmt = stmt.order_by(PublishedContentDB.published_at.desc())

    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total_items = total_result.scalar() or 0

    # Apply pagination
    paginator = Paginator(page=page, page_size=size)
    stmt = stmt.offset(paginator.offset).limit(paginator.limit)

    result = await db.execute(stmt)
    posts = result.scalars().all()

    return posts, paginator, total_items


async def get_report_summary(self, db, user_id: str, is_admin: bool = False):
    """
    Get overall analytics report summary for user.
    MIGRATION SOURCE: src/api/routes/analytics.py - GET /analytics/report
    """
    from sqlalchemy import select, func
    from src.api.utils.models import PublishedContentDB

    # Total posts
    where_clause = PublishedContentDB.user_id == user_id if not is_admin else True
    posts_result = await db.execute(
        select(func.count(PublishedContentDB.id)).where(where_clause)
    )
    total_posts = posts_result.scalar() or 0

    # Aggregate metrics
    stmt_metrics = select(
        func.sum(PublishedContentDB.view_count).label("total_views"),
        func.sum(PublishedContentDB.like_count).label("total_likes"),
        func.sum(PublishedContentDB.share_count).label("total_shares"),
        func.sum(PublishedContentDB.comment_count).label("total_comments"),
        func.avg(PublishedContentDB.retention_rate).label("avg_retention")
    )
    if not is_admin:
        stmt_metrics = stmt_metrics.where(PublishedContentDB.user_id == user_id)

    result = await db.execute(stmt_metrics)
    row = result.fetchone()

    total_views = row.total_views or 0
    total_likes = row.total_likes or 0
    total_shares = row.total_shares or 0
    total_comments = row.total_comments or 0
    avg_retention = row.avg_retention or 0.0

    return {
        "total_posts": total_posts,
        "total_views": int(total_views),
        "total_likes": int(total_likes),
        "total_shares": int(total_shares),
        "total_comments": int(total_comments),
        "avg_views": int(total_views / total_posts) if total_posts > 0 else 0,
        "avg_likes": int(total_likes / total_posts) if total_posts > 0 else 0,
        "avg_retention": float(avg_retention),
    }


async def verify_content_ownership(self, db, post_id: str, user_id: str, is_admin: bool):
    """
    Verify user owns a content post (or is admin).
    MIGRATION SOURCE: src/api/routes/analytics.py (multiple endpoints - auth checks)
    """
    from sqlalchemy import select
    from src.api.utils.models import PublishedContentDB

    stmt = select(PublishedContentDB).where(PublishedContentDB.id == post_id)
    result = await db.execute(stmt)
    content = result.scalar_one_or_none()

    if not content:
        return False, None
    
    if is_admin or content.user_id == user_id:
        return True, content
    
    return False, None


async def get_ab_test_results(self, db, content_id: str):
    """
    Get A/B test results for a content post.
    MIGRATION SOURCE: src/api/routes/analytics.py - GET /analytics/ab/results/{content_id}
    """
    from sqlalchemy import select
    from src.api.utils.models import ABTestDB

    stmt = select(ABTestDB).where(ABTestDB.content_id == content_id)
    result = await db.execute(stmt)
    test = result.scalar_one_or_none()

    if not test:
        return None

    winner = "A" if test.variant_a_view_count > test.variant_b_view_count else "B"
    return {
        "test_id": test.id,
        "variant_a_title": test.variant_a_title,
        "variant_b_title": test.variant_b_title,
        "variant_a_view_count": test.variant_a_view_count,
        "variant_b_view_count": test.variant_b_view_count,
        "winner": winner,
        "created_at": test.created_at,
    }
```

### Then update routes in `src/api/routes/analytics.py`:

**OLD:**
```python
@router.get("/posts")
async def list_analytics_posts(page: int = 1, size: int = 20, current_user: UserDB = Depends(get_current_user), db=Depends(get_db)):
    # Direct DB queries here...
    stmt = select(PublishedContentDB).where(...)
```

**NEW:**
```python
@router.get("/posts")
async def list_analytics_posts(
    page: int = 1, 
    size: int = 20, 
    current_user: UserDB = Depends(get_current_user), 
    db=Depends(get_db)
):
    try:
        is_admin = current_user.role == UserRole.ADMIN
        posts, paginator, total_items = await base_analytics_service.list_published_posts(
            db, current_user.id, page, size, is_admin
        )
        return success_response(data=paginator.paginate_response(posts, total_items))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content metrics failed: {e}")
        raise HTTPException(status_code=503, detail="Analytics service unavailable")
```

---

## Phase 2: Video Jobs Service Extension (1-2 hours)

### Target: `src/services/video_engine/job_service.py`

Add this method:

```python
async def abort_job(self, db, job_id: str, user_id: str, is_admin: bool):
    """
    Abort a running video processing job with auth checks.
    MIGRATION SOURCE: src/api/routes/video_jobs.py - POST /video/jobs/{job_id}/abort
    """
    from src.api.utils.celery import celery_app
    from src.api.utils.models import VideoJobDB, NexusJobDB
    from src.shared.enums import SystemJobStatus
    from sqlalchemy import select

    # Try Video jobs first
    stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    # Try Nexus jobs if not found
    if not job:
        stmt = select(NexusJobDB).where(NexusJobDB.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()

    if not job:
        return None, "Job not found"

    # Auth check
    if not is_admin and job.user_id != user_id:
        return None, "Not authorized"

    # Abort the job
    celery_app.control.revoke(job_id, terminate=True)
    job.status = SystemJobStatus.ABORTED
    await db.commit()

    return job, None  # Returns (job, error_message)
```

### Then update route:

**OLD:**
```python
@router.post("/{job_id}/abort")
async def abort_job(job_id: str, current_user: UserDB = Depends(get_current_user), db=Depends(get_db)):
    # Direct queries...
    stmt = select(VideoJobDB).where(VideoJobDB.id == job_id)
```

**NEW:**
```python
@router.post("/{job_id}/abort")
async def abort_job(
    job_id: str,
    current_user: UserDB = Depends(get_current_user),
    job_service: VideoJobService = Depends(get_video_job_service),
    db=Depends(get_db)
):
    try:
        is_admin = current_user.role == UserRole.ADMIN
        job, error = await job_service.abort_job(db, job_id, current_user.id, is_admin)
        
        if error:
            status_code = 404 if "not found" in error.lower() else 403
            raise HTTPException(status_code=status_code, detail=error)

        return success_response(data={"status": SystemJobStatus.ABORTED.value, "job_id": job_id})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error aborting job: {e}")
        raise HTTPException(status_code=500, detail="Failed to abort job")
```

---

## Phase 3: Discovery Service Refactoring (2-3 hours)

### Target: `src/services/discovery/service.py`

Extract trend aggregation logic currently in `src/api/routes/discovery.py` (lines 311-327):

```python
async def aggregate_niche_trends_with_scan(self, db, niche: str, tier: str = "free"):
    """
    Get aggregated trends for a niche, triggering scan if no data exists.
    MIGRATION SOURCE: src/api/routes/discovery.py - GET /discovery/niche-trends/{niche}
    """
    # Existing aggregate_niche_trends call, then:
    trend = await self.aggregate_niche_trends(niche)
    if not trend:
        # If no data yet, try to scan first
        await self.find_trending_content(niche, tier=tier)
        trend = await self.aggregate_niche_trends(niche)
    
    return trend  # Returns formatted trend data or empty dict
```

---

## Testing Strategy

After each phase:

1. **Route still works:**
   ```bash
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/analytics/posts
   ```

2. **Service returns expected data:**
   - Add unit test in `src/api/tests/test_services/test_analytics.py`
   - Mock database session
   - Assert returned data structure

3. **API contract unchanged:**
   - Response format must be identical before/after refactor
   - Status codes must match
   - Error messages should be same

---

## Verification Checklist

### Phase 1 - Analytics Service
- [ ] Added 5 new methods to AnalyticsService
- [ ] Updated 8+ analytics routes to use new methods
- [ ] All endpoints return same response format
- [ ] Unit tests added for each method
- [ ] E2E tests pass for /analytics/* endpoints

### Phase 2 - Video Jobs Service
- [ ] Added abort_job method to VideoJobService
- [ ] Updated video_jobs route
- [ ] Auth checks still work correctly
- [ ] Tests pass for abort endpoint

### Phase 3 - Discovery Service
- [ ] Trend aggregation logic extracted
- [ ] Routes updated
- [ ] No behavioral change from user perspective
- [ ] Tests pass

---

## Common Pitfalls

1. **Forgetting user_id filter:** Always check `is_admin` before applying user isolation
2. **Auth checks:** Ensure moved methods still validate user ownership
3. **Error handling:** Service methods should return (data, error) or raise exceptions consistently
4. **Imports:** May need new imports in service when moving queries
5. **Async/await:** All database operations are async - don't forget `await`

---

## Success Criteria

✅ All database queries moved from routes to services  
✅ API responses unchanged (same format, status codes, messages)  
✅ Auth checks still enforced  
✅ All unit and E2E tests pass  
✅ Code is testable - services can be unit tested with mock database  
✅ Clean architecture - routes are thin, services contain business logic

---

**Next:** Begin with Phase 1 (Analytics Service). Expected to complete by end of day.
