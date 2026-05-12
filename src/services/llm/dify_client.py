import httpx
import logging
import json
from typing import Any, Dict, List, Optional
from src.api.config import settings

logger = logging.getLogger("DifyClient")

class DifyClient:
    """
    Client for Dify.ai Application API.
    Supports Chat, Completion, and Workflow execution.
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.DIFY_API_KEY
        self.base_url = (base_url or settings.DIFY_API_URL).rstrip("/")
        self.timeout = settings.DIFY_TIMEOUT

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise ValueError("Dify API Key is missing. Set DIFY_API_KEY in environment.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def chat_messages(
        self,
        query: str,
        user_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        response_mode: str = "blocking",
        files: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a Chatbot app.
        """
        url = f"{self.base_url}/chat-messages"
        payload = {
            "query": query,
            "user": user_id,
            "inputs": inputs or {},
            "response_mode": response_mode,
            "conversation_id": conversation_id or "",
            "files": files or []
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Dify Chat API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Dify Chat API unexpected error: {e}")
                raise

    async def completion_messages(
        self,
        inputs: Dict[str, Any],
        user_id: str,
        response_mode: str = "blocking",
        files: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Send inputs to a Completion (Text Generator) app.
        """
        url = f"{self.base_url}/completion-messages"
        payload = {
            "inputs": inputs,
            "user": user_id,
            "response_mode": response_mode,
            "files": files or []
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Dify Completion API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Dify Completion API unexpected error: {e}")
                raise

    async def run_workflow(
        self,
        inputs: Dict[str, Any],
        user_id: str,
        response_mode: str = "blocking"
    ) -> Dict[str, Any]:
        """
        Execute a Dify Workflow.
        """
        url = f"{self.base_url}/workflows/run"
        payload = {
            "inputs": inputs,
            "user": user_id,
            "response_mode": response_mode
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Dify Workflow API error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Dify Workflow API unexpected error: {e}")
                raise

# Singleton accessor
base_dify_client = DifyClient()
