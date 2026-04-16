import os
import re
import requests
import asyncio
import logging
from typing import Optional, Dict
from services.optimization.auth import token_manager

logger = logging.getLogger(__name__)


async def get_youtube_streaming_url(
    video_id: str, 
    api_key: Optional[str] = None, 
    user_id: Optional[int] = None
) -> Optional[str]:
    """
    Get video streaming URL using YouTube Data API.
    Supports both Public (API Key) and Private (OAuth) access.
    Returns the best quality adaptive format URL.
    """
    url = f"https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "streamingData,snippet,status",
        "id": video_id,
    }
    
    headers = {}
    
    # 1. Identity Resolution (OAuth vs Public)
    if user_id:
        token = await token_manager.get_token("youtube", user_id=str(user_id))
        if token:
            headers["Authorization"] = f"Bearer {token}"
            logger.info(f"[YouTube API] Using OAuth for video {video_id} (User: {user_id})")
        elif api_key:
            params["key"] = api_key
    elif api_key:
        params["key"] = api_key
    else:
        # Fallback to env
        env_key = os.getenv("YOUTUBE_API_KEY")
        if env_key:
            params["key"] = env_key
        else:
            logger.error("[YouTube API] No authentication provided (API_KEY or USER_ID)")
            return None
    
    try:
        # Use asyncio.to_thread for blocking requests call
        def _fetch():
            return requests.get(url, params=params, headers=headers, timeout=10)
            
        response = await asyncio.to_thread(_fetch)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"[YouTube API] API Error {response.status_code}: {data.get('error', {}).get('message')}")
            return None
        
        if "items" in data and len(data["items"]) > 0:
            item = data["items"][0]
            streaming_data = item.get("streamingData", {})
            
            # Check if video is restricted/age-gated (hardened check)
            status = item.get("status", {})
            if not status.get("embeddable", True):
                logger.warning(f"[YouTube API] Video {video_id} is not embeddable.")
            
            # Get adaptive formats (highest quality)
            adaptive_formats = streaming_data.get("adaptiveFormats", [])
            
            if adaptive_formats:
                # Get video-only format (highest quality)
                # Filter for mp4 to ensure compatibility with our FFmpeg pipeline
                for fmt in adaptive_formats:
                    if "video/mp4" in fmt.get("mimeType", "") and "videoOnly" in fmt.get("type", "videoOnly"):
                        return fmt.get("url")
                
                # Fallback to any adaptive format
                return adaptive_formats[0].get("url")
            
            # Fallback to regular formats
            formats = streaming_data.get("formats", [])
            if formats:
                return formats[0].get("url")
        
        logger.warning(f"[YouTube API] No streaming data found for video {video_id}")
        return None
    except Exception as e:
        logger.error(f"[YouTube API] Exception fetching video {video_id}: {e}")
        return None


def extract_video_id_from_url(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    if not url:
        return None
        
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'vid=([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None
