from typing import Any
from pydantic import ValidationError

from app.ai.schemas import (
    ExtractionResult,
    Project,
    Geography,
    BeneficiaryProfile,
    Financials,
    ImpactMetric,
    EvidenceItem,
    ProjectSector,
    VerificationStatus,
)
from app.ai.prompts.builder import PromptBuilder
from app.ai.client import LLMClient, ModelOutputInvalidError


class ProposalExtractor:
    """Proposal extractor supporting both deterministic mock and live LLM integration."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder()

    def extract(
        self,
        document_text: str,
        document_id: str,
        proposal_id: str = "PRO-0001",
    ) -> ExtractionResult:
        """Extract structured proposal data into an ExtractionResult."""
        if self.llm_client is None:
            return self._extract_mock(document_text, document_id, proposal_id)

        prompt = self.prompt_builder.build_extraction_prompt(document_text)
        raw_json = self.llm_client.generate_json(prompt)

        return self._parse_and_validate(raw_json, document_id, proposal_id)

    def _normalize_financials(self, fin: dict[str, Any]) -> None:
        """Ensure requested_amount_paise is strictly an integer. Convert rupees to paise if needed."""
        if "requested_amount_inr" in fin and "requested_amount_paise" not in fin:
            fin["requested_amount_paise"] = int(round(float(fin["requested_amount_inr"]) * 100))
        elif "requested_amount" in fin and "requested_amount_paise" not in fin:
            val = float(fin["requested_amount"])
            # If the value is small (< 10M), it's likely in rupees, convert to paise
            fin["requested_amount_paise"] = int(round(val * 100))
        elif "requested_amount_paise" in fin:
            fin["requested_amount_paise"] = int(fin["requested_amount_paise"])

    def _parse_and_validate(
        self,
        raw_json: dict[str, Any],
        document_id: str,
        proposal_id: str,
    ) -> ExtractionResult:
        """Validate raw JSON payload against ExtractionResult schema."""
        try:
            # Handle whether project data is nested under extracted_project or flat
            if "extracted_project" in raw_json and isinstance(raw_json["extracted_project"], dict):
                project_dict = raw_json["extracted_project"]
            else:
                project_dict = {
                    k: v for k, v in raw_json.items()
                    if k in Project.model_fields
                }
                raw_json["extracted_project"] = project_dict

            # Normalize financials
            if "financials" in project_dict and isinstance(project_dict["financials"], dict):
                self._normalize_financials(project_dict["financials"])

            # Ensure default metadata fields
            raw_json.setdefault("proposal_id", proposal_id)
            raw_json.setdefault("document_id", document_id)
            raw_json.setdefault("schema_version", "extraction-v1")
            raw_json.setdefault("prompt_version", PromptBuilder.PROPOSAL_EXTRACTION_PROMPT_VERSION)
            raw_json.setdefault("model_name", self.llm_client.model if self.llm_client else "mock-extractor")
            raw_json.setdefault("evidence", [])
            raw_json.setdefault("missing_fields", [])
            raw_json.setdefault("warnings", [])
            raw_json.setdefault("extraction_confidence", 0.85)

            return ExtractionResult.model_validate(raw_json)
        except (ValidationError, TypeError) as exc:
            raise ModelOutputInvalidError(f"MODEL_OUTPUT_INVALID: {exc}") from exc

    def _extract_mock(
        self,
        document_text: str,
        document_id: str,
        proposal_id: str,
    ) -> ExtractionResult:
        """Deterministic mock fallback when no LLMClient is configured."""
        project = Project(
            project_id="PRJ-0001",
            name="Rural Digital Literacy Initiative",
            ngo_id="NGO-0001",
            sector=ProjectSector.EDUCATION,
            geographies=[
                Geography(state="Bihar", district="Gaya", block="Bodh Gaya")
            ],
            beneficiary_profile=BeneficiaryProfile(
                target_count=3500,
                groups=["students", "rural_youth"],
                age_ranges=["10-18"],
                vulnerable_groups=["first_generation_learners"],
            ),
            financials=Financials(
                requested_amount_paise=250000000,  # ₹25,00,000 in integer paise
                current_funding_paise=0,
                other_funding_paise=0,
            ),
            duration_months=12,
            impact_metrics=[
                ImpactMetric(
                    metric_id="MET-001",
                    name="Students certified in basic digital literacy",
                    unit="students",
                    baseline=0.0,
                    target=3500.0,
                    measurement_method="Standardized online assessment",
                )
            ],
            description="Equipping rural high schools with computer labs and delivering foundational digital literacy curriculum.",
            schema_version="project-v1",
        )

        evidence = [
            EvidenceItem(
                evidence_id="EVD-0001",
                source_type="PDF_PROPOSAL",
                source_reference="Page 4, Paragraph 2",
                claim="Previous cohort achieved 92% completion rate across 10 centers.",
                extracted_value="92% completion",
                confidence=0.88,
                verification_status=VerificationStatus.PARTIALLY_VERIFIED,
            )
        ]

        return ExtractionResult(
            proposal_id=proposal_id,
            document_id=document_id,
            extracted_project=project,
            evidence=evidence,
            missing_fields=["district_survey_data"],
            warnings=["Target completion timeline is aggressive for winter months."],
            extraction_confidence=0.86,
            model_name="mock-extractor-v1",
            prompt_version="proposal_extraction_v1",
            schema_version="extraction-v1",
        )
