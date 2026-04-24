from fastapi import APIRouter
from src.api.utils.api_responses import success_response

router = APIRouter(prefix="/proxy", tags=["Proxy"])

@router.get("/status")
async def proxy_status():
    return success_response(data={"status": "active"})
