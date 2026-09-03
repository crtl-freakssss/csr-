"""FastAPI integration test suite for AllocateAI Decision Engine API (Member C Phase 6).

Verifies:
1. POST /api/v1/optimize success
2. POST /api/v1/optimize invalid body (HTTP 422)
3. POST /api/v1/simulate success
4. POST /api/v1/simulate invalid increment (HTTP 400 or 422)
5. GET /api/v1/health (deterministic health status)
6. GET /api/v1/version (engine and schema versions)
7. API response contains explainability metadata
8. API deterministic repeatability (identical SHA-256 hash)
9. API returns optimization_audit with exact financial totals
10. API returns allocation_explanation on every allocation
"""

import hashlib
import json
import pytest
from fastapi.testclient import TestClient

from backend.app.engine.constants import (
    API_VERSION,
    CALCULATION_VERSIONS,
    DEFAULT_MARGINAL_INCREMENT_PAISE,
    OPTIMIZER_CALCULATION_VERSION,
)
from backend.app.main import app

client = TestClient(app)


@pytest.fixture
def valid_optimize_payload() -> dict:
    """Canonical valid optimize request payload targeting seed projects."""
    return {
        "budget_paise": 30_000_000,
        "project_ids": ["PRJ-0001", "PRJ-0002"],
        "weights": {
            "need": 0.20,
            "marginal_impact": 0.25,
            "cost_efficiency": 0.20,
            "evidence": 0.15,
            "scalability": 0.10,
            "equity": 0.10,
            "risk_penalty": 0.10,
        },
        "constraints": {
            "max_allocation_per_project_paise": None,
            "max_allocation_per_region_paise": None,
            "minimum_allocation_per_project_paise": None,
            "require_full_budget_allocation": True,
            "regional_equity_enabled": True,
        },
        "marginal_increment_paise": 10_000_000,
    }


# ---------------------------------------------------------------------------
# Test 1: POST /api/v1/optimize Success
# ---------------------------------------------------------------------------

def test_1_post_optimize_success(valid_optimize_payload: dict):
    """POST /api/v1/optimize returns HTTP 200 and validated OptimizationResult."""
    response = client.post("/api/v1/optimize", json=valid_optimize_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["budget_paise"] == 30_000_000
    assert data["allocated_paise"] == 30_000_000
    assert data["unallocated_paise"] == 0
    assert len(data["allocations"]) == 2
    assert "portfolio_breakdown" in data
    assert "optimization_audit" in data


# ---------------------------------------------------------------------------
# Test 2: POST /api/v1/optimize Invalid Body
# ---------------------------------------------------------------------------

def test_2_post_optimize_invalid_body():
    """POST /api/v1/optimize with invalid structure returns HTTP 422 with structured error."""
    bad_payload = {
        "budget_paise": -500,  # Negative budget
        "project_ids": [],     # Empty list
    }
    response = client.post("/api/v1/optimize", json=bad_payload)
    assert response.status_code == 422

    error_data = response.json()
    assert "error" in error_data
    assert "code" in error_data
    assert "message" in error_data


# ---------------------------------------------------------------------------
# Test 3: POST /api/v1/simulate Success
# ---------------------------------------------------------------------------

def test_3_post_simulate_success():
    """POST /api/v1/simulate returns HTTP 200 with MarginalImpactResult."""
    sim_payload = {
        "project_id": "PRJ-0001",
        "increment_paise": 10_000_000,
    }
    response = client.post("/api/v1/simulate", json=sim_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["project_id"] == "PRJ-0001"
    assert data["increment_paise"] == 10_000_000
    assert 0.0 <= data["marginal_impact_score"] <= 1.0
    assert 0.0 <= data["diminishing_return_factor"] <= 1.0
    assert data["incremental_impact"] > 0.0


# ---------------------------------------------------------------------------
# Test 4: POST /api/v1/simulate Invalid Increment
# ---------------------------------------------------------------------------

def test_4_post_simulate_invalid_increment():
    """POST /api/v1/simulate with non-positive increment returns HTTP 422 or 400."""
    bad_payload = {
        "project_id": "PRJ-0001",
        "increment_paise": 0,  # Zero increment
    }
    response = client.post("/api/v1/simulate", json=bad_payload)
    assert response.status_code in [400, 422]

    error_data = response.json()
    assert "error" in error_data
    assert "message" in error_data


# ---------------------------------------------------------------------------
# Test 5: GET /api/v1/health
# ---------------------------------------------------------------------------

def test_5_get_health():
    """GET /api/v1/health returns deterministic health payload without timestamps."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_version"] == API_VERSION
    assert data["optimizer_version"] == OPTIMIZER_CALCULATION_VERSION
    assert data["uptime"] == "deterministic"
    assert "timestamp" not in data
    assert "engines" in data
    assert data["engines"]["scoring"] == "scoring-v1"


# ---------------------------------------------------------------------------
# Test 6: GET /api/v1/version
# ---------------------------------------------------------------------------

def test_6_get_version():
    """GET /api/v1/version returns engine and schema version metadata."""
    response = client.get("/api/v1/version")
    assert response.status_code == 200

    data = response.json()
    assert data["api"] == API_VERSION
    assert data["engines"]["optimizer"] == OPTIMIZER_CALCULATION_VERSION
    assert data["schema_versions"]["project"] == "project-v1"
    assert data["schema_versions"]["dna"] == "dna-v1"


# ---------------------------------------------------------------------------
# Test 7: API Response Contains Explainability Metadata
# ---------------------------------------------------------------------------

def test_7_api_response_contains_explainability(valid_optimize_payload: dict):
    """API response contains allocation_context and portfolio_breakdown."""
    response = client.post("/api/v1/optimize", json=valid_optimize_payload)
    assert response.status_code == 200

    data = response.json()
    alloc0 = data["allocations"][0]
    assert "allocation_context" in alloc0
    ac = alloc0["allocation_context"]
    assert "requested_amount_paise" in ac
    assert "remaining_need_paise" in ac
    assert "allocation_fraction" in ac
    assert "optimization_score" in ac

    assert "portfolio_breakdown" in data
    pb = data["portfolio_breakdown"]
    assert "budget_utilization" in pb
    assert "project_count_funded" in pb
    assert "state_allocation_distribution" in pb
    assert "sector_allocation_distribution" in pb


# ---------------------------------------------------------------------------
# Test 8: API Deterministic Repeatability
# ---------------------------------------------------------------------------

def test_8_api_deterministic_repeatability(valid_optimize_payload: dict):
    """Multiple identical HTTP requests return bitwise identical JSON responses."""
    resp1 = client.post("/api/v1/optimize", json=valid_optimize_payload)
    assert resp1.status_code == 200
    h1 = hashlib.sha256(resp1.content).hexdigest()

    for _ in range(10):
        resp = client.post("/api/v1/optimize", json=valid_optimize_payload)
        assert resp.status_code == 200
        h = hashlib.sha256(resp.content).hexdigest()
        assert h == h1


# ---------------------------------------------------------------------------
# Test 9: API Returns optimization_audit
# ---------------------------------------------------------------------------

def test_9_api_returns_optimization_audit(valid_optimize_payload: dict):
    """API response includes optimization_audit with exact financial totals."""
    response = client.post("/api/v1/optimize", json=valid_optimize_payload)
    assert response.status_code == 200

    data = response.json()
    assert "optimization_audit" in data
    oa = data["optimization_audit"]

    assert oa["total_projects_considered"] == 2
    assert oa["projects_funded"] >= 1
    assert oa["budget_allocated_total_paise"] == data["allocated_paise"]
    assert oa["budget_unallocated_paise"] == data["unallocated_paise"]
    assert oa["budget_allocated_total_paise"] + oa["budget_unallocated_paise"] == data["budget_paise"]


# ---------------------------------------------------------------------------
# Test 10: API Returns allocation_explanation
# ---------------------------------------------------------------------------

def test_10_api_returns_allocation_explanation(valid_optimize_payload: dict):
    """Every allocation in API response includes allocation_explanation with primary_driver."""
    response = client.post("/api/v1/optimize", json=valid_optimize_payload)
    assert response.status_code == 200

    data = response.json()
    for alloc in data["allocations"]:
        assert "allocation_explanation" in alloc
        ae = alloc["allocation_explanation"]
        assert "primary_driver" in ae
        assert isinstance(ae["primary_driver"], str)
        assert "score_components" in ae
        sc = ae["score_components"]
        assert "base_score" in sc
        assert "marginal_score" in sc
        assert "equity_bonus" in sc
        assert "risk_penalty" in sc
