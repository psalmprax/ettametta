# Remotion Rendering Pipeline Details

## Python Bridge: RemotionService

File: `src/services/video_engine/remotion_service.py`

### Render Flow

```
render_video()
  │
  ├─ 1. Pre-checks
  │     ├─ Circuit breaker state check
  │     ├─ Props validation (schema, memory size, duration)
  │     └─ Acquire semaphore slot (default: 2)
  │
  ├─ 2. Asset Staging
  │     ├─ Create sandbox: public/assets/{job_id}/
  │     ├─ Discover local files in props (recursive)
  │     ├─ Validate against LFI jail (8 allowed roots)
  │     └─ Copy with O_NOFOLLOW (no symlinks, TOCTOU-safe)
  │
  ├─ 3. Props File
  │     ├─ Serialize to JSON
  │     ├─ Check disk space (20MB minimum)
  │     ├─ Write to temp file
  │     ├─ fsync + atomic rename (os.replace)
  │     └─ 2 local retries on failure
  │
  ├─ 4. Build Command
  │     ├─ Discover remotion binary (node_modules/.bin or npx)
  │     ├─ nice -n 10 (priority adjustment)
  │     ├─ --props {props_path}
  │     ├─ --browser-executable (Chromium path)
  │     ├─ --concurrency 1 (frame-level)
  │     ├─ --chromium-flags (no-sandbox, disable-gpu, dynamic max-old-space-size)
  │     ├─ --public-dir (studio public folder)
  │     ├─ --scale (0.5 test, 0.75 default)
  │     └─ --force
  │
  ├─ 5. Execute
  │     ├─ asyncio.create_subprocess_exec()
  │     ├─ Separate stdout/stderr drain tasks
  │     ├─ 900s timeout (configurable)
  │     └─ Force-kill on timeout/cancellation
  │
  ├─ 6. Verify
  │     ├─ Output file exists
  │     └─ Output file is non-zero size
  │
  └─ 7. Cleanup
        ├─ Delete props JSON
        └─ Remove sandbox directory
```

### Chromium Memory Management

Dynamic V8 heap allocation:
- Reads cgroup v1/v2 limits or `/proc/meminfo`
- Allocates 60% of available memory to Chromium
- Clamped to 1024-8192 MB range
- Passed as `--max-old-space-size={size}` in `--chromium-flags`

### Prometheus Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `ettametta_remotion_render_duration_seconds` | Histogram | `composition_id` |
| `ettametta_remotion_renders_total` | Counter | `composition_id`, `status` |
| `ettametta_remotion_circuit_breaker_state` | Gauge | — (0=Closed, 1=Half-Open, 2=Open) |

### Error Classification

| Error | Type | Retryable |
|-------|------|-----------|
| Invalid props/schema | `RemotionFatalError` | No |
| Props validation failed | `RemotionFatalError` | No |
| Process timeout | `RemotionTransientError` | Yes (2 attempts) |
| Process crash | `RemotionTransientError` | Yes (2 attempts) |
| Disk full | `RemotionTransientError` | Yes |
| LFI rejection | `RemotionFatalError` | No |

### Fallback Chain

```
Remotion render
  ↓ (on failure)
FFmpeg pipeline (VideoProcessor)
  ↓ (on failure)
Return error
```

The `VideoProcessor` falls back to an FFmpeg-based pipeline when Remotion fails. The `MotionGraphicsService` returns `None` on failure.
