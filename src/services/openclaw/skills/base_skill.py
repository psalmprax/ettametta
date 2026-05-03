import logging
from abc import ABC, abstractmethod
from src.api.config import settings

logger = logging.getLogger(__name__)

class OpenClawBaseSkill(ABC):
    """
    Base class for all ettametta Official Skills.
    Enforces the mission-based pattern for workforce operations.
    """
    def __init__(self):
        self.api_url = getattr(settings, "API_URL", "http://api:7001")
        self.logger = logging.getLogger(self.__class__.__name__)
        self.metadata = {
            "name": self.__class__.__name__.replace("Skill", ""),
            "category": "General",
            "stability": "Stable",
            "credits_per_task": 10,
            "description": self.__doc__.strip() if self.__doc__ else "No description available."
        }

    def _get_headers(self) -> dict:
        """Standardized authorization headers for internal OpenClaw routing."""
        headers = {}
        token = getattr(settings, "INTERNAL_API_TOKEN", None)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @abstractmethod
    def execute(self, *args, **kwargs) -> str:
        """
        Execute the primary mission of the skill.
        Must be implemented by all subclasses.
        Returns a formatted markdown string of the execution result.
        """
        pass
