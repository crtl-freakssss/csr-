"""Base Impact Scoring Engine for AllocateAI Decision Engine (Member C Phase 2).

Converts AI-generated ImpactDNA into a deterministic Base Impact Score.
Authoritative source: Software Contract v1.0 & Technical Contract v1.0.
Strictly deterministic: zero LLM calls, zero randomness, zero timestamps.
"""

from typing import Any, Final

from backend.app.engine.constants import (
    DNA_SCHEMA_VERSION,
    OPTIMIZER_CALCULATION_VERSION,
    SCORE_MAX,
    SCORE_MIN,
)
from backend.app.engine.exceptions import (
    InvalidProjectDataError,
    WeightValidationError,
)
from backend.app.engine.schemas import ImpactDNA, OptimizationWeights, Project
from backend.app.engine.utils import (
    clip_score,
    normalize_weights,
    validate_score,
    validate_weights,
)

# ---------------------------------------------------------------------------
# Scoring Constants & Version Metadata (Task D)
# ---------------------------------------------------------------------------

CALCULATION_VERSION: Final[str] = OPTIMIZER_CALCULATION_VERSION  # "optimizer-v1"
INPUT_SCHEMA: Final[str] = DNA_SCHEMA_VERSION                    # "dna-v1"
ENGINE_VERSION: Final[str] = "scoring-v1"
DEFAULT_SCORE_PRECISION: Final[int] = 6

# Canonical default weights (sum to 1.0)
DEFAULT_SCORING_WEIGHTS: Final[dict[str, float]] = {
    "need": 0.20,
    "marginal_impact": 0.25,
    "cost_efficiency": 0.20,
    "evidence": 0.15,
    "scalability": 0.10,
    "risk_penalty": 0.10,
}


class ScoringEngine:
    """Deterministic Base Impact Scoring Engine."""

    calculation_version: Final[str] = CALCULATION_VERSION
    input_schema: Final[str] = INPUT_SCHEMA
    engine_version: Final[str] = ENGINE_VERSION

    def __init__(self, precision: int = DEFAULT_SCORE_PRECISION) -> None:
        """Initialize the scoring engine with deterministic precision.

        Args:
            precision: Decimal places for final score rounding (default: 6).
        """
        self.precision = precision

    # -----------------------------------------------------------------------
    # Helper: Extract & Normalize Weights
    # -----------------------------------------------------------------------

    def _extract_and_normalize_weights(
        self,
        weights: OptimizationWeights | dict[str, float] | None,
    ) -> dict[str, float]:
        """Extract and deterministically normalize the 6 scoring weights.

        Args:
            weights: OptimizationWeights instance, dict of weights, or None.

        Returns:
            Dictionary of 6 normalized weights summing to 1.0.

        Raises:
            WeightValidationError: If weights are invalid, out of bounds, or non-numeric.
        """
        if weights is None:
            raw_weights = dict(DEFAULT_SCORING_WEIGHTS)
        elif isinstance(weights, OptimizationWeights):
            raw_weights = {
                "need": weights.need,
                "marginal_impact": weights.marginal_impact,
                "cost_efficiency": weights.cost_efficiency,
                "evidence": weights.evidence,
                "scalability": weights.scalability,
                "risk_penalty": weights.risk_penalty,
            }
        elif isinstance(weights, dict):
            if not weights:
                raise WeightValidationError("Weights dictionary cannot be empty")
            raw_weights = {
                "need": weights.get("need", DEFAULT_SCORING_WEIGHTS["need"]),
                "marginal_impact": weights.get("marginal_impact", DEFAULT_SCORING_WEIGHTS["marginal_impact"]),
                "cost_efficiency": weights.get("cost_efficiency", DEFAULT_SCORING_WEIGHTS["cost_efficiency"]),
                "evidence": weights.get("evidence", DEFAULT_SCORING_WEIGHTS["evidence"]),
                "scalability": weights.get("scalability", DEFAULT_SCORING_WEIGHTS["scalability"]),
                "risk_penalty": weights.get("risk_penalty", DEFAULT_SCORING_WEIGHTS["risk_penalty"]),
            }
        else:
            raise WeightValidationError(
                f"Weights must be OptimizationWeights or dict, got {type(weights).__name__}"
            )

        # Validate that each weight is numeric and non-negative
        for k, v in raw_weights.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise WeightValidationError(
                    f"Weight '{k}' must be a numeric value, got {type(v).__name__}",
                    invalid_weights={k: v},
                )
            if v < 0.0:
                raise WeightValidationError(
                    f"Weight '{k}' cannot be negative, got {v}",
                    invalid_weights={k: v},
                )

        # Normalize across the 6 scoring dimensions to guarantee sum == 1.0
        return normalize_weights(raw_weights)

    # -----------------------------------------------------------------------
    # Helper: Resolve Impact DNA
    # -----------------------------------------------------------------------

    def _resolve_dna(
        self,
        project: Project,
        dna: ImpactDNA | None = None,
    ) -> ImpactDNA:
        """Resolve ImpactDNA from arguments or embedded project attribute.

        Args:
            project: Project instance.
            dna: Explicit ImpactDNA or None.

        Returns:
            Resolved ImpactDNA instance.

        Raises:
            InvalidProjectDataError: If Project is invalid or ImpactDNA is missing.
        """
        if not isinstance(project, Project):
            raise InvalidProjectDataError(
                f"project must be an instance of Project, got {type(project).__name__}"
            )

        target_dna = dna or getattr(project, "impact_dna", None)
        if target_dna is None:
            raise InvalidProjectDataError(
                f"Project '{project.project_id}' is missing required ImpactDNA fingerprint",
                project_id=project.project_id,
                field_name="impact_dna",
            )

        if not isinstance(target_dna, ImpactDNA):
            raise InvalidProjectDataError(
                f"ImpactDNA must be an instance of ImpactDNA, got {type(target_dna).__name__}",
                project_id=project.project_id,
                field_name="impact_dna",
            )

        return target_dna

    # -----------------------------------------------------------------------
    # Task A: Public Method - validate_inputs
    # -----------------------------------------------------------------------

    def validate_inputs(
        self,
        project: Project,
        weights: OptimizationWeights | dict[str, float] | None = None,
        dna: ImpactDNA | None = None,
    ) -> None:
        """Validate project, DNA scores, and policy weights for scoring feasibility.

        Args:
            project: Candidate project model.
            weights: Optional priority weights.
            dna: Optional explicit ImpactDNA.

        Raises:
            InvalidProjectDataError: If project or DNA fields are invalid or out of bounds.
            WeightValidationError: If weights fail bounds or normalization checks.
        """
        resolved_dna = self._resolve_dna(project, dna)

        # Validate all 6 core score dimensions are valid [0.0, 1.0] numbers
        score_fields = [
            ("need_score", resolved_dna.need_score),
            ("expected_impact_score", resolved_dna.expected_impact_score),
            ("cost_efficiency_score", resolved_dna.cost_efficiency_score),
            ("evidence_strength_score", resolved_dna.evidence_strength_score),
            ("scalability_score", resolved_dna.scalability_score),
            ("implementation_risk_score", resolved_dna.implementation_risk_score),
        ]

        for field_name, score_val in score_fields:
            try:
                validate_score(score_val, name=field_name)
            except InvalidProjectDataError as e:
                e.project_id = project.project_id
                raise e

        # Validate weights if explicitly supplied
        if weights is not None:
            if isinstance(weights, dict):
                if not weights:
                    raise WeightValidationError("Weights dictionary cannot be empty")
                for k, v in weights.items():
                    if not isinstance(v, (int, float)) or isinstance(v, bool):
                        raise WeightValidationError(f"Weight '{k}' must be numeric, got {v}")
                    if v < 0.0:
                        raise WeightValidationError(f"Weight '{k}' cannot be negative, got {v}")
                if sum(weights.values()) <= 0:
                    raise WeightValidationError("Sum of weights must be strictly positive")
            elif not isinstance(weights, OptimizationWeights):
                raise WeightValidationError(
                    f"Invalid weights type: {type(weights).__name__}"
                )

    # -----------------------------------------------------------------------
    # Task B: Public Method - calculate_base_score
    # -----------------------------------------------------------------------

    def calculate_base_score(
        self,
        project: Project,
        weights: OptimizationWeights | dict[str, float] | ImpactDNA | None = None,
        dna: ImpactDNA | None = None,
    ) -> float:
        """Calculate deterministic Base Impact Score for a project.

        Formula:
            Base Score =
                need_weight * need_score
              + marginal_impact_weight * expected_impact_score
              + cost_efficiency_weight * cost_efficiency_score
              + evidence_weight * evidence_strength_score
              + scalability_weight * scalability_score
              - risk_penalty_weight * implementation_risk_score

        Args:
            project: Candidate project with ImpactDNA.
            weights: Priority weights or explicit ImpactDNA (for interface flexibility).
            dna: Optional explicit ImpactDNA.

        Returns:
            Deterministic Base Impact Score clipped to [0.0, 1.0] and rounded.

        Raises:
            InvalidProjectDataError: On missing or invalid DNA inputs.
            WeightValidationError: On invalid or non-numeric weights.
        """
        # Handle flexible signature (project, dna, weights)
        actual_weights: OptimizationWeights | dict[str, float] | None
        if isinstance(weights, ImpactDNA):
            resolved_dna = weights
            actual_weights = None
        else:
            resolved_dna = self._resolve_dna(project, dna)
            actual_weights = weights

        self.validate_inputs(project, actual_weights, resolved_dna)
        norm_weights = self._extract_and_normalize_weights(actual_weights)

        # Compute weighted contributions
        raw_score = (
            norm_weights["need"] * resolved_dna.need_score
            + norm_weights["marginal_impact"] * resolved_dna.expected_impact_score
            + norm_weights["cost_efficiency"] * resolved_dna.cost_efficiency_score
            + norm_weights["evidence"] * resolved_dna.evidence_strength_score
            + norm_weights["scalability"] * resolved_dna.scalability_score
            - norm_weights["risk_penalty"] * resolved_dna.implementation_risk_score
        )

        # Clip strictly to [0.0, 1.0] and round to deterministic precision
        clipped = clip_score(raw_score, min_val=SCORE_MIN, max_val=SCORE_MAX)
        return round(clipped, self.precision)

    # -----------------------------------------------------------------------
    # Task C: Public Method - calculate_component_scores
    # -----------------------------------------------------------------------

    def calculate_component_scores(
        self,
        project: Project,
        weights: OptimizationWeights | dict[str, float] | None = None,
        dna: ImpactDNA | None = None,
    ) -> dict[str, Any]:
        """Compute the detailed contribution breakdown of each score component.

        Used for explainability, auditability, and visualization.

        Args:
            project: Candidate project with ImpactDNA.
            weights: Optional priority weights (uses canonical defaults if None).
            dna: Optional explicit ImpactDNA.

        Returns:
            Dictionary containing:
                - need_component
                - impact_component
                - efficiency_component
                - evidence_component
                - scalability_component
                - risk_penalty_component
                - base_score
                - calculation_version
                - input_schema
                - engine_version
        """
        resolved_dna = self._resolve_dna(project, dna)
        self.validate_inputs(project, weights, resolved_dna)
        norm_weights = self._extract_and_normalize_weights(weights)

        need_comp = round(norm_weights["need"] * resolved_dna.need_score, self.precision)
        impact_comp = round(norm_weights["marginal_impact"] * resolved_dna.expected_impact_score, self.precision)
        eff_comp = round(norm_weights["cost_efficiency"] * resolved_dna.cost_efficiency_score, self.precision)
        evid_comp = round(norm_weights["evidence"] * resolved_dna.evidence_strength_score, self.precision)
        scale_comp = round(norm_weights["scalability"] * resolved_dna.scalability_score, self.precision)
        risk_comp = round(norm_weights["risk_penalty"] * resolved_dna.implementation_risk_score, self.precision)

        raw_score = (
            norm_weights["need"] * resolved_dna.need_score
            + norm_weights["marginal_impact"] * resolved_dna.expected_impact_score
            + norm_weights["cost_efficiency"] * resolved_dna.cost_efficiency_score
            + norm_weights["evidence"] * resolved_dna.evidence_strength_score
            + norm_weights["scalability"] * resolved_dna.scalability_score
            - norm_weights["risk_penalty"] * resolved_dna.implementation_risk_score
        )

        base_score = round(clip_score(raw_score, min_val=SCORE_MIN, max_val=SCORE_MAX), self.precision)

        weighted_inputs = {
            "need": norm_weights["need"],
            "marginal_impact": norm_weights["marginal_impact"],
            "cost_efficiency": norm_weights["cost_efficiency"],
            "evidence": norm_weights["evidence"],
            "scalability": norm_weights["scalability"],
            "risk_penalty": norm_weights["risk_penalty"],
        }

        return {
            "need_component": need_comp,
            "impact_component": impact_comp,
            "efficiency_component": eff_comp,
            "evidence_component": evid_comp,
            "scalability_component": scale_comp,
            "risk_penalty_component": risk_comp,
            "base_score": base_score,
            "weighted_inputs": weighted_inputs,
            "calculation_version": self.calculation_version,
            "input_schema": self.input_schema,
            "engine_version": self.engine_version,
            "metadata": {
                "calculation_version": self.calculation_version,
                "input_schema": self.input_schema,
                "engine_version": self.engine_version,
                "weighted_inputs": weighted_inputs,
            },
        }
