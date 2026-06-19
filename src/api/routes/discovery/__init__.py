from fastapi import APIRouter
from src.api.routes.discovery.scan import router as scan_router
from src.api.routes.discovery.candidates import router as candidates_router
from src.api.routes.discovery.analysis import router as analysis_router

router = APIRouter(prefix="/discovery", tags=["Discovery"])
router.include_router(scan_router)
router.include_router(candidates_router)
router.include_router(analysis_router)
