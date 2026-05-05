import os
import json
import logging
import asyncio
import httpx
from typing import Any, List, Dict
from pathlib import Path
from datetime import datetime
from src.api.config import settings

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """
    Ettametta Knowledge Base Service
    Upgraded: Uses Qdrant for scalable vector search and hybrid retrieval.
    Fallback: Gracefully handles connection issues to Qdrant.
    """

    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        self.collection_name = "ettametta_knowledge"
        self._client = None
        self._initialized = False

    async def _get_client(self):
        """Lazy initialization of the Qdrant client."""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                from qdrant_client.http import models
                
                self._client = QdrantClient(url=self.qdrant_url)
                
                # Check if collection exists, if not create it
                collections = self._client.get_collections().collections
                exists = any(c.name == self.collection_name for c in collections)
                
                if not exists:
                    logger.info(f"🏗️ [KnowledgeBase] Creating Qdrant collection: {self.collection_name}")
                    await self._create_collection()
                else:
                    # Check dimension compatibility
                    collection_info = self._client.get_collection(collection_name=self.collection_name)
                    sample_embedding = await self.get_embedding("test")
                    if sample_embedding:
                        vector_size = len(sample_embedding)
                        if collection_info.config.params.vectors.size != vector_size:
                            logger.warning(f"🔄 [KnowledgeBase] Dimension mismatch (expected {collection_info.config.params.vectors.size}, got {vector_size}). Recreating collection...")
                            self._client.delete_collection(collection_name=self.collection_name)
                            await self._create_collection()
                    else:
                        logger.warning("⚠️ [KnowledgeBase] Could not verify dimensions: Embedding service unavailable.")
                        
                self._initialized = True
            except ImportError:
                logger.error("[KnowledgeBase] qdrant-client not installed.")
                return None
            except Exception as e:
                logger.error(f"[KnowledgeBase] Qdrant connection failed: {e}")
                return None
        return self._client

    async def _create_collection(self):
        """Helper to create collection with correct dimensions."""
        from qdrant_client.http import models
        sample_embedding = await self.get_embedding("test")
        vector_size = len(sample_embedding)
        
        self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            )
        )

    async def get_embedding(self, text: str) -> List[float]:
        """Generates an embedding for the given text using Ollama."""
        url = f"{settings.OLLAMA_URL.rstrip('/')}/api/embeddings"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": text
        }
        
        async with httpx.AsyncClient(timeout=300) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data["embedding"]
            except Exception as e:
                logger.error(f"[KnowledgeBase] Embedding generation failed: {e}")
                # Don't return a hardcoded 4096 vector as it causes dimension mismatch cascades
                raise e

    async def ingest_text(self, text: str, metadata: Dict[str, Any] | None = None):
        """Ingests a text block into Qdrant."""
        client = await self._get_client()
        if not client or not text.strip():
            logger.warning("[KnowledgeBase] Qdrant not available, skipping ingestion.")
            return None

        embedding = await self.get_embedding(text)
        
        from qdrant_client.http import models
        from uuid import uuid4

        doc_id = str(uuid4())
        client.upsert(
            collection_name=self.collection_name,
            points=[
                models.PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "content": text,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": metadata or {}
                    }
                )
            ]
        )
        logger.info(f"📥 [KnowledgeBase] Ingested document: {doc_id}")
        return doc_id

    async def query(self, text: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Queries Qdrant for similar documents (Hybrid Search approach)."""
        client = await self._get_client()
        if not client:
            return []

        embedding = await self.get_embedding(text)
        
        # Vector Search using new unified Query API (v1.17+)
        search_result = client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=limit,
            with_payload=True
        ).points
        
        results = []
        for hit in search_result:
            results.append({
                "content": hit.payload.get("content", ""),
                "score": hit.score,
                "metadata": hit.payload.get("metadata", {})
            })
        
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Returns statistics from Qdrant."""
        try:
            if not self._client:
                return {"healthy": False, "msg": "Client not initialized"}
            
            collection_info = self._client.get_collection(collection_name=self.collection_name)
            return {
                "document_count": collection_info.points_count,
                "status": collection_info.status,
                "healthy": True
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}

# Singleton instance
base_knowledge_service = KnowledgeBaseService()
