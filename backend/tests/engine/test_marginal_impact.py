"""Comprehensive unit test suite for AllocateAI Marginal Impact Engine (Member C Phase 4).

Verifies Software Contract v1.0, Technical Contract v1.0, deterministic marginal formulas,
diminishing-return elasticity, simulation tiers, boundary conditions, error handling,
repeatability, and seed dataset integration.
"""

import json
from pathlib import Path
import pytest

from backend.app.engine.constants import (
    DEFAULT_MARGINAL_INCREMENT_PAISE,
    DNA_SCHEMA_VERSION,
    MARGINAL_CALCULATION_VERSION,
    PAISE_PER_LAKH,
    ProjectSector,
)
from backend.app.engine.exceptions import (
    BudgetValidationError,
    InvalidProjectDataError,
)
from backend.app.engine.marginal_impact import (
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
from backend.app.engine.schemas import (
    BeneficiaryProfile,
    Financials,
    Geography,
    ImpactDNA,
    MarginalImpactResult,
    Project,
    SaturationContext,
    SaturationResult,
)
from backend.app.engine.saturation import SaturationEngine

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def marginal_engine() -> MarginalImpactEngine:
    """Fixture providing a fresh MarginalImpactEngine instance."""
    return MarginalImpactEngine()


def make_test_project(
    project_id: str = "PRJ-MARG-TEST",
    requested_amount_paise: int = 50_000_000,  # ₹5 Lakh
    current_funding_paise: int = 10_000_000,   # ₹1 Lakh
    impact_per_lakh: float = 40.0,
    cost_efficiency_score: float = 0.80,
    need_score: float = 0.85,
    with_dna: bool = True,
) -> Project:
    """Helper to build a valid Project entity with configurable financials and ImpactDNA."""
    dna = None
    if with_dna:
        dna = ImpactDNA(
            dna_id=f"DNA-{project_id}",
            project_id=project_id,
            need_score=need_score,
            expected_impact_score=0.85,
            cost_efficiency_score=cost_efficiency_score,
            evidence_strength_score=0.90,
            scalability_score=0.75,
            implementation_risk_score=0.15,
            beneficiary_reach=5000,
            estimated_impact_per_lakh=impact_per_lakh,
            extraction_confidence=0.90,
            model_name="dna-v1",
            prompt_version="v1.0",
        )

    return Project(
        project_id=project_id,
        name=f"Test Project {project_id}",
        ngo_id="NGO-MARG-TEST",
        sector=ProjectSector.EDUCATION,
        geographies=[Geography(state="Bihar", district="Gaya", block="Mohanpur")],
        beneficiary_profile=BeneficiaryProfile(target_count=5000),
        financials=Financials(
            requested_amount_paise=requested_amount_paise,
            current_funding_paise=current_funding_paise,
        ),
        duration_months=12,
        impact_dna=dna,
    )


def make_test_saturation_result(
    saturation_index: float = 0.20,
    need_score: float = 0.85,
) -> SaturationResult:
    """Helper to construct a mock SaturationResult."""
    return SaturationResult(
        project_id="PRJ-MARG-TEST",
        state="Bihar",
        sector=ProjectSector.EDUCATION,
        saturation_index=saturation_index,
        need_score=need_score,
        existing_csr_amount_paise=10_000_000_000,
        estimated_beneficiary_coverage=0.10,
        confidence=0.95,
        calculation_version="saturation-v1",
    )


# ---------------------------------------------------------------------------
# Test Cases (Minimum 30 Required)
# ---------------------------------------------------------------------------

def test_1_baseline_increment_default(marginal_engine: MarginalImpactEngine):
    """Verify calculate_marginal_impact defaults to ₹1 Lakh increment."""
    project = make_test_project()
    result = marginal_engine.calculate_marginal_impact(project)

    assert isinstance(result, MarginalImpactResult)
    assert result.increment_paise == DEFAULT_MARGINAL_INCREMENT_PAISE
    assert result.baseline_budget_paise == 10_000_000
    assert result.projected_budget_paise == 20_000_000
    assert 0.0 <= result.marginal_impact_score <= 1.0


def test_2_calculate_alias_matches_calculate_marginal_impact(marginal_engine: MarginalImpactEngine):
    """Verify calculate() alias returns identical results to calculate_marginal_impact()."""
    project = make_test_project()
    sat_res = make_test_saturation_result()

    res1 = marginal_engine.calculate_marginal_impact(project, sat_res, 20_000_000)
    res2 = marginal_engine.calculate(project, 20_000_000, sat_res)

    assert res1.model_dump() == res2.model_dump()


def test_3_increment_1_lakh(marginal_engine: MarginalImpactEngine):
    """Verify specific ₹1 Lakh increment (10,000,000 paise)."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project, increment_paise=10_000_000)
    assert res.increment_paise == 10_000_000
    assert res.incremental_impact > 0.0


def test_4_increment_2_lakh(marginal_engine: MarginalImpactEngine):
    """Verify specific ₹2 Lakh increment (20,000,000 paise)."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project, increment_paise=20_000_000)
    assert res.increment_paise == 20_000_000
    assert res.projected_budget_paise == project.financials.current_funding_paise + 20_000_000


def test_5_increment_5_lakh(marginal_engine: MarginalImpactEngine):
    """Verify specific ₹5 Lakh increment (50,000,000 paise)."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project, increment_paise=50_000_000)
    assert res.increment_paise == 50_000_000


def test_6_increment_10_lakh(marginal_engine: MarginalImpactEngine):
    """Verify specific ₹10 Lakh increment (100,000,000 paise)."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project, increment_paise=100_000_000)
    assert res.increment_paise == 100_000_000


def test_7_zero_increment_raises_budget_validation_error(marginal_engine: MarginalImpactEngine):
    """Zero increment must raise BudgetValidationError."""
    project = make_test_project()
    with pytest.raises(BudgetValidationError):
        marginal_engine.calculate_marginal_impact(project, increment_paise=0)


def test_8_negative_increment_raises_budget_validation_error(marginal_engine: MarginalImpactEngine):
    """Negative increment must raise BudgetValidationError."""
    project = make_test_project()
    with pytest.raises(BudgetValidationError):
        marginal_engine.calculate_marginal_impact(project, increment_paise=-10_000_000)


def test_9_float_increment_raises_budget_validation_error(marginal_engine: MarginalImpactEngine):
    """Float increment must raise BudgetValidationError (integer paise strictly enforced)."""
    project = make_test_project()
    with pytest.raises(BudgetValidationError):
        marginal_engine.calculate_marginal_impact(project, increment_paise=10000000.5)  # type: ignore


def test_10_high_saturation_penalty(marginal_engine: MarginalImpactEngine):
    """Higher saturation must yield a lower diminishing-return factor and lower marginal impact score."""
    project = make_test_project()
    low_sat = make_test_saturation_result(saturation_index=0.05)
    high_sat = make_test_saturation_result(saturation_index=0.95)

    res_low = marginal_engine.calculate_marginal_impact(project, low_sat)
    res_high = marginal_engine.calculate_marginal_impact(project, high_sat)

    assert res_low.diminishing_return_factor > res_high.diminishing_return_factor
    assert res_low.marginal_impact_score > res_high.marginal_impact_score


def test_11_low_saturation_bonus(marginal_engine: MarginalImpactEngine):
    """Underserved low-saturation intervention maintains high efficiency."""
    project = make_test_project()
    sat_zero = make_test_saturation_result(saturation_index=0.0)
    res = marginal_engine.calculate_marginal_impact(project, sat_zero)

    assert res.diminishing_return_factor > 0.70
    assert res.marginal_impact_score > 0.50


def test_12_high_need_bonus(marginal_engine: MarginalImpactEngine):
    """High-need projects retain higher marginal efficiency."""
    high_need_prj = make_test_project(need_score=0.95)
    low_need_prj = make_test_project(need_score=0.05)

    res_high = marginal_engine.calculate_marginal_impact(high_need_prj)
    res_low = marginal_engine.calculate_marginal_impact(low_need_prj)

    assert res_high.diminishing_return_factor > res_low.diminishing_return_factor
    assert res_high.marginal_impact_score > res_low.marginal_impact_score


def test_13_zero_funding_project_baseline(marginal_engine: MarginalImpactEngine):
    """Projects with 0 baseline funding have 0 baseline impact and maximum base decay."""
    project = make_test_project(current_funding_paise=0)
    res = marginal_engine.calculate_marginal_impact(project)

    assert res.baseline_budget_paise == 0
    assert res.baseline_impact == 0.0
    assert res.projected_impact == res.incremental_impact


def test_14_already_saturated_project(marginal_engine: MarginalImpactEngine):
    """Projects in saturated environment (saturation_index = 1.0) receive maximum saturation penalty."""
    project = make_test_project()
    sat_full = make_test_saturation_result(saturation_index=1.0)
    res = marginal_engine.calculate_marginal_impact(project, sat_full)

    assert res.component_breakdown["saturation_penalty"] == 1.0
    assert res.diminishing_return_factor < 0.70


def test_15_huge_funding_project_diminishing_returns(marginal_engine: MarginalImpactEngine):
    """Projects funded far beyond requested amount suffer massive diminishing returns."""
    normal_prj = make_test_project(requested_amount_paise=50_000_000, current_funding_paise=10_000_000)
    overfunded_prj = make_test_project(requested_amount_paise=50_000_000, current_funding_paise=500_000_000)

    res_norm = marginal_engine.calculate_marginal_impact(normal_prj)
    res_over = marginal_engine.calculate_marginal_impact(overfunded_prj)

    assert res_over.diminishing_return_factor < res_norm.diminishing_return_factor
    assert res_over.impact_per_lakh < res_norm.impact_per_lakh


def test_16_monotonic_decay_with_increasing_budget(marginal_engine: MarginalImpactEngine):
    """As cumulative projected budget increases, diminishing_return_factor must monotonically decrease."""
    project = make_test_project(requested_amount_paise=100_000_000, current_funding_paise=0)
    sat = make_test_saturation_result(saturation_index=0.20)

    factors = []
    increments = [10_000_000, 20_000_000, 50_000_000, 100_000_000, 200_000_000]
    for inc in increments:
        factor = marginal_engine.calculate_diminishing_return(project, sat, inc)
        factors.append(factor)

    for i in range(len(factors) - 1):
        assert factors[i] >= factors[i + 1], f"Failed monotonicity: {factors[i]} < {factors[i+1]}"


def test_17_monotonic_decrease_of_impact_per_lakh_across_simulation_tiers(marginal_engine: MarginalImpactEngine):
    """Impact per lakh must be non-increasing as increment tier increases."""
    project = make_test_project()
    sims = marginal_engine.simulate_increment(project)
    assert isinstance(sims, dict)

    rate_1L = sims["1L"].impact_per_lakh
    rate_2L = sims["2L"].impact_per_lakh
    rate_5L = sims["5L"].impact_per_lakh
    rate_10L = sims["10L"].impact_per_lakh

    assert rate_1L >= rate_2L >= rate_5L >= rate_10L


def test_18_missing_dna_raises_invalid_project_data_error(marginal_engine: MarginalImpactEngine):
    """Project without ImpactDNA must raise InvalidProjectDataError."""
    project = make_test_project(with_dna=False)
    with pytest.raises(InvalidProjectDataError) as excinfo:
        marginal_engine.calculate_marginal_impact(project)
    assert excinfo.value.field_name == "impact_dna"


def test_19_missing_saturation_result_defaults_gracefully(marginal_engine: MarginalImpactEngine):
    """calculate_marginal_impact operates gracefully with saturation_result=None."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project, saturation_result=None)
    assert isinstance(res, MarginalImpactResult)
    assert res.component_breakdown["saturation_penalty"] == 0.0


def test_20_deterministic_repeatability_100_runs(marginal_engine: MarginalImpactEngine):
    """100 consecutive executions must produce bitwise identical output."""
    project = make_test_project()
    sat = make_test_saturation_result()

    first_dump = marginal_engine.calculate_marginal_impact(project, sat).model_dump()
    for _ in range(100):
        current_dump = marginal_engine.calculate_marginal_impact(project, sat).model_dump()
        assert current_dump == first_dump


def test_21_component_reconciliation(marginal_engine: MarginalImpactEngine):
    """projected_impact must equal baseline_impact + incremental_impact within precision."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project)

    reconciled = res.baseline_impact + res.incremental_impact
    assert res.projected_impact == pytest.approx(reconciled, abs=1e-5)


def test_22_component_breakdown_metadata_fields(marginal_engine: MarginalImpactEngine):
    """component_breakdown must include all required fields."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project)

    cb = res.component_breakdown
    assert isinstance(cb, dict)
    expected_keys = {
        "baseline_impact",
        "projected_impact",
        "incremental_impact",
        "impact_per_lakh",
        "diminishing_return_factor",
        "saturation_penalty",
        "need_bonus",
    }
    assert expected_keys.issubset(cb.keys())


def test_23_weights_used_sum_to_unity(marginal_engine: MarginalImpactEngine):
    """weights_used must sum to exactly 1.0."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project)

    wu = res.weights_used
    assert isinstance(wu, dict)
    expected_keys = {"need_bonus_weight", "saturation_penalty_weight", "cost_efficiency_weight"}
    assert expected_keys.issubset(wu.keys())

    total_w = wu["need_bonus_weight"] + wu["saturation_penalty_weight"] + wu["cost_efficiency_weight"]
    assert total_w == pytest.approx(1.0, abs=1e-6)


def test_24_version_metadata(marginal_engine: MarginalImpactEngine):
    """Verify calculation_version, engine_version, input_schema, and zero timestamps."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project)

    assert res.calculation_version == MARGINAL_CALCULATION_VERSION == "marginal-v1"
    assert res.engine_version == "marginal-impact-engine"
    assert res.input_schema == "dna-v1"
    assert not hasattr(res, "timestamp")
    assert not hasattr(res, "created_at")


def test_25_dependency_versions(marginal_engine: MarginalImpactEngine):
    """Verify dependency_versions points to scoring-v1 and saturation-v1."""
    project = make_test_project()
    res = marginal_engine.calculate_marginal_impact(project)

    assert res.dependency_versions["scoring"] == "scoring-v1"
    assert res.dependency_versions["saturation"] == "saturation-v1"


def test_26_output_clipping_bounds(marginal_engine: MarginalImpactEngine):
    """marginal_impact_score and diminishing_return_factor must always be in [0.0, 1.0]."""
    project = make_test_project(need_score=1.0, cost_efficiency_score=1.0)
    res = marginal_engine.calculate_marginal_impact(project)

    assert 0.0 <= res.marginal_impact_score <= 1.0
    assert 0.0 <= res.diminishing_return_factor <= 1.0


def test_27_simulation_helper_all_tiers(marginal_engine: MarginalImpactEngine):
    """simulate_increment without arguments produces 1L, 2L, 5L, 10L tiers."""
    project = make_test_project()
    sims = marginal_engine.simulate_increment(project)

    assert isinstance(sims, dict)
    assert set(sims.keys()) == {"1L", "2L", "5L", "10L"}
    for tier, r in sims.items():
        assert isinstance(r, MarginalImpactResult)
        assert r.increment_paise == SIMULATION_TIERS[tier]


def test_28_simulation_helper_custom_increment(marginal_engine: MarginalImpactEngine):
    """simulate_increment with custom increment returns single MarginalImpactResult."""
    project = make_test_project()
    sim = marginal_engine.simulate_increment(project, increment_paise=35_000_000)

    assert isinstance(sim, MarginalImpactResult)
    assert sim.increment_paise == 35_000_000


def test_29_seed_dataset_integration(marginal_engine: MarginalImpactEngine):
    """All 18 projects in seed dataset must compute marginal impact successfully."""
    seed_file = WORKSPACE_ROOT / "data" / "sample" / "member_c_seed_projects.json"
    with open(seed_file, "r", encoding="utf-8") as f:
        projects_data = json.load(f)

    assert len(projects_data) == 18

    results = []
    for p_dict in projects_data:
        project = Project.model_validate(p_dict)
        res = marginal_engine.calculate_marginal_impact(project)
        assert isinstance(res, MarginalImpactResult)
        assert 0.0 <= res.marginal_impact_score <= 1.0
        assert 0.0 <= res.diminishing_return_factor <= 1.0
        assert res.incremental_impact > 0.0
        results.append(res)

    # Verify score variance across the portfolio
    scores = [r.marginal_impact_score for r in results]
    assert max(scores) > min(scores)


def test_30_combined_pipeline_scoring_saturation_marginal():
    """Verify full Member C pipeline integration: Scoring -> Saturation -> Marginal Impact."""
    from backend.app.engine.scoring import ScoringEngine

    scoring = ScoringEngine()
    saturation = SaturationEngine()
    marginal = MarginalImpactEngine()

    project = make_test_project()
    context = SaturationContext(
        state="Bihar",
        sector=ProjectSector.EDUCATION,
        total_regional_csr_paise=5_000_000_000,
        total_population=10_000_000,
        target_population=1_000_000,
    )

    base_score = scoring.calculate_base_score(project)
    sat_result = saturation.calculate_saturation(project, context)
    marg_result = marginal.calculate_marginal_impact(project, saturation_result=sat_result)

    assert 0.0 <= base_score <= 1.0
    assert 0.0 <= sat_result.saturation_index <= 1.0
    assert 0.0 <= marg_result.marginal_impact_score <= 1.0
    assert marg_result.diminishing_return_factor <= 1.0


def test_31_allocation_context_metadata(marginal_engine: MarginalImpactEngine):
    """Verify allocation_context field exists and contains all required structural ratios."""
    project = make_test_project(
        requested_amount_paise=50_000_000,
        current_funding_paise=10_000_000,
    )
    result = marginal_engine.calculate_marginal_impact(project, increment_paise=10_000_000)

    assert result.allocation_context is not None
    ac = result.allocation_context

    assert ac["baseline_budget_lakh"] == 1.0
    assert ac["projected_budget_lakh"] == 2.0
    assert ac["increment_lakh"] == 1.0
    assert ac["budget_ratio"] == 0.40  # 20,000,000 / 50,000,000 = 0.40


def test_32_reconciliation_exact_formula(marginal_engine: MarginalImpactEngine):
    """Verify exact formula reconciliation: baseline + incremental == projected and effective_rate * increment_lakh == incremental."""
    project = make_test_project()
    sat = make_test_saturation_result()
    result = marginal_engine.calculate_marginal_impact(project, sat, increment_paise=25_000_000)

    # 1. baseline + incremental == projected
    diff1 = abs((result.baseline_impact + result.incremental_impact) - result.projected_impact)
    assert diff1 <= 1e-6

    # 2. impact_per_lakh * increment_lakh == incremental_impact
    inc_lakh = 25_000_000 / PAISE_PER_LAKH
    expected_incremental = result.impact_per_lakh * inc_lakh
    diff2 = abs(expected_incremental - result.incremental_impact)
    assert diff2 <= 1e-6

