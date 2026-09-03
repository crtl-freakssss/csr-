"""Budget Allocation Optimizer and Simulation API routes for AllocateAI."""

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict, Field

from backend.app.engine.constants import DEFAULT_MARGINAL_INCREMENT_PAISE
from backend.app.engine.schemas import (
    MarginalImpactResult,
    OptimizationRequest,
    OptimizationResult,
)
from backend.app.services.optimization_service import OptimizationService

router = APIRouter(tags=["Optimizer"])


class SimulateRequest(BaseModel):
    """Payload for incremental marginal impact simulation."""
    model_config = ConfigDict(extra="ignore")

    project_id: str
    increment_paise: int = Field(
        default=DEFAULT_MARGINAL_INCREMENT_PAISE,
        gt=0,
        description="Incremental investment in integer paise (strictly > 0)",
    )


# Singleton service dependency
_service_instance: OptimizationService | None = None


def get_optimization_service() -> OptimizationService:
    """Dependency provider returning singleton OptimizationService instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = OptimizationService()
    return _service_instance


@router.post(
    "/optimize",
    response_model=OptimizationResult,
    status_code=status.HTTP_200_OK,
    summary="Execute Deterministic Budget Optimization",
    description="Calculates optimal CSR budget allocation across candidate projects under statutory and policy constraints.",
)
def run_optimization(
    request: OptimizationRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizationResult:
    """Execute end-to-end deterministic budget optimization pipeline.

    Args:
        request: OptimizationRequest containing budget, candidate project_ids, weights, constraints.
        service: Injected OptimizationService.

    Returns:
        Validated OptimizationResult including allocations, portfolio_breakdown, and optimization_audit.
    """
    return service.optimize(request=request)


@router.post(
    "/simulate",
    response_model=MarginalImpactResult,
    status_code=status.HTTP_200_OK,
    summary="Simulate Incremental Marginal Impact",
    description="Estimates incremental impact and diminishing returns for an incremental investment into a project.",
)
def run_simulation(
    request: SimulateRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> MarginalImpactResult:
    """Execute marginal impact simulation for an incremental investment.

    Args:
        request: SimulateRequest containing project_id and increment_paise.
        service: Injected OptimizationService.

    Returns:
        Validated MarginalImpactResult describing incremental expected outcome.
    """
    return service.simulate(
        project_id=request.project_id,
        increment_paise=request.increment_paise,
    )
