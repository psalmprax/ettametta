from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from api.utils.database import get_db
from api.utils.models import PersonaDB
from api.routes.auth import get_current_user
import uuid
import os
import requests
from config import settings
from pydantic import BaseModel

router = APIRouter(prefix="/persona", tags=["Persona Engine"])

class PersonaResponse(BaseModel):
    id: int
    name: str
    reference_image_url: str | None = None
    voice_clone_id: str | None = None

class PersonaGenerateRequest(BaseModel):
    persona_id: int
    topic: str
    script: str = None  # Optional override

@router.post("/create", response_model=PersonaResponse)
async def create_persona(
    name: str,
    image: UploadFile = File(None),
    audio: UploadFile = File(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registers a new Persona for deepfake generation.
    In a real system, files are uploaded to S3. Here we mock storage.
    """
    persona = PersonaDB(
        name=name,
        user_id=current_user.id
    )
    
    # Mock file upload
    if image:
        persona.reference_image_url = f"https://storage.googleapis.com/viral-forge-assets/personas/{current_user.id}/{uuid.uuid4()}.jpg"
    
    if audio:
        persona.voice_clone_id = f"xtts_clone_{uuid.uuid4().hex[:8]}"
        
    db.add(persona)
    db.commit()
    db.refresh(persona)
    
    return persona
    
@router.post("/generate")
async def generate_persona_video(request: PersonaGenerateRequest, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Initiates the deepfake generation pipeline via PersonaService.
    """
    persona = db.query(PersonaDB).filter(PersonaDB.id == request.persona_id, PersonaDB.user_id == current_user.id).first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
        
    from services.video_engine.persona_service import persona_service
    
    try:
        url = await persona_service.animate_persona(
            persona.reference_image_url, 
            request.topic,
            request.script
        )
        return {"status": "success", "video_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
