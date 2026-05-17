from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
import uuid
from src.api.routes.auth import get_current_user
from src.api.utils.user_models import UserDB
from src.api.utils.api_responses import success_response
from src.services.knowledge.service import base_knowledge_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge", tags=["Knowledge Base"])

class QueryRequest(BaseModel):
    text: str
    limit: int = 3

class IngestRequest(BaseModel):
    text: str
    metadata: Dict[str, Any] | None = None

@router.post("/ingest")
async def ingest_knowledge(
    body: IngestRequest,
    current_user: UserDB = Depends(get_current_user)
):
    """
    Ingest text into the knowledge base.
    """
    try:
        doc_id = await base_knowledge_service.ingest_text(
            text=body.text,
            dataset_id="default",
            metadata=body.metadata or {}
        )
        return success_response(data={"document_id": doc_id, "status": "ingested"})
    except Exception as e:
        logger.error(f"[Knowledge] Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
async def query_knowledge(
    body: QueryRequest,
    current_user: UserDB = Depends(get_current_user)
):
    """
    Query the knowledge base for relevant documents.
    """
    try:
        results = await base_knowledge_service.query(
            text=body.text,
            dataset_id="default",
            limit=body.limit
        )
        return success_response(data={"results": results})
    except Exception as e:
        logger.error(f"[Knowledge] Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_knowledge_stats(
    current_user: UserDB = Depends(get_current_user)
):
    """
    Get knowledge base statistics.
    """
    try:
        stats = await base_knowledge_service.get_stats(dataset_id="default")
        return success_response(data=stats)
    except Exception as e:
        logger.error(f"[Knowledge] Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_user)
):
    """
    Upload and ingest a document file (Text for now).
    """
    try:
        content = await file.read()
        text = content.decode("utf-8")
        
        doc_id = await base_knowledge_service.ingest_text(
            text=text,
            dataset_id="default",
            metadata={"filename": file.filename}
        )
        
        return success_response(data={
            "document_id": doc_id,
            "filename": file.filename,
            "status": "ingested"
        })
    except Exception as e:
        logger.error(f"[Knowledge] File upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process file. Ensure it is a valid text file.")
