import os
from celery import Celery
from src.shared.observability import setup_observability

setup_observability("ettametta-worker")

try:
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
    CeleryInstrumentor().instrument()
except ImportError:
    pass

from src.api.config import settings

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", settings.REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", settings.REDIS_URL)

celery_app = Celery(
    "ettametta",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "src.services.video_engine.tasks",
        "src.services.nexus_engine.tasks",
        "src.services.discovery.tasks",
        "src.services.discovery.scanner_service",
        "src.services.optimization.scheduler_tasks",
        "src.services.security.tasks",
        "src.services.storage.tasks",
        "src.services.openclaw.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "sentinel-trend-watcher-4h": {
            "task": "src.services.discovery.tasks.sentinel_watcher",
            "schedule": 14400.0,  # Every 4 hours
        },
        "scan-trending-content-2h": {
            "task": "services.discovery.scanner_service.scan_trending_content",
            "schedule": 7200.0,  # Every 2 hours
        },
        "check-scheduled-posts-5m": {
            "task": "optimization.check_and_post_scheduled",
            "schedule": 300.0,  # Every 5 minutes
        },
        "retry-missed-schedules-5m": {
            "task": "optimization.retry_missed_schedules",
            "schedule": 300.0,  # Every 5 minutes
        },
        "system-security-audit-daily": {
            "task": "security.system_audit",
            "schedule": 86400.0,  # Every 24 hours
        },
        "storage-lifecycle-manager-daily": {
            "task": "storage.manage_lifecycle",
            "schedule": 86400.0,  # Every 24 hours
        },
        "ettametta-job-polling-10m": {
            "task": "openclaw.ettametta_polling",
            "schedule": 600.0,  # Every 10 minutes
        },
        "viral-loop-compilation-12h": {
            "task": "optimization.viral_loop_compilation",
            "schedule": 43200.0,  # Every 12 hours
            "args": ("AI Technology",),
        },
        "autonomous-nexus-trigger-1h": {
            "task": "discovery.process_high_potential",
            "schedule": 3600.0,  # Every hour
        },
        "nexus-cleanup-stale-jobs-10m": {
            "task": "nexus.cleanup_stale_jobs",
            "schedule": 600.0,  # Every 10 minutes
        },
    },
)
