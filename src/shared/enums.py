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
    PENDING = "Pending"
    PROCESSING = "Processing"
