from fastapi import APIRouter
from src.api.utils.api_responses import success_response
import time

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
async def health_check():
    return success_response(data={
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    })
