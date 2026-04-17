from abc import ABC, abstractmethod
import datetime
from .models import ContentCandidate

class TrendScanner(ABC):
    @abstractmethod
    async def scan_trends(self, niche: str, published_after: datetime.datetime | None = None) -> list[ContentCandidate]:
        pass

    @abstractmethod
    def identify_viral_velocity(self, candidate: ContentCandidate) -> float:
        """Calculates how fast the content is gaining views/engagement."""
        pass
