"""CSR Saturation Engine subpackage for AllocateAI Decision Engine.

Authoritative source: Technical Contract v1.0 Section 11 & 59.
Phase 3: Full deterministic CSR Saturation Index Engine implementation.
"""

from backend.app.engine.saturation.engine import (
    BENCHMARK_PER_CAPITA_CSR_PAISE,
    CALCULATION_VERSION,
    MODEL_NAME,
    SCHEMA_VERSION,
    WEIGHT_BENEFICIARY_COVERAGE,
    WEIGHT_FUNDING_DENSITY,
    WEIGHT_NEED_ADJUSTMENT,
    SaturationEngine,
)
from backend.app.engine.schemas import SaturationContext, SaturationResult

__all__ = [
    "SaturationEngine",
    "SaturationContext",
    "SaturationResult",
    "CALCULATION_VERSION",
    "MODEL_NAME",
    "SCHEMA_VERSION",
    "BENCHMARK_PER_CAPITA_CSR_PAISE",
    "WEIGHT_FUNDING_DENSITY",
    "WEIGHT_BENEFICIARY_COVERAGE",
    "WEIGHT_NEED_ADJUSTMENT",
]
