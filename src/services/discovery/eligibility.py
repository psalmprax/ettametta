import logging
import datetime
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

async def check_content_freshness(url: str, min_days: int = 1, max_days: int = 30) -> dict[str, Any]:
    """
    Check if content is within the 'Viral Sweet Spot' (1-30 days old).
    Returns a dictionary with freshness metrics.
    """
    try:
        # Use yt-dlp to get upload date
        cmd = [
            "yt-dlp",
            "--print", "%(upload_date)s",
            "--no-download",
            url
        ]
        
        # Run safely
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0 and result.stdout.strip():
            upload_date_str = result.stdout.strip() # YYYYMMDD
            upload_date = datetime.datetime.strptime(upload_date_str, "%Y%m%d")
            now = datetime.datetime.now()
            
            age_days = (now - upload_date).days
            within_range = min_days <= age_days <= max_days
            
            return {
                "age_days": age_days,
                "within_range": within_range,
                "status": "FRESH" if within_range else ("TOO_NEW" if age_days < min_days else "STALE")
            }
            
    except Exception as e:
        logger.exception(f"[Eligibility] Freshness check failed for {url}: {e}")
        
    return {"age_days": -1, "within_range": True, "status": "UNKNOWN"}

async def audit_content_quality(title: str, description: str, metadata: dict[str, Any] = None) -> dict[str, Any]:
    """
    Professional content audit based on 30+ quality indicators.
    Returns quality score (0-1) and audit flags.
    """
    flags = []
    score = 1.0
    text = f"{title} {description}".lower()
    
    # 1. Format Rejections (Ported from workflow)
    if any(kw in text for kw in ["vlog", "daily life", "my day"]):
        flags.append("VLOG_DETECTED")
        score -= 0.4
        
    if any(kw in text for kw in ["live", "stream", "recorded live"]):
        flags.append("LIVE_STREAM")
        score -= 0.3
        
    if any(kw in text for kw in ["music video", "official video", "lyric video"]):
        flags.append("MUSIC_CONTENT")
        score -= 0.5
        
    if any(kw in text for kw in ["prank", "social experiment"]):
        flags.append("PRANK_CONTENT")
        score -= 0.2
        
    # 2. Pacing/Engagement Indicators
    if len(title) < 15:
        flags.append("LOW_EFFORT_TITLE")
        score -= 0.1
        
    if not description or len(description) < 50:
        flags.append("STUB_DESCRIPTION")
        score -= 0.1
        
    # 3. Platform Metadata (If available)
    if metadata:
        # Use duration_seconds if available (set by DiscoveryService)
        duration = metadata.get("duration_seconds")
        if duration is None:
            duration = metadata.get("duration", 0)
            
        try:
            # Cast to float to handle strings that are numeric
            duration_val = float(duration)
            if duration_val > 1800: # Over 30 mins
                flags.append("LONG_FORM_CONTENT")
                score -= 0.3
                
            if duration_val < 10:
                flags.append("TOO_SHORT")
                score -= 0.2
        except (ValueError, TypeError):
            # If it's a string like PT1M30S and we couldn't parse it elsewhere, skip comparison
            pass

    # Final Score Normalization
    score = max(0.1, round(score, 2))
    
    return {
        "score": score,
        "flags": flags,
        "is_low_quality": score < 0.6
    }
