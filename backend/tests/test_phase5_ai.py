import io
from unittest.mock import MagicMock
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.ai import (
    AIPipeline,
    LLMClient,
    ProposalExtractor,
    ImpactDNAService,
    DueDiligenceService,
    PDFTextExtractor,
    Project,
    ImpactDNA,
    DueDiligenceReport,
    ExtractionResult,
    VerificationStatus,
    DueDiligenceRisk,
    ProjectSector,
)
from app.ai.due_diligence.service import CANONICAL_DISCLAIMER


def create_synthetic_proposal_pdf(title: str = "Jharkhand Clean Energy Clinic") -> bytes:
    """Helper to generate valid in-memory PDF bytes."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, f"Project Title: {title}")
    c.drawString(100, 730, "Target beneficiaries: 4,000 rural residents.")
    c.drawString(100, 710, "Requested Budget: INR 40,00,000.")
    c.save()
    return buffer.getvalue()


def test_pipeline_e2e_mock_mode():
    """Verify AIPipeline end-to-end flow in deterministic mock mode without live LLM."""
    pdf_bytes = create_synthetic_proposal_pdf("Assam Floating Health Clinic")
    pipeline = AIPipeline(llm_client=None)

    # 1. Process proposal PDF -> (ExtractionResult, ImpactDNA)
    extraction_res, dna = pipeline.process_proposal_pdf(
        pdf_bytes=pdf_bytes,
        document_id="DOC-5001",
        proposal_id="PRO-5001",
    )

    assert isinstance(extraction_res, ExtractionResult)
    assert extraction_res.proposal_id == "PRO-5001"
    assert extraction_res.document_id == "DOC-5001"
    assert extraction_res.schema_version == "extraction-v1"

    # Verify project details
    project = extraction_res.extracted_project
    assert isinstance(project, Project)
    assert project.schema_version == "project-v1"
    assert project.financials.requested_amount_paise == 250000000  # ₹25L in paise

    # Verify Impact DNA
    assert isinstance(dna, ImpactDNA)
    assert dna.schema_version == "dna-v1"
    assert dna.project_id == project.project_id
    assert dna.dna_id.startswith("DNA-")
    assert 0.0 <= dna.need_score <= 1.0
    assert 0.0 <= dna.cost_efficiency_score <= 1.0

    # 2. Evaluate NGO Due Diligence
    dd_report = pipeline.evaluate_ngo("NGO-5001")
    assert isinstance(dd_report, DueDiligenceReport)
    assert dd_report.ngo_id == "NGO-5001"
    assert dd_report.report_id.startswith("DD-")
    assert dd_report.model_version == "due-diligence-v1"
    assert dd_report.disclaimer == CANONICAL_DISCLAIMER
    assert len(dd_report.checks) > 0


def test_pipeline_e2e_with_mocked_llm():
    """Verify AIPipeline orchestrates live extraction and Impact DNA generation through mock LLMClient."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.model = "mock-pipeline-model"

    # Extraction output
    extraction_json = {
        "extracted_project": {
            "project_id": "PRJ-7001",
            "name": "Odisha Coastal Mangrove Shield",
            "ngo_id": "NGO-7001",
            "sector": "ENVIRONMENT",
            "geographies": [{"state": "Odisha", "district": "Kendrapara"}],
            "beneficiary_profile": {"target_count": 5000},
            "financials": {"requested_amount_paise": 300000000},
            "duration_months": 24,
        },
        "evidence": [
            {
                "evidence_id": "EVD-7001",
                "source_type": "PDF",
                "claim": "Will plant 100,000 mangrove saplings.",
                "confidence": 0.95,
                "verification_status": "VERIFIED",
            }
        ],
        "missing_fields": [],
        "warnings": [],
    }

    # Impact DNA output
    dna_json = {
        "dna_id": "DNA-7001",
        "project_id": "PRJ-7001",
        "need_score": 0.92,
        "expected_impact_score": 0.88,
        "cost_efficiency_score": 0.85,
        "evidence_strength_score": 0.80,
        "scalability_score": 0.75,
        "implementation_risk_score": 0.18,
        "beneficiary_reach": 5000,
        "estimated_impact_per_lakh": 16.67,
    }

    # Due Diligence output
    dd_json = {
        "report_id": "DD-7001",
        "ngo_id": "NGO-7001",
        "overall_status": "VERIFIED",
        "risk_level": "LOW",
        "checks": [],
    }

    mock_llm.generate_json.side_effect = [extraction_json, dna_json, dd_json]

    pipeline = AIPipeline(llm_client=mock_llm)
    pdf_bytes = create_synthetic_proposal_pdf("Odisha Mangrove Project")

    extraction_res, dna = pipeline.process_proposal_pdf(pdf_bytes, document_id="DOC-7001", proposal_id="PRO-7001")

    assert extraction_res.extracted_project.project_id == "PRJ-7001"
    assert extraction_res.extracted_project.financials.requested_amount_paise == 300000000
    assert dna.dna_id == "DNA-7001"
    assert dna.need_score == 0.92

    dd_report = pipeline.evaluate_ngo("NGO-7001")
    assert dd_report.report_id == "DD-7001"
    assert dd_report.disclaimer == CANONICAL_DISCLAIMER


def test_pipeline_rejects_corrupt_pdf():
    """Verify AIPipeline rejects invalid non-PDF bytes immediately before reaching LLM."""
    pipeline = AIPipeline(llm_client=None)
    invalid_bytes = b"This is not a PDF file."

    with pytest.raises(ValueError, match="FILE_INVALID"):
        pipeline.process_proposal_pdf(invalid_bytes, document_id="DOC-ERROR")


def test_top_level_exports_available():
    """Verify clean public exports from app.ai package for Member D."""
    import app.ai as ai_module

    expected_exports = [
        "AIPipeline",
        "LLMClient",
        "ProposalExtractor",
        "ImpactDNAService",
        "DueDiligenceService",
        "PDFTextExtractor",
        "Project",
        "ImpactDNA",
        "DueDiligenceReport",
        "ExtractionResult",
        "ProjectSector",
        "ProposalStatus",
        "VerificationStatus",
        "DueDiligenceRisk",
    ]

    for export_name in expected_exports:
        assert hasattr(ai_module, export_name), f"Missing export: {export_name}"
