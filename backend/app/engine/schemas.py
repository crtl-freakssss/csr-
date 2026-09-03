"""Canonical Pydantic v2 schemas for AllocateAI Decision Engine.

Authoritative source: Software Contract v1.0 & Technical Contract v1.0.
Strict field definitions matching the contract specifications without renaming.
"""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.engine.constants import (
    DEFAULT_MARGINAL_INCREMENT_PAISE,
    DNA_SCHEMA_VERSION,
    MARGINAL_CALCULATION_VERSION,
    PROJECT_SCHEMA_VERSION,
    SATURATION_CALCULATION_VERSION,
    AllocationStatus,
    OptimizationStatus,
    ProjectSector,
    ReasonCode,
)
from backend.app.engine.utils import validate_budget, validate_paise


# ---------------------------------------------------------------------------
# Project Domain Models (Technical Contract Section 9)
# ---------------------------------------------------------------------------

class Geography(BaseModel):
    """Geographical jurisdiction of a CSR intervention."""
    model_config = ConfigDict(extra="ignore")

    state: str = Field(min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    block: str | None = Field(default=None, max_length=100)


class BeneficiaryProfile(BaseModel):
    """Target beneficiary population and demographic segments."""
    model_config = ConfigDict(extra="ignore")

    target_count: int = Field(ge=0)
    groups: list[str] = Field(default_factory=list)
    age_ranges: list[str] = Field(default_factory=list)
    vulnerable_groups: list[str] = Field(default_factory=list)


class Financials(BaseModel):
    """Monetary requirements and funding status in integer paise."""
    model_config = ConfigDict(extra="ignore")

    requested_amount_paise: int = Field(gt=0)
    current_funding_paise: int = Field(ge=0, default=0)
    other_funding_paise: int = Field(ge=0, default=0)

    @field_validator("requested_amount_paise")
    @classmethod
    def validate_requested_amount(cls, v: Any) -> int:
        """Validate requested funding amount is integer paise strictly > 0."""
        return validate_paise(v, name="requested_amount_paise", allow_zero=False)

    @field_validator("current_funding_paise", "other_funding_paise")
    @classmethod
    def validate_other_amounts(cls, v: Any, info: Any) -> int:
        """Validate funding amounts are non-negative integer paise."""
        return validate_paise(v, name=info.field_name, allow_zero=True)


class ImpactMetric(BaseModel):
    """Measurable Key Performance Indicator for impact evaluation."""
    model_config = ConfigDict(extra="ignore")

    metric_id: str
    name: str
    unit: str
    baseline: float | None = None
    target: float | None = None
    measurement_method: str | None = None


# ---------------------------------------------------------------------------
# Impact DNA Model (Technical Contract Section 10)
# ---------------------------------------------------------------------------

class ImpactDNA(BaseModel):
    """Structured project fingerprint generated from AI extraction."""
    model_config = ConfigDict(extra="ignore")

    dna_id: str
    project_id: str

    need_score: float = Field(ge=0, le=1)
    expected_impact_score: float = Field(ge=0, le=1)
    cost_efficiency_score: float = Field(ge=0, le=1)
    evidence_strength_score: float = Field(ge=0, le=1)
    scalability_score: float = Field(ge=0, le=1)
    implementation_risk_score: float = Field(ge=0, le=1)

    beneficiary_reach: int = Field(ge=0)
    estimated_impact_per_lakh: float = Field(ge=0)

    missing_fields: list[str] = Field(default_factory=list)
    extraction_confidence: float = Field(ge=0, le=1)

    model_name: str
    prompt_version: str
    schema_version: str = DNA_SCHEMA_VERSION


class Project(BaseModel):
    """Authoritative project representation."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    name: str
    ngo_id: str
    sector: ProjectSector
    geographies: list[Geography]
    beneficiary_profile: BeneficiaryProfile
    financials: Financials
    duration_months: int = Field(gt=0)
    impact_metrics: list[ImpactMetric] = Field(default_factory=list)
    description: str | None = None
    schema_version: str = PROJECT_SCHEMA_VERSION
    impact_dna: ImpactDNA | None = None


# ---------------------------------------------------------------------------
# Saturation Result Model (Technical Contract Section 11)
# ---------------------------------------------------------------------------

class SaturationContext(BaseModel):
    """Contextual demographic and funding metadata for saturation analysis."""
    model_config = ConfigDict(extra="ignore")

    state: str
    sector: ProjectSector
    total_regional_csr_paise: int = Field(ge=0, default=0)
    total_population: int = Field(ge=0, default=0)
    target_population: int = Field(ge=0, default=0)


class SaturationResult(BaseModel):
    """CSR funding saturation assessment for a project location and sector."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    state: str
    sector: ProjectSector

    saturation_index: float = Field(ge=0, le=1)
    need_score: float = Field(ge=0, le=1)

    existing_csr_amount_paise: int = Field(ge=0)
    estimated_beneficiary_coverage: float = Field(ge=0, le=1)

    confidence: float = Field(ge=0, le=1)

    calculation_version: str = SATURATION_CALCULATION_VERSION
    component_breakdown: dict[str, Any] | None = None

    @field_validator("existing_csr_amount_paise")
    @classmethod
    def validate_existing_csr(cls, v: Any) -> int:
        """Validate existing regional CSR amount is non-negative integer paise."""
        return validate_paise(v, name="existing_csr_amount_paise", allow_zero=True)


# ---------------------------------------------------------------------------
# Marginal Impact Result Model (Technical Contract Section 12)
# ---------------------------------------------------------------------------

class MarginalImpactResult(BaseModel):
    """Evaluates incremental return of an additional budget increment."""
    model_config = ConfigDict(extra="ignore")

    project_id: str

    increment_paise: int = Field(gt=0)

    baseline_budget_paise: int = Field(ge=0)
    projected_budget_paise: int = Field(gt=0)

    baseline_impact: float = Field(ge=0)
    projected_impact: float = Field(ge=0)

    incremental_impact: float = Field(ge=0)
    impact_per_lakh: float = Field(ge=0)

    marginal_impact_score: float = Field(ge=0, le=1)

    diminishing_return_factor: float = Field(ge=0, le=1)

    calculation_version: str = MARGINAL_CALCULATION_VERSION
    component_breakdown: dict[str, Any] | None = None
    weights_used: dict[str, float] | None = None
    allocation_context: dict[str, float] | None = None
    engine_version: str = "marginal-impact-engine"
    input_schema: str = "dna-v1"
    dependency_versions: dict[str, str] = Field(
        default_factory=lambda: {
            "scoring": "scoring-v1",
            "saturation": "saturation-v1",
        }
    )

    @field_validator("increment_paise", "projected_budget_paise")
    @classmethod
    def validate_positive_amounts(cls, v: Any, info: Any) -> int:
        """Validate budget increments and projected amounts are positive integer paise."""
        return validate_paise(v, name=info.field_name, allow_zero=False)

    @field_validator("baseline_budget_paise")
    @classmethod
    def validate_non_negative_amounts(cls, v: Any, info: Any) -> int:
        """Validate baseline amounts are non-negative integer paise."""
        return validate_paise(v, name=info.field_name, allow_zero=True)


# ---------------------------------------------------------------------------
# Optimization Weights & Constraints (Technical Contract Section 14)
# ---------------------------------------------------------------------------

class OptimizationWeights(BaseModel):
    """Policy priority weights configured for allocation optimization."""
    model_config = ConfigDict(extra="ignore")

    need: float = Field(ge=0, le=1)
    marginal_impact: float = Field(ge=0, le=1)
    cost_efficiency: float = Field(ge=0, le=1)
    evidence: float = Field(ge=0, le=1)
    scalability: float = Field(ge=0, le=1)
    equity: float = Field(ge=0, le=1)
    risk_penalty: float = Field(ge=0, le=1)

    def to_dict(self) -> dict[str, float]:
        """Return weights as a dictionary."""
        return {
            "need": self.need,
            "marginal_impact": self.marginal_impact,
            "cost_efficiency": self.cost_efficiency,
            "evidence": self.evidence,
            "scalability": self.scalability,
            "equity": self.equity,
            "risk_penalty": self.risk_penalty,
        }


class OptimizationConstraints(BaseModel):
    """Policy and regional constraints applied during budget allocation."""
    model_config = ConfigDict(extra="ignore")

    max_allocation_per_project_paise: int | None = Field(default=None, ge=0)
    max_allocation_per_region_paise: int | None = Field(default=None, ge=0)
    minimum_allocation_per_project_paise: int | None = Field(default=None, ge=0)
    require_full_budget_allocation: bool = True
    regional_equity_enabled: bool = True


class OptimizationRequest(BaseModel):
    """Request payload to trigger deterministic budget optimization."""
    model_config = ConfigDict(extra="ignore")

    budget_paise: int = Field(gt=0)
    project_ids: list[str] = Field(min_length=1)
    weights: OptimizationWeights
    constraints: OptimizationConstraints
    marginal_increment_paise: int = Field(
        default=DEFAULT_MARGINAL_INCREMENT_PAISE,
        gt=0,
    )

    @field_validator("budget_paise")
    @classmethod
    def validate_budget_field(cls, v: Any) -> int:
        """Validate budget is integer paise strictly > 0."""
        return validate_budget(v)

    @field_validator("marginal_increment_paise")
    @classmethod
    def validate_increment_field(cls, v: Any) -> int:
        """Validate marginal increment is integer paise strictly > 0."""
        return validate_paise(v, name="marginal_increment_paise", allow_zero=False)


# ---------------------------------------------------------------------------
# Allocation & Optimization Result (Technical Contract Section 15 & 16)
# ---------------------------------------------------------------------------

class Allocation(BaseModel):
    """Individual project allocation recommendation with explainability codes."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    allocated_amount_paise: int = Field(ge=0)

    marginal_impact_score: float = Field(ge=0, le=1)
    base_score: float = Field(ge=0, le=1)
    saturation_index: float = Field(ge=0, le=1)

    reason_codes: list[ReasonCode]
    rank: int = Field(gt=0)

    status: AllocationStatus = AllocationStatus.PROPOSED
    allocation_context: dict[str, Any] | None = None
    allocation_explanation: dict[str, Any] | None = None

    @field_validator("allocated_amount_paise")
    @classmethod
    def validate_allocated_paise(cls, v: Any) -> int:
        """Validate allocated amount is non-negative integer paise."""
        return validate_paise(v, name="allocated_amount_paise", allow_zero=True)


class OptimizationResult(BaseModel):
    """Output artifact of deterministic budget optimization."""
    model_config = ConfigDict(extra="ignore")

    run_id: str
    status: OptimizationStatus

    budget_paise: int = Field(ge=0)
    allocated_paise: int = Field(ge=0)
    unallocated_paise: int = Field(ge=0)

    allocations: list[Allocation]

    total_predicted_impact: float = Field(ge=0)
    average_saturation: float = Field(ge=0, le=1)
    underserved_region_allocation_share: float = Field(ge=0, le=1)

    weights: OptimizationWeights
    constraints: OptimizationConstraints

    calculation_versions: dict[str, str]

    created_at: str
    portfolio_breakdown: dict[str, Any] | None = None
    optimization_audit: dict[str, Any] | None = None
    pipeline_summary: dict[str, Any] | None = None

    @field_validator("budget_paise", "allocated_paise", "unallocated_paise")
    @classmethod
    def validate_result_amounts(cls, v: Any, info: Any) -> int:
        """Validate result financial amounts are non-negative integer paise."""
        return validate_paise(v, name=info.field_name, allow_zero=True)


# ---------------------------------------------------------------------------
# Dynamic Fund Reallocation (Technical Contract Section 17)
# ---------------------------------------------------------------------------

class ProjectPerformanceUpdate(BaseModel):
    """Mid-cycle project performance data used to evaluate reallocation."""
    model_config = ConfigDict(extra="ignore")

    project_id: str

    actual_beneficiaries: int | None = Field(default=None, ge=0)
    actual_spend_paise: int | None = Field(default=None, ge=0)
    progress_percent: float | None = Field(default=None, ge=0, le=100)
    updated_risk_score: float | None = Field(default=None, ge=0, le=1)
    updated_impact_score: float | None = Field(default=None, ge=0, le=1)

    @field_validator("actual_spend_paise")
    @classmethod
    def validate_spend(cls, v: Any) -> int | None:
        """Validate spend is non-negative integer paise or None."""
        if v is None:
            return None
        return validate_paise(v, name="actual_spend_paise", allow_zero=True)


class ReallocationRequest(BaseModel):
    """Request payload for deterministic fund reallocation."""
    model_config = ConfigDict(extra="ignore")

    previous_run_id: str
    budget_paise: int = Field(gt=0)
    performance_updates: list[ProjectPerformanceUpdate]
    weights: OptimizationWeights
    constraints: OptimizationConstraints

    @field_validator("budget_paise")
    @classmethod
    def validate_reallocation_budget(cls, v: Any) -> int:
        """Validate reallocation budget is integer paise strictly > 0."""
        return validate_budget(v)


class ReallocationResult(BaseModel):
    """Deterministic result showing before/after fund reallocations and shift explanation."""
    model_config = ConfigDict(extra="ignore")

    run_id: str
    previous_run_id: str

    old_allocations: list[Allocation]
    new_allocations: list[Allocation]

    changed_projects: list[str]
    total_budget_shifted_paise: int = Field(ge=0)

    explanation: list[str]

    calculation_versions: dict[str, str]
    created_at: str

    @field_validator("total_budget_shifted_paise")
    @classmethod
    def validate_shifted_paise(cls, v: Any) -> int:
        """Validate shifted budget is non-negative integer paise."""
        return validate_paise(v, name="total_budget_shifted_paise", allow_zero=True)
