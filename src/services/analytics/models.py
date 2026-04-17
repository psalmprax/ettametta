from pydantic import BaseModel
from datetime import datetime

class ContentPerformance(BaseModel):
    post_id: str
    views: int
    watch_time: float # hours
    retention_rate: float # 0.0 - 1.0
    likes: int
    shares: int
    comments: int
    follows_gained: int
    retention_data: list[int] = []
    optimization_insight: str | None = None
    timestamp: datetime = datetime.utcnow()
