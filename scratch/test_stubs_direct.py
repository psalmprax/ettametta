import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.services.discovery.video_lead_scanner import VideoLeadScanner

async def run_direct_test():
    scanner = VideoLeadScanner()
    uri = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    niche = "Motivation"
    
    print(f"Evaluating performance for: {uri}")
    res = await scanner.evaluate_video_performance(uri, niche)
    
    print("\n--- PERFORMANCE EVALUATION RESULT ---")
    print(f"Title: {res.get('video_data', {}).get('title')}")
    print(f"Creator: {res.get('video_data', {}).get('creator')}")
    print(f"Views: {res.get('video_data', {}).get('view_count')}")
    print(f"Likes: {res.get('video_data', {}).get('like_count')}")
    print(f"Comments: {res.get('video_data', {}).get('comment_count')}")
    print(f"Duration: {res.get('video_data', {}).get('duration')} seconds")
    print("\nEngagement Analysis:")
    print(res.get("engagement_analysis"))
    print("\nViral Factors:")
    print(res.get("viral_factors"))
    print("\nRepurposing Suggestions:")
    print(res.get("repurposing_suggestions"))
    print("\nContent Template:")
    print(res.get("content_template"))

if __name__ == "__main__":
    asyncio.run(run_direct_test())
