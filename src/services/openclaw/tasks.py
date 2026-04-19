import logging
from api.utils.celery import celery_app
from services.openclaw.skills.cashclaw import cashclaw_skill

logger = logging.getLogger(__name__)

@celery_app.task(name="openclaw.cashclaw_polling")
def cashclaw_polling_task():
    """
    Periodic task to poll the HYRVE AI marketplace for new gigs
    and automatically accept them if they meet the ROI threshold.
    """
    logger.info("[Celery] Running CashClaw polling daemon...")
    try:
        result = cashclaw_skill.auto_accept_gigs()
        logger.info(f"[Celery] CashClaw result: {result}")
        return result
    except Exception as e:
        logger.error(f"[Celery] CashClaw polling failed: {e}")
        return str(e)
