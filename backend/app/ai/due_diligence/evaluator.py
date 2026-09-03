from app.ai.schemas import (
    DueDiligenceCheck,
    DueDiligenceRisk,
    VerificationStatus,
)

CORE_DUE_DILIGENCE_CRITERIA = {
    "12A_80G_STATUS": "Income Tax exemption validity under Sections 12A and 80G.",
    "FCRA_COMPLIANCE": "Foreign Contribution Regulation Act compliance and designated bank linkage.",
    "FINANCIAL_AUDIT_COMPLETENESS": "Audited balance sheets, P&L, and auditor reports for past 2-3 fiscal years.",
    "GOVERNANCE_DISCLOSURE": "Board structure, executive compensation, key trustees, and conflict of interest disclosures.",
    "PAST_IMPACT_RECORD": "Verifiable track record of executed programs, beneficiary outreach, and published annual reports.",
}


def derive_overall_risk(
    checks: list[DueDiligenceCheck],
    flags: list[str] | None = None,
) -> tuple[VerificationStatus, DueDiligenceRisk]:
    """Derives aggregate verification status and risk level based on checks and risk flags.
    
    Technical Contract Rules:
    - If any check is FLAGGED or a critical check is MISSING, or flags exist: returns (FLAGGED, HIGH/CRITICAL).
    - If key checks are PARTIALLY_VERIFIED or UNVERIFIED without critical flags: returns (PARTIALLY_VERIFIED, MEDIUM).
    - If all checks are VERIFIED and flags is empty: returns (VERIFIED, LOW).
    """
    flags = flags or []

    critical_flag_keywords = {"LITIGATION", "CRIMINAL", "ADVERSE", "FRAUD", "REVOKED", "EXPIRED", "CRITICAL"}
    has_critical_flags = any(
        any(keyword in flag.upper() for keyword in critical_flag_keywords)
        for flag in flags
    )

    has_flagged_check = any(c.status == VerificationStatus.FLAGGED for c in checks)
    has_missing_critical = any(
        c.status == VerificationStatus.MISSING
        for c in checks
        if any(crit in c.check_name.lower() for crit in ["12a", "80g", "tax", "fcra", "registration"])
    )

    if has_critical_flags or has_flagged_check or has_missing_critical:
        risk = DueDiligenceRisk.CRITICAL if (has_critical_flags and has_flagged_check) else DueDiligenceRisk.HIGH
        return VerificationStatus.FLAGGED, risk

    has_partial_or_unverified = any(
        c.status in (VerificationStatus.PARTIALLY_VERIFIED, VerificationStatus.UNVERIFIED, VerificationStatus.MISSING)
        for c in checks
    )

    if has_partial_or_unverified or len(flags) > 0:
        return VerificationStatus.PARTIALLY_VERIFIED, DueDiligenceRisk.MEDIUM

    return VerificationStatus.VERIFIED, DueDiligenceRisk.LOW
