import os
import re
import requests
from typing import Optional

def get_youtube_streaming_url(video_id: str, api_key: str) -> Optional[str]:
    """
    Get video streaming URL using YouTube Data API.
    Returns the best quality adaptive format URL.
    """
    if not api_key:
        return None
    
    # YouTube Data API endpoint for video details
    url = f"https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "streamingData",
        "id": video_id,
        "key": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if "items" in data and len(data["items"]) > 0:
            streaming_data = data["items"][0].get("streamingData", {})
            
            # Get adaptive formats (highest quality)
            adaptive_formats = streaming_data.get("adaptiveFormats", [])
            
            if adaptive_formats:
                # Get video-only format (highest quality)
                for fmt in adaptive_formats:
                    if "videoOnly" in fmt.get("type", ""):
                        return fmt.get("url")
                
                # If no video-only, get first adaptive format
                return adaptive_formats[0].get("url")
            
            # Fallback to regular formats
            formats = streaming_data.get("formats", [])
            if formats:
                return formats[0].get("url")
        
        return None
    except Exception as e:
        print(f"[YouTube API] Error: {e}")
        return None


def extract_video_id_from_url(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    # Handle different YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None
