# Databricks notebook source

# COMMAND ----------
from enum import Enum


class SystemJobStatus(str, Enum):
    """Unified job status enum for all ettametta services."""

    # Discovery & Ingestion
    # Lifecycle
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    SCANNING = "SCANNING"
    ANALYZING = "ANALYZING"
    VALIDATING = "VALIDATING"
    DOWNLOADING = "DOWNLOADING"
    DOWNLOADING_ASSET = "DOWNLOADING_ASSET"
    INTELLIGENT_DISCOVERY = "INTELLIGENT_DISCOVERY"

    # Analysis & Strategy
    ANALYZING_VISUALS = "ANALYZING_VISUALS"
    STRATEGIZING = "STRATEGIZING"
    SCRIPTING = "SCRIPTING"
    NARRATIVE_ANALYSIS = "NARRATIVE_ANALYSIS"

    # Transformation & Synthesis
    TRANSFORMING = "TRANSFORMING"
    SYNTHESIZING = "SYNTHESIZING"
    SYNTHESIZING_STORY = "SYNTHESIZING_STORY"
    RENDERING = "RENDERING"
    COMPOSING = "COMPOSING"
    CINEMATIC_FUSION = "CINEMATIC_FUSION"

    # Enhancements
    ADDING_SOUND_DESIGN = "ADDING_SOUND_DESIGN"
    ADDING_MOTION_GRAPHICS = "ADDING_MOTION_GRAPHICS"

    # Assembly & Finalization
    ASSEMBLING = "ASSEMBLING"
    OPTIMIZING = "OPTIMIZING"
    UPLOADING = "UPLOADING"
    TIKTOK_UPLOAD = "TIKTOK_UPLOAD"

    # Terminal States
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    RETRYING = "RETRYING"

    # Error States
    FAILED_INVALID_INPUT = "FAILED_INVALID_INPUT"
    FAILED_DOWNLOAD_ERROR = "FAILED_DOWNLOAD_ERROR"
    FAILED_SYNTHESIS_ERROR = "FAILED_SYNTHESIS_ERROR"

    # Intermediate / Legacy Fallbacks
    PROCESSING = "PROCESSING"


class ContentPublishStatus(str, Enum):
    """Status enum for content publishing operations."""

    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    PENDING_AUTH = "PENDING_AUTH"
    EXPIRED = "EXPIRED"


class ScanStatus(str, Enum):
    """Status enum for discovery scan operations."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ABTestStatus(str, Enum):
    """Status enum for A/B testing operations."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PAUSED = "PAUSED"


class SessionStatus(str, Enum):
    """Status enum for external service sessions."""

    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    EXPIRED = "EXPIRED"
    ERROR = "ERROR"


class ExperimentCohortStatus(str, Enum):
    """Status enum for experiment cohort operations."""

    ROLLING_OUT = "ROLLING_OUT"
    FULL_WAITING_DATA = "FULL_WAITING_DATA"
    COMPLETED = "COMPLETED"


class StrategyStatus(str, Enum):
    """Status enum for strategy lifecycle management."""

    ACTIVE = "ACTIVE"
    DOMINANT = "DOMINANT"
    KILLED = "KILLED"


class ReferralStatus(str, Enum):
    """Status enum for referral lifecycle."""

    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    REWARD_CLAIMED = "REWARD_CLAIMED"


class NodeStatus(str, Enum):
    """Status enum for DAG pipeline node execution."""

    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CreditAction(str, Enum):
    """Credit action types for type-safe credit consumption."""

    VIDEO_GENERATION = "VIDEO_GENERATION"
    VIDEO_TRANSFORMATION = "VIDEO_TRANSFORMATION"
    VIDEO_RETRY = "VIDEO_RETRY"
    STORYTELLING = "STORYTELLING"
    STORY_GENERATION = "STORY_GENERATION"
    VIRAL_ANALYSIS = "VIRAL_ANALYSIS"
    SOCIAL_PUBLISH = "SOCIAL_PUBLISH"
    ADMIN_ENV_UPLOAD = "ADMIN_ENV_UPLOAD"
    ADMIN_SYSTEM_RESTART = "ADMIN_SYSTEM_RESTART"
    AUTO_MERCH = "AUTO_MERCH"
    VIDEO_GENERATE_VARIANTS_START = "VIDEO_GENERATE_VARIANTS_START"
    STORY_GENERATE_START = "STORY_GENERATE_START"
    VIDEO_JOB_RETRY = "VIDEO_JOB_RETRY"
