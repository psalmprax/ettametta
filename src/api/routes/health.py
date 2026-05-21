import time
from fastapi import APIRouter
from sqlalchemy import text
from src.api.utils.api_responses import success_response, error_response
from src.api.utils.database import AsyncSessionLocal
from src.api.utils.redis import get_redis

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """Health check with dependency verification."""
    checks = {}
    overall_status = "healthy"

    # Database check
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        overall_status = "degraded"

    # Redis check
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        checks["redis"] = "connected"
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:100]}"
        overall_status = "degraded"

    data = {
        "status": overall_status,
        "timestamp": time.time(),
        "version": "1.0.0",
        "dependencies": checks
    }

    if overall_status == "healthy":
        return success_response(data=data)
    return error_response(message="Service degraded", status_code=503, details=data)
