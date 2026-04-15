import importlib.util
import logging

logger = logging.getLogger(__name__)

def is_package_available(package_name: str) -> bool:
    """Check if a python package is installed in the current environment."""
    return importlib.util.find_spec(package_name) is not None

def require_package(package_name: str):
    """Decorator or helper to verify a package is available before running a function."""
    if not is_package_available(package_name):
        logger.warning(f"Feature requires '{package_name}' but it is not installed.")
        return False
    return True
