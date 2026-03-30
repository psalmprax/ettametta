from abc import ABC, abstractmethod
from typing import Optional
from .models import PostMetadata

class SocialPublisher(ABC):
    @abstractmethod
    async def upload_video(self, video_path: str, metadata: PostMetadata) -> Optional[str]:
        """Uploads video to platform and returns post ID/URL."""
        pass

    @abstractmethod
    async def get_metrics(self, platform_id: str, user_id: int, account_id: Optional[int] = None) -> dict:
        """Fetches live engagement metrics (views, likes, shares, comments) for a post."""
        pass

    @abstractmethod
    def health_check(self, user_id: int) -> bool:
        """Verifies API credentials and connectivity."""
        pass
