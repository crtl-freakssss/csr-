import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from app.ai.schemas import (
    Project,
    ImpactDNA,
    DueDiligenceReport,
    ExtractionResult,
    VerificationStatus,
    DueDiligenceRisk,
    ProjectSector,
)
from app.ai.extraction.service import ProposalExtractor
from app.ai.impact_dna.service import ImpactDNAService
from app.ai.due_diligence.service import DueDiligenceService


def test_mock_proposal_extractor_conforms_to_contract():
    """Verify extraction result structure, ID formats, and integer paise precision."""
    extractor = ProposalExtractor()
    result = extractor.extract(
        document_text="Sample text content",
        document_id="DOC-0001",
        proposal_id="PRO-0001",
    )

    assert isinstance(result, ExtractionResult)
    assert result.proposal_id == "PRO-0001"
    assert result.document_id == "DOC-0001"
    assert result.schema_version == "extraction-v1"
    assert 0.0 <= result.extraction_confidence <= 1.0

    # Project checks
    project = result.extracted_project
    assert isinstance(project, Project)
    assert project.project_id.startswith("PRJ-")
    assert project.schema_version == "project-v1"

    # Monetary checks - strictly integer paise
    assert isinstance(project.financials.requested_amount_paise, int)
    assert project.financials.requested_amount_paise == 250000000
    assert project.financials.current_funding_paise >= 0
    assert project.financials.other_funding_paise >= 0

    # Evidence items check
    assert len(result.evidence) > 0
    for item in result.evidence:
        assert item.evidence_id.startswith("EVD-")
        assert 0.0 <= item.confidence <= 1.0
        assert isinstance(item.verification_status, VerificationStatus)


def test_mock_impact_dna_scores_bounded():
    """Verify all 6 DNA scores are strictly bounded between 0.0 and 1.0."""
    extractor = ProposalExtractor()
    extraction_res = extractor.extract(
        document_text="Sample text content",
        document_id="DOC-0001",
        proposal_id="PRO-0001",
    )

    dna_service = ImpactDNAService()
    dna = dna_service.generate(extraction_res.extracted_project)

    assert isinstance(dna, ImpactDNA)
    assert dna.dna_id.startswith("DNA-")
    assert dna.project_id == extraction_res.extracted_project.project_id
    assert dna.schema_version == "dna-v1"

    # 6 normalized scoring dimensions
    assert 0.0 <= dna.need_score <= 1.0
    assert 0.0 <= dna.expected_impact_score <= 1.0
    assert 0.0 <= dna.cost_efficiency_score <= 1.0
    assert 0.0 <= dna.evidence_strength_score <= 1.0
    assert 0.0 <= dna.scalability_score <= 1.0
    assert 0.0 <= dna.implementation_risk_score <= 1.0

    assert dna.beneficiary_reach >= 0
    assert dna.estimated_impact_per_lakh >= 0.0
    assert 0.0 <= dna.extraction_confidence <= 1.0


def test_mock_due_diligence_report_contract():
    """Verify enum integrity, checks, and required legal disclaimer text."""
    dd_service = DueDiligenceService()
    report = dd_service.evaluate("NGO-0001")

    assert isinstance(report, DueDiligenceReport)
    assert report.report_id.startswith("DD-")
    assert report.ngo_id == "NGO-0001"
    assert report.model_version == "due-diligence-v1"
    assert isinstance(report.overall_status, VerificationStatus)
    assert isinstance(report.risk_level, DueDiligenceRisk)

    # Mandatory legal disclaimer text according to contract
    expected_disclaimer = (
        "This report is an evidence and risk-assessment layer "
        "and does not constitute legal or regulatory certification."
    )
    assert report.disclaimer == expected_disclaimer

    assert len(report.checks) > 0
    for check in report.checks:
        assert isinstance(check.status, VerificationStatus)
        assert 0.0 <= check.confidence <= 1.0
        assert check.checked_at


def test_seed_dataset_validation():
    """Load data/seed/projects.json, parse into Project, verify count >= 15, states >= 6, and null district edge cases."""
    # Find data/seed/projects.json relative to project root
    root_dir = Path(__file__).resolve().parent.parent.parent
    seed_file = root_dir / "data" / "seed" / "projects.json"

    assert seed_file.exists(), f"Seed file not found at {seed_file}"

    with open(seed_file, "r", encoding="utf-8") as f:
        raw_projects = json.load(f)

    assert len(raw_projects) >= 15, f"Expected at least 15 projects, got {len(raw_projects)}"

    parsed_projects: list[Project] = []
    states = set()
    has_null_district = False

    for item in raw_projects:
        project = Project.model_validate(item)
        parsed_projects.append(project)

        # Money must be strictly integer paise
        assert isinstance(project.financials.requested_amount_paise, int)
        assert project.financials.requested_amount_paise > 0

        for geo in project.geographies:
            states.add(geo.state)
            if geo.district is None:
                has_null_district = True

    assert len(states) >= 6, f"Expected at least 6 states, got {len(states)}: {states}"
    assert has_null_district, "Expected at least one project with district: null as an edge case"


def test_rejection_of_invalid_score_bounds():
    """Verify Pydantic raises ValidationError when a score is outside [0.0, 1.0]."""
    valid_payload = {
        "dna_id": "DNA-9999",
        "project_id": "PRJ-9999",
        "need_score": 0.85,
        "expected_impact_score": 0.75,
        "cost_efficiency_score": 0.80,
        "evidence_strength_score": 0.70,
        "scalability_score": 0.65,
        "implementation_risk_score": 0.20,
        "beneficiary_reach": 1000,
        "estimated_impact_per_lakh": 10.0,
        "missing_fields": [],
        "extraction_confidence": 0.90,
        "model_name": "test-model",
        "prompt_version": "test-v1",
        "schema_version": "dna-v1",
    }

    # Score > 1.0 must fail
    invalid_over = valid_payload.copy()
    invalid_over["need_score"] = 1.05
    with pytest.raises(ValidationError):
        ImpactDNA.model_validate(invalid_over)

    # Score < 0.0 must fail
    invalid_under = valid_payload.copy()
    invalid_under["cost_efficiency_score"] = -0.1
    with pytest.raises(ValidationError):
        ImpactDNA.model_validate(invalid_under)

    # Financials requested_amount_paise <= 0 must fail
    with pytest.raises(ValidationError):
        from app.ai.schemas import Financials
        Financials(requested_amount_paise=0)
