# AllocateAI Decision Engine — REST API Documentation

**API Version:** `api-v1`  
**Optimizer Engine Version:** `optimizer-v1`  
**Authoritative Contracts:** Software Contract v1.0 & Technical Contract v1.0  
**Specification:** OpenAPI 3.0 / FastAPI  

---

## 1. Overview
The AllocateAI Decision Engine API provides deterministic, verifiable, mathematical endpoints for CSR budget allocation, marginal simulation, health monitoring, and engine version discovery.

All financial amounts are strictly accepted and emitted in **integer paise** ($1\text{ Rupee} = 100\text{ paise}$, $1\text{ Lakh} = 10,000,000\text{ paise}$).

---

## 2. Endpoints Summary

| Method | Path | Summary | Description |
|---|---|---|---|
| `POST` | `/api/v1/optimize` | Execute Budget Optimization | Runs deterministic 4-stage pipeline across candidate projects. |
| `POST` | `/api/v1/simulate` | Simulate Marginal Return | Computes diminishing return and incremental impact for a project. |
| `GET` | `/api/v1/health` | Health Check | Deterministic liveness probe without timestamps or clocks. |
| `GET` | `/api/v1/version` | Version Discovery | Emits versions of calculation engines and canonical schemas. |

---

## 3. Endpoints Specification

### 3.1 `POST /api/v1/optimize`

Executes deterministic multi-criteria portfolio optimization under statutory and policy constraints.

#### Request Headers
* `Content-Type: application/json`

#### Request Schema (`OptimizationRequest`)
```json
{
  "budget_paise": 30000000,
  "project_ids": ["PRJ-0001", "PRJ-0002"],
  "weights": {
    "need": 0.20,
    "marginal_impact": 0.25,
    "cost_efficiency": 0.20,
    "evidence": 0.15,
    "scalability": 0.10,
    "equity": 0.10,
    "risk_penalty": 0.10
  },
  "constraints": {
    "max_allocation_per_project_paise": null,
    "max_allocation_per_region_paise": null,
    "minimum_allocation_per_project_paise": null,
    "require_full_budget_allocation": true,
    "regional_equity_enabled": true
  },
  "marginal_increment_paise": 10000000
}
```

#### Response Schema (`OptimizationResult`) — HTTP 200 OK
```json
{
  "run_id": "OPT-30000000-2",
  "status": "COMPLETED",
  "budget_paise": 30000000,
  "allocated_paise": 30000000,
  "unallocated_paise": 0,
  "allocations": [
    {
      "project_id": "PRJ-0002",
      "allocated_amount_paise": 30000000,
      "marginal_impact_score": 0.761175,
      "base_score": 0.75,
      "saturation_index": 0.0315,
      "reason_codes": [
        "HIGH_NEED",
        "LOW_SATURATION",
        "HIGH_MARGINAL_IMPACT",
        "HIGH_COST_EFFICIENCY"
      ],
      "rank": 1,
      "status": "PROPOSED",
      "allocation_context": {
        "requested_amount_paise": 35000000,
        "remaining_need_paise": 0,
        "allocation_fraction": 0.857143,
        "optimization_score": 0.747403
      },
      "allocation_explanation": {
        "primary_driver": "regional_equity",
        "score_components": {
          "base_score": 0.75,
          "marginal_score": 0.761175,
          "equity_bonus": 0.9685,
          "risk_penalty": 0.28
        }
      }
    }
  ],
  "total_predicted_impact": 116.55,
  "average_saturation": 0.0315,
  "underserved_region_allocation_share": 1.0,
  "weights": { ... },
  "constraints": { ... },
  "calculation_versions": {
    "project": "project-v1",
    "dna": "dna-v1",
    "saturation": "saturation-v1",
    "marginal": "marginal-v1",
    "optimizer": "optimizer-v1",
    "api": "api-v1"
  },
  "created_at": "2026-09-01T00:00:00Z",
  "portfolio_breakdown": {
    "budget_utilization": 1.0,
    "project_count_funded": 1,
    "state_allocation_distribution": {
      "Bihar": 30000000
    },
    "sector_allocation_distribution": {
      "HEALTHCARE": 30000000
    },
    "average_base_score": 0.75,
    "average_marginal_score": 0.761175,
    "average_saturation": 0.0315
  },
  "optimization_audit": {
    "total_projects_considered": 2,
    "projects_funded": 1,
    "projects_skipped": 1,
    "budget_requested_total_paise": 85000000,
    "budget_allocated_total_paise": 30000000,
    "budget_unallocated_paise": 0
  }
}
```

---

### 3.2 `POST /api/v1/simulate`

Simulates discrete marginal return for an incremental CSR step size without running full portfolio reallocation.

#### Request Schema (`SimulateRequest`)
```json
{
  "project_id": "PRJ-0001",
  "increment_paise": 10000000
}
```

#### Response Schema (`MarginalImpactResult`) — HTTP 200 OK
```json
{
  "project_id": "PRJ-0001",
  "increment_paise": 10000000,
  "baseline_budget_paise": 10000000,
  "projected_budget_paise": 20000000,
  "baseline_impact": 45.0,
  "projected_impact": 76.5,
  "incremental_impact": 31.5,
  "impact_per_lakh": 31.5,
  "marginal_impact_score": 0.654,
  "diminishing_return_factor": 0.70,
  "calculation_version": "marginal-v1"
}
```

---

### 3.3 `GET /api/v1/health`

#### Response — HTTP 200 OK
```json
{
  "status": "healthy",
  "api_version": "api-v1",
  "optimizer_version": "optimizer-v1",
  "engines": {
    "scoring": "scoring-v1",
    "saturation": "saturation-v1",
    "marginal": "marginal-v1",
    "optimizer": "optimizer-v1"
  },
  "uptime": "deterministic"
}
```

---

### 3.4 `GET /api/v1/version`

#### Response — HTTP 200 OK
```json
{
  "project": "project-v1",
  "api": "api-v1",
  "engines": {
    "scoring": "scoring-v1",
    "saturation": "saturation-v1",
    "marginal": "marginal-v1",
    "optimizer": "optimizer-v1"
  },
  "schema_versions": {
    "project": "project-v1",
    "dna": "dna-v1"
  }
}
```

---

## 4. Error Handling & Formats

All errors are returned in structured JSON without stack trace leaks:

```json
{
  "error": "ErrorType",
  "code": "ERROR_CODE",
  "message": "Human readable description"
}
```

### Standard Error Mappings
* **HTTP 400 Bad Request**:
  * `INVALID_BUDGET`: Budget is zero, negative, or non-integer paise.
  * `INVALID_WEIGHTS`: Policy weights fail normalization or boundary constraints.
  * `INVALID_PROJECT_DATA`: Missing project IDs or duplicate project IDs.
* **HTTP 422 Unprocessable Entity**:
  * `CONSTRAINT_VIOLATION`: Operational constraint cannot be satisfied (e.g. `require_full_budget_allocation` with insufficient candidate headroom).
  * `SCHEMA_VALIDATION_ERROR`: Missing or malformed schema attributes.
