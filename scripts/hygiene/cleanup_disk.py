import os
import shutil
import logging
import subprocess

logger = logging.getLogger("Hygiene")
logging.basicConfig(level=logging.INFO)

def cleanup_disk():
    """
    Systematically clear caches and temporary files to prevent ENOSPC errors.
    """
    logger.info("Starting disk hygiene sequence...")

    # 1. Clear Docker Cache (if available)
    try:
        logger.info("Clearing Docker build cache...")
        subprocess.run(["docker", "builder", "prune", "-a", "-f"], check=False)
        logger.info("Clearing stopped Docker containers...")
        subprocess.run(["docker", "container", "prune", "-f"], check=False)
    except Exception as e:
        logger.warning(f"Docker cleanup failed: {e}")

    # 2. Clear Remotion Temporary Frames
    temp_frames_dir = "/home/psalmprax/ALL_PROJECTS/ettametta/temp_frames"
    if os.path.exists(temp_frames_dir):
        logger.info(f"Clearing Remotion frames in {temp_frames_dir}...")
        try:
            shutil.rmtree(temp_frames_dir)
            os.makedirs(temp_frames_dir)
        except Exception as e:
            logger.error(f"Failed to clear {temp_frames_dir}: {e}")

    # 3. Clear pip/npm cache
    try:
        logger.info("Clearing pip cache...")
        subprocess.run(["pip", "cache", "purge"], check=False)
        logger.info("Clearing npm cache...")
        subprocess.run(["npm", "cache", "clean", "--force"], check=False)
    except Exception as e:
        logger.warning(f"Package manager cache cleanup failed: {e}")

    # 4. Check remaining space
    total, used, free = shutil.disk_usage("/")
    logger.info(f"Cleanup complete. Free space: {free // (2**30)} GB")

if __name__ == "__main__":
    cleanup_disk()
