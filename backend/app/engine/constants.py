"""Shared constants and enums for AllocateAI Decision Engine.

Authoritative source: Software Contract v1.0 & Technical Contract v1.0.
All values are strictly deterministic, typed, and contract-compliant.
"""

from enum import Enum
from typing import Final


# ---------------------------------------------------------------------------
# Shared Enums (Technical Contract Section 6)
# ---------------------------------------------------------------------------

class ProjectSector(str, Enum):
    """Sectors recognized for CSR project classification."""
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


class ReasonCode(str, Enum):
    """Deterministic reasoning codes for allocation and scoring decisions."""
    HIGH_NEED = "HIGH_NEED"
    LOW_SATURATION = "LOW_SATURATION"
    HIGH_MARGINAL_IMPACT = "HIGH_MARGINAL_IMPACT"
    HIGH_COST_EFFICIENCY = "HIGH_COST_EFFICIENCY"
    STRONG_EVIDENCE = "STRONG_EVIDENCE"
    HIGH_SCALABILITY = "HIGH_SCALABILITY"
    HIGH_IMPLEMENTATION_RISK = "HIGH_IMPLEMENTATION_RISK"
    LOW_EVIDENCE = "LOW_EVIDENCE"
    HIGH_SATURATION = "HIGH_SATURATION"
    BUDGET_CONSTRAINT = "BUDGET_CONSTRAINT"
    REGIONAL_CAP = "REGIONAL_CAP"
    MINIMUM_ALLOCATION = "MINIMUM_ALLOCATION"
    MISSING_DATA = "MISSING_DATA"
    DUE_DILIGENCE_FLAG = "DUE_DILIGENCE_FLAG"


class OptimizationStatus(str, Enum):
    """Lifecycle states of an optimization execution run."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AllocationStatus(str, Enum):
    """Status of an individual project allocation recommendation."""
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REALLOCATED = "REALLOCATED"


class VerificationStatus(str, Enum):
    """Evidence and due diligence verification states."""
    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    MISSING = "MISSING"
    FLAGGED = "FLAGGED"


class ConfidenceLevel(str, Enum):
    """Confidence levels for extraction and assessment signals."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class DueDiligenceRisk(str, Enum):
    """Risk tiers assessed for NGOs."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class ProposalStatus(str, Enum):
    """Lifecycle states of proposal document ingestion."""
    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    VALIDATION_REQUIRED = "VALIDATION_REQUIRED"
    READY = "READY"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class AuditEventType(str, Enum):
    """Audit trail event classifications."""
    PROPOSAL_CREATED = "PROPOSAL_CREATED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    EXTRACTION_STARTED = "EXTRACTION_STARTED"
    EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED"
    PROJECT_CREATED = "PROJECT_CREATED"
    IMPACT_DNA_CREATED = "IMPACT_DNA_CREATED"
    SATURATION_CALCULATED = "SATURATION_CALCULATED"
    DUE_DILIGENCE_COMPLETED = "DUE_DILIGENCE_COMPLETED"
    OPTIMIZATION_STARTED = "OPTIMIZATION_STARTED"
    OPTIMIZATION_COMPLETED = "OPTIMIZATION_COMPLETED"
    ALLOCATION_CREATED = "ALLOCATION_CREATED"
    REALLOCATION_STARTED = "REALLOCATION_STARTED"
    REALLOCATION_COMPLETED = "REALLOCATION_COMPLETED"
    WEIGHTS_CHANGED = "WEIGHTS_CHANGED"
    CONSTRAINTS_CHANGED = "CONSTRAINTS_CHANGED"
    ERROR_OCCURRED = "ERROR_OCCURRED"


# ---------------------------------------------------------------------------
# Calculation Versions (Rule 3 - Version Everything)
# ---------------------------------------------------------------------------

PROJECT_SCHEMA_VERSION: Final[str] = "project-v1"
DNA_SCHEMA_VERSION: Final[str] = "dna-v1"
SATURATION_CALCULATION_VERSION: Final[str] = "saturation-v1"
MARGINAL_CALCULATION_VERSION: Final[str] = "marginal-v1"
OPTIMIZER_CALCULATION_VERSION: Final[str] = "optimizer-v1"
API_VERSION: Final[str] = "api-v1"

CALCULATION_VERSIONS: Final[dict[str, str]] = {
    "project": PROJECT_SCHEMA_VERSION,
    "dna": DNA_SCHEMA_VERSION,
    "saturation": SATURATION_CALCULATION_VERSION,
    "marginal": MARGINAL_CALCULATION_VERSION,
    "optimizer": OPTIMIZER_CALCULATION_VERSION,
    "api": API_VERSION,
}


# ---------------------------------------------------------------------------
# Money Representation & Increments (Rule 4 - Integer Paise)
# ---------------------------------------------------------------------------

PAISE_PER_RUPEE: Final[int] = 100
RUPEES_PER_LAKH: Final[int] = 100_000
PAISE_PER_LAKH: Final[int] = RUPEES_PER_LAKH * PAISE_PER_RUPEE  # 10,000,000 paise = ₹1 lakh

DEFAULT_MARGINAL_INCREMENT_PAISE: Final[int] = PAISE_PER_LAKH  # ₹1 lakh in paise


# ---------------------------------------------------------------------------
# Score and Weight Bounds (Rule 5 - Deterministic Only)
# ---------------------------------------------------------------------------

SCORE_MIN: Final[float] = 0.0
SCORE_MAX: Final[float] = 1.0

WEIGHT_MIN: Final[float] = 0.0
WEIGHT_MAX: Final[float] = 1.0
WEIGHT_SUM_TARGET: Final[float] = 1.0
WEIGHT_SUM_TOLERANCE: Final[float] = 1e-5


# ---------------------------------------------------------------------------
# Saturation Interpretation Thresholds (Technical Contract Section 11)
# ---------------------------------------------------------------------------

SATURATION_VERY_LOW_MAX: Final[float] = 0.24
SATURATION_LOW_MAX: Final[float] = 0.49
SATURATION_HIGH_MAX: Final[float] = 0.74
SATURATION_VERY_HIGH_MAX: Final[float] = 1.00

SATURATION_INTERPRETATION_BANDS: Final[tuple[tuple[float, float, str], ...]] = (
    (0.00, SATURATION_VERY_LOW_MAX, "very low saturation"),
    (0.25, SATURATION_LOW_MAX, "low/moderate saturation"),
    (0.50, SATURATION_HIGH_MAX, "high saturation"),
    (0.75, SATURATION_VERY_HIGH_MAX, "very high saturation"),
)
