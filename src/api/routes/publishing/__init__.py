from fastapi import APIRouter

from .platforms import router as platforms_router
from .campaigns import router as campaigns_router
from .schedule import router as schedule_router
from .publish import router as publish_router

router = APIRouter(prefix="/publish", tags=["Publishing"])

router.include_router(platforms_router)
router.include_router(campaigns_router)
router.include_router(schedule_router)
router.include_router(publish_router)
