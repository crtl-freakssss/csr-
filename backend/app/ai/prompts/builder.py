from pathlib import Path
from app.ai.prompts.sanitizer import PromptSanitizer


class PromptBuilder:
    """Prompt builder utility adhering to Technical Contract Section 68."""

    PROPOSAL_EXTRACTION_PROMPT_VERSION = "proposal_extraction_v1"
    IMPACT_DNA_PROMPT_VERSION = "impact_dna_v1"
    DUE_DILIGENCE_PROMPT_VERSION = "due_diligence_v1"

    def __init__(self, prompts_dir: Path | None = None) -> None:
        self.prompts_dir = prompts_dir or Path(__file__).resolve().parent
        self.sanitizer = PromptSanitizer()

    def _load_template(self, filename: str) -> str:
        template_path = self.prompts_dir / filename
        if not template_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {template_path}")
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()

    def build_extraction_prompt(self, raw_pdf_text: str) -> str:
        """Sanitize raw text, wrap in untrusted document boundary, and inject into extraction prompt."""
        template = self._load_template(f"{self.PROPOSAL_EXTRACTION_PROMPT_VERSION}.txt")
        bounded_payload = self.sanitizer.wrap_in_document_boundary(raw_pdf_text)
        return template.replace("{document_payload}", bounded_payload)

    def build_impact_dna_prompt(self, project_json: str) -> str:
        """Inject validated project JSON into Impact DNA prompt template."""
        template = self._load_template(f"{self.IMPACT_DNA_PROMPT_VERSION}.txt")
        return template.replace("{project_payload}", project_json)

    def build_due_diligence_prompt(self, ngo_info_json: str) -> str:
        """Inject NGO information JSON into due diligence prompt template."""
        template = self._load_template(f"{self.DUE_DILIGENCE_PROMPT_VERSION}.txt")
        return template.replace("{ngo_payload}", ngo_info_json)
