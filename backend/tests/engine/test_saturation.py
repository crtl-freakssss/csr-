"""Comprehensive unit test suite for AllocateAI CSR Saturation Index Engine (Member C Phase 3).

Verifies Software Contract v1.0, Technical Contract v1.0, deterministic saturation
formulas, confidence degradation, interpretation bands, boundary clipping,
repeatability, and seed dataset integration.
"""

import json
from pathlib import Path
import pytest

from backend.app.engine.constants import (
    PROJECT_SCHEMA_VERSION,
    ProjectSector,
    SATURATION_CALCULATION_VERSION,
)
from backend.app.engine.exceptions import (
    InvalidProjectDataError,
)
from backend.app.engine.schemas import (
    BeneficiaryProfile,
    Financials,
    Geography,
    ImpactDNA,
    Project,
    SaturationContext,
    SaturationResult,
)
from backend.app.engine.saturation import (
    BENCHMARK_PER_CAPITA_CSR_PAISE,
    CALCULATION_VERSION,
    MODEL_NAME,
    SCHEMA_VERSION,
    WEIGHT_BENEFICIARY_COVERAGE,
    WEIGHT_FUNDING_DENSITY,
    WEIGHT_NEED_ADJUSTMENT,
    SaturationEngine,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def saturation_engine() -> SaturationEngine:
    """Fixture providing a fresh SaturationEngine instance."""
    return SaturationEngine()


def make_test_project(
    project_id: str = "PRJ-SAT-TEST",
    need_score: float = 0.80,
    target_beneficiaries: int = 5000,
    with_dna: bool = True,
) -> Project:
    """Helper to create a valid Project with customizable parameters."""
    dna = None
    if with_dna:
        dna = ImpactDNA(
            dna_id=f"DNA-{project_id}",
            project_id=project_id,
            need_score=need_score,
            expected_impact_score=0.85,
            cost_efficiency_score=0.80,
            evidence_strength_score=0.90,
            scalability_score=0.75,
            implementation_risk_score=0.15,
            beneficiary_reach=target_beneficiaries,
            estimated_impact_per_lakh=40.0,
            extraction_confidence=0.90,
            model_name="dna-v1",
            prompt_version="v1.0",
        )

    return Project(
        project_id=project_id,
        name=f"Test Project {project_id}",
        ngo_id="NGO-SAT-TEST",
        sector=ProjectSector.EDUCATION,
        geographies=[Geography(state="Bihar", district="Gaya", block="Mohanpur")],
        beneficiary_profile=BeneficiaryProfile(target_count=target_beneficiaries),
        financials=Financials(requested_amount_paise=25_000_000),
        duration_months=12,
        impact_dna=dna,
    )


def make_test_context(
    state: str = "Bihar",
    sector: ProjectSector = ProjectSector.EDUCATION,
    funding_paise: int = 5_000_000_000,  # ₹500 Lakh = ₹5 Crore
    total_population: int = 10_000_000,
    target_population: int = 1_000_000,
) -> SaturationContext:
    """Helper to create a valid SaturationContext."""
    return SaturationContext(
        state=state,
        sector=sector,
        total_regional_csr_paise=funding_paise,
        total_population=total_population,
        target_population=target_population,
    )


# ---------------------------------------------------------------------------
# Test Cases (Minimum 25 Required)
# ---------------------------------------------------------------------------

def test_1_valid_baseline_saturation(saturation_engine: SaturationEngine):
    """Verify standard calculation outputs valid SaturationResult instance."""
    project = make_test_project()
    context = make_test_context()
    result = saturation_engine.calculate_saturation(project, context)

    assert isinstance(result, SaturationResult)
    assert result.project_id == project.project_id
    assert result.state == context.state
    assert result.sector == context.sector
    assert 0.0 <= result.saturation_index <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert result.calculation_version == SATURATION_CALCULATION_VERSION


def test_2_calculate_alias_matches_calculate_saturation(saturation_engine: SaturationEngine):
    """Verify calculate() alias returns identical results to calculate_saturation()."""
    project = make_test_project()
    context = make_test_context()

    res1 = saturation_engine.calculate_saturation(project, context)
    res2 = saturation_engine.calculate(project, context)

    assert res1.model_dump() == res2.model_dump()


def test_3_very_low_saturation_scenario(saturation_engine: SaturationEngine):
    """High need (0.95), zero funding, and minimal coverage must yield VERY_LOW saturation (< 0.24)."""
    project = make_test_project(need_score=0.95, target_beneficiaries=100)
    context = make_test_context(
        funding_paise=0,
        total_population=10_000_000,
        target_population=1_000_000,
    )

    result = saturation_engine.calculate_saturation(project, context)
    assert result.saturation_index < 0.24
    label = saturation_engine.interpret_saturation(result.saturation_index)
    assert label == "VERY_LOW"


def test_4_very_high_saturation_scenario(saturation_engine: SaturationEngine):
    """Low need (0.05), heavy funding, and 100% coverage must yield VERY_HIGH saturation (> 0.74)."""
    project = make_test_project(need_score=0.05, target_beneficiaries=500_000)
    # Heavy funding: 500,000 target pop * ₹1,000 benchmark = 50,000,000,000 paise
    context = make_test_context(
        funding_paise=100_000_000_000,  # 2x benchmark capacity
        total_population=2_000_000,
        target_population=500_000,
    )

    result = saturation_engine.calculate_saturation(project, context)
    assert result.saturation_index > 0.74
    label = saturation_engine.interpret_saturation(result.saturation_index)
    assert label == "VERY_HIGH"


def test_5_moderate_saturation_scenario(saturation_engine: SaturationEngine):
    """Moderate parameters must yield moderate saturation."""
    project = make_test_project(need_score=0.50, target_beneficiaries=200_000)
    # 50% funding density
    context = make_test_context(
        funding_paise=50_000_000_000,  # ₹5,000 Lakh
        total_population=5_000_000,
        target_population=1_000_000,
    )

    result = saturation_engine.calculate_saturation(project, context)
    assert 0.25 <= result.saturation_index <= 0.74


def test_6_zero_regional_funding(saturation_engine: SaturationEngine):
    """Zero funding reports density = 0.0, but coverage and need adjustment still factor in."""
    project = make_test_project(need_score=0.60, target_beneficiaries=10_000)
    context = make_test_context(funding_paise=0)

    density = saturation_engine.calculate_funding_density(context)
    assert density == 0.0

    result = saturation_engine.calculate_saturation(project, context)
    assert result.existing_csr_amount_paise == 0
    assert result.saturation_index >= 0.0


def test_7_full_beneficiary_coverage(saturation_engine: SaturationEngine):
    """When beneficiaries reached equals or exceeds target population, coverage must clip to 1.0."""
    project = make_test_project(target_beneficiaries=2_000_000)
    context = make_test_context(target_population=1_000_000)

    coverage = saturation_engine.calculate_beneficiary_coverage(project, context)
    assert coverage == 1.0


def test_8_zero_beneficiary_coverage(saturation_engine: SaturationEngine):
    """When project has 0 beneficiaries, coverage must be 0.0."""
    project = make_test_project(target_beneficiaries=0)
    context = make_test_context()

    coverage = saturation_engine.calculate_beneficiary_coverage(project, context)
    assert coverage == 0.0


def test_9_missing_target_population_fallback_to_total_population(saturation_engine: SaturationEngine):
    """If target_population is 0, engine must fall back to total_population."""
    project = make_test_project(target_beneficiaries=10_000)
    context = make_test_context(
        target_population=0,
        total_population=5_000_000,
        funding_paise=10_000_000_000,
    )

    coverage = saturation_engine.calculate_beneficiary_coverage(project, context)
    assert coverage == pytest.approx(10_000 / 5_000_000, abs=1e-5)

    density = saturation_engine.calculate_funding_density(context)
    assert density > 0.0


def test_10_missing_both_populations_returns_zero_coverage_and_density(saturation_engine: SaturationEngine):
    """If both target and total population are 0, coverage and density must gracefully return 0.0."""
    project = make_test_project(target_beneficiaries=10_000)
    context = make_test_context(target_population=0, total_population=0)

    coverage = saturation_engine.calculate_beneficiary_coverage(project, context)
    density = saturation_engine.calculate_funding_density(context)

    assert coverage == 0.0
    assert density == 0.0


def test_11_need_adjustment_calculation(saturation_engine: SaturationEngine):
    """Verify need_adjustment equals exactly 1.0 - need_score."""
    project_high_need = make_test_project(need_score=0.85)
    adj_high = saturation_engine.calculate_need_adjustment(project_high_need)
    assert adj_high == pytest.approx(0.15, abs=1e-5)

    project_low_need = make_test_project(need_score=0.20)
    adj_low = saturation_engine.calculate_need_adjustment(project_low_need)
    assert adj_low == pytest.approx(0.80, abs=1e-5)


def test_12_confidence_full_data(saturation_engine: SaturationEngine):
    """When all inputs are complete and positive, confidence must be 1.0."""
    project = make_test_project(target_beneficiaries=5000)
    context = make_test_context(
        total_population=10_000_000,
        target_population=1_000_000,
        funding_paise=5_000_000_000,
    )

    confidence = saturation_engine.calculate_confidence(project, context)
    assert confidence == 1.0


def test_13_confidence_degrades_with_missing_populations(saturation_engine: SaturationEngine):
    """When populations are missing or zero, confidence must decrease."""
    project = make_test_project()
    context_no_pop = make_test_context(total_population=0, target_population=0)

    conf_full = saturation_engine.calculate_confidence(project, make_test_context())
    conf_no_pop = saturation_engine.calculate_confidence(project, context_no_pop)

    assert conf_no_pop < conf_full
    assert conf_no_pop == pytest.approx(0.75, abs=1e-3)


def test_14_confidence_degrades_with_zero_funding(saturation_engine: SaturationEngine):
    """Zero funding reduces funding confidence factor from 1.0 to 0.5."""
    project = make_test_project()
    context_zero_fund = make_test_context(funding_paise=0)

    conf = saturation_engine.calculate_confidence(project, context_zero_fund)
    assert conf == pytest.approx(0.875, abs=1e-3)


def test_15_confidence_degrades_with_zero_beneficiaries(saturation_engine: SaturationEngine):
    """Missing beneficiaries reduces confidence factor."""
    project = make_test_project(target_beneficiaries=0)
    if project.impact_dna:
        project.impact_dna.beneficiary_reach = 0

    conf = saturation_engine.calculate_confidence(project, make_test_context())
    assert conf == pytest.approx(0.75, abs=1e-3)


def test_16_boundary_clipping_density_and_coverage(saturation_engine: SaturationEngine):
    """Massive funding and massive beneficiaries must be clipped to [0.0, 1.0]."""
    project = make_test_project(target_beneficiaries=500_000_000)
    context = make_test_context(
        funding_paise=999_999_999_000_000,
        target_population=1000,
    )

    result = saturation_engine.calculate_saturation(project, context)
    assert result.saturation_index <= 1.0
    assert result.estimated_beneficiary_coverage <= 1.0


def test_17_deterministic_repeatability(saturation_engine: SaturationEngine):
    """Executing calculate_saturation 100 times must yield identical bitwise result."""
    project = make_test_project()
    context = make_test_context()

    first_result = saturation_engine.calculate_saturation(project, context).model_dump()

    for _ in range(100):
        current_result = saturation_engine.calculate_saturation(project, context).model_dump()
        assert current_result == first_result


def test_18_interpretation_helper_very_low():
    """interpret_saturation must return VERY_LOW for index in [0.0, 0.24]."""
    assert SaturationEngine.interpret_saturation(0.00) == "VERY_LOW"
    assert SaturationEngine.interpret_saturation(0.12) == "VERY_LOW"
    assert SaturationEngine.interpret_saturation(0.24) == "VERY_LOW"


def test_19_interpretation_helper_low():
    """interpret_saturation must return LOW for index in (0.24, 0.37]."""
    assert SaturationEngine.interpret_saturation(0.25) == "LOW"
    assert SaturationEngine.interpret_saturation(0.32) == "LOW"
    assert SaturationEngine.interpret_saturation(0.37) == "LOW"


def test_20_interpretation_helper_moderate():
    """interpret_saturation must return MODERATE for index in (0.37, 0.49]."""
    assert SaturationEngine.interpret_saturation(0.38) == "MODERATE"
    assert SaturationEngine.interpret_saturation(0.44) == "MODERATE"
    assert SaturationEngine.interpret_saturation(0.49) == "MODERATE"


def test_21_interpretation_helper_high():
    """interpret_saturation must return HIGH for index in (0.49, 0.74]."""
    assert SaturationEngine.interpret_saturation(0.50) == "HIGH"
    assert SaturationEngine.interpret_saturation(0.62) == "HIGH"
    assert SaturationEngine.interpret_saturation(0.74) == "HIGH"


def test_22_interpretation_helper_very_high():
    """interpret_saturation must return VERY_HIGH for index in (0.74, 1.00]."""
    assert SaturationEngine.interpret_saturation(0.75) == "VERY_HIGH"
    assert SaturationEngine.interpret_saturation(0.90) == "VERY_HIGH"
    assert SaturationEngine.interpret_saturation(1.00) == "VERY_HIGH"


def test_23_version_metadata(saturation_engine: SaturationEngine):
    """Verify version metadata matches contract constants and contains zero timestamps."""
    project = make_test_project()
    context = make_test_context()
    result = saturation_engine.calculate_saturation(project, context)

    assert result.calculation_version == SATURATION_CALCULATION_VERSION == "saturation-v1"
    assert saturation_engine.model_name == MODEL_NAME == "csr-saturation-engine"
    assert saturation_engine.schema_version == SCHEMA_VERSION == "project-v1"
    assert not hasattr(result, "timestamp")
    assert not hasattr(result, "created_at")


def test_24_missing_dna_raises_invalid_project_data_error(saturation_engine: SaturationEngine):
    """Project without ImpactDNA must raise InvalidProjectDataError."""
    project = make_test_project(with_dna=False)
    context = make_test_context()

    with pytest.raises(InvalidProjectDataError) as excinfo:
        saturation_engine.calculate_saturation(project, context)
    assert excinfo.value.field_name == "impact_dna"


def test_25_invalid_context_raises_invalid_project_data_error(saturation_engine: SaturationEngine):
    """Empty state or negative values in context must raise InvalidProjectDataError."""
    project = make_test_project()

    # Empty state
    invalid_context_1 = SaturationContext(state="", sector=ProjectSector.EDUCATION)
    with pytest.raises(InvalidProjectDataError):
        saturation_engine.validate_context(invalid_context_1)

    # Negative funding constructed without Pydantic validation
    invalid_context_2 = SaturationContext.model_construct(
        state="Bihar", sector=ProjectSector.EDUCATION, total_regional_csr_paise=-500,
        total_population=1000, target_population=100
    )
    with pytest.raises(InvalidProjectDataError):
        saturation_engine.validate_context(invalid_context_2)


def test_26_seed_context_dataset_integration(saturation_engine: SaturationEngine):
    """All entries in saturation_context.json must parse, validate, and compute successfully."""
    seed_context_path = WORKSPACE_ROOT / "data" / "sample" / "saturation_context.json"
    assert seed_context_path.exists(), "saturation_context.json must exist"

    with open(seed_context_path, "r", encoding="utf-8") as f:
        context_list = json.load(f)

    assert len(context_list) >= 15, "Should contain comprehensive regional context entries"

    project = make_test_project()

    saturation_indices = []
    for ctx_dict in context_list:
        context = SaturationContext.model_validate(ctx_dict)
        res = saturation_engine.calculate_saturation(project, context)
        assert 0.0 <= res.saturation_index <= 1.0
        assert 0.0 <= res.confidence <= 1.0
        saturation_indices.append(res.saturation_index)

    # Check variation across diverse contexts (saturated vs underserved)
    assert max(saturation_indices) > min(saturation_indices)
    assert min(saturation_indices) < 0.20  # Underserved region
    assert max(saturation_indices) > 0.40  # Saturated region

    # Low need project in highly funded region must exceed 0.50 saturation
    low_need_project = make_test_project(need_score=0.30)
    res_sat = saturation_engine.calculate_saturation(
        low_need_project, SaturationContext.model_validate(context_list[0])
    )
    assert res_sat.saturation_index > 0.50


def test_27_seed_projects_and_seed_contexts_pairing(saturation_engine: SaturationEngine):
    """Pair each Phase 1 seed project with its matching state/sector context."""
    projects_path = WORKSPACE_ROOT / "data" / "sample" / "member_c_seed_projects.json"
    contexts_path = WORKSPACE_ROOT / "data" / "sample" / "saturation_context.json"

    with open(projects_path, "r", encoding="utf-8") as f:
        projects_data = json.load(f)

    with open(contexts_path, "r", encoding="utf-8") as f:
        contexts_data = json.load(f)

    # Build context lookup by (state, sector)
    context_map = {}
    for c in contexts_data:
        context_map[(c["state"], c["sector"])] = SaturationContext.model_validate(c)

    matched = 0
    for p_dict in projects_data:
        project = Project.model_validate(p_dict)
        state = project.geographies[0].state
        sector = project.sector.value

        if (state, sector) in context_map:
            ctx = context_map[(state, sector)]
            res = saturation_engine.calculate_saturation(project, ctx)
            assert isinstance(res, SaturationResult)
            assert res.project_id == project.project_id
            assert res.state == state
            assert 0.0 <= res.saturation_index <= 1.0
            matched += 1

    assert matched == 18, f"All 18 seed projects must match regional context, got {matched}"


def test_28_component_breakdown_metadata(saturation_engine: SaturationEngine):
    """Verify component_breakdown metadata exists, has required keys, and sums weights to 1.0."""
    project = make_test_project()
    context = make_test_context()
    result = saturation_engine.calculate_saturation(project, context)

    assert result.component_breakdown is not None
    cb = result.component_breakdown

    assert "funding_density_score" in cb
    assert "beneficiary_coverage_score" in cb
    assert "need_adjustment_score" in cb
    assert "weights" in cb

    weights = cb["weights"]
    assert weights["funding_density"] == 0.40
    assert weights["beneficiary_coverage"] == 0.30
    assert weights["need_adjustment"] == 0.30
    assert sum(weights.values()) == pytest.approx(1.0, abs=1e-6)


def test_29_explainability_reconciliation(saturation_engine: SaturationEngine):
    """Verify 0.40 * funding_density + 0.30 * coverage + 0.30 * need_adj == saturation_index."""
    project = make_test_project()
    context = make_test_context()
    result = saturation_engine.calculate_saturation(project, context)

    cb = result.component_breakdown
    assert cb is not None

    reconstructed = (
        0.40 * cb["funding_density_score"]
        + 0.30 * cb["beneficiary_coverage_score"]
        + 0.30 * cb["need_adjustment_score"]
    )
    assert result.saturation_index == pytest.approx(reconstructed, abs=1e-6)
