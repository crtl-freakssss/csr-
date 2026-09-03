"""AllocateAI Production Decision Engine FastAPI Application.

Authoritative source: Software Contract v1.0 & Technical Contract v1.0.
Exposes deterministic endpoints for:
- Health checks: GET /api/v1/health
- Version discovery: GET /api/v1/version
- Budget optimization: POST /api/v1/optimize
- Marginal simulation: POST /api/v1/simulate

Deterministic: zero LLM calls, zero randomness, zero timestamps inside engine calculations.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api import api_v1_router
from backend.app.engine.constants import API_VERSION
from backend.app.engine.exceptions import (
    BudgetValidationError,
    CalculationVersionError,
    ConstraintViolationError,
    DecisionEngineError,
    InvalidProjectDataError,
    WeightValidationError,
)

app = FastAPI(
    title="AllocateAI Decision Engine API",
    description="Deterministic CSR Portfolio Budget Allocation & Decision Engine.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware for Member A frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Centralized Deterministic Exception Handlers
# ---------------------------------------------------------------------------

@app.exception_handler(BudgetValidationError)
def budget_validation_exception_handler(request: Request, exc: BudgetValidationError) -> JSONResponse:
    """Handle integer paise and positive budget validation failures."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "BudgetValidationError",
            "code": "INVALID_BUDGET",
            "message": exc.message,
        },
    )


@app.exception_handler(WeightValidationError)
def weight_validation_exception_handler(request: Request, exc: WeightValidationError) -> JSONResponse:
    """Handle policy weights out-of-bounds or sum violations."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "WeightValidationError",
            "code": "INVALID_WEIGHTS",
            "message": exc.message,
        },
    )


@app.exception_handler(InvalidProjectDataError)
def invalid_project_data_exception_handler(request: Request, exc: InvalidProjectDataError) -> JSONResponse:
    """Handle missing project entities, duplicate IDs, or invalid ImpactDNA."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "InvalidProjectDataError",
            "code": "INVALID_PROJECT_DATA",
            "message": exc.message,
        },
    )


@app.exception_handler(ConstraintViolationError)
def constraint_violation_exception_handler(request: Request, exc: ConstraintViolationError) -> JSONResponse:
    """Handle mathematical feasibility and operational constraint violations."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ConstraintViolationError",
            "code": "CONSTRAINT_VIOLATION",
            "message": exc.message,
        },
    )


@app.exception_handler(CalculationVersionError)
def calculation_version_exception_handler(request: Request, exc: CalculationVersionError) -> JSONResponse:
    """Handle calculation version mismatch failures."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "CalculationVersionError",
            "code": "INVALID_CALCULATION_VERSION",
            "message": exc.message,
        },
    )


@app.exception_handler(DecisionEngineError)
def decision_engine_exception_handler(request: Request, exc: DecisionEngineError) -> JSONResponse:
    """Catch-all for typed Decision Engine errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": type(exc).__name__,
            "code": "DECISION_ENGINE_ERROR",
            "message": exc.message,
        },
    )


@app.exception_handler(RequestValidationError)
def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Format FastAPI request validation errors into contract-compliant JSON."""
    error_details = exc.errors()
    first_msg = error_details[0].get("msg", "Invalid request body") if error_details else "Invalid request body"
    loc = " -> ".join(str(x) for x in error_details[0].get("loc", [])) if error_details else ""
    full_msg = f"{first_msg} (at {loc})" if loc else first_msg

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "RequestValidationError",
            "code": "SCHEMA_VALIDATION_ERROR",
            "message": full_msg,
        },
    )


@app.exception_handler(StarletteHTTPException)
def starlette_http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
        },
    )


# ---------------------------------------------------------------------------
# Mount Routers
# ---------------------------------------------------------------------------

app.include_router(api_v1_router)


@app.get("/", tags=["Root"])
def root() -> dict[str, str]:
    """Root discovery endpoint."""
    return {
        "service": "AllocateAI Decision Engine",
        "api_version": API_VERSION,
        "docs": "/docs",
    }
