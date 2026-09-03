"""Scoring engine subpackage for AllocateAI Decision Engine.

Authoritative source: Technical Contract v1.0 & Software Contract v1.0.
Phase 2: Full deterministic Base Impact Scoring Engine implementation.
"""

from backend.app.engine.scoring.engine import (
    DEFAULT_SCORING_WEIGHTS,
    ENGINE_VERSION,
    ScoringEngine,
)

__all__ = ["ScoringEngine", "DEFAULT_SCORING_WEIGHTS", "ENGINE_VERSION"]
