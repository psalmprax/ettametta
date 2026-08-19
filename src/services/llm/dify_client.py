import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Any, Dict, List, Optional
from src.api.config import settings
from src.api.utils.resilience import CircuitBreaker

logger = logging.getLogger("DifyClient")

BREAKER_OPEN_ERR = "Dify circuit breaker is OPEN"

class DifyClient:
    """
    Client for Dify.ai Application API.
    Supports Chat, Completion, and Workflow execution.
    Hardened with Circuit Breaker and Exponential Backoff.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or settings.DIFY_API_KEY
        self.base_url = (base_url or settings.DIFY_API_URL).rstrip("/")
        self.timeout = settings.DIFY_TIMEOUT
        self.breaker = CircuitBreaker(name="Dify")

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            raise ValueError("Dify API Key is missing. Set DIFY_API_KEY in environment.")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    @retry(
        stop=stop_after_attempt(settings.DEFAULT_RETRY_COUNT),
        wait=wait_exponential(
            multiplier=settings.RETRY_MULTIPLIER,
            min=settings.RETRY_MIN_WAIT,
            max=settings.RETRY_MAX_WAIT
        ),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, RuntimeError)),
        reraise=True
    )
    async def chat_messages(
        self,
        query: str,
        user_id: str,
        inputs: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        response_mode: str = "blocking",
        files: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send a message to a Chatbot app."""
        if self.breaker.is_open():
            raise RuntimeError(BREAKER_OPEN_ERR)

        url = f"{self.base_url}/chat-messages"
        payload = {
            "query": query,
            "user": user_id,
            "inputs": inputs or {},
            "response_mode": response_mode,
            "conversation_id": conversation_id or "",
            "files": files or []
        }

        logger.debug(f"Dify POST to {url} for user {user_id}")
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                data = response.json()
                self.breaker.record_success()
                return data
            except httpx.HTTPStatusError as e:
                error_body = ""
                try:
                    error_body = e.response.text
                except Exception:
                    pass
                logger.exception(f"Dify Chat API Status Error: {e.response.status_code} - Body: {error_body}")
                self.breaker.record_failure()
                raise
            except Exception:
                logger.exception("Dify Chat API error")
                self.breaker.record_failure()
                raise

    @retry(
        stop=stop_after_attempt(settings.DEFAULT_RETRY_COUNT),
        wait=wait_exponential(
            multiplier=settings.RETRY_MULTIPLIER,
            min=settings.RETRY_MIN_WAIT,
            max=settings.RETRY_MAX_WAIT
        ),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, RuntimeError)),
        reraise=True
    )
    async def completion_messages(
        self,
        inputs: Dict[str, Any],
        user_id: str,
        response_mode: str = "blocking",
        files: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send inputs to a Completion (Text Generator) app."""
        if self.breaker.is_open():
            raise RuntimeError(BREAKER_OPEN_ERR)

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
                data = response.json()
                self.breaker.record_success()
                return data
            except Exception:
                logger.exception("Dify Completion API error")
                self.breaker.record_failure()
                raise

    @retry(
        stop=stop_after_attempt(settings.DEFAULT_RETRY_COUNT),
        wait=wait_exponential(
            multiplier=settings.RETRY_MULTIPLIER,
            min=settings.RETRY_MIN_WAIT,
            max=settings.RETRY_MAX_WAIT
        ),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, RuntimeError)),
        reraise=True
    )
    async def run_workflow(
        self,
        inputs: Dict[str, Any],
        user_id: str,
        response_mode: str = "blocking"
    ) -> Dict[str, Any]:
        """Execute a Dify Workflow."""
        if self.breaker.is_open():
            raise RuntimeError(BREAKER_OPEN_ERR)

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
                data = response.json()
                self.breaker.record_success()
                return data
            except Exception:
                logger.exception("Dify Workflow API error")
                self.breaker.record_failure()
                raise

# Singleton accessor
base_dify_client = DifyClient()
