from enum import Enum


class SystemJobStatus(str, Enum):
    """Unified job status enum for all ettametta services."""

    # Discovery & Ingestion
    QUEUED = "Queued"
    SCANNING = "Scanning"
    ANALYZING = "Analyzing"
    VALIDATING = "Validating"
    DOWNLOADING = "Downloading"
    DOWNLOADING_ASSET = "Downloading Asset"
    INTELLIGENT_DISCOVERY = "Intelligent Discovery"

    # Analysis & Strategy
    ANALYZING_VISUALS = "Analyzing Visuals"
    STRATEGIZING = "Strategizing"
    SCRIPTING = "Scripting"
    NARRATIVE_ANALYSIS = "Narrative Analysis"

    # Transformation & Synthesis
    TRANSFORMING = "Transforming"
    SYNTHESIZING = "Synthesizing"
    SYNTHESIZING_STORY = "Synthesizing Story"
    RENDERING = "Rendering"
    COMPOSING = "Composing"
    CINEMATIC_FUSION = "Cinematic Fusion"

    # Enhancements
    ADDING_SOUND_DESIGN = "Adding Sound Design"
    ADDING_MOTION_GRAPHICS = "Adding Motion Graphics"

    # Assembly & Finalization
    ASSEMBLING = "Assembling"
    OPTIMIZING = "Optimizing"
    UPLOADING = "Uploading"
    TIKTOK_UPLOAD = "TikTok Upload"

    # Terminal States
    COMPLETED = "Completed"
    FAILED = "Failed"
    ABORTED = "Aborted"
    RETRYING = "Retrying"

    # Error States
    FAILED_INVALID_INPUT = "Failed: Invalid Input"
    FAILED_DOWNLOAD_ERROR = "Failed: Download Error"
    FAILED_SYNTHESIS_ERROR = "Failed: Synthesis Error"

    # Intermediate / Legacy Fallbacks
    PROCESSING = "Processing"


class ContentPublishStatus(str, Enum):
    """Status enum for content publishing operations."""

    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    PENDING_AUTH = "PENDING_AUTH"


class ScanStatus(str, Enum):
    """Status enum for discovery scan operations."""

    PENDING = "PENDING"
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


class CreditAction(str, Enum):
    """Credit action types for type-safe credit consumption."""

    VIDEO_GENERATION = "video_generation"
    VIDEO_TRANSFORMATION = "video_transformation"
    VIDEO_RETRY = "video_retry"
    STORYTELLING = "storytelling"
    STORY_GENERATION = "story_generation"
    VIRAL_ANALYSIS = "viral_analysis"
    SOCIAL_PUBLISH = "social_publish"
    ADMIN_ENV_UPLOAD = "admin_env_upload"
    ADMIN_SYSTEM_RESTART = "admin_system_restart"
    AUTO_MERCH = "auto_merch"
    VIDEO_GENERATE_VARIANTS_START = "VIDEO_GENERATE_VARIANTS_START"
    STORY_GENERATE_START = "STORY_GENERATE_START"
    VIDEO_JOB_RETRY = "VIDEO_JOB_RETRY"
