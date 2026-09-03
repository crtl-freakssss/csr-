import json
from typing import Any
from pydantic import ValidationError

from app.ai.schemas import (
    DueDiligenceReport,
    DueDiligenceCheck,
    DueDiligenceRisk,
    VerificationStatus,
)
from app.ai.prompts.builder import PromptBuilder
from app.ai.client import LLMClient, ModelOutputInvalidError
from app.ai.due_diligence.evaluator import derive_overall_risk

CANONICAL_DISCLAIMER = (
    "This report is an evidence and risk-assessment layer "
    "and does not constitute legal or regulatory certification."
)


class DueDiligenceService:
    """Due diligence evidence and risk assessment service adhering to Technical Contract Section 18."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder()

    def evaluate(
        self,
        ngo_id: str,
        ngo_data: dict[str, Any] | None = None,
        documents: list[str] | None = None,
    ) -> DueDiligenceReport:
        """Evaluates an NGO against due diligence criteria, returning a DueDiligenceReport."""
        if self.llm_client is None:
            return self._evaluate_mock(ngo_id)

        payload = ngo_data or {"ngo_id": ngo_id, "documents": documents or []}
        prompt = self.prompt_builder.build_due_diligence_prompt(json.dumps(payload))

        raw_json = self.llm_client.generate_json(prompt)
        return self._parse_and_validate(raw_json, ngo_id)

    def _parse_and_validate(
        self,
        raw_json: dict[str, Any],
        ngo_id: str,
    ) -> DueDiligenceReport:
        """Validate LLM output against DueDiligenceReport schema, enforcing canonical disclaimer."""
        try:
            suffix = ngo_id.split("-")[-1] if "-" in ngo_id else "0001"
            raw_json.setdefault("report_id", f"DD-{suffix}")
            raw_json.setdefault("ngo_id", ngo_id)
            raw_json.setdefault("model_version", "due-diligence-v1")
            raw_json.setdefault("model_name", self.llm_client.model if self.llm_client else "mock-due-diligence")
            raw_json.setdefault("checks", [])
            raw_json.setdefault("flags", [])
            raw_json.setdefault("missing_documents", [])

            # NON-NEGOTIABLE: Enforce exact contract disclaimer regardless of LLM generation
            raw_json["disclaimer"] = CANONICAL_DISCLAIMER

            report = DueDiligenceReport.model_validate(raw_json)
            return report
        except (ValidationError, TypeError) as exc:
            raise ModelOutputInvalidError(f"MODEL_OUTPUT_INVALID: {exc}") from exc

    def _evaluate_mock(self, ngo_id: str) -> DueDiligenceReport:
        """Deterministic mock fallback when no LLMClient is configured."""
        suffix = ngo_id.split("-")[-1] if "-" in ngo_id else "0001"

        checks = [
            DueDiligenceCheck(
                check_name="12A / 80G Tax Exemption Status",
                status=VerificationStatus.VERIFIED,
                source="Income Tax Department Filing",
                evidence="Valid 12A/80G registrations verified through AY 2027-28.",
                confidence=0.95,
                checked_at="2026-09-03T12:00:00Z",
            ),
            DueDiligenceCheck(
                check_name="MCA CSR-1 Registration",
                status=VerificationStatus.VERIFIED,
                source="Ministry of Corporate Affairs Portal",
                evidence="CSR-1 registration is active with valid CIN linkage.",
                confidence=0.92,
                checked_at="2026-09-03T12:00:00Z",
            ),
            DueDiligenceCheck(
                check_name="Audited Financials (3 Years)",
                status=VerificationStatus.PARTIALLY_VERIFIED,
                source="Annual Audit Filing",
                evidence="Audited balance sheets submitted for FY22 and FY23; FY24 awaiting final signoff.",
                confidence=0.80,
                checked_at="2026-09-03T12:00:00Z",
            ),
            DueDiligenceCheck(
                check_name="Litigation & Regulatory Screening",
                status=VerificationStatus.VERIFIED,
                source="eCourts and Regulatory Watchlist",
                evidence="No adverse civil or criminal judgments identified.",
                confidence=0.88,
                checked_at="2026-09-03T12:00:00Z",
            ),
        ]

        return DueDiligenceReport(
            report_id=f"DD-{suffix}",
            ngo_id=ngo_id,
            overall_status=VerificationStatus.PARTIALLY_VERIFIED,
            risk_level=DueDiligenceRisk.LOW,
            checks=checks,
            flags=["FY24_AUDIT_PENDING"],
            missing_documents=["audited_statement_fy26.pdf"],
            model_name="mock-due-diligence-v1",
            model_version="due-diligence-v1",
            disclaimer=CANONICAL_DISCLAIMER,
        )
