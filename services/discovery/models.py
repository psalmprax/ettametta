from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ContentCandidate(BaseModel):
    id: str
    platform: str
    url: str
    author: Optional[str] = "Unknown"
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    view_count: int = 0  # Legacy field for compatibility during migration
    engagement_rate: float = 0.0 # Legacy field
    views: int = 0
    engagement_score: float = 0.0
    viral_score: int = 0
    duration_seconds: float = 0.0
    discovery_date: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []
    metadata: dict = {}

class ViralPattern(BaseModel):
    id: str
    hook_score: float
    retention_estimate: float
    pacing_bpm: Optional[int] = None
    style_keywords: List[str] = []
    emotional_triggers: List[str] = []
