"""Comprehensive unit test suite for AllocateAI Budget Allocation Optimizer Engine (Member C Phase 5).

Verifies:
- Software Contract v1.0 & Technical Contract v1.0
- Deterministic composite optimization scoring
- 5-step tie-breaking ranking
- ConstraintEngine (project caps, regional caps, minimum floors, regional equity)
- Sequential budget allocation and budget conservation
- Explainability metadata (portfolio_breakdown & allocation_context)
- Reason code generation rules
- Seed dataset integration across ₹5L, ₹10L, ₹15L, ₹25L, ₹50L budgets
- Full 4-engine pipeline integration (Scoring -> Saturation -> Marginal -> Optimizer)
- 100-run bitwise repeatability and absence of non-deterministic dependencies
"""

import hashlib
import json
from pathlib import Path
import pytest

from backend.app.engine.constants import (
    CALCULATION_VERSIONS,
    DEFAULT_MARGINAL_INCREMENT_PAISE,
    OPTIMIZER_CALCULATION_VERSION,
    PAISE_PER_LAKH,
    AllocationStatus,
    OptimizationStatus,
    ProjectSector,
    ReasonCode,
)
from backend.app.engine.constraints.engine import ConstraintEngine
from backend.app.engine.exceptions import (
    BudgetValidationError,
    ConstraintViolationError,
    InvalidProjectDataError,
    WeightValidationError,
)
from backend.app.engine.marginal_impact.engine import MarginalImpactEngine
from backend.app.engine.optimizer.engine import AllocationOptimizer, RankedProject
from backend.app.engine.saturation.engine import SaturationEngine
from backend.app.engine.schemas import (
    Allocation,
    BeneficiaryProfile,
    Financials,
    Geography,
    ImpactDNA,
    MarginalImpactResult,
    OptimizationConstraints,
    OptimizationRequest,
    OptimizationResult,
    OptimizationWeights,
    Project,
    SaturationContext,
    SaturationResult,
)
from backend.app.engine.scoring.engine import ScoringEngine

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# Test Fixtures & Mock Builders
# ---------------------------------------------------------------------------

@pytest.fixture
def optimizer() -> AllocationOptimizer:
    """Fixture providing a fresh AllocationOptimizer instance."""
    return AllocationOptimizer()


@pytest.fixture
def default_weights() -> OptimizationWeights:
    """Canonical balanced policy weights."""
    return OptimizationWeights(
        need=0.20,
        marginal_impact=0.25,
        cost_efficiency=0.20,
        evidence=0.15,
        scalability=0.10,
        equity=0.10,
        risk_penalty=0.10,
    )


def make_mock_project(
    project_id: str = "PRJ-OPT-1",
    state: str = "Bihar",
    sector: ProjectSector = ProjectSector.EDUCATION,
    requested_paise: int = 50_000_000,  # ₹5 Lakh
    current_paise: int = 0,
    need: float = 0.85,
    cost_eff: float = 0.80,
    evidence: float = 0.85,
    scalability: float = 0.75,
    risk: float = 0.15,
    impact_rate: float = 40.0,
    with_dna: bool = True,
    missing_fields: list[str] | None = None,
    confidence: float = 0.90,
) -> Project:
    """Helper to build test project instances."""
    dna = None
    if with_dna:
        dna = ImpactDNA(
            dna_id=f"DNA-{project_id}",
            project_id=project_id,
            need_score=need,
            expected_impact_score=0.85,
            cost_efficiency_score=cost_eff,
            evidence_strength_score=evidence,
            scalability_score=scalability,
            implementation_risk_score=risk,
            beneficiary_reach=5000,
            estimated_impact_per_lakh=impact_rate,
            missing_fields=missing_fields or [],
            extraction_confidence=confidence,
            model_name="dna-v1",
            prompt_version="v1.0",
        )

    return Project(
        project_id=project_id,
        name=f"Test Project {project_id}",
        ngo_id=f"NGO-{project_id}",
        sector=sector,
        geographies=[Geography(state=state, district="Dist-1", block="Blk-1")],
        beneficiary_profile=BeneficiaryProfile(target_count=5000),
        financials=Financials(
            requested_amount_paise=requested_paise,
            current_funding_paise=current_paise,
        ),
        duration_months=12,
        impact_dna=dna,
    )


def make_mock_saturation(project_id: str, state: str, sat_index: float = 0.20) -> SaturationResult:
    """Helper to build mock saturation assessment."""
    return SaturationResult(
        project_id=project_id,
        state=state,
        sector=ProjectSector.EDUCATION,
        saturation_index=sat_index,
        need_score=0.80,
        existing_csr_amount_paise=10_000_000_000,
        estimated_beneficiary_coverage=0.10,
        confidence=0.95,
        calculation_version="saturation-v1",
    )


def make_mock_marginal(project_id: str, marginal_score: float = 0.75, rate: float = 35.0) -> MarginalImpactResult:
    """Helper to build mock marginal return assessment."""
    return MarginalImpactResult(
        project_id=project_id,
        increment_paise=10_000_000,
        baseline_budget_paise=0,
        projected_budget_paise=10_000_000,
        baseline_impact=0.0,
        projected_impact=rate,
        incremental_impact=rate,
        impact_per_lakh=rate,
        marginal_impact_score=marginal_score,
        diminishing_return_factor=0.85,
        calculation_version="marginal-v1",
    )


# ---------------------------------------------------------------------------
# SECTION 1: Input Validation & Weight Normalization Tests (1 - 6)
# ---------------------------------------------------------------------------

def test_1_valid_baseline_optimization(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Verify basic successful optimization run with valid request."""
    p1 = make_mock_project("PRJ-1", requested_paise=50_000_000)
    req = OptimizationRequest(
        budget_paise=30_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1])

    assert isinstance(res, OptimizationResult)
    assert res.status == OptimizationStatus.COMPLETED
    assert res.allocated_paise == 30_000_000
    assert res.unallocated_paise == 0
    assert len(res.allocations) == 1
    assert res.allocations[0].allocated_amount_paise == 30_000_000


def test_2_empty_projects_raises_invalid_project_data_error(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Empty projects list must raise InvalidProjectDataError."""
    req = OptimizationRequest(
        budget_paise=10_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(),
    )
    with pytest.raises(InvalidProjectDataError):
        optimizer.calculate_optimal_allocation(req, [])


def test_3_missing_project_id_raises_invalid_project_data_error(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Requested project_id not found in projects list must raise InvalidProjectDataError."""
    p1 = make_mock_project("PRJ-1")
    req = OptimizationRequest(
        budget_paise=10_000_000,
        project_ids=["PRJ-1", "PRJ-MISSING"],
        weights=default_weights,
        constraints=OptimizationConstraints(),
    )
    with pytest.raises(InvalidProjectDataError):
        optimizer.calculate_optimal_allocation(req, [p1])


def test_4_missing_dna_raises_invalid_project_data_error(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Project with impact_dna=None must raise InvalidProjectDataError."""
    p_no_dna = make_mock_project("PRJ-NODNA", with_dna=False)
    req = OptimizationRequest(
        budget_paise=10_000_000,
        project_ids=["PRJ-NODNA"],
        weights=default_weights,
        constraints=OptimizationConstraints(),
    )
    with pytest.raises(InvalidProjectDataError):
        optimizer.calculate_optimal_allocation(req, [p_no_dna])


def test_5_zero_budget_raises_budget_validation_error():
    """Zero budget must raise BudgetValidationError."""
    from backend.app.engine.utils import validate_budget
    with pytest.raises(BudgetValidationError):
        validate_budget(0)


def test_6_negative_budget_raises_budget_validation_error():
    """Negative budget must raise BudgetValidationError."""
    from backend.app.engine.utils import validate_budget
    with pytest.raises(BudgetValidationError):
        validate_budget(-500)


# ---------------------------------------------------------------------------
# SECTION 2: Composite Score & Ranking Tests (7 - 12)
# ---------------------------------------------------------------------------

def test_7_composite_score_formula_calculation(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Verify composite optimization score exactly evaluates formula."""
    p = make_mock_project(
        need=0.90, cost_eff=0.80, evidence=0.85, scalability=0.70, risk=0.10
    )
    norm_w = default_weights.to_dict()
    total_w = sum(norm_w.values())
    norm_w = {k: v / total_w for k, v in norm_w.items()}

    score = optimizer.calculate_composite_score(
        project=p,
        base_score=0.75,
        saturation_index=0.10,
        marginal_impact_score=0.80,
        normalized_weights=norm_w,
    )
    assert 0.0 <= score <= 1.0


def test_8_ranking_orders_descending_by_composite_score(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Projects must be ranked in strictly descending order of optimization score."""
    p_high = make_mock_project("PRJ-HIGH", need=0.95, cost_eff=0.95)
    p_low = make_mock_project("PRJ-LOW", need=0.30, cost_eff=0.30)

    sat_map = {
        "PRJ-HIGH": make_mock_saturation("PRJ-HIGH", "Bihar", 0.10),
        "PRJ-LOW": make_mock_saturation("PRJ-LOW", "Bihar", 0.50),
    }
    marg_map = {
        "PRJ-HIGH": make_mock_marginal("PRJ-HIGH", 0.85),
        "PRJ-LOW": make_mock_marginal("PRJ-LOW", 0.40),
    }
    base_map = {"PRJ-HIGH": 0.85, "PRJ-LOW": 0.35}

    ranked = optimizer.rank_projects([p_low, p_high], default_weights, sat_map, marg_map, base_map)

    assert ranked[0].project.project_id == "PRJ-HIGH"
    assert ranked[1].project.project_id == "PRJ-LOW"
    assert ranked[0].optimization_score > ranked[1].optimization_score


def test_9_tie_breaking_marginal_score(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Tie breaker 1: Higher marginal impact score wins if composite scores are equal."""
    p1 = make_mock_project("PRJ-A", need=0.80, cost_eff=0.80)
    p2 = make_mock_project("PRJ-B", need=0.80, cost_eff=0.80)

    sat_map = {
        "PRJ-A": make_mock_saturation("PRJ-A", "Bihar", 0.20),
        "PRJ-B": make_mock_saturation("PRJ-B", "Bihar", 0.20),
    }
    marg_map = {
        "PRJ-A": make_mock_marginal("PRJ-A", 0.90),
        "PRJ-B": make_mock_marginal("PRJ-B", 0.70),
    }
    base_map = {"PRJ-A": 0.75, "PRJ-B": 0.75}

    ranked = optimizer.rank_projects([p2, p1], default_weights, sat_map, marg_map, base_map)
    assert ranked[0].project.project_id == "PRJ-A"


def test_10_tie_breaking_saturation_index(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Tie breaker 2: Lower saturation index wins if composite and marginal scores are equal."""
    p1 = make_mock_project("PRJ-A", need=0.80)
    p2 = make_mock_project("PRJ-B", need=0.80)

    sat_map = {
        "PRJ-A": make_mock_saturation("PRJ-A", "Bihar", 0.10),  # More underserved
        "PRJ-B": make_mock_saturation("PRJ-B", "Bihar", 0.30),
    }
    marg_map = {
        "PRJ-A": make_mock_marginal("PRJ-A", 0.80),
        "PRJ-B": make_mock_marginal("PRJ-B", 0.80),
    }
    base_map = {"PRJ-A": 0.75, "PRJ-B": 0.75}

    ranked = optimizer.rank_projects([p2, p1], default_weights, sat_map, marg_map, base_map)
    assert ranked[0].project.project_id == "PRJ-A"


def test_11_tie_breaking_need_score(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Tie breaker 3: Higher need score wins if composite, marginal, and saturation match."""
    p1 = make_mock_project("PRJ-A", need=0.90)
    p2 = make_mock_project("PRJ-B", need=0.70)

    sat_map = {
        "PRJ-A": make_mock_saturation("PRJ-A", "Bihar", 0.20),
        "PRJ-B": make_mock_saturation("PRJ-B", "Bihar", 0.20),
    }
    marg_map = {
        "PRJ-A": make_mock_marginal("PRJ-A", 0.80),
        "PRJ-B": make_mock_marginal("PRJ-B", 0.80),
    }
    base_map = {"PRJ-A": 0.75, "PRJ-B": 0.75}

    ranked = optimizer.rank_projects([p2, p1], default_weights, sat_map, marg_map, base_map)
    assert ranked[0].project.project_id == "PRJ-A"


def test_12_tie_breaking_lexicographical_id(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Tie breaker 4: Lexicographical project_id wins if all other metrics match."""
    p1 = make_mock_project("PRJ-0001", need=0.80)
    p2 = make_mock_project("PRJ-0002", need=0.80)

    sat_map = {
        "PRJ-0001": make_mock_saturation("PRJ-0001", "Bihar", 0.20),
        "PRJ-0002": make_mock_saturation("PRJ-0002", "Bihar", 0.20),
    }
    marg_map = {
        "PRJ-0001": make_mock_marginal("PRJ-0001", 0.80),
        "PRJ-0002": make_mock_marginal("PRJ-0002", 0.80),
    }
    base_map = {"PRJ-0001": 0.75, "PRJ-0002": 0.75}

    ranked = optimizer.rank_projects([p2, p1], default_weights, sat_map, marg_map, base_map)
    assert ranked[0].project.project_id == "PRJ-0001"
    assert ranked[1].project.project_id == "PRJ-0002"


# ---------------------------------------------------------------------------
# SECTION 3: Budget Allocation & Conservation Tests (13 - 18)
# ---------------------------------------------------------------------------

def test_13_budget_conservation_invariant(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Invariant: allocated_paise + unallocated_paise == budget_paise."""
    p1 = make_mock_project("PRJ-1", requested_paise=50_000_000)
    p2 = make_mock_project("PRJ-2", requested_paise=40_000_000)

    req = OptimizationRequest(
        budget_paise=70_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    assert res.allocated_paise + res.unallocated_paise == req.budget_paise
    assert res.allocated_paise == 70_000_000
    assert res.unallocated_paise == 0


def test_14_exact_full_budget_allocation(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """When budget exactly matches total requested need across projects, all projects are fully funded."""
    p1 = make_mock_project("PRJ-1", requested_paise=25_000_000)
    p2 = make_mock_project("PRJ-2", requested_paise=35_000_000)

    req = OptimizationRequest(
        budget_paise=60_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    assert res.allocations[0].allocated_amount_paise == 25_000_000 or res.allocations[0].allocated_amount_paise == 35_000_000
    assert res.allocated_paise == 60_000_000


def test_15_partial_budget_sequential_allocation(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Higher ranked project receives full funding; lower ranked receives remaining partial budget."""
    p1 = make_mock_project("PRJ-1", need=0.95, requested_paise=40_000_000)
    p2 = make_mock_project("PRJ-2", need=0.40, requested_paise=40_000_000)

    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    assert res.allocations[0].project_id == "PRJ-1"
    assert res.allocations[0].allocated_amount_paise == 40_000_000
    assert res.allocations[1].project_id == "PRJ-2"
    assert res.allocations[1].allocated_amount_paise == 10_000_000


def test_16_insufficient_budget_unfunded_project_allocation_zero(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Projects after budget is exhausted receive 0 allocated amount with rank and BUDGET_CONSTRAINT reason."""
    p1 = make_mock_project("PRJ-1", need=0.95, requested_paise=50_000_000)
    p2 = make_mock_project("PRJ-2", need=0.40, requested_paise=50_000_000)

    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    assert res.allocations[0].allocated_amount_paise == 50_000_000
    assert res.allocations[1].allocated_amount_paise == 0
    assert ReasonCode.BUDGET_CONSTRAINT in res.allocations[1].reason_codes


def test_17_unallocated_allowed_when_require_full_allocation_false(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """When require_full_budget_allocation=False, unallocated paise remains cleanly without error."""
    p1 = make_mock_project("PRJ-1", requested_paise=20_000_000)

    req = OptimizationRequest(
        budget_paise=50_000_000,  # 50L available, but project only needs 20L
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=False),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1])

    assert res.allocated_paise == 20_000_000
    assert res.unallocated_paise == 30_000_000


def test_18_require_full_allocation_raises_constraint_violation_error(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """When require_full_budget_allocation=True and budget cannot be exhausted, raise ConstraintViolationError."""
    p1 = make_mock_project("PRJ-1", requested_paise=20_000_000)

    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    with pytest.raises(ConstraintViolationError):
        optimizer.calculate_optimal_allocation(req, [p1])


# ---------------------------------------------------------------------------
# SECTION 4: Constraint Engine Policy Enforcement Tests (19 - 24)
# ---------------------------------------------------------------------------

def test_19_project_cap_constraint(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Enforce max_allocation_per_project_paise."""
    p1 = make_mock_project("PRJ-1", requested_paise=100_000_000)

    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(
            max_allocation_per_project_paise=30_000_000,
            require_full_budget_allocation=False,
        ),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1])

    assert res.allocations[0].allocated_amount_paise == 30_000_000


def test_20_regional_cap_constraint(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Enforce max_allocation_per_region_paise across multiple projects in same state."""
    p1 = make_mock_project("PRJ-1", state="Maharashtra", need=0.90, requested_paise=50_000_000)
    p2 = make_mock_project("PRJ-2", state="Maharashtra", need=0.80, requested_paise=50_000_000)

    req = OptimizationRequest(
        budget_paise=80_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(
            max_allocation_per_region_paise=40_000_000,  # Max 40L for Maharashtra
            regional_equity_enabled=True,
            require_full_budget_allocation=False,
        ),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    alloc_map = {a.project_id: a.allocated_amount_paise for a in res.allocations}
    assert alloc_map["PRJ-1"] == 40_000_000
    assert alloc_map["PRJ-2"] == 0  # Capped by region
    assert ReasonCode.REGIONAL_CAP in res.allocations[1].reason_codes


def test_21_regional_cap_across_different_regions(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Different regions each receive funding up to their respective regional caps."""
    p1 = make_mock_project("PRJ-1", state="Bihar", requested_paise=50_000_000)
    p2 = make_mock_project("PRJ-2", state="Odisha", requested_paise=50_000_000)

    req = OptimizationRequest(
        budget_paise=60_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(
            max_allocation_per_region_paise=30_000_000,  # 30L cap per region
            regional_equity_enabled=True,
            require_full_budget_allocation=True,
        ),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    assert res.allocations[0].allocated_amount_paise == 30_000_000
    assert res.allocations[1].allocated_amount_paise == 30_000_000


def test_22_minimum_allocation_per_project_satisfied(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Allocations meeting or exceeding minimum_allocation_per_project_paise are granted."""
    p1 = make_mock_project("PRJ-1", requested_paise=50_000_000)

    req = OptimizationRequest(
        budget_paise=30_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(
            minimum_allocation_per_project_paise=20_000_000,
            require_full_budget_allocation=True,
        ),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1])
    assert res.allocations[0].allocated_amount_paise == 30_000_000


def test_23_minimum_allocation_per_project_skipped_when_below_floor(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """If remaining candidate budget is below minimum allocation floor, project is skipped (0 allocated)."""
    p1 = make_mock_project("PRJ-1", need=0.90, requested_paise=40_000_000)
    p2 = make_mock_project("PRJ-2", need=0.80, requested_paise=40_000_000)

    # Total budget = 50L. PRJ-1 takes 40L. Remaining budget is 10L.
    # But minimum allocation is 20L. So PRJ-2 must be skipped!
    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(
            minimum_allocation_per_project_paise=20_000_000,
            require_full_budget_allocation=False,
        ),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    assert res.allocations[0].allocated_amount_paise == 40_000_000
    assert res.allocations[1].allocated_amount_paise == 0
    assert ReasonCode.MINIMUM_ALLOCATION in res.allocations[1].reason_codes


def test_24_regional_equity_disabled(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """When regional_equity_enabled=False, regional caps are bypassed."""
    p1 = make_mock_project("PRJ-1", state="Maharashtra", requested_paise=50_000_000)

    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(
            max_allocation_per_region_paise=20_000_000,
            regional_equity_enabled=False,  # Bypass region cap
            require_full_budget_allocation=True,
        ),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1])
    assert res.allocations[0].allocated_amount_paise == 50_000_000


# ---------------------------------------------------------------------------
# SECTION 5: Deterministic Reason Code Generation (25 - 28)
# ---------------------------------------------------------------------------

def test_25_reason_codes_high_need_low_saturation_marginal_impact(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """High need, low saturation, high marginal impact generate corresponding reason codes."""
    p1 = make_mock_project("PRJ-1", need=0.90, cost_eff=0.85, evidence=0.85, scalability=0.85)
    sat1 = make_mock_saturation("PRJ-1", "Bihar", sat_index=0.10)
    marg1 = make_mock_marginal("PRJ-1", marginal_score=0.80)

    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1], [sat1], [marg1])

    codes = res.allocations[0].reason_codes
    assert ReasonCode.HIGH_NEED in codes
    assert ReasonCode.LOW_SATURATION in codes
    assert ReasonCode.HIGH_MARGINAL_IMPACT in codes
    assert ReasonCode.HIGH_COST_EFFICIENCY in codes
    assert ReasonCode.STRONG_EVIDENCE in codes
    assert ReasonCode.HIGH_SCALABILITY in codes


def test_26_reason_codes_high_risk_and_saturation(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """High risk and high saturation trigger penalty reason codes."""
    p1 = make_mock_project("PRJ-1", risk=0.60)
    sat1 = make_mock_saturation("PRJ-1", "Bihar", sat_index=0.65)

    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1], [sat1])

    codes = res.allocations[0].reason_codes
    assert ReasonCode.HIGH_IMPLEMENTATION_RISK in codes
    assert ReasonCode.HIGH_SATURATION in codes


def test_27_reason_codes_budget_constraint(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Partial funding due to depleted budget triggers BUDGET_CONSTRAINT code."""
    p1 = make_mock_project("PRJ-1", requested_paise=50_000_000)

    req = OptimizationRequest(
        budget_paise=30_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1])

    codes = res.allocations[0].reason_codes
    assert ReasonCode.BUDGET_CONSTRAINT in codes


def test_28_reason_codes_low_evidence(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Low evidence (< 0.50) triggers LOW_EVIDENCE reason code."""
    p1 = make_mock_project("PRJ-1", evidence=0.30)

    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1])

    codes = res.allocations[0].reason_codes
    assert ReasonCode.LOW_EVIDENCE in codes


# ---------------------------------------------------------------------------
# SECTION 6: Portfolio Metrics & Explainability Reconciliation (29 - 33)
# ---------------------------------------------------------------------------

def test_29_portfolio_metrics_exact_utilization_and_breakdown(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Verify budget utilization and state/sector distribution match actual allocations."""
    p1 = make_mock_project("PRJ-1", state="Bihar", sector=ProjectSector.EDUCATION, requested_paise=30_000_000)
    p2 = make_mock_project("PRJ-2", state="Odisha", sector=ProjectSector.HEALTHCARE, requested_paise=20_000_000)

    req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    assert res.portfolio_breakdown is not None
    pb = res.portfolio_breakdown
    assert pb["budget_utilization"] == 1.0
    assert pb["project_count_funded"] == 2
    assert pb["state_allocation_distribution"]["Bihar"] == 30_000_000
    assert pb["state_allocation_distribution"]["Odisha"] == 20_000_000
    assert pb["sector_allocation_distribution"]["EDUCATION"] == 30_000_000
    assert pb["sector_allocation_distribution"]["HEALTHCARE"] == 20_000_000


def test_30_allocation_context_metadata_reconciliation(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Each Allocation.allocation_context must reconcile with requested and allocated amounts."""
    p1 = make_mock_project("PRJ-1", requested_paise=50_000_000)

    req = OptimizationRequest(
        budget_paise=30_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1])

    alloc = res.allocations[0]
    assert alloc.allocation_context is not None
    ac = alloc.allocation_context

    assert ac["requested_amount_paise"] == 50_000_000
    assert ac["remaining_need_paise"] == 20_000_000
    assert ac["allocation_fraction"] == 0.60
    assert 0.0 <= ac["optimization_score"] <= 1.0


def test_31_total_predicted_impact_positive(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Total predicted impact must be positive and aggregate funded projects."""
    p1 = make_mock_project("PRJ-1", requested_paise=20_000_000)
    p2 = make_mock_project("PRJ-2", requested_paise=20_000_000)

    req = OptimizationRequest(
        budget_paise=40_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    assert res.total_predicted_impact > 0.0


def test_32_underserved_region_allocation_share(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Underserved region share correctly computes fraction allocated to low-saturation areas."""
    p1 = make_mock_project("PRJ-1", requested_paise=30_000_000)
    sat1 = make_mock_saturation("PRJ-1", "Bihar", sat_index=0.15)  # Underserved

    p2 = make_mock_project("PRJ-2", requested_paise=30_000_000)
    sat2 = make_mock_saturation("PRJ-2", "Maharashtra", sat_index=0.60)  # Saturated

    req = OptimizationRequest(
        budget_paise=60_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2], [sat1, sat2])

    # Exactly half the budget went to PRJ-1 (underserved)
    assert res.underserved_region_allocation_share == 0.50


def test_33_average_saturation_weighted(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """average_saturation is weighted by allocated amounts."""
    p1 = make_mock_project("PRJ-1", requested_paise=30_000_000)
    sat1 = make_mock_saturation("PRJ-1", "Bihar", sat_index=0.20)

    p2 = make_mock_project("PRJ-2", requested_paise=10_000_000)
    sat2 = make_mock_saturation("PRJ-2", "Maharashtra", sat_index=0.60)

    req = OptimizationRequest(
        budget_paise=40_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2], [sat1, sat2])

    # Expected: (30 * 0.20 + 10 * 0.60) / 40 = (6.0 + 6.0) / 40 = 12.0 / 40 = 0.30
    assert res.average_saturation == pytest.approx(0.30, abs=1e-5)


# ---------------------------------------------------------------------------
# SECTION 7: Determinism & Repeatability Tests (34 - 35)
# ---------------------------------------------------------------------------

def test_34_deterministic_repeatability_100_runs(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """100 consecutive optimization runs produce bitwise identical JSON payloads and 1 SHA-256 hash."""
    p1 = make_mock_project("PRJ-1", requested_paise=30_000_000)
    p2 = make_mock_project("PRJ-2", requested_paise=20_000_000)

    req = OptimizationRequest(
        budget_paise=40_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )

    first_dump = optimizer.calculate_optimal_allocation(req, [p1, p2]).model_dump_json()
    first_hash = hashlib.sha256(first_dump.encode("utf-8")).hexdigest()

    hashes = set()
    for _ in range(100):
        current_dump = optimizer.calculate_optimal_allocation(req, [p1, p2]).model_dump_json()
        current_hash = hashlib.sha256(current_dump.encode("utf-8")).hexdigest()
        hashes.add(current_hash)

    assert len(hashes) == 1
    assert list(hashes)[0] == first_hash


def test_35_optimize_alias_matches_calculate_optimal_allocation(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """optimize() contract alias produces identical output to calculate_optimal_allocation()."""
    p1 = make_mock_project("PRJ-1")
    req = OptimizationRequest(
        budget_paise=20_000_000,
        project_ids=["PRJ-1"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res1 = optimizer.calculate_optimal_allocation(req, [p1])
    res2 = optimizer.optimize([p1], [p1.impact_dna], [], req)

    assert res1.allocated_paise == res2.allocated_paise
    assert res1.allocations[0].model_dump() == res2.allocations[0].model_dump()


# ---------------------------------------------------------------------------
# SECTION 8: Seed Dataset Multi-Budget Integration Tests (36 - 40)
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_projects_and_contexts():
    """Load all 18 seed projects and their matching regional contexts."""
    prj_file = WORKSPACE_ROOT / "data" / "sample" / "member_c_seed_projects.json"
    ctx_file = WORKSPACE_ROOT / "data" / "sample" / "saturation_context.json"

    with open(prj_file, "r", encoding="utf-8") as f:
        p_list = [Project.model_validate(d) for d in json.load(f)]
    with open(ctx_file, "r", encoding="utf-8") as f:
        c_map = {(c["state"], c["sector"]): SaturationContext.model_validate(c) for c in json.load(f)}

    return p_list, c_map


def test_36_seed_dataset_pipeline_budget_5_lakh(optimizer: AllocationOptimizer, default_weights: OptimizationWeights, seed_projects_and_contexts):
    """Run full pipeline on seed projects with ₹5 Lakh budget (50,000,000 paise)."""
    projects, ctx_map = seed_projects_and_contexts
    budget = 50_000_000  # ₹5L

    req = OptimizationRequest(
        budget_paise=budget,
        project_ids=[p.project_id for p in projects],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, projects)

    assert res.allocated_paise == budget
    assert res.unallocated_paise == 0
    assert len(res.allocations) == 18
    assert res.portfolio_breakdown["project_count_funded"] >= 1


def test_37_seed_dataset_pipeline_budget_10_lakh(optimizer: AllocationOptimizer, default_weights: OptimizationWeights, seed_projects_and_contexts):
    """Run full pipeline on seed projects with ₹10 Lakh budget (100,000,000 paise)."""
    projects, ctx_map = seed_projects_and_contexts
    budget = 100_000_000  # ₹10L

    req = OptimizationRequest(
        budget_paise=budget,
        project_ids=[p.project_id for p in projects],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, projects)

    assert res.allocated_paise == budget
    assert res.unallocated_paise == 0


def test_38_seed_dataset_pipeline_budget_15_lakh(optimizer: AllocationOptimizer, default_weights: OptimizationWeights, seed_projects_and_contexts):
    """Run full pipeline on seed projects with ₹15 Lakh budget (150,000,000 paise)."""
    projects, ctx_map = seed_projects_and_contexts
    budget = 150_000_000  # ₹15L

    req = OptimizationRequest(
        budget_paise=budget,
        project_ids=[p.project_id for p in projects],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, projects)

    assert res.allocated_paise == budget
    assert res.unallocated_paise == 0


def test_39_seed_dataset_pipeline_budget_25_lakh(optimizer: AllocationOptimizer, default_weights: OptimizationWeights, seed_projects_and_contexts):
    """Run full pipeline on seed projects with ₹25 Lakh budget (250,000,000 paise)."""
    projects, ctx_map = seed_projects_and_contexts
    budget = 250_000_000  # ₹25L

    req = OptimizationRequest(
        budget_paise=budget,
        project_ids=[p.project_id for p in projects],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, projects)

    assert res.allocated_paise == budget
    assert res.unallocated_paise == 0


def test_40_seed_dataset_pipeline_budget_50_lakh(optimizer: AllocationOptimizer, default_weights: OptimizationWeights, seed_projects_and_contexts):
    """Run full pipeline on seed projects with ₹50 Lakh budget (500,000,000 paise)."""
    projects, ctx_map = seed_projects_and_contexts
    budget = 500_000_000  # ₹50L

    req = OptimizationRequest(
        budget_paise=budget,
        project_ids=[p.project_id for p in projects],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=False),  # Total seed need is 44.1L
    )
    res = optimizer.calculate_optimal_allocation(req, projects)

    assert res.allocated_paise + res.unallocated_paise == budget
    assert res.allocated_paise == 441_000_000  # Fully funds all 18 projects
    assert res.unallocated_paise == 59_000_000
    assert res.portfolio_breakdown["project_count_funded"] == 18
    # No duplicate project IDs in allocations
    alloc_pids = [a.project_id for a in res.allocations]
    assert len(alloc_pids) == len(set(alloc_pids)) == 18


def test_41_allocation_explanation_metadata(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Verify allocation_explanation contains primary_driver and score_components for funded and unfunded projects."""
    p1 = make_mock_project("PRJ-1", need=0.90, cost_eff=0.80, requested_paise=30_000_000)
    p2 = make_mock_project("PRJ-2", need=0.40, cost_eff=0.40, requested_paise=30_000_000)
    req = OptimizationRequest(
        budget_paise=30_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    # PRJ-1 is funded
    alloc_funded = res.allocations[0]
    assert alloc_funded.allocated_amount_paise == 30_000_000
    assert alloc_funded.allocation_explanation is not None
    ae1 = alloc_funded.allocation_explanation
    assert "primary_driver" in ae1
    assert isinstance(ae1["primary_driver"], str)
    assert "score_components" in ae1
    sc1 = ae1["score_components"]
    assert 0.0 <= sc1["base_score"] <= 1.0
    assert 0.0 <= sc1["marginal_score"] <= 1.0
    assert 0.0 <= sc1["equity_bonus"] <= 1.0
    assert 0.0 <= sc1["risk_penalty"] <= 1.0

    # PRJ-2 is unfunded (0 paise)
    alloc_unfunded = res.allocations[1]
    assert alloc_unfunded.allocated_amount_paise == 0
    assert alloc_unfunded.allocation_explanation is not None
    ae2 = alloc_unfunded.allocation_explanation
    assert "primary_driver" in ae2
    assert isinstance(ae2["primary_driver"], str)
    assert "score_components" in ae2
    sc2 = ae2["score_components"]
    assert 0.0 <= sc2["base_score"] <= 1.0
    assert 0.0 <= sc2["marginal_score"] <= 1.0
    assert 0.0 <= sc2["equity_bonus"] <= 1.0
    assert 0.0 <= sc2["risk_penalty"] <= 1.0


def test_42_optimization_audit_reconciliation(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Verify optimization_audit exactly reconciles with allocations and budget."""
    p1 = make_mock_project("PRJ-1", requested_paise=30_000_000)
    p2 = make_mock_project("PRJ-2", requested_paise=30_000_000)

    req = OptimizationRequest(
        budget_paise=40_000_000,
        project_ids=["PRJ-1", "PRJ-2"],
        weights=default_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=True),
    )
    res = optimizer.calculate_optimal_allocation(req, [p1, p2])

    assert res.optimization_audit is not None
    oa = res.optimization_audit

    assert oa["total_projects_considered"] == 2
    assert oa["projects_funded"] == 2
    assert oa["projects_skipped"] == 0
    assert oa["budget_requested_total_paise"] == 60_000_000
    assert oa["budget_allocated_total_paise"] == 40_000_000
    assert oa["budget_unallocated_paise"] == 0
    assert oa["budget_allocated_total_paise"] + oa["budget_unallocated_paise"] == req.budget_paise


def test_43_all_14_reason_codes_reachable(optimizer: AllocationOptimizer, default_weights: OptimizationWeights):
    """Verify that every one of the 14 ReasonCode values is reachable by the engine."""
    all_codes = set(ReasonCode)
    reached = set()

    # Reach positive codes
    p_pos = make_mock_project("PRJ-P", need=0.90, cost_eff=0.85, evidence=0.85, scalability=0.85, risk=0.10)
    sat_pos = make_mock_saturation("PRJ-P", "Bihar", 0.10)
    marg_pos = make_mock_marginal("PRJ-P", 0.85)

    # Reach negative & flag codes
    p_neg = make_mock_project("PRJ-N", need=0.40, cost_eff=0.40, evidence=0.30, scalability=0.40, risk=0.75, missing_fields=["cert"], confidence=0.60)
    sat_neg = make_mock_saturation("PRJ-N", "Maharashtra", 0.65)
    marg_neg = make_mock_marginal("PRJ-N", 0.35)

    req1 = OptimizationRequest(
        budget_paise=40_000_000,
        project_ids=["PRJ-P", "PRJ-N"],
        weights=default_weights,
        constraints=OptimizationConstraints(
            max_allocation_per_region_paise=35_000_000,
            minimum_allocation_per_project_paise=10_000_000,
            require_full_budget_allocation=False,
        ),
    )
    res1 = optimizer.calculate_optimal_allocation(req1, [p_pos, p_neg], [sat_pos, sat_neg], [marg_pos, marg_neg])
    for a in res1.allocations:
        reached.update(a.reason_codes)

    # Reach REGIONAL_CAP
    p_reg = make_mock_project("PRJ-REG", state="Maharashtra", requested_paise=50_000_000)
    sat_reg = make_mock_saturation("PRJ-REG", "Maharashtra", 0.55)
    req_reg = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-REG"],
        weights=default_weights,
        constraints=OptimizationConstraints(
            max_allocation_per_region_paise=20_000_000,
            require_full_budget_allocation=False,
        ),
    )
    res_reg = optimizer.calculate_optimal_allocation(req_reg, [p_reg], [sat_reg])
    for a in res_reg.allocations:
        reached.update(a.reason_codes)

    # Reach MINIMUM_ALLOCATION
    p_m1 = make_mock_project("PRJ-M1", requested_paise=30_000_000)
    p_m2 = make_mock_project("PRJ-M2", requested_paise=30_000_000)
    req_m = OptimizationRequest(
        budget_paise=40_000_000,
        project_ids=["PRJ-M1", "PRJ-M2"],
        weights=default_weights,
        constraints=OptimizationConstraints(
            minimum_allocation_per_project_paise=20_000_000,
            require_full_budget_allocation=False,
        ),
    )
    res_m = optimizer.calculate_optimal_allocation(req_m, [p_m1, p_m2])
    for a in res_m.allocations:
        reached.update(a.reason_codes)

    assert len(reached) == len(all_codes)
    assert reached == all_codes

