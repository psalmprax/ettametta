from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    JSON,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Enum,
)
from .database import Base
from .user_models import UserDB, UserRole, SubscriptionTier
from datetime import datetime
import enum
import uuid


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    key = Column(String, unique=True, index=True)
    value = Column(String)  # Encrypted or plain for non-sensitive
    category = Column(String, default="general")  # api_key, engine, etc.
    description = Column(String, nullable=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )


class UserSetting(Base):
    __tablename__ = "user_settings"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    key = Column(String, index=True)
    value = Column(String)
    category = Column(String, default="general")
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )


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
    view_count = Column(Integer, default=0)  # Legacy
    engagement_rate = Column(Float, default=0.0)  # Legacy
    views = Column(Integer, default=0)
    engagement_score = Column(Float, default=0.0)
    viral_score = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    discovery_date = Column(DateTime, default=lambda: datetime.utcnow())
    category = Column(String, default="video")  # video, blog, social, news, other
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
    analyzed_at = Column(DateTime, default=lambda: datetime.utcnow())


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    platform = Column(String, index=True)  # youtube, tiktok
    username = Column(String, nullable=True)
    access_token = Column(String)
    refresh_token = Column(String, nullable=True)
    expiry = Column(DateTime, nullable=True)
    token_type = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )


class NicheTrendDB(Base):
    __tablename__ = "niche_trends"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    niche = Column(String, index=True)
    platform = Column(String)
    top_keywords = Column(JSON)  # ["keyword1", "keyword2"]
    avg_engagement = Column(Float)
    viral_pattern_ids = Column(JSON)  # Reference to ViralPatternDB IDs
    last_updated = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )


class PublishedContentDB(Base):
    __tablename__ = "published_content"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    title = Column(String)
    platform = Column(String)
    status = Column(String)  # Published, Failed
    url = Column(String, nullable=True)
    published_at = Column(DateTime, default=lambda: datetime.utcnow())
    account_id = Column(String(36), ForeignKey("social_accounts.id"), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    niche = Column(String, index=True, nullable=True)

    # Metrics fields
    view_count = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    retention_rate = Column(Float, default=0.0)


class VideoJobDB(Base):
    __tablename__ = "video_jobs"

    id = Column(String(36), primary_key=True, index=True)  # Task ID (UUID)
    title = Column(String)
    status = Column(
        String
    )  # Queued, Validating, Downloading, Analyzing, Strategizing, Rendering, Retrying, Completed, Failed, Failed - API Limit, etc.
    progress = Column(Integer, default=0)
    time_remaining = Column(String, nullable=True)
    input_url = Column(String)
    output_path = Column(String, nullable=True)
    error_message = Column(String, nullable=True)  # Detailed error information
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )


class MonitoredNiche(Base):
    __tablename__ = "monitored_niches"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    niche = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    last_scanned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    __table_args__ = (UniqueConstraint("user_id", "niche", name="uix_user_niche"),)


class AffiliateLinkDB(Base):
    __tablename__ = "affiliate_links"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    product_name = Column(String)
    niche = Column(String, index=True)
    link = Column(String)
    cta_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class RevenueLogDB(Base):
    __tablename__ = "revenue_logs"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    platform = Column(String, index=True)
    niche = Column(String, index=True)
    amount = Column(Float, default=0.0)
    views = Column(Integer, default=0)
    date = Column(DateTime, default=lambda: datetime.utcnow())
    user_id = Column(String(36), ForeignKey("users.id"), index=True)


class PersonaDB(Base):
    __tablename__ = "personas"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    name = Column(String)
    reference_image_url = Column(String, nullable=True)  # Used for face animation
    reference_video_url = Column(String, nullable=True)
    voice_clone_id = Column(String, nullable=True)  # Reference to XTTS or ElevenLabs ID
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class NexusJobDB(Base):
    __tablename__ = "nexus_jobs"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    status = Column(
        String, default="PENDING"
    )  # PENDING, COMPOSING, RENDERING, COMPLETED, FAILED
    niche = Column(String)
    output_path = Column(String, nullable=True)
    progress = Column(Integer, default=0)
    error_log = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    user_id = Column(String(36), ForeignKey("users.id"), index=True)


class BlueprintDB(Base):
    __tablename__ = "nexus_blueprints"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    nodes = Column(JSON)  # List of node dictionaries
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class ABTestDB(Base):
    __tablename__ = "ab_tests"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    content_id = Column(String, index=True)  # Parent video ID
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    variant_a_title = Column(String)
    variant_b_title = Column(String)
    variant_a_description = Column(String, nullable=True)
    variant_b_description = Column(String, nullable=True)
    variant_a_views = Column(Integer, default=0)
    variant_b_views = Column(Integer, default=0)
    variant_a_clicks = Column(Integer, default=0)
    variant_b_clicks = Column(Integer, default=0)
    variant_a_conversions = Column(Integer, default=0)
    variant_b_conversions = Column(Integer, default=0)
    target_metric = Column(String, default="views")  # views, clicks, conversions
    status = Column(String, default="active")  # active, completed, paused
    winner_variant = Column(String, nullable=True)  # 'A' or 'B'
    confidence_level = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)


class ScheduledPostDB(Base):
    __tablename__ = "scheduled_posts"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    video_path = Column(String)
    platform = Column(String)
    scheduled_time = Column(DateTime)
    status = Column(String, default="PENDING")  # PENDING, PUBLISHED, FAILED
    metadata_json = Column(JSON)
    account_id = Column(String(36), ForeignKey("social_accounts.id"), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    retry_count = Column(Integer, default=0)  # Number of retry attempts
    error_message = Column(String, nullable=True)  # Last error message
    published_at = Column(DateTime, nullable=True)  # When actually published
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class AuditLogDB(Base):
    __tablename__ = "audit_logs"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    action = Column(
        String, index=True
    )  # e.g., "LOGIN", "GENERATE_VIDEO_START", "SUBSCRIPTION_CHANGE"
    resource_type = Column(String, nullable=True)  # e.g., "VIDEO", "USER", "BILLING"
    resource_id = Column(String, nullable=True)
    details = Column(JSON, nullable=True)  # Additional context
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class SelfHealingAuditDB(Base):
    """
    Standard: Hardening Observability - Fault Persistence.
    Persists catastrophic faults with tracebacks for automated or manual recovery.
    """

    __tablename__ = "self_healing_audits"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    path = Column(String, index=True)
    method = Column(String)
    exception_type = Column(String)
    message = Column(String)
    traceback = Column(String)
    resolved = Column(Boolean, default=False)
    resolution_notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class SystemActivityDB(Base):
    __tablename__ = "system_activity"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    level = Column(String, default="INFO")  # INFO, WARNING, ERROR, SYSTEM, SUCCESS
    module = Column(String, index=True)  # AGENT_ZERO, DISCOVERY, NEXUS, etc.
    message = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class OpenCLISessionDB(Base):
    """Per-user opencli-rs session tracking.
    Each user has their own set of connected platform sessions
    backed by their Chrome browser cookies via the opencli extension.
    """

    __tablename__ = "opencli_sessions"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    platform = Column(String, index=True)  # youtube, tiktok, instagram, x, reddit, etc.
    status = Column(
        String, default="disconnected"
    )  # connected, disconnected, expired, error
    session_data = Column(
        String, nullable=True
    )  # Encrypted cookie/session blob from extension
    last_verified = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    capabilities = Column(
        JSON, default=list
    )  # ["search", "feed", "post", "comment", "like"]
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )


class DiscoveryInteractionDB(Base):
    __tablename__ = "discovery_interactions"
    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    candidate_id = Column(String, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    action = Column(String)  # handshake, negotiate, bookmark, ignore
    status = Column(Integer, default=0)  # 0: pending, 1: established, 2: failed
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class WebhookEventDB(Base):
    __tablename__ = "webhook_events"
    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    event_type = Column(String, index=True)
    platform = Column(String, index=True)
    external_id = Column(String, index=True)
    payload_json = Column(JSON, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class TradingPortfolioDB(Base):
    __tablename__ = "trading_portfolios"
    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    cash_balance = Column(Float, default=10000.0)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )


class TradingPositionDB(Base):
    __tablename__ = "trading_positions"
    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    portfolio_id = Column(String(36), ForeignKey("trading_portfolios.id"), index=True)
    symbol = Column(String, index=True)
    quantity = Column(Float)
    avg_price = Column(Float)
    position_type = Column(String, default="buy")  # buy, short
    opened_at = Column(DateTime, default=lambda: datetime.utcnow())


class TradingAlertDB(Base):
    __tablename__ = "trading_alerts"
    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    symbol = Column(String, index=True)
    target_price = Column(Float)
    condition = Column(String, default="above")  # above, below
    triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class TradingTransactionDB(Base):
    __tablename__ = "trading_transactions"
    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    portfolio_id = Column(String(36), ForeignKey("trading_portfolios.id"), index=True)
    symbol = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    transaction_type = Column(String)  # buy, sell
    total_value = Column(Float)
    executed_at = Column(DateTime, default=lambda: datetime.utcnow())


class BotCodeDB(Base):
    __tablename__ = "bot_codes"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    platform = Column(String)  # telegram, whatsapp
    code = Column(String, unique=True)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class DigitalProductDB(Base):
    __tablename__ = "digital_products"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    name = Column(String)
    niche = Column(String, index=True)
    description = Column(String, nullable=True)
    price = Column(Float)
    purchase_url = Column(String)
    cta_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class MembershipPlanDB(Base):
    __tablename__ = "membership_plans"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    name = Column(String)
    niche = Column(String, index=True)
    description = Column(String, nullable=True)
    monthly_price = Column(Float)
    sign_up_url = Column(String)
    benefits = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
