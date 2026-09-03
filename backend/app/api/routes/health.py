"""Health check API route for AllocateAI Decision Engine."""

from typing import Any
from fastapi import APIRouter

from backend.app.engine.constants import (
    API_VERSION,
    MARGINAL_CALCULATION_VERSION,
    OPTIMIZER_CALCULATION_VERSION,
    SATURATION_CALCULATION_VERSION,
)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=dict[str, Any])
def get_health() -> dict[str, Any]:
    """Retrieve operational health status of the AllocateAI Decision Engine API.

    Returns:
        Deterministic health status payload without timestamps.
    """
    return {
        "status": "healthy",
        "api_version": API_VERSION,
        "optimizer_version": OPTIMIZER_CALCULATION_VERSION,
        "engines": {
            "scoring": "scoring-v1",
            "saturation": SATURATION_CALCULATION_VERSION,
            "marginal": MARGINAL_CALCULATION_VERSION,
            "optimizer": OPTIMIZER_CALCULATION_VERSION,
        },
        "uptime": "deterministic",
    }
