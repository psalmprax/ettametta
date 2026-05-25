# Production Smoke Testing

Use `scripts/production_smoke_test.py` as the canonical remote-server test ladder for the main ettametta workflow.

## Fast Remote Check

```bash
cd /home/ubuntu/ettametta
python3 scripts/production_smoke_test.py \
  --api-url http://localhost:7201 \
  --dashboard-url http://localhost:7200 \
  --docker
```

This verifies:
- API root
- direct `/health`
- versioned `/api/v1/health`
- dashboard nginx proxy to `/api/v1/health`
- dashboard HTML
- OpenAPI presence for the golden-path route families
- Docker Compose service visibility

## Browser E2E

```bash
python3 scripts/production_smoke_test.py \
  --api-url http://localhost:7201 \
  --dashboard-url http://localhost:7200 \
  --docker \
  --e2e
```

The runner sets `BASE_URL` and `SKIP_WEB_SERVER=1` before invoking Playwright in `src/tests/e2e`.

## Video Render Smoke

```bash
DATABASE_URL="$DATABASE_URL" REDIS_URL="$REDIS_URL" \
python3 scripts/production_smoke_test.py \
  --api-url http://localhost:7201 \
  --dashboard-url http://localhost:7200 \
  --docker \
  --video-scenario 0
```

The video smoke delegates to `scratch/test_full_production.py`, which seeds a job and renders a short MP4 through the production creator service.

## Acceptance Bar

The remote server is considered production-main-functional when:
- health passes through direct API and nginx dashboard proxy
- OpenAPI includes discovery, auth, video, Nexus, publishing, and analytics routes
- browser E2E passes against the remote dashboard
- at least one controlled video render creates a playable MP4
- publishing is verified in dry-run or against a private/sandbox account before any public post
