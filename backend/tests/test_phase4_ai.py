from unittest.mock import MagicMock
import pytest

from app.ai.client import LLMClient, ModelOutputInvalidError
from app.ai.due_diligence.service import DueDiligenceService, CANONICAL_DISCLAIMER
from app.ai.due_diligence.evaluator import derive_overall_risk
from app.ai.schemas import (
    DueDiligenceReport,
    DueDiligenceCheck,
    DueDiligenceRisk,
    VerificationStatus,
)


def test_due_diligence_mock_fallback():
    """Verify fallback DueDiligenceService produces valid report without live LLM."""
    service = DueDiligenceService(llm_client=None)
    report = service.evaluate("NGO-0001")

    assert isinstance(report, DueDiligenceReport)
    assert report.report_id.startswith("DD-")
    assert report.ngo_id == "NGO-0001"
    assert len(report.checks) >= 2
    assert isinstance(report.overall_status, VerificationStatus)
    assert isinstance(report.risk_level, DueDiligenceRisk)
    assert report.disclaimer == CANONICAL_DISCLAIMER


def test_due_diligence_with_mocked_llm():
    """Verify DueDiligenceService parses valid LLM response into DueDiligenceReport."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.model = "mock-gpt-4o"
    mock_llm.generate_json.return_value = {
        "report_id": "DD-9999",
        "ngo_id": "NGO-9999",
        "overall_status": "VERIFIED",
        "risk_level": "LOW",
        "checks": [
            {
                "check_name": "12A / 80G Registration",
                "status": "VERIFIED",
                "source": "Income Tax Department",
                "evidence": "Valid through AY 2028.",
                "confidence": 0.95,
                "checked_at": "2026-09-03T12:00:00Z",
            }
        ],
        "flags": [],
        "missing_documents": [],
    }

    service = DueDiligenceService(llm_client=mock_llm)
    report = service.evaluate("NGO-9999")

    assert isinstance(report, DueDiligenceReport)
    assert report.report_id == "DD-9999"
    assert report.ngo_id == "NGO-9999"
    assert report.overall_status == VerificationStatus.VERIFIED
    assert report.risk_level == DueDiligenceRisk.LOW
    assert len(report.checks) == 1
    assert report.checks[0].status == VerificationStatus.VERIFIED
    assert report.disclaimer == CANONICAL_DISCLAIMER


def test_due_diligence_invalid_enum_rejection():
    """Verify service rejects invalid enum values from the LLM with ModelOutputInvalidError."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.model = "mock-gpt-4o"
    # Return invalid enum "COMPLETELY_APPROVED"
    mock_llm.generate_json.return_value = {
        "report_id": "DD-9999",
        "ngo_id": "NGO-9999",
        "overall_status": "COMPLETELY_APPROVED",
        "risk_level": "SAFE",
        "checks": [],
    }

    service = DueDiligenceService(llm_client=mock_llm)
    with pytest.raises(ModelOutputInvalidError) as exc_info:
        service.evaluate("NGO-9999")

    assert exc_info.value.code == "MODEL_OUTPUT_INVALID"


def test_due_diligence_risk_derivation_logic():
    """Verify derive_overall_risk correctly categorizes risk levels according to contract rules."""
    check_verified = DueDiligenceCheck(
        check_name="12A Registration",
        status=VerificationStatus.VERIFIED,
        source="Income Tax Portal",
        evidence="Active registration",
        confidence=0.95,
        checked_at="2026-09-03T12:00:00Z",
    )
    check_flagged = DueDiligenceCheck(
        check_name="FCRA Compliance",
        status=VerificationStatus.FLAGGED,
        source="MHA Watchlist",
        evidence="Suspended license",
        confidence=0.90,
        checked_at="2026-09-03T12:00:00Z",
    )
    check_missing = DueDiligenceCheck(
        check_name="12A / 80G Tax Exemption",
        status=VerificationStatus.MISSING,
        source="IT Department",
        evidence="No filing found",
        confidence=0.95,
        checked_at="2026-09-03T12:00:00Z",
    )

    # 1. Clean checks -> (VERIFIED, LOW)
    status, risk = derive_overall_risk([check_verified], flags=[])
    assert status == VerificationStatus.VERIFIED
    assert risk == DueDiligenceRisk.LOW

    # 2. Flagged check -> (FLAGGED, HIGH)
    status, risk = derive_overall_risk([check_verified, check_flagged], flags=[])
    assert status == VerificationStatus.FLAGGED
    assert risk in (DueDiligenceRisk.HIGH, DueDiligenceRisk.CRITICAL)

    # 3. Missing critical registration check -> (FLAGGED, HIGH)
    status, risk = derive_overall_risk([check_missing], flags=[])
    assert status == VerificationStatus.FLAGGED
    assert risk == DueDiligenceRisk.HIGH

    # 4. Critical flag keyword present -> (FLAGGED, CRITICAL or HIGH)
    status, risk = derive_overall_risk([check_verified], flags=["ACTIVE_CRIMINAL_LITIGATION"])
    assert status == VerificationStatus.FLAGGED
    assert risk in (DueDiligenceRisk.HIGH, DueDiligenceRisk.CRITICAL)


def test_mandatory_disclaimer_preservation():
    """Verify service forces the canonical legal disclaimer even if LLM returns a hallucinated one."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.model = "mock-gpt-4o"
    mock_llm.generate_json.return_value = {
        "report_id": "DD-9999",
        "ngo_id": "NGO-9999",
        "overall_status": "VERIFIED",
        "risk_level": "LOW",
        "checks": [],
        "disclaimer": "This NGO is 100% legally certified and guaranteed by the Government.",  # Hallucinated!
    }

    service = DueDiligenceService(llm_client=mock_llm)
    report = service.evaluate("NGO-9999")

    # MUST be overwritten with the canonical disclaimer
    assert report.disclaimer == CANONICAL_DISCLAIMER
    assert "100% legally certified" not in report.disclaimer
