from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, ForeignKey
from .database import Base
from datetime import datetime
# Import UserDB to ensure 'users' table is registered in metadata for foreign keys
from .user_models import UserDB 

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String) # Encrypted or plain for non-sensitive
    category = Column(String, default="general") # api_key, engine, etc.
    description = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class VideoFilterDB(Base):
    __tablename__ = "video_filters"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    enabled = Column(Boolean, default=True)
    description = Column(String, nullable=True)

class ContentCandidateDB(Base):
    __tablename__ = "content_candidates"

    id = Column(String, primary_key=True, index=True)
    platform = Column(String)
    url = Column(String)
    author = Column(String, nullable=True)
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    view_count = Column(Integer, default=0) # Legacy
    engagement_rate = Column(Float, default=0.0) # Legacy
    views = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    viral_score = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    discovery_date = Column(DateTime, default=datetime.utcnow)
    tags = Column(JSON, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    metadata_json = Column(JSON, default={})
    niche = Column(String, index=True, nullable=True)

class ViralPatternDB(Base):
    __tablename__ = "viral_patterns"

    id = Column(String, primary_key=True, index=True)
    content_id = Column(String, index=True)
    hook_score = Column(Float)
    retention_estimate = Column(Float)
    pacing_bpm = Column(Integer, nullable=True)
    style_keywords = Column(JSON)
    emotional_triggers = Column(JSON)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True) # youtube, tiktok
    username = Column(String, nullable=True)
    access_token = Column(String)
    refresh_token = Column(String, nullable=True)
    expiry = Column(DateTime, nullable=True)
    token_type = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class NicheTrendDB(Base):
    __tablename__ = "niche_trends"

    id = Column(Integer, primary_key=True, index=True)
    niche = Column(String, index=True)
    platform = Column(String)
    top_keywords = Column(JSON) # ["keyword1", "keyword2"]
    avg_engagement = Column(Float)
    viral_pattern_ids = Column(JSON) # Reference to ViralPatternDB IDs
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PublishedContentDB(Base):
    __tablename__ = "published_content"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    platform = Column(String)
    status = Column(String) # Published, Failed
    url = Column(String, nullable=True)
    published_at = Column(DateTime, default=datetime.utcnow)
    account_id = Column(Integer, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    niche = Column(String, index=True, nullable=True)

    # Metrics fields
    view_count = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    retention_rate = Column(Float, default=0.0)

class VideoJobDB(Base):
    __tablename__ = "video_jobs"

    id = Column(String, primary_key=True, index=True) # Task ID
    title = Column(String)
    status = Column(String) # Queued, Transcribing, Rendering, Completed, Failed
    progress = Column(Integer, default=0)
    time_remaining = Column(String, nullable=True)
    input_url = Column(String)
    output_path = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MonitoredNiche(Base):
    __tablename__ = "monitored_niches"

    id = Column(Integer, primary_key=True, index=True)
    niche = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    last_scanned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AffiliateLinkDB(Base):
    __tablename__ = "affiliate_links"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String)
    niche = Column(String, index=True)
    link = Column(String)
    cta_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class RevenueLogDB(Base):
    __tablename__ = "revenue_logs"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, index=True)
    niche = Column(String, index=True)
    amount = Column(Float, default=0.0)
    views = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

class PersonaDB(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    reference_image_url = Column(String, nullable=True) # Used for face animation
    reference_video_url = Column(String, nullable=True) 
    voice_clone_id = Column(String, nullable=True) # Reference to XTTS or ElevenLabs ID
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class NexusJobDB(Base):
    __tablename__ = "nexus_jobs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="PENDING") # PENDING, COMPOSING, RENDERING, COMPLETED, FAILED
    niche = Column(String)
    output_path = Column(String, nullable=True)
    progress = Column(Integer, default=0)
    error_log = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)

class ABTestDB(Base):
    __tablename__ = "ab_tests"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String, index=True) # Parent video ID
    variant_a_title = Column(String)
    variant_b_title = Column(String)
    variant_a_views = Column(Integer, default=0)
    variant_b_views = Column(Integer, default=0)
    winner_variant = Column(String, nullable=True) # 'A' or 'B'
    created_at = Column(DateTime, default=datetime.utcnow)

class ScheduledPostDB(Base):
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    video_path = Column(String)
    platform = Column(String)
    scheduled_time = Column(DateTime)
    status = Column(String, default="PENDING") # PENDING, PUBLISHED, FAILED
    metadata_json = Column(JSON)
    account_id = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
