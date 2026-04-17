"""
Periodic task scheduler configuration.

This module provides backward compatibility for scheduler references.
The actual Celery beat schedule is configured in celery.py.

The scheduler supports:
- scan-trending: Runs every 2 hours to scan trending content
"""

from .celery import celery_app

# Export for backward compatibility
# The beat_schedule is defined in celery.py
__all__ = ["celery_app"]

# Note: The beat_schedule is configured in celery.py:
# celery_app.conf.beat_schedule = {
#     "scan-trending": {
#         "task": "services.discovery.scanner_service.scan_trending_content",
#         "schedule": 7200.0,  # Every 2 hours
#     },
#     ...
# }
