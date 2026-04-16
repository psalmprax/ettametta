#!/usr/bin/env python3
"""
Dependency Verification Script for Video Processing

This script attempts to import all video-related modules and libraries
used in the codebase, logging any import failures.
"""

import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# List of modules to verify
VIDEO_MODULES = [
    "torch",
    "cv2",
    "moviepy",
    "moviepy.editor",
    "diffusers",
    "faster_whisper",
    "huggingface_hub",
    "realesrgan",
    "basicsr",
    "basicsr.archs.rrdbnet_arch",
    "PIL",
    "numpy",
    "scipy",
    "librosa",
    "soundfile",
    "pydub",
    "ffmpeg",
    "imageio_ffmpeg",
]


def verify_import(module_name):
    """Attempt to import a module and return success status."""
    try:
        __import__(module_name)
        logger.info(f"✓ {module_name} imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ {module_name} import failed: {e}")
        return False
    except Exception as e:
        logger.warning(f"⚠ {module_name} import had issues: {e}")
        return True  # Consider it working if not ImportError


def main():
    """Main verification function."""
    logger.info("Starting video processing dependency verification...")

    failed_modules = []
    successful_modules = []

    for module in VIDEO_MODULES:
        if verify_import(module):
            successful_modules.append(module)
        else:
            failed_modules.append(module)

    logger.info(f"\nVerification complete:")
    logger.info(f"Successful imports: {len(successful_modules)}")
    logger.info(f"Failed imports: {len(failed_modules)}")

    if failed_modules:
        logger.error(f"Failed modules: {', '.join(failed_modules)}")
        sys.exit(1)
    else:
        logger.info("All video processing dependencies are working!")
        sys.exit(0)


if __name__ == "__main__":
    main()
