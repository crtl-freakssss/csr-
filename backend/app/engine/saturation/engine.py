"""CSR Saturation Index Engine for AllocateAI Decision Engine (Member C Phase 3).

Measures regional and sector CSR saturation deterministically.
Authoritative source: Software Contract v1.0 & Technical Contract v1.0.
Strictly deterministic: zero LLM calls, zero randomness, zero external APIs, zero database calls.
"""

from typing import Final

from backend.app.engine.constants import (
    PROJECT_SCHEMA_VERSION,
    SATURATION_CALCULATION_VERSION,
    SATURATION_HIGH_MAX,
    SATURATION_LOW_MAX,
    SATURATION_VERY_LOW_MAX,
    SCORE_MAX,
    SCORE_MIN,
)
from backend.app.engine.exceptions import (
    InvalidProjectDataError,
)
from backend.app.engine.schemas import (
    ImpactDNA,
    Project,
    SaturationContext,
    SaturationResult,
)
from backend.app.engine.utils import (
    clip_score,
    safe_division,
    validate_score,
)

# ---------------------------------------------------------------------------
# Saturation Constants & Coefficients (Task B & E)
# ---------------------------------------------------------------------------

CALCULATION_VERSION: Final[str] = SATURATION_CALCULATION_VERSION  # "saturation-v1"
MODEL_NAME: Final[str] = "csr-saturation-engine"
SCHEMA_VERSION: Final[str] = PROJECT_SCHEMA_VERSION              # "project-v1"

DEFAULT_SATURATION_PRECISION: Final[int] = 6

# Canonical Benchmark: ₹1,000 per capita in target population = 100,000 paise
# Represents an adequately funded intervention density threshold
BENCHMARK_PER_CAPITA_CSR_PAISE: Final[int] = 100_000

# Canonical component weights summing strictly to 1.0
WEIGHT_FUNDING_DENSITY: Final[float] = 0.40
WEIGHT_BENEFICIARY_COVERAGE: Final[float] = 0.30
WEIGHT_NEED_ADJUSTMENT: Final[float] = 0.30

# Presentation Interpretation Boundaries (Task D & Technical Contract Section 11)
INTERPRETATION_VERY_LOW_MAX: Final[float] = SATURATION_VERY_LOW_MAX   # 0.24
INTERPRETATION_LOW_MAX: Final[float] = 0.37
INTERPRETATION_MODERATE_MAX: Final[float] = SATURATION_LOW_MAX         # 0.49
INTERPRETATION_HIGH_MAX: Final[float] = SATURATION_HIGH_MAX           # 0.74


class SaturationEngine:
    """Deterministic CSR Saturation Index Engine."""

    calculation_version: Final[str] = CALCULATION_VERSION
    model_name: Final[str] = MODEL_NAME
    schema_version: Final[str] = SCHEMA_VERSION

    def __init__(
        self,
        precision: int = DEFAULT_SATURATION_PRECISION,
        benchmark_per_capita_paise: int = BENCHMARK_PER_CAPITA_CSR_PAISE,
    ) -> None:
        """Initialize the Saturation Engine.

        Args:
            precision: Rounding decimal places (default: 6).
            benchmark_per_capita_paise: Baseline per-capita paise benchmark for density.
        """
        self.precision = precision
        self.benchmark_per_capita_paise = benchmark_per_capita_paise

    # -----------------------------------------------------------------------
    # Validation Helpers
    # -----------------------------------------------------------------------

    def validate_context(self, context: SaturationContext) -> None:
        """Validate regional demographic and CSR context payload.

        Args:
            context: Contextual demographic and funding metadata.

        Raises:
            InvalidProjectDataError: If context contains invalid or negative attributes.
        """
        if not isinstance(context, SaturationContext):
            raise InvalidProjectDataError(
                f"context must be a SaturationContext instance, got {type(context).__name__}"
            )

        if not context.state or not context.state.strip():
            raise InvalidProjectDataError("context.state cannot be empty", field_name="state")

        if context.total_regional_csr_paise < 0:
            raise InvalidProjectDataError(
                f"total_regional_csr_paise must be non-negative, got {context.total_regional_csr_paise}",
                field_name="total_regional_csr_paise",
            )

        if context.total_population < 0:
            raise InvalidProjectDataError(
                f"total_population must be non-negative, got {context.total_population}",
                field_name="total_population",
            )

        if context.target_population < 0:
            raise InvalidProjectDataError(
                f"target_population must be non-negative, got {context.target_population}",
                field_name="target_population",
            )

    def _resolve_need_score(self, project: Project) -> float:
        """Extract and validate need_score from project's ImpactDNA."""
        if not isinstance(project, Project):
            raise InvalidProjectDataError(
                f"project must be an instance of Project, got {type(project).__name__}"
            )

        dna = getattr(project, "impact_dna", None)
        if dna is None or not isinstance(dna, ImpactDNA):
            raise InvalidProjectDataError(
                f"Project '{project.project_id}' is missing required ImpactDNA fingerprint",
                project_id=project.project_id,
                field_name="impact_dna",
            )

        validate_score(dna.need_score, name="need_score")
        return float(dna.need_score)

    # -----------------------------------------------------------------------
    # Task B: Public Component Methods
    # -----------------------------------------------------------------------

    def calculate_need_adjustment(self, project: Project) -> float:
        """Calculate need adjustment score.

        Formula:
            need_adjustment = 1.0 - need_score

        Higher need results in lower saturation pressure (encourages funding).
        Lower need results in higher saturation pressure.

        Args:
            project: Project with validated ImpactDNA.

        Returns:
            Normalized need adjustment in range [0.0, 1.0].
        """
        need_score = self._resolve_need_score(project)
        adjustment = 1.0 - need_score
        return round(clip_score(adjustment, SCORE_MIN, SCORE_MAX), self.precision)

    def calculate_beneficiary_coverage(
        self,
        project: Project,
        context: SaturationContext,
    ) -> float:
        """Calculate estimated beneficiary coverage ratio.

        Formula:
            coverage = beneficiaries_reached / target_population

        Uses project target count (or DNA reach) against the regional target population.

        Args:
            project: Candidate project.
            context: Regional demographic context.

        Returns:
            Clipped beneficiary coverage in range [0.0, 1.0].
        """
        self.validate_context(context)

        # Beneficiaries reached from project profile or DNA
        beneficiaries_reached = 0
        if project.beneficiary_profile and project.beneficiary_profile.target_count > 0:
            beneficiaries_reached = project.beneficiary_profile.target_count
        elif project.impact_dna and project.impact_dna.beneficiary_reach > 0:
            beneficiaries_reached = project.impact_dna.beneficiary_reach

        # Denominator: prefer target_population, fall back to total_population
        effective_population = context.target_population
        if effective_population <= 0:
            effective_population = context.total_population

        if effective_population <= 0:
            return 0.0

        raw_coverage = safe_division(float(beneficiaries_reached), float(effective_population), default=0.0)
        return round(clip_score(raw_coverage, SCORE_MIN, SCORE_MAX), self.precision)

    def calculate_funding_density(
        self,
        context: SaturationContext,
    ) -> float:
        """Calculate normalized regional funding density score.

        Formula:
            density = existing_csr_amount / (target_population * benchmark_per_capita)

        Args:
            context: Regional demographic and funding context.

        Returns:
            Clipped funding density score in range [0.0, 1.0].
        """
        self.validate_context(context)

        effective_population = context.target_population
        if effective_population <= 0:
            effective_population = context.total_population

        if effective_population <= 0 or context.total_regional_csr_paise <= 0:
            return 0.0

        # Total expected funding threshold for this demographic
        benchmark_capacity_paise = float(effective_population) * float(self.benchmark_per_capita_paise)
        raw_density = safe_division(
            float(context.total_regional_csr_paise),
            benchmark_capacity_paise,
            default=0.0,
        )
        return round(clip_score(raw_density, SCORE_MIN, SCORE_MAX), self.precision)

    # -----------------------------------------------------------------------
    # Task C: Confidence Calculation
    # -----------------------------------------------------------------------

    def calculate_confidence(
        self,
        project: Project,
        context: SaturationContext,
    ) -> float:
        """Deterministically calculate confidence score based on input completeness.

        Factors:
            1. Population completeness (0.25)
            2. Funding completeness (0.25)
            3. Beneficiary completeness (0.25)
            4. Need score availability (0.25)

        Args:
            project: Candidate project.
            context: Regional context.

        Returns:
            Confidence scalar in range [0.0, 1.0].
        """
        # 1. Population completeness
        if context.target_population > 0 and context.total_population > 0:
            pop_factor = 1.0
        elif context.target_population > 0 or context.total_population > 0:
            pop_factor = 0.5
        else:
            pop_factor = 0.0

        # 2. Funding completeness
        if context.total_regional_csr_paise > 0:
            funding_factor = 1.0
        elif context.total_regional_csr_paise == 0:
            funding_factor = 0.5
        else:
            funding_factor = 0.0

        # 3. Beneficiary completeness
        if project.beneficiary_profile and project.beneficiary_profile.target_count > 0:
            ben_factor = 1.0
        elif project.impact_dna and project.impact_dna.beneficiary_reach > 0:
            ben_factor = 0.8
        else:
            ben_factor = 0.0

        # 4. Need score availability
        if project.impact_dna and isinstance(project.impact_dna.need_score, (int, float)):
            need_factor = 1.0
        else:
            need_factor = 0.0

        confidence = (
            0.25 * pop_factor
            + 0.25 * funding_factor
            + 0.25 * ben_factor
            + 0.25 * need_factor
        )
        return round(clip_score(confidence, SCORE_MIN, SCORE_MAX), 4)

    # -----------------------------------------------------------------------
    # Task D: Saturation Interpretation Helper
    # -----------------------------------------------------------------------

    @staticmethod
    def interpret_saturation(saturation_index: float) -> str:
        """Translate numeric saturation index to canonical presentation label.

        Thresholds match Technical Contract Section 11:
            0.00 - 0.24 -> VERY_LOW
            0.25 - 0.37 -> LOW
            0.38 - 0.49 -> MODERATE
            0.50 - 0.74 -> HIGH
            0.75 - 1.00 -> VERY_HIGH

        Args:
            saturation_index: Scalar index in range [0.0, 1.0].

        Returns:
            Presentation string tag.
        """
        idx = clip_score(saturation_index, SCORE_MIN, SCORE_MAX)

        if idx <= INTERPRETATION_VERY_LOW_MAX:
            return "VERY_LOW"
        if idx <= INTERPRETATION_LOW_MAX:
            return "LOW"
        if idx <= INTERPRETATION_MODERATE_MAX:
            return "MODERATE"
        if idx <= INTERPRETATION_HIGH_MAX:
            return "HIGH"
        return "VERY_HIGH"

    # -----------------------------------------------------------------------
    # Task A: Primary Calculation Method
    # -----------------------------------------------------------------------

    def calculate_saturation(
        self,
        project: Project,
        context: SaturationContext,
    ) -> SaturationResult:
        """Calculate complete deterministic CSR saturation assessment.

        Combines:
            - Funding Density (weight: 0.40)
            - Beneficiary Coverage (weight: 0.30)
            - Need Adjustment (weight: 0.30)

        Args:
            project: Candidate project entity with ImpactDNA.
            context: Regional demographic and funding metadata.

        Returns:
            Validated SaturationResult conforming to Technical Contract v1.0.
        """
        self.validate_context(context)
        need_score = self._resolve_need_score(project)

        funding_density = self.calculate_funding_density(context)
        beneficiary_coverage = self.calculate_beneficiary_coverage(project, context)
        need_adjustment = self.calculate_need_adjustment(project)

        # Weighted combination
        raw_index = (
            WEIGHT_FUNDING_DENSITY * funding_density
            + WEIGHT_BENEFICIARY_COVERAGE * beneficiary_coverage
            + WEIGHT_NEED_ADJUSTMENT * need_adjustment
        )

        saturation_index = round(
            clip_score(raw_index, SCORE_MIN, SCORE_MAX),
            self.precision,
        )

        confidence = self.calculate_confidence(project, context)

        component_breakdown = {
            "funding_density_score": funding_density,
            "beneficiary_coverage_score": beneficiary_coverage,
            "need_adjustment_score": need_adjustment,
            "weights": {
                "funding_density": WEIGHT_FUNDING_DENSITY,
                "beneficiary_coverage": WEIGHT_BENEFICIARY_COVERAGE,
                "need_adjustment": WEIGHT_NEED_ADJUSTMENT,
            },
        }

        return SaturationResult(
            project_id=project.project_id,
            state=context.state,
            sector=context.sector,
            saturation_index=saturation_index,
            need_score=round(need_score, self.precision),
            existing_csr_amount_paise=context.total_regional_csr_paise,
            estimated_beneficiary_coverage=beneficiary_coverage,
            confidence=confidence,
            calculation_version=self.calculation_version,
            component_breakdown=component_breakdown,
        )

    def calculate(
        self,
        project: Project,
        context: SaturationContext,
    ) -> SaturationResult:
        """Contract alias delegating to calculate_saturation.

        Maintains exact interface compatibility with Technical Contract Section 59.
        """
        return self.calculate_saturation(project, context)
