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
from datetime import datetime, timezone
import enum
import uuid
from src.shared.enums import (
    SystemJobStatus,
    ContentPublishStatus,
    ScanStatus,
    ABTestStatus,
    SessionStatus,
    ExperimentCohortStatus,
    StrategyStatus,
)


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
    """
    Content database model for discovered trending content.
    Used by discovery scanners to persist content candidates from various platforms.
    """

    __tablename__ = "content_candidates"

    # Core identifiers
    id = Column(String, primary_key=True, index=True)
    platform = Column(String)
    external_id = Column(
        String, unique=True, index=True, nullable=True
    )  # Platform-specific ID

    # Content metadata
    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    creator_name = Column(String, nullable=True)  # Channel/author name
    creator_id = Column(String, nullable=True)  # Channel/author ID
    source_uri = Column(String)  # Primary canonical URI
    thumbnail_uri = Column(String, nullable=True)

    # Timing fields
    published_at = Column(DateTime, nullable=True)  # When content was published
    scanned_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )  # When content was discovered

    # Duration and metrics
    duration_seconds = Column(Float, default=0.0)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(
        Integer, default=0
    )  # Legacy - platforms have different share metrics

    # Engagement and viral scoring
    # 'views' removed - use view_count as the canonical field
    engagement_score = Column(Float, default=0.0)
    viral_score = Column(Integer, default=0)

    # Categorization
    category = Column(String, default="video")  # video, article, social, news
    tags = Column(JSON, nullable=True)  # Array of strings
    niche = Column(String, index=True, nullable=True)
    region = Column(String, index=True, nullable=True, default="US")

    # Additional metadata
    metadata_json = Column(JSON, default={})

    # Analysis fields for viral pattern detection
    analysis_results = Column(
        JSON, nullable=True
    )  # topics, sentiment, viral_potential, keywords
    analyzed_at = Column(DateTime, nullable=True)  # When content was analyzed

    # Nexus Integration
    nexus_job_id = Column(String(36), ForeignKey("nexus_jobs.id"), nullable=True)
    is_processed = Column(Boolean, default=False)

    # Legacy compatibility (kept for migration)
    discovery_date = Column(DateTime, default=lambda: datetime.utcnow())


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
    avg_engagement_score = Column(Float)
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
    status = Column(
        Enum(ContentPublishStatus, native_enum=False),
        default=ContentPublishStatus.PENDING,
        nullable=False,
    )
    source_uri = Column(String, nullable=True)
    published_at = Column(DateTime, default=lambda: datetime.utcnow())
    account_id = Column(String(36), ForeignKey("social_accounts.id"), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    niche = Column(String, index=True, nullable=True)

    # Metrics fields (Normalized to *_count)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    retention_rate = Column(Float, default=0.0)


class VideoJobDB(Base):
    __tablename__ = "video_jobs"

    id = Column(String(36), primary_key=True, index=True)  # Task ID (UUID)
    title = Column(String)
    status = Column(
        Enum(SystemJobStatus, native_enum=False),
        default=SystemJobStatus.QUEUED,
        nullable=False,
    )
    progress = Column(Integer, default=0)
    time_remaining = Column(String, nullable=True)
    source_uri = Column(String)
    output_path = Column(String, nullable=True)
    job_metadata = Column(
        JSON, default=dict
    )  # Stores original generation parameters and other metadata for retry
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


class DiscoveryAlertDB(Base):
    """User alerts for when new trending content is found in a niche"""

    __tablename__ = "discovery_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    niche = Column(String, index=True, nullable=False)
    threshold = Column(Integer, default=7)  # viral_score threshold
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    __table_args__ = (
        UniqueConstraint("user_id", "niche", name="uix_user_niche_alert"),
    )


class DiscoveryFavoriteDB(Base):
    """User's favorite content candidates"""

    __tablename__ = "discovery_favorites"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    __table_args__ = (UniqueConstraint("user_id", "id", name="uix_user_favorite"),)


class ScanHistoryDB(Base):
    """History of user's discovery scans"""

    __tablename__ = "scan_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    niche = Column(String, index=True)
    status = Column(
        Enum(ScanStatus, native_enum=False),
        default=ScanStatus.PENDING,
        nullable=False,
    )
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


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
    view_count = Column(Integer, default=0)
    date = Column(DateTime, default=lambda: datetime.utcnow())
    user_id = Column(String(36), ForeignKey("users.id"), index=True)


class PersonaDB(Base):
    __tablename__ = "personas"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    name = Column(String)
    reference_image_uri = Column(String, nullable=True)  # Used for face animation
    reference_video_uri = Column(String, nullable=True)
    voice_clone_id = Column(String, nullable=True)  # Reference to XTTS or ElevenLabs ID
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class NexusJobDB(Base):
    __tablename__ = "nexus_jobs"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    status = Column(
        Enum(SystemJobStatus, native_enum=False),
        default=SystemJobStatus.QUEUED,
        nullable=False,
    )  # Unified status tracking
    niche = Column(String)
    output_path = Column(String, nullable=True)
    progress = Column(Integer, default=0)
    current_node = Column(String, nullable=True)
    node_status = Column(JSON, default=dict)
    job_metadata = Column(JSON, default=dict)
    error_log = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)


class BlueprintDB(Base):
    __tablename__ = "nexus_blueprints"

    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    nodes = Column(JSON)  # list of node dictionaries
    composition_id = Column(String, default="ViralClip")
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
    variant_a_view_count = Column(Integer, default=0)
    variant_b_view_count = Column(Integer, default=0)
    variant_a_click_count = Column(Integer, default=0)
    variant_b_click_count = Column(Integer, default=0)
    variant_a_conversion_count = Column(Integer, default=0)
    variant_b_conversion_count = Column(Integer, default=0)
    target_metric = Column(String, default="views")  # views, clicks, conversions
    status = Column(
        Enum(ABTestStatus, native_enum=False),
        default=ABTestStatus.ACTIVE,
        nullable=False,
    )
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
    status = Column(
        Enum(ContentPublishStatus, native_enum=False),
        default=ContentPublishStatus.PENDING,
        nullable=False,
    )
    metadata_json = Column(JSON)
    account_id = Column(String(36), ForeignKey("social_accounts.id"), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    retry_count = Column(Integer, default=0)  # Number of retry attempts
    error_message = Column(String, nullable=True)  # Last error message
    published_at = Column(DateTime, nullable=True)  # When actually published
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Multi-window scheduling support
    parallel_allowed = Column(Boolean, default=False)  # Allow parallel posts
    user_timezone = Column(String(50), nullable=True)  # User's timezone
    engagement_prediction = Column(Float, nullable=True)  # Predicted engagement %
    optimal_rank = Column(
        Integer, nullable=True
    )  # Which optimal window (1st, 2nd, etc.)
    last_retry_at = Column(DateTime, nullable=True)  # Last retry timestamp


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
        Enum(SessionStatus, native_enum=False),
        default=SessionStatus.DISCONNECTED,
        nullable=False,
    )
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
    purchase_uri = Column(String)
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
    sign_up_uri = Column(String)
    cta_text = Column(String, nullable=True)
    benefits = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class LeadGenDB(Base):
    __tablename__ = "lead_gen_configs"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    name = Column(String)
    niche = Column(String, index=True)
    form_uri = Column(String)
    cta_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class PerformanceSnapshotDB(Base):
    """
    Stores historical snapshots of content performance for time-series analytics.
    Replaces simulated growth curves with real telemetry history.
    """

    __tablename__ = "performance_snapshots"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    content_id = Column(String(36), ForeignKey("published_content.id"), index=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    retention_rate = Column(Float, default=0.0)
    avg_duration = Column(Float, default=0.0)
    snapshot_at = Column(DateTime, default=lambda: datetime.utcnow())


class DriftHistoryDB(Base):
    """
    10/10 Production: The Algorithm Shift Ledger.
    Stores every recorded delta for long-term trend analysis.
    """

    __tablename__ = "drift_history"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    predicted_retention = Column(Float)
    actual_retention = Column(Float)
    delta = Column(Float)
    recorded_at = Column(DateTime, default=lambda: datetime.utcnow())


class ExperimentCohortDB(Base):
    """
    10/10 Production: Persistent Experiment Groups.
    Replaces in-memory active_batches.
    """

    __tablename__ = "experiment_cohorts"

    id = Column(
        String(64), primary_key=True, index=True
    )  # custom ID like batch_123_strategy
    strategy = Column(String, index=True)
    size = Column(Integer)
    status = Column(
        Enum(ExperimentCohortStatus, native_enum=False),
        default=ExperimentCohortStatus.ROLLING_OUT,
        nullable=False,
    )
    participants = Column(JSON, default=list)  # list of video IDs
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class StrategyRegistryDB(Base):
    """
    10/10 Production: The Strategy Survival Ledger.
    Tracks the lifecycle and survival of narrative strategies.
    """

    __tablename__ = "strategy_registry"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    name = Column(String, unique=True, index=True)
    status = Column(
        Enum(StrategyStatus, native_enum=False),
        default=StrategyStatus.ACTIVE,
        nullable=False,
    )
    avg_score = Column(Float, nullable=True)
    failure_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )


class IncidentWebhookDB(Base):
    """
    Standard 3.12: Compliance Hardening (EU AI Act Article 71).
    Stores external webhook endpoints for reporting serious incidents.
    """

    __tablename__ = "incident_webhooks"

    id = Column(
        String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4())
    )
    uri = Column(String, nullable=False)
    name = Column(String, nullable=True)  # e.g., "EU Market Surveillance Authority"
    secret = Column(String, nullable=True)  # HMAC secret for signing
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


class AgentZeroState(Base):
    __tablename__ = "agent_zero_state"

    key = Column(String, primary_key=True, index=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.utcnow(),
        onupdate=lambda: datetime.utcnow(),
    )
