"""Allocation Optimizer subpackage for AllocateAI Decision Engine.

Authoritative source: Technical Contract v1.0 Section 14-16 & 51.
Phase 5: Full deterministic Allocation Optimizer implementation.
"""

from backend.app.engine.optimizer.engine import (
    CALCULATION_VERSION,
    AllocationOptimizer,
    RankedProject,
)

__all__ = ["AllocationOptimizer", "CALCULATION_VERSION", "RankedProject"]
