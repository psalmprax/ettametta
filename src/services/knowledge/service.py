import logging
import httpx
from typing import Dict, Any, List, Optional
from src.api.config import settings

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Production-grade Knowledge Service powered by Dify Datasets (RAG).
    """
    
    def __init__(self):
        self.api_key = settings.DIFY_DATASET_API_KEY
        self.base_url = settings.DIFY_API_URL.rstrip("/")
        self.timeout = settings.DIFY_TIMEOUT

    def _get_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def is_enabled(self) -> bool:
        return bool(self.api_key)

    def _resolve_dataset_id(self, dataset_id: str) -> str:
        try:
            import uuid
            uuid.UUID(dataset_id)
            return dataset_id
        except ValueError:
            return "d1f1d1f1-d1f1-d1f1-d1f1-d1f1d1f1d1f1"

    async def ingest_text(self, text: str, dataset_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Ingest text into a Dify dataset.
        """
        if not self.is_enabled():
            logger.warning("KnowledgeService (Dify) is disabled. Set DIFY_DATASET_API_KEY.")
            return "disabled-id"

        resolved_id = self._resolve_dataset_id(dataset_id)
        url = f"{self.base_url}/datasets/{resolved_id}/document/create_by_text"
        payload = {
            "name": f"ingested_{metadata.get('source', 'unknown')}" if metadata else "ingested_text",
            "text": text,
            "indexing_technique": "high_quality",
            "process_rule": {"mode": "automatic"}
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("document", {}).get("id", "unknown-id")
            except Exception as e:
                logger.exception(f"Dify ingestion failed: {e}")
                return "error-id"
    
    async def query(self, text: str, dataset_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Query the knowledge base using Dify's search API.
        """
        if not self.is_enabled():
            return []

        resolved_id = self._resolve_dataset_id(dataset_id)
        url = f"{self.base_url}/datasets/{resolved_id}/retrieve"
        payload = {
            "query": text,
            "retrieval_model": {
                "search_method": "hybrid_search",
                "top_k": limit
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                data = response.json()
                records = data.get("records", [])
                
                # Format records to ensure a flat structure with 'content' as expected by callers
                formatted = []
                for rec in records:
                    segment = rec.get("segment", {})
                    content = segment.get("content", "")
                    formatted.append({
                        "content": content,
                        "score": rec.get("score", 0.0),
                        "segment": segment
                    })
                return formatted
            except Exception as e:
                logger.exception(f"Dify query failed: {e}")
                return []
    
    async def get_stats(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get knowledge base statistics from Dify.
        """
        if not self.is_enabled():
            return {"status": "disabled"}

        resolved_id = self._resolve_dataset_id(dataset_id)
        # Dify doesn't have a direct "stats" endpoint for datasets in the public API yet,
        # but we can return basic metadata if needed.
        return {
            "provider": "dify",
            "dataset_id": resolved_id,
            "enabled": True
        }


base_knowledge_service = KnowledgeService()
