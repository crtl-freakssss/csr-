"""Marginal Impact Engine subpackage for AllocateAI Decision Engine.

Authoritative source: Technical Contract v1.0 Section 12 & 60.
Phase 4: Full deterministic Marginal Impact Engine implementation.
"""

from backend.app.engine.marginal_impact.engine import (
    CALCULATION_VERSION,
    COST_EFFICIENCY_WEIGHT,
    DEPENDENCY_VERSIONS,
    ENGINE_VERSION,
    INPUT_SCHEMA,
    NEED_BONUS_WEIGHT,
    SATURATION_PENALTY_WEIGHT,
    SIMULATION_TIERS,
    MarginalImpactEngine,
)
from backend.app.engine.schemas import MarginalImpactResult

__all__ = [
    "MarginalImpactEngine",
    "MarginalImpactResult",
    "CALCULATION_VERSION",
    "ENGINE_VERSION",
    "INPUT_SCHEMA",
    "DEPENDENCY_VERSIONS",
    "COST_EFFICIENCY_WEIGHT",
    "NEED_BONUS_WEIGHT",
    "SATURATION_PENALTY_WEIGHT",
    "SIMULATION_TIERS",
]
