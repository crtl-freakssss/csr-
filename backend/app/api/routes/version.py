"""Version discovery API route for AllocateAI Decision Engine."""

from typing import Any
from fastapi import APIRouter

from backend.app.engine.constants import (
    API_VERSION,
    DNA_SCHEMA_VERSION,
    MARGINAL_CALCULATION_VERSION,
    OPTIMIZER_CALCULATION_VERSION,
    PROJECT_SCHEMA_VERSION,
    SATURATION_CALCULATION_VERSION,
)

router = APIRouter(tags=["Version"])


@router.get("/version", response_model=dict[str, Any])
def get_version() -> dict[str, Any]:
    """Retrieve version configuration of API, calculation engines, and canonical schemas.

    Returns:
        Deterministic version configuration payload.
    """
    return {
        "project": PROJECT_SCHEMA_VERSION,
        "api": API_VERSION,
        "engines": {
            "scoring": "scoring-v1",
            "saturation": SATURATION_CALCULATION_VERSION,
            "marginal": MARGINAL_CALCULATION_VERSION,
            "optimizer": OPTIMIZER_CALCULATION_VERSION,
        },
        "schema_versions": {
            "project": PROJECT_SCHEMA_VERSION,
            "dna": DNA_SCHEMA_VERSION,
        },
    }
