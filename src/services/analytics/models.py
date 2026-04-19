from pydantic import BaseModel
from datetime import datetime

class ContentPerformance(BaseModel):
    post_id: str
    view_count: int
    watch_time: float # hours
    retention_rate: float # 0.0 - 1.0
    like_count: int
    share_count: int
    comment_count: int
    follows_gained: int
    retention_data: list[int] = []
    optimization_insight: str | None = None
    timestamp: datetime = datetime.utcnow()
