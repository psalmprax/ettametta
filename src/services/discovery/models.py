from pydantic import BaseModel, Field
from datetime import datetime

class ContentCandidate(BaseModel):
    id: str
    platform: str
    url: str
    author: str | None = "Unknown"
    title: str | None = None
    description: str | None = None
    thumbnail_url: str | None = None
    view_count: int = 0  # Legacy field for compatibility during migration
    engagement_rate: float = 0.0 # Legacy field
    views: int = 0
    engagement_score: float = 0.0
    viral_score: int = 0
    duration_seconds: float = 0.0
    category: str = "video"  # video, blog, social, news, other
    discovery_date: datetime = Field(default_factory=datetime.utcnow)
    quality_score: float = 1.0
    quality_flags: list[str] = []
    metadata: dict = {}

class ViralPattern(BaseModel):
    id: str
    hook_score: float
    retention_estimate: float
    pacing_bpm: int | None = None
    style_keywords: list[str] = []
    emotional_triggers: list[str] = []
