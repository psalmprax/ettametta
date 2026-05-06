import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Stub knowledge service - returns empty stats."""
    
    async def ingest_text(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """Ingest text into the knowledge base."""
        return "stub-doc-id"
    
    async def query(self, text: str, limit: int = 3) -> list:
        """Query the knowledge base."""
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return {
            "total_documents": 0,
            "total_queries": 0,
            "storage_used_mb": 0.0,
        }


base_knowledge_service = KnowledgeService()
