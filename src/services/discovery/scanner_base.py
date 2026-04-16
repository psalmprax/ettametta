from abc import ABC, abstractmethod
from typing import List, Optional
import datetime
from .models import ContentCandidate

class TrendScanner(ABC):
    @abstractmethod
    async def scan_trends(self, niche: str, published_after: Optional[datetime.datetime] = None) -> List[ContentCandidate]:
        pass

    @abstractmethod
    def identify_viral_velocity(self, candidate: ContentCandidate) -> float:
        """Calculates how fast the content is gaining views/engagement."""
        pass
