"""AllocateAI API package."""

from fastapi import APIRouter

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.optimizer import router as optimizer_router
from backend.app.api.routes.version import router as version_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(version_router)
api_v1_router.include_router(optimizer_router)

__all__ = ["api_v1_router"]
