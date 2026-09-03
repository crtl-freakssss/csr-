"""Independent QA Engineer Contract Verification Script for AllocateAI Member C Phase 1.

Audits repository structure, public exports, canonical schemas, edge cases,
enum equality, seed dataset integrity, documentation structure, circular dependencies,
forbidden imports, and static code quality.
"""

import ast
import importlib
import json
import math
from pathlib import Path
import re
import sys
from typing import get_type_hints

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

results = {}


def report(section: str, name: str, status: bool, detail: str = ""):
    key = f"[{section}] {name}"
    results[key] = (status, detail)
    mark = "PASS" if status else "FAIL"
    print(f"{mark}: {key} - {detail}")


# ===========================================================================
# SECTION A: Repository Contract Verification
# ===========================================================================
print("\n--- SECTION A: Repository Contract Verification ---")
engine_base = WORKSPACE_ROOT / "backend" / "app" / "engine"
required_repo_paths = [
    ("backend/app/engine/", engine_base, True),
    ("scoring/", engine_base / "scoring" / "__init__.py", False),
    ("saturation/", engine_base / "saturation" / "__init__.py", False),
    ("marginal_impact/", engine_base / "marginal_impact" / "__init__.py", False),
    ("optimizer/", engine_base / "optimizer" / "__init__.py", False),
    ("constraints/", engine_base / "constraints" / "__init__.py", False),
    ("constants.py", engine_base / "constants.py", False),
    ("exceptions.py", engine_base / "exceptions.py", False),
    ("utils.py", engine_base / "utils.py", False),
    ("schemas.py", engine_base / "schemas.py", False),
    ("__init__.py", engine_base / "__init__.py", False),
]

for label, path, is_dir in required_repo_paths:
    exists = path.is_dir() if is_dir else path.is_file()
    report("SECTION A", f"Path exists: {label}", exists, str(path.relative_to(WORKSPACE_ROOT)))


# ===========================================================================
# SECTION B: Public API Export Verification
# ===========================================================================
print("\n--- SECTION B: Public API Export Verification ---")
try:
    import backend.app.engine as engine
    all_symbols = engine.__all__
    
    # Check duplicates
    has_duplicates = len(all_symbols) != len(set(all_symbols))
    report("SECTION B", "No duplicate exports in __all__", not has_duplicates, f"Total: {len(all_symbols)}, Unique: {len(set(all_symbols))}")
    
    # Check all exported items exist
    missing_exports = [s for s in all_symbols if not hasattr(engine, s)]
    report("SECTION B", "No missing exports", len(missing_exports) == 0, f"Missing: {missing_exports}")
    
    # Check no private/internal items exported
    private_exports = [s for s in all_symbols if s.startswith("_")]
    report("SECTION B", "No internal/private helpers exported", len(private_exports) == 0, f"Private: {private_exports}")

    # Categorize exports
    exported_classes = []
    exported_constants = []
    exported_exceptions = []
    
    for s in all_symbols:
        obj = getattr(engine, s)
        if isinstance(obj, type) and issubclass(obj, Exception):
            exported_exceptions.append(s)
        elif isinstance(obj, type):
            exported_classes.append(s)
        else:
            exported_constants.append(s)
            
    print(f"Exported Classes ({len(exported_classes)}): {sorted(exported_classes)}")
    print(f"Exported Constants/Functions ({len(exported_constants)}): {sorted(exported_constants)}")
    print(f"Exported Exceptions ({len(exported_exceptions)}): {sorted(exported_exceptions)}")
    report("SECTION B", "Export categorization completed", True, f"{len(exported_classes)} classes, {len(exported_constants)} consts/funcs, {len(exported_exceptions)} exceptions")
except Exception as e:
    report("SECTION B", "Import backend.app.engine", False, str(e))


# ===========================================================================
# SECTION C: Canonical Schema Verification
# ===========================================================================
print("\n--- SECTION C: Canonical Schema Verification ---")
from backend.app.engine.schemas import (
    Geography, BeneficiaryProfile, Financials, ImpactMetric, ImpactDNA,
    Project, SaturationResult, MarginalImpactResult, OptimizationWeights,
    OptimizationConstraints, OptimizationRequest, Allocation, OptimizationResult,
    ProjectPerformanceUpdate, ReallocationRequest, ReallocationResult
)
from backend.app.engine.constants import (
    ProjectSector, ReasonCode, OptimizationStatus, AllocationStatus,
    PROJECT_SCHEMA_VERSION, DNA_SCHEMA_VERSION, SATURATION_CALCULATION_VERSION,
    MARGINAL_CALCULATION_VERSION, OPTIMIZER_CALCULATION_VERSION
)

try:
    # 1. Geography
    geo = Geography(state="Bihar", district="Gaya", block="Mohanpur")
    assert geo.state == "Bihar" and geo.district == "Gaya" and geo.block == "Mohanpur"
    
    # 2. BeneficiaryProfile
    bp = BeneficiaryProfile(target_count=5000, groups=["rural"], age_ranges=["6-14"], vulnerable_groups=["tribal"])
    assert bp.target_count == 5000
    
    # 3. Financials (default current_funding_paise=0, other_funding_paise=0)
    fin = Financials(requested_amount_paise=25_000_000)
    assert fin.requested_amount_paise == 25_000_000
    assert fin.current_funding_paise == 0
    assert fin.other_funding_paise == 0
    
    # 4. ImpactMetric
    metric = ImpactMetric(metric_id="MET-01", name="Literacy", unit="percentage", baseline=40.0, target=80.0, measurement_method="Exam")
    assert metric.metric_id == "MET-01"
    
    # 5. ImpactDNA
    dna = ImpactDNA(
        dna_id="DNA-0001", project_id="PRJ-0001", need_score=0.9, expected_impact_score=0.85,
        cost_efficiency_score=0.8, evidence_strength_score=0.75, scalability_score=0.7,
        implementation_risk_score=0.2, beneficiary_reach=5000, estimated_impact_per_lakh=45.0,
        extraction_confidence=0.88, model_name="dna-v1", prompt_version="v1.0"
    )
    assert dna.schema_version == DNA_SCHEMA_VERSION == "dna-v1"
    
    # 6. Project
    prj = Project(
        project_id="PRJ-0001", name="Education Project", ngo_id="NGO-0001", sector=ProjectSector.EDUCATION,
        geographies=[geo], beneficiary_profile=bp, financials=fin, duration_months=12, impact_metrics=[metric]
    )
    assert prj.schema_version == PROJECT_SCHEMA_VERSION == "project-v1"
    
    # 7. SaturationResult
    sat = SaturationResult(
        project_id="PRJ-0001", state="Bihar", sector=ProjectSector.EDUCATION,
        saturation_index=0.20, need_score=0.9, existing_csr_amount_paise=5_000_000,
        estimated_beneficiary_coverage=0.15, confidence=0.85
    )
    assert sat.calculation_version == SATURATION_CALCULATION_VERSION == "saturation-v1"
    
    # 8. MarginalImpactResult
    mar = MarginalImpactResult(
        project_id="PRJ-0001", increment_paise=10_000_000, baseline_budget_paise=10_000_000,
        projected_budget_paise=20_000_000, baseline_impact=100.0, projected_impact=150.0,
        incremental_impact=50.0, impact_per_lakh=50.0, marginal_impact_score=0.85,
        diminishing_return_factor=0.90
    )
    assert mar.calculation_version == MARGINAL_CALCULATION_VERSION == "marginal-v1"
    
    # 9. OptimizationWeights
    weights = OptimizationWeights(
        need=0.2, marginal_impact=0.3, cost_efficiency=0.15, evidence=0.15,
        scalability=0.1, equity=0.05, risk_penalty=0.05
    )
    assert weights.need == 0.2
    
    # 10. OptimizationConstraints
    constraints = OptimizationConstraints()
    assert constraints.require_full_budget_allocation is True
    assert constraints.regional_equity_enabled is True
    
    # 11. OptimizationRequest
    opt_req = OptimizationRequest(
        budget_paise=50_000_000, project_ids=["PRJ-0001"], weights=weights, constraints=constraints
    )
    assert opt_req.marginal_increment_paise == 10_000_000  # Default 1 lakh in paise
    
    # 12. Allocation
    alloc = Allocation(
        project_id="PRJ-0001", allocated_amount_paise=50_000_000, marginal_impact_score=0.85,
        base_score=0.80, saturation_index=0.20, reason_codes=[ReasonCode.HIGH_MARGINAL_IMPACT],
        rank=1
    )
    assert alloc.status == AllocationStatus.PROPOSED
    
    # 13. OptimizationResult
    opt_res = OptimizationResult(
        run_id="OPT-0001", status=OptimizationStatus.COMPLETED, budget_paise=50_000_000,
        allocated_paise=50_000_000, unallocated_paise=0, allocations=[alloc],
        total_predicted_impact=150.0, average_saturation=0.20, underserved_region_allocation_share=1.0,
        weights=weights, constraints=constraints, calculation_versions={"optimizer": OPTIMIZER_CALCULATION_VERSION},
        created_at="2026-09-03T12:00:00Z"
    )
    assert opt_res.run_id == "OPT-0001"
    
    # 14. ProjectPerformanceUpdate
    update = ProjectPerformanceUpdate(project_id="PRJ-0001", actual_beneficiaries=5500, actual_spend_paise=24_000_000)
    assert update.actual_spend_paise == 24_000_000
    
    # 15. ReallocationRequest
    realloc_req = ReallocationRequest(
        previous_run_id="OPT-0001", budget_paise=50_000_000, performance_updates=[update],
        weights=weights, constraints=constraints
    )
    assert realloc_req.previous_run_id == "OPT-0001"
    
    # 16. ReallocationResult
    realloc_res = ReallocationResult(
        run_id="REA-0001", previous_run_id="OPT-0001", old_allocations=[alloc], new_allocations=[alloc],
        changed_projects=["PRJ-0001"], total_budget_shifted_paise=0, explanation=["No shift needed"],
        calculation_versions={"optimizer": OPTIMIZER_CALCULATION_VERSION}, created_at="2026-09-03T12:30:00Z"
    )
    assert realloc_res.run_id == "REA-0001"
    
    report("SECTION C", "All 16 Canonical Schemas instantiated successfully with contract defaults", True)
except Exception as e:
    report("SECTION C", "Canonical Schema Verification", False, str(e))


# ===========================================================================
# SECTION D: Validation Edge Cases
# ===========================================================================
print("\n--- SECTION D: Validation Edge Cases ---")
from backend.app.engine.utils import validate_score, validate_weights, validate_budget, validate_paise
from backend.app.engine.exceptions import WeightValidationError, BudgetValidationError, InvalidProjectDataError
from pydantic import ValidationError

# Score validation
score_cases = [-0.1, 1.2, float("nan"), float("inf"), "0.5", None]
score_all_failed = True
for val in score_cases:
    try:
        validate_score(val)  # type: ignore
        score_all_failed = False
        print(f"FAILED: validate_score accepted {val}")
    except (InvalidProjectDataError, TypeError, ValueError):
        pass

report("SECTION D", "Score validation rejects [-0.1, 1.2, NaN, Inf, String, None]", score_all_failed)

# Weight validation
weight_cases = [
    ({"w1": 0.5, "w2": 0.35}, 0.85),    # sum = 0.85
    ({"w1": 0.75, "w2": 0.50}, 1.25),   # sum = 1.25
    ({"w1": -0.2, "w2": 1.2}, None),    # negative weight
    ({"w1": 1.5, "w2": -0.5}, None),    # weight > 1
]
weight_all_raised = True
for w_dict, _ in weight_cases:
    try:
        validate_weights(w_dict)
        weight_all_raised = False
        print(f"FAILED: validate_weights accepted {w_dict}")
    except WeightValidationError:
        pass

report("SECTION D", "Weight validation raises WeightValidationError for bad sums & bounds", weight_all_raised)

# Budget validation
budget_cases = [0, -1, 100.5, True]
budget_all_raised = True
for b_val in budget_cases:
    try:
        validate_budget(b_val)
        budget_all_raised = False
        print(f"FAILED: validate_budget accepted {b_val}")
    except BudgetValidationError:
        pass

report("SECTION D", "Budget validation raises BudgetValidationError for [0, -1, 100.5, True]", budget_all_raised)

# Money validation
money_all_correct = True
# Reject floats
try:
    validate_paise(100.25)
    money_all_correct = False
except BudgetValidationError:
    pass

# Reject bool
try:
    validate_paise(True)
    money_all_correct = False
except BudgetValidationError:
    pass

# Accept integer paise
try:
    p1 = validate_paise(10_000_000)
    p2 = validate_paise(0, allow_zero=True)
    if p1 != 10_000_000 or p2 != 0:
        money_all_correct = False
except Exception:
    money_all_correct = False

report("SECTION D", "Money validation: rejects floats & bool, accepts integer paise", money_all_correct)


# ===========================================================================
# SECTION E: Enum Contract Verification
# ===========================================================================
print("\n--- SECTION E: Enum Contract Verification ---")
from backend.app.engine.constants import (
    ProjectSector, ReasonCode, ProposalStatus, VerificationStatus,
    ConfidenceLevel, DueDiligenceRisk, OptimizationStatus, AllocationStatus,
    AuditEventType
)

contract_enums = {
    "ProjectSector": (
        ProjectSector,
        {"EDUCATION", "HEALTHCARE", "POVERTY_HUNGER", "ENVIRONMENT", "RURAL_DEVELOPMENT",
         "GENDER_EQUALITY", "LIVELIHOOD", "DISASTER_RELIEF", "SPORTS", "ART_CULTURE", "OTHER"}
    ),
    "ReasonCode": (
        ReasonCode,
        {"HIGH_NEED", "LOW_SATURATION", "HIGH_MARGINAL_IMPACT", "HIGH_COST_EFFICIENCY",
         "STRONG_EVIDENCE", "HIGH_SCALABILITY", "HIGH_IMPLEMENTATION_RISK", "LOW_EVIDENCE",
         "HIGH_SATURATION", "BUDGET_CONSTRAINT", "REGIONAL_CAP", "MINIMUM_ALLOCATION",
         "MISSING_DATA", "DUE_DILIGENCE_FLAG"}
    ),
    "ProposalStatus": (
        ProposalStatus,
        {"UPLOADED", "EXTRACTING", "EXTRACTED", "VALIDATION_REQUIRED", "READY", "REJECTED", "FAILED"}
    ),
    "VerificationStatus": (
        VerificationStatus,
        {"VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "MISSING", "FLAGGED"}
    ),
    "ConfidenceLevel": (
        ConfidenceLevel,
        {"HIGH", "MEDIUM", "LOW", "UNKNOWN"}
    ),
    "DueDiligenceRisk": (
        DueDiligenceRisk,
        {"LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"}
    ),
    "OptimizationStatus": (
        OptimizationStatus,
        {"QUEUED", "RUNNING", "COMPLETED", "FAILED"}
    ),
    "AllocationStatus": (
        AllocationStatus,
        {"PROPOSED", "APPROVED", "REJECTED", "REALLOCATED"}
    ),
    "AuditEventType": (
        AuditEventType,
        {"PROPOSAL_CREATED", "DOCUMENT_UPLOADED", "EXTRACTION_STARTED", "EXTRACTION_COMPLETED",
         "PROJECT_CREATED", "IMPACT_DNA_CREATED", "SATURATION_CALCULATED", "DUE_DILIGENCE_COMPLETED",
         "OPTIMIZATION_STARTED", "OPTIMIZATION_COMPLETED", "ALLOCATION_CREATED", "REALLOCATION_STARTED",
         "REALLOCATION_COMPLETED", "WEIGHTS_CHANGED", "CONSTRAINTS_CHANGED", "ERROR_OCCURRED"}
    ),
}

all_enums_match = True
for name, (enum_cls, expected_set) in contract_enums.items():
    actual_set = {m.value for m in enum_cls}
    missing = expected_set - actual_set
    unexpected = actual_set - expected_set
    matches = (actual_set == expected_set)
    if not matches:
        all_enums_match = False
    report("SECTION E", f"Enum match: {name}", matches, f"Missing: {missing}, Unexpected: {unexpected}")


# ===========================================================================
# SECTION F: Seed Dataset Verification
# ===========================================================================
print("\n--- SECTION F: Seed Dataset Verification ---")
seed_path = WORKSPACE_ROOT / "data" / "sample" / "member_c_seed_projects.json"
with open(seed_path, "r", encoding="utf-8") as f:
    seed_data = json.load(f)

count_18 = len(seed_data) == 18
report("SECTION F", "Exactly 18 projects in seed dataset", count_18, f"Count: {len(seed_data)}")

prj_ids = [p["project_id"] for p in seed_data]
unique_prj_ids = len(prj_ids) == len(set(prj_ids))
report("SECTION F", "Unique project IDs", unique_prj_ids, f"{len(set(prj_ids))} unique of {len(prj_ids)}")

dna_ids = [p["impact_dna"]["dna_id"] for p in seed_data]
unique_dna_ids = len(dna_ids) == len(set(dna_ids))
report("SECTION F", "Unique DNA IDs", unique_dna_ids, f"{len(set(dna_ids))} unique of {len(dna_ids)}")

ngo_ids = [p["ngo_id"] for p in seed_data]
unique_ngo_ids = len(ngo_ids) == len(set(ngo_ids))
report("SECTION F", "Unique NGO IDs", unique_ngo_ids, f"{len(set(ngo_ids))} unique of {len(ngo_ids)}")

states_found = set()
sectors_found = set()
all_projects_valid = True
all_dna_valid = True
all_money_paise = True
all_scores_valid = True
all_duration_valid = True
all_beneficiaries_valid = True

for p_dict in seed_data:
    try:
        p = Project.model_validate(p_dict)
        for g in p.geographies:
            states_found.add(g.state)
        sectors_found.add(p.sector.value)
        if not isinstance(p.financials.requested_amount_paise, int) or p.financials.requested_amount_paise <= 0:
            all_money_paise = False
        if p.duration_months <= 0:
            all_duration_valid = False
        if p.beneficiary_profile.target_count < 0:
            all_beneficiaries_valid = False
    except Exception:
        all_projects_valid = False

    try:
        dna_obj = ImpactDNA.model_validate(p_dict["impact_dna"])
        if not (0.0 <= dna_obj.need_score <= 1.0 and 0.0 <= dna_obj.evidence_strength_score <= 1.0 and 0.0 <= dna_obj.implementation_risk_score <= 1.0):
            all_scores_valid = False
    except Exception:
        all_dna_valid = False

report("SECTION F", "At least 6 states discovered", len(states_found) >= 6, f"Found ({len(states_found)}): {sorted(states_found)}")
required_sectors_set = {"EDUCATION", "HEALTHCARE", "ENVIRONMENT", "RURAL_DEVELOPMENT", "GENDER_EQUALITY", "POVERTY_HUNGER", "LIVELIHOOD"}
has_required_sectors = required_sectors_set.issubset(sectors_found)
report("SECTION F", "Required sectors present", has_required_sectors, f"Found ({len(sectors_found)}): {sorted(sectors_found)}")
report("SECTION F", "Every project validates against Project schema", all_projects_valid)
report("SECTION F", "Every ImpactDNA validates against ImpactDNA schema", all_dna_valid)
report("SECTION F", "Money stored in integer paise (>0)", all_money_paise)
report("SECTION F", "Need, evidence, risk scores in [0, 1]", all_scores_valid)
report("SECTION F", "Duration > 0 months", all_duration_valid)
report("SECTION F", "Beneficiary count >= 0", all_beneficiaries_valid)


# ===========================================================================
# SECTION G: Documentation Verification
# ===========================================================================
print("\n--- SECTION G: Documentation Verification ---")
doc_files = ["csr-saturation.md", "marginal-impact.md", "optimizer.md"]
required_doc_sections = ["Purpose", "Inputs", "Outputs", "Version", "Assumptions", "Future Formula"]

docs_valid = True
for doc_name in doc_files:
    doc_path = WORKSPACE_ROOT / "docs" / "models" / doc_name
    if not doc_path.exists():
        docs_valid = False
        report("SECTION G", f"Doc exists: {doc_name}", False)
        continue
    content = doc_path.read_text(encoding="utf-8").lower()
    missing_secs = [s for s in required_doc_sections if s.lower() not in content]
    status = len(missing_secs) == 0
    if not status:
        docs_valid = False
    report("SECTION G", f"Sections in {doc_name}", status, f"Missing: {missing_secs}")


# ===========================================================================
# SECTION H: Import & Circular Dependency Audit
# ===========================================================================
print("\n--- SECTION H: Import & Circular Dependency Audit ---")
subpackages = [
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

import_all_clean = True
for pkg in subpackages:
    try:
        mod = importlib.import_module(pkg)
        report("SECTION H", f"Import package: {pkg}", True)
    except Exception as e:
        import_all_clean = False
        report("SECTION H", f"Import package: {pkg}", False, str(e))


# ===========================================================================
# SECTION I: Forbidden Dependency Audit
# ===========================================================================
print("\n--- SECTION I: Forbidden Dependency Audit ---")
forbidden_modules = [
    "openai", "anthropic", "google.generativeai", "langchain",
    "transformers", "requests", "httpx", "urllib.request",
    "random", "uuid", "datetime"
]

engine_py_files = list(engine_base.rglob("*.py"))
forbidden_found = []

for fpath in engine_py_files:
    content = fpath.read_text(encoding="utf-8")
    tree = ast.parse(content, filename=str(fpath))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for forb in forbidden_modules:
                    if alias.name == forb or alias.name.startswith(f"{forb}."):
                        forbidden_found.append((fpath.relative_to(WORKSPACE_ROOT), node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                for forb in forbidden_modules:
                    if node.module == forb or node.module.startswith(f"{forb}."):
                        forbidden_found.append((fpath.relative_to(WORKSPACE_ROOT), node.lineno, node.module))

report("SECTION I", "No forbidden dependencies (AI, random, uuid, datetime, http)", len(forbidden_found) == 0, f"Violations: {forbidden_found}")


# ===========================================================================
# SECTION J: Static Quality Audit
# ===========================================================================
print("\n--- SECTION J: Static Quality Audit ---")
syntax_clean = True
todos_found = []
fixmes_found = []
classes_missing_doc = []
functions_missing_doc = []
pass_statements = []

for fpath in engine_py_files:
    code = fpath.read_text(encoding="utf-8")
    
    # Check syntax
    try:
        tree = ast.parse(code, filename=str(fpath))
    except Exception as e:
        syntax_clean = False
        report("SECTION J", f"Syntax in {fpath.name}", False, str(e))
        continue
        
    # Check comments for TODO / FIXME
    lines = code.splitlines()
    for idx, line in enumerate(lines, start=1):
        if re.search(r"#.*\bTODO\b", line, re.IGNORECASE):
            todos_found.append((fpath.name, idx, line.strip()))
        if re.search(r"#.*\bFIXME\b", line, re.IGNORECASE):
            fixmes_found.append((fpath.name, idx, line.strip()))
            
    # Check docstrings & pass statements
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if not ast.get_docstring(node):
                classes_missing_doc.append((fpath.name, node.name))
        elif isinstance(node, ast.FunctionDef):
            if not ast.get_docstring(node) and not node.name.startswith("_"):
                functions_missing_doc.append((fpath.name, node.name))
        elif isinstance(node, ast.Pass):
            # Skeleton classes/methods must raise NotImplementedError, not use pass
            pass_statements.append((fpath.name, getattr(node, "lineno", 0)))

report("SECTION J", "Python syntax clean", syntax_clean)
report("SECTION J", "No TODO comments", len(todos_found) == 0, f"Found: {todos_found}")
report("SECTION J", "No FIXME comments", len(fixmes_found) == 0, f"Found: {fixmes_found}")
report("SECTION J", "Docstrings on public classes", len(classes_missing_doc) == 0, f"Missing: {classes_missing_doc}")
report("SECTION J", "Docstrings on public functions", len(functions_missing_doc) == 0, f"Missing: {functions_missing_doc}")
report("SECTION J", "No pass statements hiding implementation", len(pass_statements) == 0, f"Found: {pass_statements}")

# Summary
total_passed = sum(1 for s, _ in results.values() if s)
total_tests = len(results)
print(f"\n=======================================================")
print(f"AUDIT SUMMARY: {total_passed}/{total_tests} CHECKS PASSED")
print(f"=======================================================")
if total_passed == total_tests:
    print("ALL CONTRACT VERIFICATIONS PASSED CLEANLY!")
    sys.exit(0)
else:
    print("SOME CHECKS FAILED!")
    sys.exit(1)
