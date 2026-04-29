import requests
import logging
from src.api.config import settings
from .base_skill import OpenClawBaseSkill

logger = logging.getLogger(__name__)


class PublishingSkill(OpenClawBaseSkill):
    def __init__(self):
        super().__init__()
        self.video_uri = f"{settings.API_URL}/video"
        self.publish_url = f"{settings.API_URL}/publish"

    def execute(
        self,
        action: str = "publish",
        job_id: str = "",
        platform: str = "YouTube Shorts",
        niche: str = "Motivation",
        **kwargs,
    ) -> str:
        """
        Polymorphic entry point for OpenClaw agent.
        """
        jid = job_id or kwargs.get("job_id", "")
        plt = platform or kwargs.get("platform", "YouTube Shorts")
        n = niche or kwargs.get("niche", "Motivation")
        
        return self.publish_job(job_id=jid, platform=plt, niche=n)


    def publish_job(
        self, job_id: str, platform: str = "YouTube Shorts", niche: str = "Motivation"
    ) -> str:
        """
        Finds a completed job and publishes it.
        """
        try:
            # 1. Find the job details to get output path/url
            # Listing all jobs and filtering (since we don't have a direct GET /jobs/{id} yet)
            jobs_response = requests.get(
                f"{self.video_uri}/jobs", headers=self._get_headers(), timeout=10
            )

            if jobs_response.status_code != 200:
                return f"⚠️ **Error fetching jobs**: {jobs_response.status_code}"

            jobs_raw = jobs_response.json()
            jobs = (
                jobs_raw.get("data", {}).get("jobs", [])
                if isinstance(jobs_raw, dict)
                else jobs_raw
            )
            target_job = next(
                (j for j in jobs if j.get("job_id") == job_id or j.get("id") == job_id),
                None,
            )

            if not target_job:
                return f"❌ **Job Not Found**: Could not find job with ID `{job_id}`."

            if (
                target_job["status"] != "Completed"
                and target_job["status"] != "Published"
            ):
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
                "inject_monetization": True,
            }

            pub_response = requests.post(
                f"{self.publish_url}/post",
                json=payload,
                headers=self._get_headers(),
                timeout=60,
            )

            if pub_response.status_code == 200:
                raw_data = pub_response.json()
                data = (
                    raw_data.get("data", {}) if isinstance(raw_data, dict) else raw_data
                )
                final_url = data.get("url", "No URL returned")
                return f"🚀 **Published Successfully!**\nURL: {final_url}\nPlatform: {platform}"
            else:
                return f"⚠️ **Publishing Failed**: {pub_response.text}"

        except Exception as e:
            logger.error(f"Publishing Skill Error: {e}")
            return f"⚠️ Skill Error: {str(e)}"


publishing_skill = PublishingSkill()
