import requests
import logging
from config import settings
from typing import Optional

logger = logging.getLogger(__name__)

class PublishingSkill:
    def __init__(self):
        self.video_url = f"{settings.API_URL}/video"
        self.publish_url = f"{settings.API_URL}/publish"

    def publish_job(self, job_id: str, platform: str = "YouTube Shorts", niche: str = "Motivation") -> str:
        """
        Finds a completed job and publishes it.
        """
        try:
            # 1. Find the job details to get output path/url
            # Listing all jobs and filtering (since we don't have a direct GET /jobs/{id} yet)
            jobs_response = requests.get(f"{self.video_url}/jobs", timeout=10)
            
            if jobs_response.status_code != 200:
                 return f"⚠️ **Error fetching jobs**: {jobs_response.status_code}"
            
            jobs = jobs_response.json()
            target_job = next((j for j in jobs if j["id"] == job_id), None)
            
            if not target_job:
                return f"❌ **Job Not Found**: Could not find job with ID `{job_id}`."
            
            if target_job["status"] != "Completed" and target_job["status"] != "Published":
                 # Allow publishing even if status is 'Published' (re-publish?) or just check for output
                 # If status is not completed, we might not have a video path.
                 # But let's check output_path presence.
                 if not target_job.get("output_path"):
                     return f"⚠️ **Job Not Ready**: Status is '{target_job['status']}' and no output path available."

            video_path = target_job.get("output_path")
            
            # 2. Call Publish Endpoint
            payload = {
                "video_path": video_path,
                "niche": niche,
                "platform": platform,
                "inject_monetization": True
            }
            
            pub_response = requests.post(f"{self.publish_url}/post", json=payload, timeout=60)
            
            if pub_response.status_code == 200:
                data = pub_response.json()
                final_url = data.get("url", "No URL returned")
                return f"🚀 **Published Successfully!**\nURL: {final_url}\nPlatform: {platform}"
            else:
                return f"⚠️ **Publishing Failed**: {pub_response.text}"

        except Exception as e:
            logger.error(f"Publishing Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"

publishing_skill = PublishingSkill()
