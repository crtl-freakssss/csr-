"""Integration tests for OptimizationService orchestration pipeline (Member C Phase 6).

Verifies:
1. Complete 4-engine pipeline execution success
2. Error handling for empty projects
3. Error handling for invalid weights
4. Error handling for zero budget
5. Error handling for duplicate project IDs
6. Error handling for missing ImpactDNA
7. 100-run deterministic repeatability
8. Pipeline financial and metrics reconciliation
9. Version propagation throughout calculation
10. Portfolio metrics and breakdown propagation
"""

import hashlib
from pathlib import Path
import pytest

from backend.app.engine.constants import (
    CALCULATION_VERSIONS,
    DEFAULT_MARGINAL_INCREMENT_PAISE,
    OPTIMIZER_CALCULATION_VERSION,
    AllocationStatus,
    OptimizationStatus,
    ProjectSector,
    ReasonCode,
)
from backend.app.engine.exceptions import (
    BudgetValidationError,
    ConstraintViolationError,
    InvalidProjectDataError,
    WeightValidationError,
)
from backend.app.engine.schemas import (
    BeneficiaryProfile,
    Financials,
    Geography,
    ImpactDNA,
    OptimizationConstraints,
    OptimizationRequest,
    OptimizationResult,
    OptimizationWeights,
    Project,
)
from backend.app.services.optimization_service import OptimizationService

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def service() -> OptimizationService:
    """Fixture providing an OptimizationService instance."""
    return OptimizationService()


@pytest.fixture
def valid_weights() -> OptimizationWeights:
    """Balanced optimization weights fixture."""
    return OptimizationWeights(
        need=0.20,
        marginal_impact=0.25,
        cost_efficiency=0.20,
        evidence=0.15,
        scalability=0.10,
        equity=0.10,
        risk_penalty=0.10,
    )


def make_test_project(
    project_id: str = "PRJ-SRV-1",
    state: str = "Bihar",
    sector: ProjectSector = ProjectSector.EDUCATION,
    requested_paise: int = 50_000_000,
    with_dna: bool = True,
) -> Project:
    """Helper to build test project instances."""
    dna = None
    if with_dna:
        dna = ImpactDNA(
            dna_id=f"DNA-{project_id}",
            project_id=project_id,
            need_score=0.85,
            expected_impact_score=0.85,
            cost_efficiency_score=0.80,
            evidence_strength_score=0.80,
            scalability_score=0.75,
            implementation_risk_score=0.15,
            beneficiary_reach=5000,
            estimated_impact_per_lakh=35.0,
            extraction_confidence=0.90,
            model_name="dna-v1",
            prompt_version="v1.0",
        )
    return Project(
        project_id=project_id,
        name=f"Service Project {project_id}",
        ngo_id=f"NGO-{project_id}",
        sector=sector,
        geographies=[Geography(state=state, district="Dist-1", block="Blk-1")],
        beneficiary_profile=BeneficiaryProfile(target_count=5000),
        financials=Financials(
            requested_amount_paise=requested_paise,
            current_funding_paise=0,
        ),
        duration_months=12,
        impact_dna=dna,
    )


# ---------------------------------------------------------------------------
# Test 1: Full Pipeline Execution Success
# ---------------------------------------------------------------------------

def test_1_optimize_pipeline_success(service: OptimizationService, valid_weights: OptimizationWeights):
    """Execute complete 4-stage pipeline on seed projects and verify result."""
    seed_projects = service.load_seed_projects()
    candidate_ids = [seed_projects[0].project_id, seed_projects[1].project_id]

    req = OptimizationRequest(
        budget_paise=30_000_000,
        project_ids=candidate_ids,
        weights=valid_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    result = service.optimize(request=req, projects=seed_projects[:2])

    assert isinstance(result, OptimizationResult)
    assert result.status == OptimizationStatus.COMPLETED
    assert result.budget_paise == 30_000_000
    assert result.allocated_paise == 30_000_000
    assert result.unallocated_paise == 0
    assert len(result.allocations) == 2
    assert result.portfolio_breakdown is not None
    assert result.optimization_audit is not None


# ---------------------------------------------------------------------------
# Test 2: Empty Projects Validation
# ---------------------------------------------------------------------------

def test_2_empty_projects(service: OptimizationService, valid_weights: OptimizationWeights):
    """Request with empty project_ids must raise InvalidProjectDataError."""
    # When instantiated via model_construct or bypassing Pydantic min_length
    req = OptimizationRequest.model_construct(
        budget_paise=10_000_000,
        project_ids=[],
        weights=valid_weights,
        constraints=OptimizationConstraints(),
        marginal_increment_paise=DEFAULT_MARGINAL_INCREMENT_PAISE,
    )
    with pytest.raises(InvalidProjectDataError):
        service.validate_request(req)


# ---------------------------------------------------------------------------
# Test 3: Invalid Weights Validation
# ---------------------------------------------------------------------------

def test_3_invalid_weights(service: OptimizationService):
    """Weights summing to invalid total must fail validation."""
    from backend.app.engine.exceptions import WeightValidationError
    from backend.app.engine.utils import validate_weights
    with pytest.raises(WeightValidationError):
        validate_weights({"need": 0.5, "marginal_impact": 0.2})  # sum = 0.7 != 1.0


# ---------------------------------------------------------------------------
# Test 4: Zero Budget Validation
# ---------------------------------------------------------------------------

def test_4_zero_budget(service: OptimizationService, valid_weights: OptimizationWeights):
    """Zero budget must raise BudgetValidationError."""
    req = OptimizationRequest.model_construct(
        budget_paise=0,
        project_ids=["PRJ-0001"],
        weights=valid_weights,
        constraints=OptimizationConstraints(),
        marginal_increment_paise=DEFAULT_MARGINAL_INCREMENT_PAISE,
    )
    with pytest.raises(BudgetValidationError):
        service.validate_request(req)


# ---------------------------------------------------------------------------
# Test 5: Duplicate Project IDs Validation
# ---------------------------------------------------------------------------

def test_5_duplicate_project_ids(service: OptimizationService, valid_weights: OptimizationWeights):
    """Duplicate project_ids in request must raise InvalidProjectDataError."""
    req = OptimizationRequest(
        budget_paise=10_000_000,
        project_ids=["PRJ-0001", "PRJ-0001"],  # duplicate
        weights=valid_weights,
        constraints=OptimizationConstraints(),
    )
    with pytest.raises(InvalidProjectDataError) as exc_info:
        service.validate_request(req)
    assert "Duplicate project_ids" in exc_info.value.message


# ---------------------------------------------------------------------------
# Test 6: Missing ImpactDNA Validation
# ---------------------------------------------------------------------------

def test_6_missing_dna(service: OptimizationService, valid_weights: OptimizationWeights):
    """Candidate project missing required ImpactDNA must raise InvalidProjectDataError."""
    p_no_dna = make_test_project("PRJ-NODNA", with_dna=False)
    req = OptimizationRequest(
        budget_paise=10_000_000,
        project_ids=["PRJ-NODNA"],
        weights=valid_weights,
        constraints=OptimizationConstraints(),
    )
    with pytest.raises(InvalidProjectDataError) as exc_info:
        service.validate_request(req, candidate_projects=[p_no_dna])
    assert "missing required ImpactDNA" in exc_info.value.message


# ---------------------------------------------------------------------------
# Test 7: Deterministic Repeatability
# ---------------------------------------------------------------------------

def test_7_deterministic_repeatability(service: OptimizationService, valid_weights: OptimizationWeights):
    """100 consecutive full service optimization runs produce 1 unique SHA-256 hash."""
    seed_projects = service.load_seed_projects()[:3]
    req = OptimizationRequest(
        budget_paise=25_000_000,
        project_ids=[p.project_id for p in seed_projects],
        weights=valid_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )

    first_dump = service.optimize(req, projects=seed_projects).model_dump_json()
    first_hash = hashlib.sha256(first_dump.encode("utf-8")).hexdigest()

    hashes = set()
    for _ in range(100):
        dump = service.optimize(req, projects=seed_projects).model_dump_json()
        h = hashlib.sha256(dump.encode("utf-8")).hexdigest()
        hashes.add(h)

    assert len(hashes) == 1
    assert list(hashes)[0] == first_hash


# ---------------------------------------------------------------------------
# Test 8: Pipeline Financial & Metrics Reconciliation
# ---------------------------------------------------------------------------

def test_8_pipeline_reconciliation(service: OptimizationService, valid_weights: OptimizationWeights):
    """allocated + unallocated must exactly equal budget, and audit numbers must reconcile."""
    seed_projects = service.load_seed_projects()[:4]
    budget = 40_000_000

    req = OptimizationRequest(
        budget_paise=budget,
        project_ids=[p.project_id for p in seed_projects],
        weights=valid_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    result = service.optimize(req, projects=seed_projects)

    assert result.allocated_paise + result.unallocated_paise == budget
    oa = result.optimization_audit
    assert oa is not None
    assert oa["budget_allocated_total_paise"] == result.allocated_paise
    assert oa["budget_unallocated_paise"] == result.unallocated_paise
    assert oa["budget_allocated_total_paise"] + oa["budget_unallocated_paise"] == budget
    assert oa["projects_funded"] + oa["projects_skipped"] == oa["total_projects_considered"]


# ---------------------------------------------------------------------------
# Test 9: Version Propagation
# ---------------------------------------------------------------------------

def test_9_version_propagation(service: OptimizationService, valid_weights: OptimizationWeights):
    """Result contains all canonical version strings from CALCULATION_VERSIONS."""
    p1 = make_test_project("PRJ-1")
    req = OptimizationRequest(
        budget_paise=20_000_000,
        project_ids=["PRJ-1"],
        weights=valid_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    result = service.optimize(req, projects=[p1])

    assert result.calculation_versions == CALCULATION_VERSIONS
    assert result.calculation_versions["optimizer"] == OPTIMIZER_CALCULATION_VERSION


# ---------------------------------------------------------------------------
# Test 10: Portfolio Metrics Propagation
# ---------------------------------------------------------------------------

def test_10_portfolio_metrics_propagation(service: OptimizationService, valid_weights: OptimizationWeights):
    """Portfolio metrics, breakdown, and explainability propagate correctly."""
    seed_projects = service.load_seed_projects()[:3]
    req = OptimizationRequest(
        budget_paise=30_000_000,
        project_ids=[p.project_id for p in seed_projects],
        weights=valid_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    result = service.optimize(req, projects=seed_projects)

    assert result.total_predicted_impact > 0.0
    assert 0.0 <= result.average_saturation <= 1.0
    assert 0.0 <= result.underserved_region_allocation_share <= 1.0

    pb = result.portfolio_breakdown
    assert pb is not None
    assert pb["budget_utilization"] == 1.0
    assert pb["project_count_funded"] >= 1

    summary = service.get_pipeline_summary(result)
    assert summary["projects_processed"] == 3
    assert summary["funded_projects"] >= 1
    assert summary["budget_utilization"] == 1.0
    assert summary["engine_versions"] == CALCULATION_VERSIONS
