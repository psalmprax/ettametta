import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.api.utils.database import get_db
from src.api.utils.models import PersonaDB
from src.api.routes.auth import get_current_user
import uuid
import os
import requests
from src.api.config import settings
from pydantic import BaseModel
from src.api.utils.api_responses import success_response

router = APIRouter(prefix="/persona", tags=["Persona Engine"])


class PersonaResponse(BaseModel):
    id: str
    name: str
    reference_image_uri: str | None = None
    voice_clone_id: str | None = None

    class Config:
        from_attributes = True


class PersonaGenerateRequest(BaseModel):
    persona_id: str
    topic: str
    script: str = None  # Any override


@router.post("/create")
async def create_persona(
    name: str,
    reference_image_uri: str | None = None,
    image: UploadFile = File(None),
    audio: UploadFile = File(None),
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Registers a new Persona for autonomous character generation.
    Files are uploaded to the configured S3-compatible storage.
    If reference_image_uri is provided, it is used directly.
    """
    from src.api.utils.storage import storage_service
    import tempfile
    
    persona = PersonaDB(name=name, user_id=current_user.id, reference_image_uri=reference_image_uri)

    # Handle image upload to S3 storage
    if image:
        # Save to temp file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            content = await image.read()
            tmp.write(content)
            tmp_path = tmp.name

        remote_name = f"personas/{current_user.id}/{uuid.uuid4()}.jpg"
        url = await storage_service.upload_asset(tmp_path, remote_name)
        if url:
            persona.reference_image_uri = url
        else:
            # Fallback: return local path indicator
            persona.reference_image_uri = f"local://{remote_name}"

        # Cleanup temp file
        os.unlink(tmp_path)

    if audio:
        persona.voice_clone_id = f"xtts_clone_{uuid.uuid4().hex[:8]}"

    db.add(persona)
    await db.commit()
    await db.refresh(persona)

    return success_response(data=PersonaResponse.model_validate(persona).model_dump())


@router.post("/generate")
async def generate_persona_video(
    request: PersonaGenerateRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Initiates the autonomous character generation pipeline via PersonaService.
    """
    stmt = select(PersonaDB).where(
        PersonaDB.id == request.persona_id, PersonaDB.user_id == current_user.id
    )
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    from src.services.video_engine.persona_service import base_persona_service

    try:
        url = await base_persona_service.animate_persona(
            persona.reference_image_uri, 
            request.topic, 
            request.script,
            voice_id=persona.voice_clone_id
        )
        return success_response(data={"status": "success", "video_uri": url})
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Persona animation failed: {e}")
        raise HTTPException(status_code=503, detail="Persona service unavailable")


@router.get("/list")
async def list_personas(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Returns all personas created by the current user.
    """
    stmt = select(PersonaDB).where(PersonaDB.user_id == current_user.id)
    result = await db.execute(stmt)
    personas = result.scalars().all()
    return success_response(
        data=[PersonaResponse.model_validate(p).model_dump() for p in personas]
    )


@router.get("/active")
async def list_active_personas(
    current_user=Depends(get_current_user), db=Depends(get_db)
):
    """
    Returns only active personas (all personas for now).
    """
    stmt = select(PersonaDB).where(PersonaDB.user_id == current_user.id)
    result = await db.execute(stmt)
    personas = result.scalars().all()
    return success_response(
        data=[PersonaResponse.model_validate(p).model_dump() for p in personas]
    )


@router.delete("/{persona_id}")
async def delete_persona(
    persona_id: str,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Purges a digital identity from the Persona Lab.
    """
    from sqlalchemy import delete
    stmt = delete(PersonaDB).where(
        PersonaDB.id == persona_id, PersonaDB.user_id == current_user.id
    )
    result = await db.execute(stmt)
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Persona not found or unauthorized")
        
    return success_response(data={"status": "purged", "id": persona_id})
