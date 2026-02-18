from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.utils.database import get_db
from api.utils.models import ABTestDB
from api.routes.auth import get_current_user
from api.utils.user_models import UserDB
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/ab", tags=["A/B Testing"])

class ABTestCreate(BaseModel):
    content_id: str
    variant_a_title: str
    variant_b_title: str

@router.post("/test/start")
async def start_ab_test(request: ABTestCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Initializes an A/B test for a piece of content.
    """
    test = ABTestDB(
        content_id=request.content_id,
        variant_a_title=request.variant_a_title,
        variant_b_title=request.variant_b_title
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return test

@router.get("/test/{test_id}")
async def get_test_results(test_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    test = db.query(ABTestDB).filter(ABTestDB.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@router.post("/record-view/{content_id}")
async def record_variant_view(content_id: str, variant: str, db: Session = Depends(get_db)):
    """
    Records a view for a specific variant. Variant should be 'A' or 'B'.
    """
    test = db.query(ABTestDB).filter(ABTestDB.content_id == content_id).first()
    if not test:
        return {"status": "no_test_active"}
    
    if variant.upper() == 'A':
        test.variant_a_views += 1
    elif variant.upper() == 'B':
        test.variant_b_views += 1
    
    db.commit()
    return {"status": "success"}
