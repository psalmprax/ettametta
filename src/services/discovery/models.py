from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any


class ContentCandidate(BaseModel):
    """Unified content candidate model covering both discovery and search results.
    Spans fields from ContentCandidateDB and additional metadata.

    Note: Uses 'metadata' as alias for 'metadata_json' to maintain consistency
    with ContentCandidateDB field name via model_config.
    """

    id: str
    platform: str
    source_url: str

    # Creator fields
    creator_name: Optional[str] = None
    creator_id: Optional[str] = None

    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    # Timestamps
    published_at: Optional[datetime] = None
    scanned_at: Optional[datetime] = None
    # Metrics
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    engagement_score: float = 0.0
    viral_score: int = 0
    duration_seconds: float = 0.0
    # Categorization
    category: str = "video"
    tags: List[str] = []
    niche: Optional[str] = None
    # Quality & analysis
    quality_score: float = 1.0
    quality_flags: List[str] = []
    analysis_results: Optional[dict] = None
    analyzed_at: Optional[datetime] = None
    # Misc
    external_id: Optional[str] = None
    discovery_date: datetime = Field(default_factory=datetime.utcnow)
    # Use metadata_json to match DB field name, with 'metadata' as alias for convenience
    metadata_json: dict = Field(default_factory=dict)

    class Config:
        populate_by_name = True
        fields = {
            "metadata_json": "metadata",
        }


class ViralPattern(BaseModel):
    id: str
    hook_score: float
    retention_estimate: float
    pacing_bpm: int | None = None
    style_keywords: list[str] = []
    emotional_triggers: list[str] = []
