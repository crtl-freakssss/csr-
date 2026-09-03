from typing import Any

from app.ai.client import LLMClient
from app.ai.extraction.pdf_parser import PDFTextExtractor
from app.ai.extraction.service import ProposalExtractor
from app.ai.impact_dna.service import ImpactDNAService
from app.ai.due_diligence.service import DueDiligenceService
from app.ai.schemas import (
    ExtractionResult,
    ImpactDNA,
    DueDiligenceReport,
)


class AIPipeline:
    """Unified high-level facade for all AI pipeline operations (Technical Contract Sections 4, 50, 54).
    
    Provides Member D (Backend/API) with a clean, decoupled interface to process proposals,
    generate Impact DNA fingerprints, and evaluate NGO due diligence without needing
    to handle internal prompt engineering, text extraction, or sanitization details.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client
        self.pdf_extractor = PDFTextExtractor()
        self.proposal_extractor = ProposalExtractor(llm_client=llm_client)
        self.impact_dna_service = ImpactDNAService(llm_client=llm_client)
        self.due_diligence_service = DueDiligenceService(llm_client=llm_client)

    def process_proposal_pdf(
        self,
        pdf_bytes: bytes,
        document_id: str,
        proposal_id: str = "PRO-0001",
    ) -> tuple[ExtractionResult, ImpactDNA]:
        """End-to-end proposal intake pipeline:
        
        1. Validates PDF magic bytes & extracts cleaned text.
        2. Sanitizes text against prompt injections.
        3. Extracts structured Project, Evidence, and Missing Fields.
        4. Generates multi-dimensional Impact DNA fingerprint.
        
        Returns:
            tuple[ExtractionResult, ImpactDNA]
        """
        # 1. Parse and sanitize text from raw PDF bytes
        extracted_text = self.pdf_extractor.extract_text_from_bytes(pdf_bytes)

        # 2. Extract structured proposal project
        extraction_result = self.proposal_extractor.extract(
            document_text=extracted_text,
            document_id=document_id,
            proposal_id=proposal_id,
        )

        # 3. Generate Impact DNA fingerprint from extracted project
        impact_dna = self.impact_dna_service.generate(
            project=extraction_result.extracted_project
        )

        return extraction_result, impact_dna

    def evaluate_ngo(
        self,
        ngo_id: str,
        ngo_data: dict[str, Any] | None = None,
        documents: list[str] | None = None,
    ) -> DueDiligenceReport:
        """Evaluates NGO disclosures and compliance records, returning an evidence-based DueDiligenceReport."""
        return self.due_diligence_service.evaluate(
            ngo_id=ngo_id,
            ngo_data=ngo_data,
            documents=documents,
        )
