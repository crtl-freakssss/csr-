"""AllocateAI API Routes subpackage."""

from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.optimizer import router as optimizer_router
from backend.app.api.routes.version import router as version_router

__all__ = ["health_router", "optimizer_router", "version_router"]
