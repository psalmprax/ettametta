import logging
from api.utils.celery import celery_app
from services.openclaw.skills.ettametta import ettametta_skill

logger = logging.getLogger(__name__)

@celery_app.task(name="openclaw.ettametta_polling")
def ettametta_polling_task():
    """
    Background task to poll for new high-ROI gigs.
    """
    logger.info("[Celery] Running ettametta polling daemon...")
    try:
        result = ettametta_skill.auto_accept_gigs()
        logger.info(f"[Celery] ettametta result: {result}")
        return result
    except Exception as e:
        logger.error(f"[Celery] ettametta polling failed: {e}")
        return str(e)
