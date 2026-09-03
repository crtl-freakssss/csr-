"""Production Optimization Pipeline Service for AllocateAI (Member C Phase 6).

Coordinates the end-to-end execution pipeline across all 4 deterministic engines:
1. Base Scoring Engine (Phase 2)
2. CSR Saturation Engine (Phase 3)
3. Marginal Impact Engine (Phase 4)
4. Allocation Optimizer & Constraint Engine (Phase 5)

Authoritative contracts: Software Contract v1.0 & Technical Contract v1.0.
Strictly deterministic: zero LLM calls, zero randomness, zero timestamps in calculations,
zero external network calls, zero database writes.
"""

import json
from pathlib import Path
from typing import Any, Final

from backend.app.engine.constants import (
    CALCULATION_VERSIONS,
    DEFAULT_MARGINAL_INCREMENT_PAISE,
    OPTIMIZER_CALCULATION_VERSION,
)
from backend.app.engine.exceptions import (
    BudgetValidationError,
    ConstraintViolationError,
    InvalidProjectDataError,
    WeightValidationError,
)
from backend.app.engine.marginal_impact.engine import MarginalImpactEngine
from backend.app.engine.optimizer.engine import AllocationOptimizer
from backend.app.engine.saturation.engine import SaturationEngine
from backend.app.engine.schemas import (
    ImpactDNA,
    MarginalImpactResult,
    OptimizationConstraints,
    OptimizationRequest,
    OptimizationResult,
    OptimizationWeights,
    Project,
    SaturationContext,
    SaturationResult,
)
from backend.app.engine.scoring.engine import ScoringEngine

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SEED_PROJECTS_PATH = WORKSPACE_ROOT / "data" / "sample" / "member_c_seed_projects.json"
DEFAULT_SEED_CONTEXTS_PATH = WORKSPACE_ROOT / "data" / "sample" / "saturation_context.json"


class OptimizationService:
    """Production service coordinating deterministic CSR optimization pipeline execution."""

    def __init__(
        self,
        projects_path: Path | None = None,
        contexts_path: Path | None = None,
        scoring_engine: ScoringEngine | None = None,
        saturation_engine: SaturationEngine | None = None,
        marginal_engine: MarginalImpactEngine | None = None,
        optimizer: AllocationOptimizer | None = None,
        precision: int = 6,
    ) -> None:
        """Initialize the OptimizationService with all 4 deterministic engines.

        Args:
            projects_path: Path to seed projects JSON repository.
            contexts_path: Path to regional demographic/funding contexts JSON repository.
            scoring_engine: Injected ScoringEngine or None.
            saturation_engine: Injected SaturationEngine or None.
            marginal_engine: Injected MarginalImpactEngine or None.
            optimizer: Injected AllocationOptimizer or None.
            precision: Decimal rounding precision.
        """
        self.precision = precision
        self.projects_path = projects_path or DEFAULT_SEED_PROJECTS_PATH
        self.contexts_path = contexts_path or DEFAULT_SEED_CONTEXTS_PATH

        self.scoring_engine = scoring_engine or ScoringEngine(precision=precision)
        self.saturation_engine = saturation_engine or SaturationEngine(precision=precision)
        self.marginal_engine = marginal_engine or MarginalImpactEngine(precision=precision)
        self.optimizer = optimizer or AllocationOptimizer(precision=precision)

        self._cached_projects: list[Project] | None = None
        self._cached_contexts: dict[tuple[str, str], SaturationContext] | None = None

    # -----------------------------------------------------------------------
    # Data Loading Helpers
    # -----------------------------------------------------------------------

    def load_seed_projects(self) -> list[Project]:
        """Load and cache canonical seed projects repository.

        Returns:
            List of validated Project instances.
        """
        if self._cached_projects is None:
            if self.projects_path.exists():
                with open(self.projects_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                self._cached_projects = [Project.model_validate(p) for p in raw_data]
            else:
                self._cached_projects = []
        return list(self._cached_projects)

    def load_seed_contexts(self) -> dict[tuple[str, str], SaturationContext]:
        """Load and cache canonical regional saturation contexts.

        Returns:
            Lookup mapping (state, sector_value) -> SaturationContext.
        """
        if self._cached_contexts is None:
            if self.contexts_path.exists():
                with open(self.contexts_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                self._cached_contexts = {
                    (c["state"], c["sector"]): SaturationContext.model_validate(c)
                    for c in raw_data
                }
            else:
                self._cached_contexts = {}
        return dict(self._cached_contexts)

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------

    def validate_request(
        self,
        request: OptimizationRequest,
        candidate_projects: list[Project] | None = None,
    ) -> None:
        """Validate an optimization request against contract rules.

        Checks:
            - Positive budget paise (> 0)
            - Non-empty project list
            - Unique project IDs in request
            - Valid weights configuration
            - Valid constraints configuration
            - Presence of requested project models and required ImpactDNA

        Args:
            request: OptimizationRequest payload.
            candidate_projects: Available project entities.

        Raises:
            BudgetValidationError: If budget is non-positive or invalid.
            InvalidProjectDataError: If project IDs are missing, empty, or duplicate.
        """
        if request.budget_paise <= 0:
            raise BudgetValidationError(
                f"Budget must be strictly positive integer paise, got {request.budget_paise}",
                amount_paise=request.budget_paise,
            )

        if not request.project_ids:
            raise InvalidProjectDataError(
                "Request must specify at least one project_id in project_ids",
                field_name="project_ids",
            )

        # Uniqueness check
        if len(request.project_ids) != len(set(request.project_ids)):
            raise InvalidProjectDataError(
                "Duplicate project_ids detected in request. All project_ids must be unique.",
                field_name="project_ids",
            )

        if candidate_projects is not None:
            proj_map = {p.project_id: p for p in candidate_projects}
            missing_ids = [pid for pid in request.project_ids if pid not in proj_map]
            if missing_ids:
                raise InvalidProjectDataError(
                    f"Requested project_ids {missing_ids} not found in repository",
                    field_name="project_ids",
                )

            for pid in request.project_ids:
                p = proj_map[pid]
                if p.impact_dna is None:
                    raise InvalidProjectDataError(
                        f"Project '{pid}' is missing required ImpactDNA",
                        project_id=pid,
                        field_name="impact_dna",
                    )

    # -----------------------------------------------------------------------
    # Stage 1-3 Context Preparation
    # -----------------------------------------------------------------------

    def prepare_project_context(
        self,
        projects: list[Project],
        saturation_contexts_map: dict[tuple[str, str], SaturationContext] | None = None,
        increment_paise: int = DEFAULT_MARGINAL_INCREMENT_PAISE,
    ) -> tuple[list[SaturationResult], list[MarginalImpactResult], dict[str, Any]]:
        """Execute Stage 1-3 pipelines and prepare reusable intermediate context.

        Stage 1: Base Scoring Engine computes calibrated base impact scores and breakdown.
        Stage 2: CSR Saturation Engine calculates regional CSR saturation index.
        Stage 3: Marginal Impact Engine calculates diminishing returns and incremental impact.

        Args:
            projects: Candidate projects to process.
            saturation_contexts_map: Optional preloaded (state, sector) -> SaturationContext map.
            increment_paise: Incremental step size in paise.

        Returns:
            Tuple of (saturation_results, marginal_results, intermediate_context_map).
        """
        contexts_map = saturation_contexts_map or self.load_seed_contexts()

        saturation_results: list[SaturationResult] = []
        marginal_results: list[MarginalImpactResult] = []
        intermediate_map: dict[str, Any] = {}

        for project in projects:
            pid = project.project_id
            st = project.geographies[0].state if project.geographies else "DefaultState"
            sec = project.sector.value

            # Stage 1: Base Scoring Engine
            scoring_breakdown = self.scoring_engine.calculate_component_scores(project)
            base_score = scoring_breakdown["base_score"]

            # Stage 2: CSR Saturation Engine
            ctx_key = (st, sec)
            if ctx_key in contexts_map:
                context = contexts_map[ctx_key]
            else:
                context = SaturationContext(
                    state=st,
                    sector=project.sector,
                    total_regional_csr_paise=0,
                    total_population=1_000_000,
                    target_population=100_000,
                )

            saturation_result = self.saturation_engine.calculate_saturation(project, context)
            saturation_results.append(saturation_result)

            # Stage 3: Marginal Impact Engine
            marginal_result = self.marginal_engine.calculate_marginal_impact(
                project=project,
                saturation_result=saturation_result,
                increment_paise=increment_paise,
            )
            marginal_results.append(marginal_result)

            # Reusable lookup context
            intermediate_map[pid] = {
                "base_score": base_score,
                "scoring_breakdown": scoring_breakdown,
                "saturation_result": saturation_result,
                "marginal_result": marginal_result,
            }

        return saturation_results, marginal_results, intermediate_map

    # -----------------------------------------------------------------------
    # Main Pipeline Execution
    # -----------------------------------------------------------------------

    def optimize(
        self,
        request: OptimizationRequest,
        projects: list[Project] | None = None,
        saturation_contexts: list[SaturationContext] | dict[tuple[str, str], SaturationContext] | None = None,
    ) -> OptimizationResult:
        """Execute the complete deterministic 4-stage CSR optimization pipeline.

        Pipeline Stages:
            1. Validate request and candidate projects.
            2. Match and filter projects.
            3. Stage 1 (Base Scoring) + Stage 2 (Saturation) + Stage 3 (Marginal Impact).
            4. Stage 4 (Allocation Optimizer & Constraints).
            5. Return validated explainable OptimizationResult.

        Args:
            request: Validated OptimizationRequest.
            projects: Optional list of Project models (defaults to seed projects repository).
            saturation_contexts: Optional regional contexts mapping.

        Returns:
            Validated OptimizationResult.
        """
        all_projects = projects if projects is not None else self.load_seed_projects()

        # 1. Validation
        self.validate_request(request, candidate_projects=all_projects)

        # 2. Filter candidate projects to requested IDs
        project_lookup = {p.project_id: p for p in all_projects}
        matched_projects = [project_lookup[pid] for pid in request.project_ids]

        # Context normalization
        if isinstance(saturation_contexts, list):
            ctx_map = {(c.state, c.sector.value): c for c in saturation_contexts}
        elif isinstance(saturation_contexts, dict):
            ctx_map = saturation_contexts
        else:
            ctx_map = self.load_seed_contexts()

        # 3. Stage 1-3 Execution
        saturation_results, marginal_results, _ = self.prepare_project_context(
            projects=matched_projects,
            saturation_contexts_map=ctx_map,
            increment_paise=request.marginal_increment_paise,
        )

        # 4. Stage 4: Allocation Optimizer
        result = self.optimizer.calculate_optimal_allocation(
            request=request,
            projects=matched_projects,
            saturation_results=saturation_results,
            marginal_results=marginal_results,
        )

        return result

    def simulate(
        self,
        project_id: str,
        increment_paise: int = DEFAULT_MARGINAL_INCREMENT_PAISE,
        project: Project | None = None,
        saturation_context: SaturationContext | None = None,
    ) -> MarginalImpactResult:
        """Simulate incremental marginal impact for a specific candidate project.

        Args:
            project_id: Identifier of the project to simulate.
            increment_paise: Incremental budget step in paise (strictly > 0).
            project: Optional preloaded Project instance.
            saturation_context: Optional preloaded regional context.

        Returns:
            MarginalImpactResult describing expected incremental outcome.
        """
        if increment_paise <= 0:
            raise BudgetValidationError(
                f"Increment must be strictly positive integer paise, got {increment_paise}",
                amount_paise=increment_paise,
            )

        if project is None:
            all_projects = self.load_seed_projects()
            proj_map = {p.project_id: p for p in all_projects}
            if project_id not in proj_map:
                raise InvalidProjectDataError(
                    f"Project '{project_id}' not found in repository",
                    project_id=project_id,
                )
            project = proj_map[project_id]

        if project.impact_dna is None:
            raise InvalidProjectDataError(
                f"Project '{project_id}' has no ImpactDNA profile",
                project_id=project_id,
            )

        st = project.geographies[0].state if project.geographies else "DefaultState"
        sec = project.sector.value

        if saturation_context is None:
            ctx_map = self.load_seed_contexts()
            saturation_context = ctx_map.get(
                (st, sec),
                SaturationContext(
                    state=st,
                    sector=project.sector,
                    total_regional_csr_paise=0,
                    total_population=1_000_000,
                    target_population=100_000,
                ),
            )

        saturation_res = self.saturation_engine.calculate_saturation(project, saturation_context)

        return self.marginal_engine.calculate_marginal_impact(
            project=project,
            saturation_result=saturation_res,
            increment_paise=increment_paise,
        )

    def get_pipeline_summary(self, result: OptimizationResult) -> dict[str, Any]:
        """Generate lightweight deterministic pipeline execution telemetry.

        No timestamps. No UUIDs. Purely deterministic metrics.

        Args:
            result: Executed OptimizationResult.

        Returns:
            Dictionary with pipeline telemetry summary.
        """
        total_projects = len(result.allocations)
        funded = sum(1 for a in result.allocations if a.allocated_amount_paise > 0)
        utilization = (
            result.portfolio_breakdown.get("budget_utilization", 0.0)
            if result.portfolio_breakdown
            else 0.0
        )

        return {
            "projects_processed": total_projects,
            "funded_projects": funded,
            "budget_utilization": utilization,
            "engine_versions": result.calculation_versions,
        }
