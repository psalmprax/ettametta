import httpx
import logging
import asyncio
from src.api.config import settings

logger = logging.getLogger("InternalJobClient")

class InternalJobClient:
    """
    Client for internal services to communicate with the API.
    Used for database decoupling (Standard 3.12).
    """
    def __init__(self, base_url: str = None):
        # Use API_URL (internal docker networking) if available
        self.base_url = base_url or settings.API_URL or "http://api:8000"
        self.token = settings.INTERNAL_API_TOKEN

    async def create_job(self, task_id: str, title: str, user_id: str, metadata: dict = None):
        url = f"{self.base_url}/api/v1/internal/jobs"
        payload = {
            "id": task_id,
            "title": title,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        headers = {"X-Internal-Token": self.token}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Failed to create internal job: {resp.status_code} - {resp.text}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Internal job creation error: {e}")
            return False

    async def update_job(self, job_id: str, status: str = None, progress: int = None, output_path: str = None, error_message: str = None):
        url = f"{self.base_url}/api/v1/internal/jobs/{job_id}"
        payload = {}
        if status: payload["status"] = status
        if progress is not None: payload["progress"] = progress
        if output_path: payload["output_path"] = output_path
        if error_message: payload["error_message"] = error_message
        
        headers = {"X-Internal-Token": self.token}
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.patch(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"Failed to update internal job: {resp.status_code} - {resp.text}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Internal job update error: {e}")
            return False

# Global instance for easy use
internal_job_client = InternalJobClient()
