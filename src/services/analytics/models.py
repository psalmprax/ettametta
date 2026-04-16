from typing import List, Optional
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
    retention_data: List[int] = []
    optimization_insight: Optional[str] = None
    timestamp: datetime = datetime.utcnow()
