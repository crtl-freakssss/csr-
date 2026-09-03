from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Shared Enums (Technical Contract Section 6)
# ---------------------------------------------------------

class ProjectSector(str, Enum):
    EDUCATION = "EDUCATION"
    HEALTHCARE = "HEALTHCARE"
    POVERTY_HUNGER = "POVERTY_HUNGER"
    ENVIRONMENT = "ENVIRONMENT"
    RURAL_DEVELOPMENT = "RURAL_DEVELOPMENT"
    GENDER_EQUALITY = "GENDER_EQUALITY"
    LIVELIHOOD = "LIVELIHOOD"
    DISASTER_RELIEF = "DISASTER_RELIEF"
    SPORTS = "SPORTS"
    ART_CULTURE = "ART_CULTURE"
    OTHER = "OTHER"


class ProposalStatus(str, Enum):
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    READY = "READY"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    MISSING = "MISSING"
    FLAGGED = "FLAGGED"


class DueDiligenceRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------
# Canonical Domain Models (Technical Contract Section 9)
# ---------------------------------------------------------

class Geography(BaseModel):
    state: str = Field(min_length=1, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    block: str | None = Field(default=None, max_length=100)


class BeneficiaryProfile(BaseModel):
    target_count: int = Field(ge=0)
    groups: list[str] = Field(default_factory=list)
    age_ranges: list[str] = Field(default_factory=list)
    vulnerable_groups: list[str] = Field(default_factory=list)


class Financials(BaseModel):
    requested_amount_paise: int = Field(gt=0)
    current_funding_paise: int = Field(ge=0, default=0)
    other_funding_paise: int = Field(ge=0, default=0)


class ImpactMetric(BaseModel):
    metric_id: str
    name: str
    unit: str
    baseline: float | None = None
    target: float | None = None
    measurement_method: str | None = None


class Project(BaseModel):
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
    schema_version: str = "project-v1"


# ---------------------------------------------------------
# Impact DNA Model (Technical Contract Section 10)
# ---------------------------------------------------------

class ImpactDNA(BaseModel):
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
    schema_version: str = "dna-v1"


# ---------------------------------------------------------
# Due Diligence Models (Technical Contract Section 18)
# ---------------------------------------------------------

class DueDiligenceCheck(BaseModel):
    check_name: str
    status: VerificationStatus
    source: str | None = None
    evidence: str | None = None
    confidence: float = Field(ge=0, le=1, default=0.0)
    checked_at: str


class DueDiligenceReport(BaseModel):
    report_id: str
    ngo_id: str

    overall_status: VerificationStatus
    risk_level: DueDiligenceRisk

    checks: list[DueDiligenceCheck]

    flags: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)

    model_name: str | None = None
    model_version: str = "due-diligence-v1"

    disclaimer: str = (
        "This report is an evidence and risk-assessment layer "
        "and does not constitute legal or regulatory certification."
    )


# ---------------------------------------------------------
# Evidence Model (Technical Contract Section 19)
# ---------------------------------------------------------

class EvidenceItem(BaseModel):
    evidence_id: str
    source_type: str
    source_reference: str | None = None
    claim: str
    extracted_value: str | None = None
    confidence: float = Field(ge=0, le=1)
    verification_status: VerificationStatus


# ---------------------------------------------------------
# Proposal Extraction Model (Technical Contract Section 20)
# ---------------------------------------------------------

class ExtractionResult(BaseModel):
    proposal_id: str
    document_id: str

    extracted_project: Project

    evidence: list[EvidenceItem]

    missing_fields: list[str]
    warnings: list[str]

    extraction_confidence: float = Field(ge=0, le=1)

    model_name: str
    prompt_version: str
    schema_version: str = "extraction-v1"
