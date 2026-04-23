from celery import Celery
import os

from src.api.config import settings

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", settings.REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", settings.REDIS_URL)

celery_app = Celery(
    "ettametta",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "services.video_engine.tasks",
        "services.discovery.tasks",
        "services.discovery.scanner_service",
        "services.optimization.scheduler_tasks",
        "services.security.tasks",
        "services.storage.tasks",
        "services.openclaw.tasks",
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
            "task": "discovery.sentinel_watcher",
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
    },
)
