"""Phase 1 Verification Test Suite for AllocateAI Decision Engine (Member C).

Validates strict adherence to Software Contract v1.0 and Technical Contract v1.0.
Every checklist item is tested exhaustively with deterministic checks.
"""

import importlib
import json
from pathlib import Path
import sys
import pytest
from pydantic import ValidationError

from backend.app.engine import (
    API_VERSION,
    CALCULATION_VERSIONS,
    DEFAULT_MARGINAL_INCREMENT_PAISE,
    DNA_SCHEMA_VERSION,
    MARGINAL_CALCULATION_VERSION,
    OPTIMIZER_CALCULATION_VERSION,
    PAISE_PER_LAKH,
    PAISE_PER_RUPEE,
    PROJECT_SCHEMA_VERSION,
    RUPEES_PER_LAKH,
    SATURATION_CALCULATION_VERSION,
    Allocation,
    AllocationOptimizer,
    AllocationStatus,
    BeneficiaryProfile,
    BudgetValidationError,
    CalculationVersionError,
    ConfidenceLevel,
    ConstraintEngine,
    ConstraintViolationError,
    DecisionEngineError,
    DueDiligenceRisk,
    Financials,
    Geography,
    ImpactDNA,
    ImpactMetric,
    InvalidProjectDataError,
    MarginalImpactEngine,
    MarginalImpactResult,
    OptimizationConstraints,
    OptimizationRequest,
    OptimizationResult,
    OptimizationStatus,
    OptimizationWeights,
    Project,
    ProjectPerformanceUpdate,
    ProjectSector,
    ProposalStatus,
    ReasonCode,
    ReallocationRequest,
    ReallocationResult,
    SaturationContext,
    SaturationEngine,
    SaturationResult,
    ScoringEngine,
    VerificationStatus,
    WeightValidationError,
    clip_score,
    normalize_weights,
    safe_division,
    validate_budget,
    validate_calculation_version,
    validate_paise,
    validate_score,
    validate_weights,
)


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


# ===========================================================================
# 1. Repository Structure & Required Files Checklist
# ===========================================================================

def test_checklist_repository_structure_and_files_exist():
    """Verify that all required files and subdirectories exist exactly as specified."""
    required_files = [
        "backend/app/engine/__init__.py",
        "backend/app/engine/constants.py",
        "backend/app/engine/exceptions.py",
        "backend/app/engine/utils.py",
        "backend/app/engine/schemas.py",
        "backend/app/engine/scoring/__init__.py",
        "backend/app/engine/saturation/__init__.py",
        "backend/app/engine/marginal_impact/__init__.py",
        "backend/app/engine/optimizer/__init__.py",
        "backend/app/engine/constraints/__init__.py",
        "data/sample/member_c_seed_projects.json",
        "docs/models/csr-saturation.md",
        "docs/models/marginal-impact.md",
        "docs/models/optimizer.md",
    ]

    for rel_path in required_files:
        full_path = WORKSPACE_ROOT / rel_path
        assert full_path.exists(), f"Required file missing: {rel_path}"
        assert full_path.is_file(), f"Path is not a regular file: {rel_path}"


# ===========================================================================
# 2. Package Imports & No Circular Imports
# ===========================================================================

def test_checklist_modules_import_cleanly_and_no_circular_dependencies():
    """Verify that every module imports successfully with clean dependencies."""
    module_names = [
        "backend.app.engine.constants",
        "backend.app.engine.exceptions",
        "backend.app.engine.utils",
        "backend.app.engine.schemas",
        "backend.app.engine.scoring",
        "backend.app.engine.saturation",
        "backend.app.engine.marginal_impact",
        "backend.app.engine.optimizer",
        "backend.app.engine.constraints",
        "backend.app.engine",
    ]

    for mod in module_names:
        if mod in sys.modules:
            del sys.modules[mod]
        loaded = importlib.import_module(mod)
        assert loaded is not None, f"Failed to import {mod}"


# ===========================================================================
# 3. Rule 2 — Zero LLM or AI Inference Calls
# ===========================================================================

def test_checklist_zero_llm_imports_or_ai_calls():
    """Verify that no LLM/AI libraries or API clients are imported anywhere in engine."""
    engine_dir = WORKSPACE_ROOT / "backend" / "app" / "engine"
    forbidden_tokens = [
        "openai",
        "gemini",
        "google.generativeai",
        "anthropic",
        "langchain",
        "cohere",
        "transformers",
        "huggingface",
        "prompt_template",
    ]

    for py_file in engine_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8").lower()
        for token in forbidden_tokens:
            assert f"import {token}" not in content, f"Forbidden import '{token}' found in {py_file.name}"
            assert f"from {token}" not in content, f"Forbidden import '{token}' found in {py_file.name}"


# ===========================================================================
# 4. Phase 1 Skeleton — No Calculation Logic Yet
# ===========================================================================

def test_checklist_no_calculation_logic_exists_in_phase_1():
    """Ensure engine classes define clean interfaces and raise NotImplementedError."""
    scoring = ScoringEngine()
    dummy_geo = Geography(state="Bihar", district="Gaya")
    dummy_profile = BeneficiaryProfile(target_count=1000)
    dummy_fin = Financials(requested_amount_paise=10_000_000)
    dummy_project = Project(
        project_id="PRJ-TEST",
        name="Test",
        ngo_id="NGO-TEST",
        sector=ProjectSector.EDUCATION,
        geographies=[dummy_geo],
        beneficiary_profile=dummy_profile,
        financials=dummy_fin,
        duration_months=12,
    )
    dummy_dna = ImpactDNA(
        dna_id="DNA-TEST",
        project_id="PRJ-TEST",
        need_score=0.8,
        expected_impact_score=0.8,
        cost_efficiency_score=0.8,
        evidence_strength_score=0.8,
        scalability_score=0.8,
        implementation_risk_score=0.2,
        beneficiary_reach=1000,
        estimated_impact_per_lakh=40.0,
        extraction_confidence=0.90,
        model_name="dna-v1",
        prompt_version="v1.0",
    )
    dummy_weights = OptimizationWeights(
        need=0.2, marginal_impact=0.3, cost_efficiency=0.1,
        evidence=0.1, scalability=0.1, equity=0.1, risk_penalty=0.1
    )

    # In Phase 2, ScoringEngine calculates the score deterministically
    calculated_score = scoring.calculate_base_score(dummy_project, dummy_dna, dummy_weights)
    assert 0.0 <= calculated_score <= 1.0

    saturation = SaturationEngine()
    context = SaturationContext(state="Bihar", sector=ProjectSector.EDUCATION)
    dummy_project.impact_dna = dummy_dna
    # In Phase 3, SaturationEngine calculates saturation deterministically
    sat_res = saturation.calculate(dummy_project, context)
    assert 0.0 <= sat_res.saturation_index <= 1.0

    marginal = MarginalImpactEngine()
    # In Phase 4, MarginalImpactEngine calculates marginal impact deterministically
    marg_res = marginal.calculate(dummy_project, increment_paise=10_000_000, saturation_result=sat_res)
    assert 0.0 <= marg_res.marginal_impact_score <= 1.0

    optimizer = AllocationOptimizer()
    opt_req = OptimizationRequest(
        budget_paise=50_000_000,
        project_ids=["PRJ-TEST"],
        weights=dummy_weights,
        constraints=OptimizationConstraints(require_full_budget_allocation=False),
    )
    opt_res = optimizer.optimize([dummy_project], [dummy_dna], [sat_res], opt_req)
    assert opt_res.allocated_paise <= opt_req.budget_paise

    constraint_engine = ConstraintEngine()
    constraint_engine.validate_constraints(opt_req, [dummy_project])


# ===========================================================================
# 5. Shared Enums & Technical Contract Exact Match
# ===========================================================================

def test_checklist_enum_values_exactly_match_contract():
    """Verify all enums exactly match the Technical Contract Section 6."""
    expected_sectors = {
        "EDUCATION", "HEALTHCARE", "POVERTY_HUNGER", "ENVIRONMENT",
        "RURAL_DEVELOPMENT", "GENDER_EQUALITY", "LIVELIHOOD",
        "DISASTER_RELIEF", "SPORTS", "ART_CULTURE", "OTHER"
    }
    assert {s.value for s in ProjectSector} == expected_sectors

    expected_reasons = {
        "HIGH_NEED", "LOW_SATURATION", "HIGH_MARGINAL_IMPACT", "HIGH_COST_EFFICIENCY",
        "STRONG_EVIDENCE", "HIGH_SCALABILITY", "HIGH_IMPLEMENTATION_RISK",
        "LOW_EVIDENCE", "HIGH_SATURATION", "BUDGET_CONSTRAINT", "REGIONAL_CAP",
        "MINIMUM_ALLOCATION", "MISSING_DATA", "DUE_DILIGENCE_FLAG"
    }
    assert {r.value for r in ReasonCode} == expected_reasons

    expected_opt_status = {"QUEUED", "RUNNING", "COMPLETED", "FAILED"}
    assert {s.value for s in OptimizationStatus} == expected_opt_status

    expected_alloc_status = {"PROPOSED", "APPROVED", "REJECTED", "REALLOCATED"}
    assert {s.value for s in AllocationStatus} == expected_alloc_status

    expected_verif_status = {"VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "MISSING", "FLAGGED"}
    assert {s.value for s in VerificationStatus} == expected_verif_status

    expected_confidence = {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}
    assert {c.value for c in ConfidenceLevel} == expected_confidence

    expected_risk = {"LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"}
    assert {r.value for r in DueDiligenceRisk} == expected_risk


# ===========================================================================
# 6. Rule 3 — Calculation Version Constants
# ===========================================================================

def test_checklist_version_constants_match_contract():
    """Verify calculation version constants exactly match Rule 3."""
    assert PROJECT_SCHEMA_VERSION == "project-v1"
    assert DNA_SCHEMA_VERSION == "dna-v1"
    assert SATURATION_CALCULATION_VERSION == "saturation-v1"
    assert MARGINAL_CALCULATION_VERSION == "marginal-v1"
    assert OPTIMIZER_CALCULATION_VERSION == "optimizer-v1"
    assert API_VERSION == "api-v1"
    assert CALCULATION_VERSIONS["project"] == "project-v1"
    assert CALCULATION_VERSIONS["dna"] == "dna-v1"
    assert CALCULATION_VERSIONS["saturation"] == "saturation-v1"
    assert CALCULATION_VERSIONS["marginal"] == "marginal-v1"
    assert CALCULATION_VERSIONS["optimizer"] == "optimizer-v1"
    assert CALCULATION_VERSIONS["api"] == "api-v1"


# ===========================================================================
# 7. Rule 4 — Money Representation as Integer Paise
# ===========================================================================

def test_checklist_money_represented_as_integer_paise():
    """Verify money fields strictly enforce integer paise without floats."""
    assert PAISE_PER_RUPEE == 100
    assert RUPEES_PER_LAKH == 100_000
    assert PAISE_PER_LAKH == 10_000_000
    assert DEFAULT_MARGINAL_INCREMENT_PAISE == 10_000_000

    # validate_paise helper rejects floats
    with pytest.raises(BudgetValidationError):
        validate_paise(100.50, name="amount_paise")

    with pytest.raises(BudgetValidationError):
        validate_paise(True, name="amount_paise")

    with pytest.raises(BudgetValidationError):
        validate_paise(-100, name="amount_paise")

    assert validate_paise(10_000_000) == 10_000_000
    assert validate_paise(0, allow_zero=True) == 0

    # Financials Pydantic model rejects floats
    with pytest.raises(ValidationError):
        Financials(requested_amount_paise=1000.50)  # type: ignore


# ===========================================================================
# 8. Rule 1 — No Contract Fields Renamed
# ===========================================================================

def test_checklist_no_contract_fields_renamed():
    """Verify exact field names as specified in Technical Contract."""
    # Project
    p_fields = Project.model_fields
    assert "project_id" in p_fields
    assert "name" in p_fields
    assert "ngo_id" in p_fields
    assert "sector" in p_fields
    assert "geographies" in p_fields
    assert "beneficiary_profile" in p_fields
    assert "financials" in p_fields
    assert "duration_months" in p_fields
    assert "impact_metrics" in p_fields
    assert "schema_version" in p_fields

    # ImpactDNA
    dna_fields = ImpactDNA.model_fields
    assert "dna_id" in dna_fields
    assert "project_id" in dna_fields
    assert "need_score" in dna_fields
    assert "expected_impact_score" in dna_fields
    assert "cost_efficiency_score" in dna_fields
    assert "evidence_strength_score" in dna_fields
    assert "scalability_score" in dna_fields
    assert "implementation_risk_score" in dna_fields
    assert "beneficiary_reach" in dna_fields
    assert "estimated_impact_per_lakh" in dna_fields
    assert "schema_version" in dna_fields

    # SaturationResult
    sat_fields = SaturationResult.model_fields
    assert "project_id" in sat_fields
    assert "state" in sat_fields
    assert "sector" in sat_fields
    assert "saturation_index" in sat_fields
    assert "need_score" in sat_fields
    assert "existing_csr_amount_paise" in sat_fields
    assert "estimated_beneficiary_coverage" in sat_fields
    assert "calculation_version" in sat_fields

    # MarginalImpactResult
    mar_fields = MarginalImpactResult.model_fields
    assert "project_id" in mar_fields
    assert "increment_paise" in mar_fields
    assert "baseline_budget_paise" in mar_fields
    assert "projected_budget_paise" in mar_fields
    assert "marginal_impact_score" in mar_fields
    assert "diminishing_return_factor" in mar_fields
    assert "calculation_version" in mar_fields

    # OptimizationRequest
    req_fields = OptimizationRequest.model_fields
    assert "budget_paise" in req_fields
    assert "project_ids" in req_fields
    assert "weights" in req_fields
    assert "constraints" in req_fields
    assert "marginal_increment_paise" in req_fields

    # Allocation
    alloc_fields = Allocation.model_fields
    assert "project_id" in alloc_fields
    assert "allocated_amount_paise" in alloc_fields
    assert "marginal_impact_score" in alloc_fields
    assert "base_score" in alloc_fields
    assert "saturation_index" in alloc_fields
    assert "reason_codes" in alloc_fields
    assert "rank" in alloc_fields
    assert "status" in alloc_fields

    # OptimizationResult
    res_fields = OptimizationResult.model_fields
    assert "run_id" in res_fields
    assert "status" in res_fields
    assert "budget_paise" in res_fields
    assert "allocated_paise" in res_fields
    assert "unallocated_paise" in res_fields
    assert "allocations" in res_fields
    assert "total_predicted_impact" in res_fields
    assert "average_saturation" in res_fields
    assert "underserved_region_allocation_share" in res_fields
    assert "calculation_versions" in res_fields


# ===========================================================================
# 9. Pydantic Models Instantiation & Field Validation
# ===========================================================================

def test_checklist_pydantic_models_instantiate_and_validate():
    """Verify all Pydantic models instantiate and validate bounds properly."""
    weights = OptimizationWeights(
        need=0.25, marginal_impact=0.25, cost_efficiency=0.15,
        evidence=0.15, scalability=0.10, equity=0.05, risk_penalty=0.05
    )
    assert weights.need == 0.25
    assert len(weights.to_dict()) == 7

    constraints = OptimizationConstraints(
        max_allocation_per_project_paise=50_000_000,
        require_full_budget_allocation=True,
        regional_equity_enabled=True,
    )
    assert constraints.max_allocation_per_project_paise == 50_000_000

    request = OptimizationRequest(
        budget_paise=100_000_000,
        project_ids=["PRJ-0001", "PRJ-0002"],
        weights=weights,
        constraints=constraints,
    )
    assert request.budget_paise == 100_000_000
    assert request.marginal_increment_paise == 10_000_000

    allocation = Allocation(
        project_id="PRJ-0001",
        allocated_amount_paise=50_000_000,
        marginal_impact_score=0.88,
        base_score=0.82,
        saturation_index=0.23,
        reason_codes=[ReasonCode.HIGH_MARGINAL_IMPACT, ReasonCode.LOW_SATURATION],
        rank=1,
        status=AllocationStatus.PROPOSED,
    )
    assert allocation.status == AllocationStatus.PROPOSED
    assert allocation.rank == 1

    opt_result = OptimizationResult(
        run_id="OPT-0001",
        status=OptimizationStatus.COMPLETED,
        budget_paise=100_000_000,
        allocated_paise=100_000_000,
        unallocated_paise=0,
        allocations=[allocation],
        total_predicted_impact=840.5,
        average_saturation=0.23,
        underserved_region_allocation_share=1.0,
        weights=weights,
        constraints=constraints,
        calculation_versions=CALCULATION_VERSIONS,
        created_at="2026-09-03T12:00:00Z",
    )
    assert opt_result.run_id == "OPT-0001"
    assert opt_result.status == OptimizationStatus.COMPLETED

    perf_update = ProjectPerformanceUpdate(
        project_id="PRJ-0001",
        actual_beneficiaries=5000,
        actual_spend_paise=30_000_000,
        progress_percent=85.0,
    )
    assert perf_update.actual_spend_paise == 30_000_000

    realloc_req = ReallocationRequest(
        previous_run_id="OPT-0001",
        budget_paise=100_000_000,
        performance_updates=[perf_update],
        weights=weights,
        constraints=constraints,
    )
    assert realloc_req.previous_run_id == "OPT-0001"

    realloc_res = ReallocationResult(
        run_id="REA-0001",
        previous_run_id="OPT-0001",
        old_allocations=[allocation],
        new_allocations=[allocation],
        changed_projects=["PRJ-0001"],
        total_budget_shifted_paise=10_000_000,
        explanation=["Performance update increased marginal priority"],
        calculation_versions=CALCULATION_VERSIONS,
        created_at="2026-09-03T12:30:00Z",
    )
    assert realloc_res.total_budget_shifted_paise == 10_000_000


# ===========================================================================
# 10. Checklist Specific Exception Tests
# ===========================================================================

def test_checklist_invalid_score_raises_validation_error():
    """Verify that scores outside [0.0, 1.0] raise ValidationError in models and utils."""
    # In Pydantic model
    with pytest.raises(ValidationError):
        OptimizationWeights(
            need=1.5, marginal_impact=0.2, cost_efficiency=0.1,  # need > 1.0
            evidence=0.1, scalability=0.1, equity=0.1, risk_penalty=0.1
        )

    with pytest.raises(ValidationError):
        OptimizationWeights(
            need=-0.1, marginal_impact=0.2, cost_efficiency=0.1,  # need < 0.0
            evidence=0.1, scalability=0.1, equity=0.1, risk_penalty=0.1
        )

    # In validate_score utility
    with pytest.raises(InvalidProjectDataError):
        validate_score(1.2, name="need_score")

    with pytest.raises(InvalidProjectDataError):
        validate_score(-0.05, name="need_score")

    with pytest.raises(InvalidProjectDataError):
        validate_score(float("nan"), name="need_score")


def test_checklist_invalid_weights_raise_weight_validation_error():
    """Verify that invalid weights raise WeightValidationError."""
    # Out of bounds weight
    with pytest.raises(WeightValidationError):
        validate_weights({"need": 1.5, "impact": 0.5})

    # Negative weight
    with pytest.raises(WeightValidationError):
        validate_weights({"need": -0.2, "impact": 1.2})

    # Weights sum to 0.70 instead of 1.0
    with pytest.raises(WeightValidationError) as excinfo:
        validate_weights({"need": 0.4, "impact": 0.3})
    assert excinfo.value.weight_sum == pytest.approx(0.7)


def test_checklist_invalid_budget_raises_budget_validation_error():
    """Verify that invalid budget raises BudgetValidationError."""
    # Negative budget
    with pytest.raises(BudgetValidationError):
        validate_budget(-1_000_000)

    # Zero budget
    with pytest.raises(BudgetValidationError):
        validate_budget(0)

    # Float budget
    with pytest.raises(BudgetValidationError):
        validate_budget(5000.75)  # type: ignore

    # In OptimizationRequest, invalid budget raises ValidationError / BudgetValidationError
    with pytest.raises((BudgetValidationError, ValidationError)):
        OptimizationRequest(
            budget_paise=-1000,
            project_ids=["PRJ-0001"],
            weights=OptimizationWeights(
                need=0.2, marginal_impact=0.3, cost_efficiency=0.1,
                evidence=0.1, scalability=0.1, equity=0.1, risk_penalty=0.1
            ),
            constraints=OptimizationConstraints(),
        )


def test_checklist_calculation_version_validation():
    """Verify validate_calculation_version raises CalculationVersionError on mismatch."""
    validate_calculation_version("saturation-v1", "saturation-v1")
    with pytest.raises(CalculationVersionError):
        validate_calculation_version("saturation-v2", "saturation-v1")


def test_checklist_utility_functions_deterministic_behavior():
    """Verify deterministic clipping, division, and weight normalization."""
    assert clip_score(1.5) == 1.0
    assert clip_score(-0.5) == 0.0
    assert clip_score(0.73) == 0.73

    assert safe_division(100.0, 0.0, default=0.0) == 0.0
    assert safe_division(100.0, 4.0) == 25.0

    normalized = normalize_weights({"w1": 2.0, "w2": 3.0})
    assert normalized["w1"] == pytest.approx(0.4)
    assert normalized["w2"] == pytest.approx(0.6)
    assert sum(normalized.values()) == pytest.approx(1.0)


# ===========================================================================
# 11. Seed Dataset Loading & Validation Checklist
# ===========================================================================

def test_checklist_seed_dataset_loads_and_validates():
    """Verify seed JSON loads successfully and all projects validate against Project schema."""
    seed_file = WORKSPACE_ROOT / "data" / "sample" / "member_c_seed_projects.json"
    assert seed_file.exists(), "Seed dataset file missing"

    with open(seed_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Project count between 15-20
    assert 15 <= len(data) <= 20, f"Expected 15-20 projects, found {len(data)}"

    states_represented = set()
    sectors_represented = set()

    for item in data:
        # Every seed project validates against Project schema
        project = Project.model_validate(item)
        assert project.schema_version == "project-v1"
        assert project.duration_months > 0
        assert project.financials.requested_amount_paise > 0
        assert project.financials.current_funding_paise >= 0
        assert isinstance(project.financials.requested_amount_paise, int)

        # Beneficiary target count is non-negative integer
        assert project.beneficiary_profile.target_count >= 0

        # State representation
        for geo in project.geographies:
            states_represented.add(geo.state)

        # Sector representation
        sectors_represented.add(project.sector)

        # Validate embedded Impact DNA
        assert item.get("impact_dna") is not None, f"Missing impact_dna in {project.project_id}"
        dna = ImpactDNA.model_validate(item["impact_dna"])
        assert dna.project_id == project.project_id
        assert dna.schema_version == "dna-v1"
        assert 0.0 <= dna.need_score <= 1.0
        assert 0.0 <= dna.expected_impact_score <= 1.0
        assert 0.0 <= dna.cost_efficiency_score <= 1.0
        assert 0.0 <= dna.evidence_strength_score <= 1.0
        assert 0.0 <= dna.scalability_score <= 1.0
        assert 0.0 <= dna.implementation_risk_score <= 1.0
        assert dna.beneficiary_reach >= 0
        assert dna.estimated_impact_per_lakh >= 0

    # Verify 6+ states
    assert len(states_represented) >= 6, f"Expected 6+ states, found {len(states_represented)}: {states_represented}"

    # Verify required sectors
    required_sectors = {
        ProjectSector.EDUCATION,
        ProjectSector.HEALTHCARE,
        ProjectSector.ENVIRONMENT,
        ProjectSector.RURAL_DEVELOPMENT,
        ProjectSector.GENDER_EQUALITY,
        ProjectSector.POVERTY_HUNGER,
        ProjectSector.LIVELIHOOD,
    }
    assert required_sectors.issubset(sectors_represented), (
        f"Missing sectors: {required_sectors - sectors_represented}"
    )

    # Verify Demo Case 1: PRJ-0001 (High total score, low marginal return per lakh)
    prj_1 = next(p for p in data if p["project_id"] == "PRJ-0001")
    assert prj_1["impact_dna"]["expected_impact_score"] >= 0.90
    assert prj_1["impact_dna"]["estimated_impact_per_lakh"] <= 15.0

    # Verify Demo Case 2: PRJ-0002 (Underserved region with extreme need)
    prj_2 = next(p for p in data if p["project_id"] == "PRJ-0002")
    assert prj_2["impact_dna"]["need_score"] >= 0.95
    assert prj_2["impact_dna"]["estimated_impact_per_lakh"] >= 40.0

    # Verify Demo Case 3: PRJ-0003 (Saturated metro region)
    prj_3 = next(p for p in data if p["project_id"] == "PRJ-0003")
    assert prj_3["impact_dna"]["need_score"] <= 0.50

    # Verify Demo Case 6: PRJ-0006 (Missing fields flagged transparently)
    prj_6 = next(p for p in data if p["project_id"] == "PRJ-0006")
    assert len(prj_6["impact_dna"]["missing_fields"]) > 0


# ===========================================================================
# 12. Documentation Files Checklist
# ===========================================================================

def test_checklist_documentation_files_created_with_required_structure():
    """Verify that all three documentation files exist and include required sections."""
    doc_paths = [
        WORKSPACE_ROOT / "docs" / "models" / "csr-saturation.md",
        WORKSPACE_ROOT / "docs" / "models" / "marginal-impact.md",
        WORKSPACE_ROOT / "docs" / "models" / "optimizer.md",
    ]

    required_sections = [
        "## 1. Purpose",
        "## 2. Inputs",
        "## 3. Outputs",
        "## 4. Version",
        "## 5. Assumptions",
        "## 6. Future Formula Section",
    ]

    for doc in doc_paths:
        assert doc.exists(), f"Doc missing: {doc.name}"
        content = doc.read_text(encoding="utf-8")
        for sec in required_sections:
            assert sec in content, f"Section '{sec}' missing in {doc.name}"


# ===========================================================================
# 13. Public Exports Checklist
# ===========================================================================

def test_checklist_public_exports_work():
    """Verify backend.app.engine exports all required symbols through __init__.py."""
    import backend.app.engine as engine

    exported_names = engine.__all__
    assert len(exported_names) >= 40, f"Expected at least 40 exported symbols, got {len(exported_names)}"

    for name in exported_names:
        assert hasattr(engine, name), f"Exported symbol '{name}' not found in engine module"
