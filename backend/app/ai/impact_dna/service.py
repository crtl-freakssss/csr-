from typing import Any
from pydantic import ValidationError

from app.ai.schemas import ImpactDNA, Project
from app.ai.prompts.builder import PromptBuilder
from app.ai.client import LLMClient, ModelOutputInvalidError


class ImpactDNAService:
    """Impact DNA generation service supporting deterministic mock and live LLM integration."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.prompt_builder = prompt_builder or PromptBuilder()

    def generate(self, project: Project) -> ImpactDNA:
        """Generate structured Impact DNA fingerprint from Project data."""
        if self.llm_client is None:
            return self._generate_mock(project)

        prompt = self.prompt_builder.build_impact_dna_prompt(project.model_dump_json())
        raw_json = self.llm_client.generate_json(prompt)

        return self._parse_and_validate(raw_json, project)

    def _parse_and_validate(self, raw_json: dict[str, Any], project: Project) -> ImpactDNA:
        """Validate raw JSON against ImpactDNA schema, clamping/checking bounds."""
        try:
            dna_suffix = project.project_id.split("-")[-1] if "-" in project.project_id else "0001"
            raw_json.setdefault("dna_id", f"DNA-{dna_suffix}")
            raw_json.setdefault("project_id", project.project_id)
            raw_json.setdefault("beneficiary_reach", project.beneficiary_profile.target_count)

            # Auto-calculate impact per lakh if missing or zero
            budget_lakhs = project.financials.requested_amount_paise / 10_000_000
            if "estimated_impact_per_lakh" not in raw_json and budget_lakhs > 0:
                raw_json["estimated_impact_per_lakh"] = round(project.beneficiary_profile.target_count / budget_lakhs, 2)

            raw_json.setdefault("missing_fields", [])
            raw_json.setdefault("extraction_confidence", 0.90)
            raw_json.setdefault("model_name", self.llm_client.model if self.llm_client else "mock-dna-generator")
            raw_json.setdefault("prompt_version", PromptBuilder.IMPACT_DNA_PROMPT_VERSION)
            raw_json.setdefault("schema_version", "dna-v1")

            return ImpactDNA.model_validate(raw_json)
        except (ValidationError, TypeError) as exc:
            raise ModelOutputInvalidError(f"MODEL_OUTPUT_INVALID: {exc}") from exc

    def _generate_mock(self, project: Project) -> ImpactDNA:
        """Deterministic mock fallback when no LLMClient is configured."""
        # 1 Lakh INR = 10,000,000 paise
        budget_lakhs = project.financials.requested_amount_paise / 10_000_000
        reach = project.beneficiary_profile.target_count
        impact_per_lakh = reach / budget_lakhs if budget_lakhs > 0 else 0.0

        dna_suffix = project.project_id.split("-")[-1] if "-" in project.project_id else "0001"

        return ImpactDNA(
            dna_id=f"DNA-{dna_suffix}",
            project_id=project.project_id,
            need_score=0.85,
            expected_impact_score=0.78,
            cost_efficiency_score=0.82,
            evidence_strength_score=0.74,
            scalability_score=0.70,
            implementation_risk_score=0.25,
            beneficiary_reach=reach,
            estimated_impact_per_lakh=round(impact_per_lakh, 2),
            missing_fields=[],
            extraction_confidence=0.90,
            model_name="mock-dna-generator-v1",
            prompt_version="impact_dna_v1",
            schema_version="dna-v1",
        )
