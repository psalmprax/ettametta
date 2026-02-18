from abc import ABC, abstractmethod
from typing import Optional
from .models import PostMetadata

class SocialPublisher(ABC):
    @abstractmethod
    async def upload_video(self, video_path: str, metadata: PostMetadata) -> Optional[str]:
        """Uploads video to platform and returns post ID/URL."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Verifies API credentials and connectivity."""
        pass
