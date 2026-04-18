from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.utils.database import get_db
from api.utils.models import PersonaDB
from api.routes.auth import get_current_user
import uuid
import os
import requests
from api.config import settings
from pydantic import BaseModel
from api.utils.api_responses import success_response

router = APIRouter(prefix="/persona", tags=["Persona Engine"])


class PersonaResponse(BaseModel):
    id: str
    name: str
    reference_image_url: str | None = None
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
    image: UploadFile = File(None),
    audio: UploadFile = File(None),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Registers a new Persona for deepfake generation.
    Files are uploaded to the configured S3-compatible storage.
    """
    from api.utils.storage import storage_service
    import tempfile

    persona = PersonaDB(name=name, user_id=current_user.id)

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
            persona.reference_image_url = url
        else:
            # Fallback: return local path indicator
            persona.reference_image_url = f"local://{remote_name}"

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
    db: AsyncSession = Depends(get_db),
):
    """
    Initiates the deepfake generation pipeline via PersonaService.
    """
    stmt = select(PersonaDB).where(
        PersonaDB.id == request.persona_id, PersonaDB.user_id == current_user.id
    )
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    from services.video_engine.persona_service import base_persona_service

    try:
        url = await base_persona_service.animate_persona(
            persona.reference_image_url, request.topic, request.script
        )
        return success_response(data={"status": "success", "video_url": url})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_personas(
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
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
    current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)
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
