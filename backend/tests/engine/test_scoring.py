"""Comprehensive unit test suite for AllocateAI Base Impact Scoring Engine (Member C Phase 2).

Verifies strict adherence to Software Contract v1.0, Technical Contract v1.0,
deterministic scoring formulas, component breakdowns, weight normalization,
error handling, and repeatability.
"""

import json
from pathlib import Path
import pytest

from backend.app.engine.constants import (
    DNA_SCHEMA_VERSION,
    OPTIMIZER_CALCULATION_VERSION,
    ProjectSector,
)
from backend.app.engine.exceptions import (
    InvalidProjectDataError,
    WeightValidationError,
)
from backend.app.engine.schemas import (
    BeneficiaryProfile,
    Financials,
    Geography,
    ImpactDNA,
    OptimizationWeights,
    Project,
)
from backend.app.engine.scoring import (
    DEFAULT_SCORING_WEIGHTS,
    ENGINE_VERSION,
    ScoringEngine,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def scoring_engine() -> ScoringEngine:
    """Fixture providing a fresh ScoringEngine instance."""
    return ScoringEngine()


def make_test_project(
    project_id: str = "PRJ-TEST",
    need_score: float = 0.80,
    expected_impact_score: float = 0.85,
    cost_efficiency_score: float = 0.75,
    evidence_strength_score: float = 0.90,
    scalability_score: float = 0.70,
    implementation_risk_score: float = 0.15,
    with_dna: bool = True,
) -> Project:
    """Helper to build a valid Project instance with configurable ImpactDNA."""
    dna = None
    if with_dna:
        dna = ImpactDNA(
            dna_id=f"DNA-{project_id}",
            project_id=project_id,
            need_score=need_score,
            expected_impact_score=expected_impact_score,
            cost_efficiency_score=cost_efficiency_score,
            evidence_strength_score=evidence_strength_score,
            scalability_score=scalability_score,
            implementation_risk_score=implementation_risk_score,
            beneficiary_reach=5000,
            estimated_impact_per_lakh=40.0,
            extraction_confidence=0.90,
            model_name="dna-v1",
            prompt_version="v1.0",
        )

    return Project(
        project_id=project_id,
        name=f"Test Project {project_id}",
        ngo_id="NGO-TEST",
        sector=ProjectSector.EDUCATION,
        geographies=[Geography(state="Bihar", district="Gaya", block="Mohanpur")],
        beneficiary_profile=BeneficiaryProfile(target_count=5000),
        financials=Financials(requested_amount_paise=25_000_000),
        duration_months=12,
        impact_dna=dna,
    )


# ---------------------------------------------------------------------------
# Test Cases (Minimum 20 Required)
# ---------------------------------------------------------------------------

def test_1_valid_scoring_with_default_weights(scoring_engine: ScoringEngine):
    """Verify standard valid project scoring with default canonical weights."""
    project = make_test_project()
    score = scoring_engine.calculate_base_score(project)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert score > 0.60


def test_2_valid_scoring_with_custom_weights(scoring_engine: ScoringEngine):
    """Verify scoring with user-defined valid custom weights."""
    project = make_test_project(need_score=0.90, expected_impact_score=0.90)
    weights = {
        "need": 0.40,
        "marginal_impact": 0.30,
        "cost_efficiency": 0.10,
        "evidence": 0.10,
        "scalability": 0.05,
        "risk_penalty": 0.05,
    }
    score = scoring_engine.calculate_base_score(project, weights=weights)
    assert 0.0 <= score <= 1.0


def test_3_scoring_with_optimization_weights_model(scoring_engine: ScoringEngine):
    """Verify ScoringEngine supports OptimizationWeights Pydantic model directly."""
    project = make_test_project()
    opt_weights = OptimizationWeights(
        need=0.25, marginal_impact=0.25, cost_efficiency=0.15,
        evidence=0.15, scalability=0.10, equity=0.05, risk_penalty=0.05
    )
    score = scoring_engine.calculate_base_score(project, weights=opt_weights)
    assert 0.0 <= score <= 1.0


def test_4_all_zero_project(scoring_engine: ScoringEngine):
    """All DNA scores at 0.0 with 0 risk must produce a base score of 0.0."""
    project = make_test_project(
        need_score=0.0, expected_impact_score=0.0, cost_efficiency_score=0.0,
        evidence_strength_score=0.0, scalability_score=0.0, implementation_risk_score=0.0
    )
    score = scoring_engine.calculate_base_score(project)
    assert score == 0.0


def test_5_all_one_project_zero_risk(scoring_engine: ScoringEngine):
    """All positive DNA scores at 1.0 and 0.0 risk must produce a base score of 0.90 with default weights (w_risk=0.10)."""
    project = make_test_project(
        need_score=1.0, expected_impact_score=1.0, cost_efficiency_score=1.0,
        evidence_strength_score=1.0, scalability_score=1.0, implementation_risk_score=0.0
    )
    # Default weights: need=0.20, marginal=0.25, eff=0.20, evid=0.15, scale=0.10 -> sum of positive weights = 0.90
    score = scoring_engine.calculate_base_score(project)
    assert score == pytest.approx(0.90, abs=1e-5)


def test_6_all_one_project_with_zero_risk_weight(scoring_engine: ScoringEngine):
    """When positive weights sum to 1.0 and risk is 0, score must be exactly 1.0."""
    project = make_test_project(
        need_score=1.0, expected_impact_score=1.0, cost_efficiency_score=1.0,
        evidence_strength_score=1.0, scalability_score=1.0, implementation_risk_score=0.0
    )
    weights = {
        "need": 0.25,
        "marginal_impact": 0.25,
        "cost_efficiency": 0.25,
        "evidence": 0.15,
        "scalability": 0.10,
        "risk_penalty": 0.0,
    }
    score = scoring_engine.calculate_base_score(project, weights=weights)
    assert score == 1.0


def test_7_high_risk_penalty(scoring_engine: ScoringEngine):
    """High implementation risk must substantially reduce base score."""
    low_risk_prj = make_test_project(implementation_risk_score=0.05)
    high_risk_prj = make_test_project(implementation_risk_score=0.95)

    low_risk_score = scoring_engine.calculate_base_score(low_risk_prj)
    high_risk_score = scoring_engine.calculate_base_score(high_risk_prj)

    assert low_risk_score > high_risk_score
    # Difference should match w_risk * delta_risk = 0.10 * 0.90 = 0.09
    assert (low_risk_score - high_risk_score) == pytest.approx(0.09, abs=1e-4)


def test_8_extreme_risk_penalty_clips_to_zero(scoring_engine: ScoringEngine):
    """When risk penalty exceeds positive components, score must clip to 0.0."""
    project = make_test_project(
        need_score=0.10, expected_impact_score=0.10, cost_efficiency_score=0.10,
        evidence_strength_score=0.10, scalability_score=0.10, implementation_risk_score=1.0
    )
    heavy_risk_weights = {
        "need": 0.10,
        "marginal_impact": 0.10,
        "cost_efficiency": 0.10,
        "evidence": 0.05,
        "scalability": 0.05,
        "risk_penalty": 0.60,
    }
    score = scoring_engine.calculate_base_score(project, weights=heavy_risk_weights)
    assert score == 0.0


def test_9_weight_normalization(scoring_engine: ScoringEngine):
    """Unnormalized weights (e.g. 2.0x scale) must normalize deterministically to same score."""
    project = make_test_project()
    raw_weights_1 = {
        "need": 0.20, "marginal_impact": 0.25, "cost_efficiency": 0.20,
        "evidence": 0.15, "scalability": 0.10, "risk_penalty": 0.10
    }
    raw_weights_2 = {
        "need": 2.0, "marginal_impact": 2.5, "cost_efficiency": 2.0,
        "evidence": 1.5, "scalability": 1.0, "risk_penalty": 1.0
    }

    score_1 = scoring_engine.calculate_base_score(project, weights=raw_weights_1)
    score_2 = scoring_engine.calculate_base_score(project, weights=raw_weights_2)

    assert score_1 == score_2


def test_10_negative_weights_raise_weight_validation_error(scoring_engine: ScoringEngine):
    """Negative weights must raise WeightValidationError."""
    project = make_test_project()
    invalid_weights = dict(DEFAULT_SCORING_WEIGHTS)
    invalid_weights["need"] = -0.5

    with pytest.raises(WeightValidationError):
        scoring_engine.calculate_base_score(project, weights=invalid_weights)


def test_11_non_numeric_weights_raise_weight_validation_error(scoring_engine: ScoringEngine):
    """Non-numeric weights must raise WeightValidationError."""
    project = make_test_project()
    invalid_weights = dict(DEFAULT_SCORING_WEIGHTS)
    invalid_weights["need"] = "high"  # type: ignore

    with pytest.raises(WeightValidationError):
        scoring_engine.calculate_base_score(project, weights=invalid_weights)


def test_12_empty_weights_raise_weight_validation_error(scoring_engine: ScoringEngine):
    """Empty weights dictionary must raise WeightValidationError."""
    project = make_test_project()
    with pytest.raises(WeightValidationError):
        scoring_engine.calculate_base_score(project, weights={})


def test_13_missing_dna_raises_invalid_project_data_error(scoring_engine: ScoringEngine):
    """Project without ImpactDNA must raise InvalidProjectDataError."""
    project = make_test_project(with_dna=False)
    with pytest.raises(InvalidProjectDataError) as excinfo:
        scoring_engine.calculate_base_score(project)
    assert excinfo.value.field_name == "impact_dna"


def test_14_out_of_bounds_dna_score_raises_invalid_project_data_error(scoring_engine: ScoringEngine):
    """DNA score > 1.0 must raise InvalidProjectDataError during validation."""
    project = make_test_project()
    project.impact_dna.need_score = 1.45  # type: ignore

    with pytest.raises(InvalidProjectDataError):
        scoring_engine.calculate_base_score(project)


def test_15_negative_dna_score_raises_invalid_project_data_error(scoring_engine: ScoringEngine):
    """Negative DNA score must raise InvalidProjectDataError."""
    project = make_test_project()
    project.impact_dna.implementation_risk_score = -0.2  # type: ignore

    with pytest.raises(InvalidProjectDataError):
        scoring_engine.calculate_base_score(project)


def test_16_nan_in_dna_score_raises_invalid_project_data_error(scoring_engine: ScoringEngine):
    """NaN in DNA score must raise InvalidProjectDataError."""
    project = make_test_project()
    project.impact_dna.expected_impact_score = float("nan")

    with pytest.raises(InvalidProjectDataError):
        scoring_engine.calculate_base_score(project)


def test_17_deterministic_repeatability(scoring_engine: ScoringEngine):
    """Executing calculate_base_score 100 times on identical input must yield bitwise identical output."""
    project = make_test_project()
    first_score = scoring_engine.calculate_base_score(project)

    for _ in range(100):
        score = scoring_engine.calculate_base_score(project)
        assert score == first_score


def test_18_precision_rounding():
    """ScoringEngine respects configured precision parameter."""
    engine_4 = ScoringEngine(precision=4)
    engine_2 = ScoringEngine(precision=2)

    project = make_test_project()
    score_4 = engine_4.calculate_base_score(project)
    score_2 = engine_2.calculate_base_score(project)

    assert len(str(score_4).split(".")[1]) <= 4
    assert len(str(score_2).split(".")[1]) <= 2


def test_19_component_scores_breakdown(scoring_engine: ScoringEngine):
    """calculate_component_scores must return all required breakdown fields."""
    project = make_test_project()
    components = scoring_engine.calculate_component_scores(project)

    expected_keys = {
        "need_component",
        "impact_component",
        "efficiency_component",
        "evidence_component",
        "scalability_component",
        "risk_penalty_component",
        "base_score",
        "weighted_inputs",
        "calculation_version",
        "input_schema",
        "engine_version",
        "metadata",
    }
    assert expected_keys.issubset(components.keys())

    # Component values must be non-negative numbers
    for k in [
        "need_component", "impact_component", "efficiency_component",
        "evidence_component", "scalability_component", "risk_penalty_component"
    ]:
        assert isinstance(components[k], float)
        assert components[k] >= 0.0

    # Base score matches calculate_base_score
    base_score = scoring_engine.calculate_base_score(project)
    assert components["base_score"] == base_score


def test_24_weighted_inputs_specification(scoring_engine: ScoringEngine):
    """Verify weighted_inputs contains normalized weights summing to 1.0 and does not mutate input."""
    project = make_test_project()
    raw_input_weights = {
        "need": 2.0,
        "marginal_impact": 3.0,
        "cost_efficiency": 2.0,
        "evidence": 1.0,
        "scalability": 1.0,
        "risk_penalty": 1.0,
    }
    raw_copy = dict(raw_input_weights)

    comp = scoring_engine.calculate_component_scores(project, weights=raw_input_weights)
    weighted_inputs = comp["weighted_inputs"]

    # Verify all 6 keys present
    required_keys = {"need", "marginal_impact", "cost_efficiency", "evidence", "scalability", "risk_penalty"}
    assert set(weighted_inputs.keys()) == required_keys

    # Verify all values are float and sum to exactly 1.0
    for k, v in weighted_inputs.items():
        assert isinstance(v, float)
        assert 0.0 <= v <= 1.0

    assert sum(weighted_inputs.values()) == pytest.approx(1.0, abs=1e-6)

    # Verify input dictionary was not mutated
    assert raw_input_weights == raw_copy


def test_20_component_reconciliation_with_base_score(scoring_engine: ScoringEngine):
    """Sum of positive components minus risk component must equal base_score (within precision)."""
    project = make_test_project()
    comp = scoring_engine.calculate_component_scores(project)

    positive_sum = (
        comp["need_component"]
        + comp["impact_component"]
        + comp["efficiency_component"]
        + comp["evidence_component"]
        + comp["scalability_component"]
    )
    net_score = positive_sum - comp["risk_penalty_component"]
    assert comp["base_score"] == pytest.approx(net_score, abs=1e-5)


def test_21_version_metadata(scoring_engine: ScoringEngine):
    """Verify version metadata matches contracts and contains zero timestamps."""
    project = make_test_project()
    comp = scoring_engine.calculate_component_scores(project)

    assert comp["calculation_version"] == OPTIMIZER_CALCULATION_VERSION == "optimizer-v1"
    assert comp["input_schema"] == DNA_SCHEMA_VERSION == "dna-v1"
    assert comp["engine_version"] == "scoring-v1"
    assert "timestamp" not in comp
    assert "created_at" not in comp


def test_22_validate_inputs_method(scoring_engine: ScoringEngine):
    """validate_inputs must succeed on valid data and raise on invalid."""
    valid_project = make_test_project()
    scoring_engine.validate_inputs(valid_project)

    invalid_weights = {"need": -1.0}
    with pytest.raises(WeightValidationError):
        scoring_engine.validate_inputs(valid_project, weights=invalid_weights)


def test_23_seed_projects_scoring_integration(scoring_engine: ScoringEngine):
    """All 18 projects in the Phase 1 seed dataset must score successfully."""
    seed_file = WORKSPACE_ROOT / "data" / "sample" / "member_c_seed_projects.json"
    with open(seed_file, "r", encoding="utf-8") as f:
        seed_projects = json.load(f)

    assert len(seed_projects) == 18

    scores = []
    for p_dict in seed_projects:
        project = Project.model_validate(p_dict)
        score = scoring_engine.calculate_base_score(project)
        assert 0.0 <= score <= 1.0
        scores.append(score)

    # Verify score variance across the realistic portfolio
    assert max(scores) > min(scores)
    assert min(scores) > 0.40
    assert max(scores) < 0.95
