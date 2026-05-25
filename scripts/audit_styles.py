import sys
import os
import uuid
import logging
from src.services.nexus_engine.tasks import create_cinema_video_task

# Add current dir to path
sys.path.insert(0, os.getcwd())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("StyleAudit")

STYLES_TO_TEST = [
    "STOIC_WISDOM",
    "VOX_EXPLAINER",
    "REDDIT_STORY",
    "FAST_HYPE",
    "NOIR_MYSTERY"
]

TOPIC = "The Hidden Secrets of Stoicism"
NICHE = "Philosophy"

def run_audit():
    logger.info(f"Starting Style Audit for topic: {TOPIC}")
    results = {}

    for style in STYLES_TO_TEST:
        job_id = f"audit_{style.lower()}_{uuid.uuid4().hex[:6]}"
        logger.info(f"--- Testing Style: {style} (Job: {job_id}) ---")
        
        # We use .delay() to dispatch to Celery
        try:
            task = create_cinema_video_task.delay(
                job_id=job_id,
                topic=TOPIC,
                niche=NICHE,
                style=style,
                duration_seconds=30 # Short duration for audit
            )
            logger.info(f"Task {task.id} dispatched.")
            results[style] = task.id
        except Exception as e:
            logger.error(f"Failed to dispatch task for {style}: {e}")
            results[style] = "FAILED_DISPATCH"

    logger.info("\nAudit Summary (Dispatched Tasks):")
    for style, task_id in results.items():
        print(f"Style: {style} -> Task ID: {task_id}")

    print("\nWaiting for tasks to complete (polling logs is recommended)...")

if __name__ == "__main__":
    run_audit()
