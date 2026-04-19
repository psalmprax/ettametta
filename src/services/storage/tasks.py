from api.utils.celery import celery_app
from .manager import storage_manager
import logging
import asyncio

@celery_app.task(name="storage.manage_lifecycle")
def manage_lifecycle():
    """Daily task to enforce storage thresholds and retention policies."""
    logging.info("[StorageTasks] Starting storage lifecycle management.")
    
    # We use asyncio.run to call the async methods of StorageManager
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    loop.run_until_complete(storage_manager.enforce_threshold())
    loop.run_until_complete(storage_manager.apply_retention_policy(days=90))
    
    logging.info("[StorageTasks] Storage lifecycle management complete.")
