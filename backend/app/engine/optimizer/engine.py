"""Budget Allocation Optimizer Engine for AllocateAI Decision Engine (Member C Phase 5).

Combines:
- Phase 2: Base Scoring Engine
- Phase 3: CSR Saturation Engine
- Phase 4: Marginal Impact Engine
into a deterministic optimizer that decides optimal CSR budget allocation under constraints.

Authoritative contracts: Software Contract v1.0 & Technical Contract v1.0.
Strictly deterministic: zero LLM calls, zero randomness, zero external APIs, zero temporal dependencies.
All monetary amounts represented in integer paise.
"""

from dataclasses import dataclass
import hashlib
from typing import Any, Final

from backend.app.engine.constants import (
    CALCULATION_VERSIONS,
    OPTIMIZER_CALCULATION_VERSION,
    PAISE_PER_LAKH,
    AllocationStatus,
    OptimizationStatus,
    ReasonCode,
    SCORE_MAX,
    SCORE_MIN,
)
from backend.app.engine.constraints.engine import ConstraintEngine
from backend.app.engine.exceptions import (
    ConstraintViolationError,
    InvalidProjectDataError,
)
from backend.app.engine.marginal_impact.engine import MarginalImpactEngine
from backend.app.engine.saturation.engine import SaturationEngine
from backend.app.engine.schemas import (
    Allocation,
    ImpactDNA,
    MarginalImpactResult,
    OptimizationConstraints,
    OptimizationRequest,
    OptimizationResult,
    OptimizationWeights,
    Project,
    SaturationResult,
)
from backend.app.engine.scoring.engine import ScoringEngine
from backend.app.engine.utils import (
    clip_score,
    normalize_weights,
    safe_division,
    validate_score,
)

CALCULATION_VERSION: Final[str] = OPTIMIZER_CALCULATION_VERSION  # "optimizer-v1"
DEFAULT_OPTIMIZER_PRECISION: Final[int] = 6


@dataclass(frozen=True)
class RankedProject:
    """Internal immutable data container for project ranking."""
    project: Project
    base_score: float
    saturation_index: float
    marginal_impact_score: float
    optimization_score: float
    need_score: float


class AllocationOptimizer:
    """Deterministic mathematical budget allocation optimizer."""

    calculation_version: Final[str] = CALCULATION_VERSION

    def __init__(
        self,
        precision: int = DEFAULT_OPTIMIZER_PRECISION,
        constraint_engine: ConstraintEngine | None = None,
        scoring_engine: ScoringEngine | None = None,
        saturation_engine: SaturationEngine | None = None,
        marginal_engine: MarginalImpactEngine | None = None,
    ) -> None:
        """Initialize the AllocationOptimizer.

        Args:
            precision: Decimal precision for scores and metrics (default: 6).
            constraint_engine: Injected ConstraintEngine instance or None.
            scoring_engine: Injected ScoringEngine instance or None.
            saturation_engine: Injected SaturationEngine instance or None.
            marginal_engine: Injected MarginalImpactEngine instance or None.
        """
        self.precision = precision
        self.constraint_engine = constraint_engine or ConstraintEngine()
        self.scoring_engine = scoring_engine or ScoringEngine(precision=precision)
        self.saturation_engine = saturation_engine or SaturationEngine(precision=precision)
        self.marginal_engine = marginal_engine or MarginalImpactEngine(precision=precision)

    # -----------------------------------------------------------------------
    # Step 1: Input Validation
    # -----------------------------------------------------------------------

    def validate_inputs(
        self,
        request: OptimizationRequest,
        projects: list[Project],
        saturation_results: list[SaturationResult] | None = None,
        marginal_results: list[MarginalImpactResult] | None = None,
    ) -> None:
        """Validate the consistency and completeness of optimization inputs.

        Args:
            request: OptimizationRequest payload.
            projects: Candidate project entities.
            saturation_results: Optional precomputed saturation results.
            marginal_results: Optional precomputed marginal impact results.

        Raises:
            InvalidProjectDataError: If request or project data is invalid or missing.
        """
        if not isinstance(request, OptimizationRequest):
            raise InvalidProjectDataError(
                f"request must be an OptimizationRequest, got {type(request).__name__}"
            )

        if not projects:
            raise InvalidProjectDataError("Projects list cannot be empty")

        project_map = {p.project_id: p for p in projects}
        missing_ids = [pid for pid in request.project_ids if pid not in project_map]
        if missing_ids:
            raise InvalidProjectDataError(
                f"Requested project_ids {missing_ids} not found in provided projects list",
                field_name="project_ids",
            )

        for p in projects:
            if not isinstance(p, Project):
                raise InvalidProjectDataError(
                    f"All items in projects must be Project instances, got {type(p).__name__}"
                )
            if p.impact_dna is None:
                raise InvalidProjectDataError(
                    f"Project '{p.project_id}' is missing required ImpactDNA",
                    project_id=p.project_id,
                    field_name="impact_dna",
                )

        if saturation_results is not None:
            for s in saturation_results:
                if not isinstance(s, SaturationResult):
                    raise InvalidProjectDataError(
                        f"All items in saturation_results must be SaturationResult instances, got {type(s).__name__}"
                    )

        if marginal_results is not None:
            for m in marginal_results:
                if not isinstance(m, MarginalImpactResult):
                    raise InvalidProjectDataError(
                        f"All items in marginal_results must be MarginalImpactResult instances, got {type(m).__name__}"
                    )

    # -----------------------------------------------------------------------
    # Step 2: Composite Optimization Score
    # -----------------------------------------------------------------------

    def calculate_composite_score(
        self,
        project: Project,
        base_score: float,
        saturation_index: float,
        marginal_impact_score: float,
        normalized_weights: dict[str, float],
    ) -> float:
        """Compute the composite optimization score for a candidate project.

        Formula:
            Optimization Score =
                need_weight * need_score
              + marginal_weight * marginal_impact_score
              + efficiency_weight * cost_efficiency_score
              + evidence_weight * evidence_strength_score
              + scalability_weight * scalability_score
              + equity_weight * (1.0 - saturation_index)
              - risk_penalty_weight * implementation_risk_score

        Args:
            project: Project entity with ImpactDNA.
            base_score: Calibrated base impact score.
            saturation_index: CSR saturation index.
            marginal_impact_score: Incremental marginal return score.
            normalized_weights: Normalized policy weights.

        Returns:
            Optimization score clipped to [0.0, 1.0] rounded to precision.
        """
        dna = project.impact_dna
        assert dna is not None

        need_sc = dna.need_score
        cost_eff = dna.cost_efficiency_score
        evidence_sc = dna.evidence_strength_score
        scalability_sc = dna.scalability_score
        risk_sc = dna.implementation_risk_score

        w_need = normalized_weights["need"]
        w_marg = normalized_weights["marginal_impact"]
        w_eff = normalized_weights["cost_efficiency"]
        w_evi = normalized_weights["evidence"]
        w_scal = normalized_weights["scalability"]
        w_eq = normalized_weights["equity"]
        w_risk = normalized_weights["risk_penalty"]

        raw_score = (
            w_need * need_sc
            + w_marg * marginal_impact_score
            + w_eff * cost_eff
            + w_evi * evidence_sc
            + w_scal * scalability_sc
            + w_eq * (1.0 - saturation_index)
            - w_risk * risk_sc
        )

        clipped = clip_score(raw_score, min_val=SCORE_MIN, max_val=SCORE_MAX)
        return round(clipped, self.precision)

    # -----------------------------------------------------------------------
    # Step 3: Deterministic Ranking & Tie-Breaking
    # -----------------------------------------------------------------------

    def rank_projects(
        self,
        projects: list[Project],
        weights: OptimizationWeights,
        saturation_map: dict[str, SaturationResult],
        marginal_map: dict[str, MarginalImpactResult],
        base_scores_map: dict[str, float],
    ) -> list[RankedProject]:
        """Rank projects deterministically using composite scores and strict tie-breaking.

        Tie-breaking hierarchy:
            1. Higher optimization_score
            2. Higher marginal_impact_score
            3. Lower saturation_index
            4. Higher need_score
            5. Lexicographical project_id

        Args:
            projects: Candidate projects to rank.
            weights: OptimizationWeights configuration.
            saturation_map: Project ID -> SaturationResult lookup.
            marginal_map: Project ID -> MarginalImpactResult lookup.
            base_scores_map: Project ID -> base_score lookup.

        Returns:
            Sorted list of RankedProject objects.
        """
        norm_weights = normalize_weights(weights.to_dict())

        scored_list: list[RankedProject] = []
        for p in projects:
            dna = p.impact_dna
            assert dna is not None

            base_sc = base_scores_map[p.project_id]
            sat_idx = saturation_map[p.project_id].saturation_index
            marg_sc = marginal_map[p.project_id].marginal_impact_score

            opt_score = self.calculate_composite_score(
                project=p,
                base_score=base_sc,
                saturation_index=sat_idx,
                marginal_impact_score=marg_sc,
                normalized_weights=norm_weights,
            )

            scored_list.append(
                RankedProject(
                    project=p,
                    base_score=base_sc,
                    saturation_index=sat_idx,
                    marginal_impact_score=marg_sc,
                    optimization_score=opt_score,
                    need_score=dna.need_score,
                )
            )

        # Stable sort with multi-key tie-breaker
        scored_list.sort(
            key=lambda item: (
                -item.optimization_score,
                -item.marginal_impact_score,
                item.saturation_index,
                -item.need_score,
                item.project.project_id,
            )
        )

        return scored_list

    # -----------------------------------------------------------------------
    # Step 7: Deterministic Reason Codes Generator
    # -----------------------------------------------------------------------

    def generate_reason_codes(
        self,
        ranked: RankedProject,
        allocated_amount_paise: int,
        project_cap_remaining: int,
        region_cap_remaining: int,
        budget_remaining: int,
        minimum_allocation_paise: int | None,
    ) -> list[ReasonCode]:
        """Generate deterministic, explainable reason codes for an allocation decision.

        Args:
            ranked: Scored and ranked project.
            allocated_amount_paise: Final committed allocation in paise.
            project_cap_remaining: Project cap headroom.
            region_cap_remaining: Regional cap headroom.
            budget_remaining: Remaining budget before allocation.
            minimum_allocation_paise: Optional minimum allocation threshold.

        Returns:
            List of ReasonCode enums.
        """
        dna = ranked.project.impact_dna
        assert dna is not None

        codes: list[ReasonCode] = []

        # Positive qualitative factors
        if dna.need_score >= 0.80:
            codes.append(ReasonCode.HIGH_NEED)
        if ranked.saturation_index <= 0.24:
            codes.append(ReasonCode.LOW_SATURATION)
        if ranked.marginal_impact_score >= 0.70:
            codes.append(ReasonCode.HIGH_MARGINAL_IMPACT)
        if dna.cost_efficiency_score >= 0.80:
            codes.append(ReasonCode.HIGH_COST_EFFICIENCY)
        if dna.evidence_strength_score >= 0.80:
            codes.append(ReasonCode.STRONG_EVIDENCE)
        if dna.scalability_score >= 0.80:
            codes.append(ReasonCode.HIGH_SCALABILITY)

        # Risk and penalty factors
        if dna.evidence_strength_score < 0.50:
            codes.append(ReasonCode.LOW_EVIDENCE)
        if dna.implementation_risk_score >= 0.50:
            codes.append(ReasonCode.HIGH_IMPLEMENTATION_RISK)
        if ranked.saturation_index >= 0.50:
            codes.append(ReasonCode.HIGH_SATURATION)

        # Missing data and due diligence flags
        if dna.missing_fields or dna.extraction_confidence < 0.70:
            codes.append(ReasonCode.MISSING_DATA)
        if dna.implementation_risk_score >= 0.70 or dna.extraction_confidence < 0.50:
            codes.append(ReasonCode.DUE_DILIGENCE_FLAG)

        # Constraint limiting factors
        if allocated_amount_paise > 0:
            if minimum_allocation_paise is not None and allocated_amount_paise == minimum_allocation_paise:
                codes.append(ReasonCode.MINIMUM_ALLOCATION)
            if allocated_amount_paise < project_cap_remaining:
                if budget_remaining < project_cap_remaining:
                    codes.append(ReasonCode.BUDGET_CONSTRAINT)
                if region_cap_remaining < project_cap_remaining:
                    codes.append(ReasonCode.REGIONAL_CAP)
        else:
            # Unfunded project reasons
            if minimum_allocation_paise is not None and budget_remaining < minimum_allocation_paise:
                codes.append(ReasonCode.MINIMUM_ALLOCATION)
            elif budget_remaining == 0:
                codes.append(ReasonCode.BUDGET_CONSTRAINT)
            elif region_cap_remaining == 0:
                codes.append(ReasonCode.REGIONAL_CAP)

        return codes

    # -----------------------------------------------------------------------
    # Step 7: Build Allocation Object
    # -----------------------------------------------------------------------

    def build_allocation(
        self,
        ranked: RankedProject,
        allocated_amount_paise: int,
        rank: int,
        reason_codes: list[ReasonCode],
    ) -> Allocation:
        """Construct a validated Allocation object with allocation_context and allocation_explanation metadata.

        Args:
            ranked: Evaluated RankedProject.
            allocated_amount_paise: Committed amount in paise.
            rank: 1-indexed priority rank.
            reason_codes: Deterministic justification codes.

        Returns:
            Validated Allocation schema instance.
        """
        p = ranked.project
        dna = p.impact_dna
        assert dna is not None
        req_paise = p.financials.requested_amount_paise
        curr_paise = p.financials.current_funding_paise
        remaining_need = max(0, req_paise - curr_paise - allocated_amount_paise)
        alloc_fraction = round(safe_division(float(allocated_amount_paise), float(req_paise), default=0.0), self.precision)

        allocation_context = {
            "requested_amount_paise": req_paise,
            "remaining_need_paise": remaining_need,
            "allocation_fraction": alloc_fraction,
            "optimization_score": ranked.optimization_score,
        }

        # Determine primary driver
        driver_components = {
            "need": dna.need_score,
            "marginal_impact": ranked.marginal_impact_score,
            "cost_efficiency": dna.cost_efficiency_score,
            "evidence": dna.evidence_strength_score,
            "scalability": dna.scalability_score,
            "regional_equity": 1.0 - ranked.saturation_index,
        }
        primary_driver = max(driver_components.items(), key=lambda x: x[1])[0]

        allocation_explanation = {
            "primary_driver": primary_driver,
            "score_components": {
                "base_score": round(ranked.base_score, self.precision),
                "marginal_score": round(ranked.marginal_impact_score, self.precision),
                "equity_bonus": round(1.0 - ranked.saturation_index, self.precision),
                "risk_penalty": round(dna.implementation_risk_score, self.precision),
            },
        }

        return Allocation(
            project_id=p.project_id,
            allocated_amount_paise=allocated_amount_paise,
            marginal_impact_score=ranked.marginal_impact_score,
            base_score=ranked.base_score,
            saturation_index=ranked.saturation_index,
            reason_codes=reason_codes,
            rank=rank,
            status=AllocationStatus.PROPOSED,
            allocation_context=allocation_context,
            allocation_explanation=allocation_explanation,
        )

    # -----------------------------------------------------------------------
    # Step 8 & 9: Portfolio Metrics Calculation
    # -----------------------------------------------------------------------

    def calculate_portfolio_metrics(
        self,
        allocations: list[Allocation],
        total_budget_paise: int,
        projects_map: dict[str, Project],
        marginal_map: dict[str, MarginalImpactResult],
    ) -> dict[str, Any]:
        """Compute portfolio summary metrics and explainability breakdown.

        Args:
            allocations: List of final Allocation objects.
            total_budget_paise: Initial total budget in paise.
            projects_map: Map of project_id to Project.
            marginal_map: Map of project_id to MarginalImpactResult.

        Returns:
            Dictionary containing portfolio metrics and portfolio_breakdown.
        """
        allocated_total = sum(a.allocated_amount_paise for a in allocations)
        unallocated_total = max(0, total_budget_paise - allocated_total)

        total_predicted_impact = 0.0
        underserved_allocated = 0
        state_allocations: dict[str, int] = {}
        sector_allocations: dict[str, int] = {}

        funded_base_scores: list[float] = []
        funded_marginal_scores: list[float] = []
        funded_saturations: list[float] = []

        for alloc in allocations:
            p = projects_map[alloc.project_id]
            st = p.geographies[0].state if p.geographies else "UNKNOWN"
            sec = p.sector.value

            if alloc.allocated_amount_paise > 0:
                # Add predicted impact
                marg = marginal_map[alloc.project_id]
                alloc_lakh = float(alloc.allocated_amount_paise) / float(PAISE_PER_LAKH)
                total_predicted_impact += marg.impact_per_lakh * alloc_lakh

                # Track regional and sector distributions
                state_allocations[st] = state_allocations.get(st, 0) + alloc.allocated_amount_paise
                sector_allocations[sec] = sector_allocations.get(sec, 0) + alloc.allocated_amount_paise

                # Track underserved allocation share (saturation <= 0.24)
                if alloc.saturation_index <= 0.24:
                    underserved_allocated += alloc.allocated_amount_paise

                funded_base_scores.append(alloc.base_score)
                funded_marginal_scores.append(alloc.marginal_impact_score)
                funded_saturations.append(alloc.saturation_index)

        # Calculate average saturation
        if allocated_total > 0:
            weighted_sat = sum(
                a.allocated_amount_paise * a.saturation_index for a in allocations
            ) / allocated_total
            average_saturation = round(weighted_sat, self.precision)
        elif allocations:
            average_saturation = round(
                sum(a.saturation_index for a in allocations) / len(allocations),
                self.precision,
            )
        else:
            average_saturation = 0.0

        underserved_share = round(
            safe_division(float(underserved_allocated), float(allocated_total), default=0.0),
            self.precision,
        )

        budget_utilization = round(
            safe_division(float(allocated_total), float(total_budget_paise), default=0.0),
            self.precision,
        )

        avg_base = round(
            sum(funded_base_scores) / len(funded_base_scores) if funded_base_scores else 0.0,
            self.precision,
        )
        avg_marg = round(
            sum(funded_marginal_scores) / len(funded_marginal_scores) if funded_marginal_scores else 0.0,
            self.precision,
        )
        avg_funded_sat = round(
            sum(funded_saturations) / len(funded_saturations) if funded_saturations else 0.0,
            self.precision,
        )

        portfolio_breakdown = {
            "budget_utilization": budget_utilization,
            "project_count_funded": len(funded_base_scores),
            "state_allocation_distribution": state_allocations,
            "sector_allocation_distribution": sector_allocations,
            "average_base_score": avg_base,
            "average_marginal_score": avg_marg,
            "average_saturation": avg_funded_sat,
        }

        optimization_audit = {
            "total_projects_considered": len(allocations),
            "projects_funded": len(funded_base_scores),
            "projects_skipped": len(allocations) - len(funded_base_scores),
            "budget_requested_total_paise": sum(
                projects_map[a.project_id].financials.requested_amount_paise for a in allocations
            ),
            "budget_allocated_total_paise": allocated_total,
            "budget_unallocated_paise": unallocated_total,
        }

        pipeline_summary = {
            "projects_processed": len(allocations),
            "funded_projects": len(funded_base_scores),
            "budget_utilization": portfolio_breakdown["budget_utilization"],
            "engine_versions": CALCULATION_VERSIONS,
        }

        return {
            "allocated_paise": allocated_total,
            "unallocated_paise": unallocated_total,
            "total_predicted_impact": round(total_predicted_impact, self.precision),
            "average_saturation": average_saturation,
            "underserved_region_allocation_share": underserved_share,
            "portfolio_breakdown": portfolio_breakdown,
            "optimization_audit": optimization_audit,
            "pipeline_summary": pipeline_summary,
        }

    # -----------------------------------------------------------------------
    # Primary Optimization Method
    # -----------------------------------------------------------------------

    def calculate_optimal_allocation(
        self,
        request: OptimizationRequest,
        projects: list[Project],
        saturation_results: list[SaturationResult] | None = None,
        marginal_results: list[MarginalImpactResult] | None = None,
        run_id: str | None = None,
        created_at: str = "2026-09-01T00:00:00Z",
    ) -> OptimizationResult:
        """Execute deterministic budget optimization across candidate projects.

        Steps:
            1. Validate input request and project parameters.
            2. Match projects and precomputed scores (or compute if missing).
            3. Validate constraints feasibility via ConstraintEngine.
            4. Rank projects using composite score and 5-step tie-breaking.
            5. Sequentially allocate budget respecting project, region, and minimum caps.
            6. Generate deterministic reason codes for every project.
            7. Calculate portfolio metrics and explainability breakdown.
            8. Emit validated OptimizationResult.

        Args:
            request: OptimizationRequest payload.
            projects: Candidate project entities.
            saturation_results: Optional precomputed saturation results.
            marginal_results: Optional precomputed marginal impact results.
            run_id: Optional deterministic run identifier.
            created_at: Schema timestamp metadata string.

        Returns:
            Validated OptimizationResult.
        """
        # 1. Validation
        self.validate_inputs(request, projects, saturation_results, marginal_results)

        projects_by_id = {p.project_id: p for p in projects}
        matched_projects = [projects_by_id[pid] for pid in request.project_ids]

        # 2. Build maps for saturation and marginal results (fallback computation if omitted)
        saturation_map: dict[str, SaturationResult] = {}
        if saturation_results:
            for s in saturation_results:
                saturation_map[s.project_id] = s

        marginal_map: dict[str, MarginalImpactResult] = {}
        if marginal_results:
            for m in marginal_results:
                marginal_map[m.project_id] = m

        base_scores_map: dict[str, float] = {}
        for p in matched_projects:
            # Base score
            base_scores_map[p.project_id] = self.scoring_engine.calculate_base_score(p)

            # Saturation result fallback
            if p.project_id not in saturation_map:
                st = p.geographies[0].state if p.geographies else "DefaultState"
                from backend.app.engine.schemas import SaturationContext
                ctx = SaturationContext(
                    state=st,
                    sector=p.sector,
                    total_regional_csr_paise=0,
                    total_population=1_000_000,
                    target_population=100_000,
                )
                saturation_map[p.project_id] = self.saturation_engine.calculate_saturation(p, ctx)

            # Marginal result fallback
            if p.project_id not in marginal_map:
                sat_res = saturation_map[p.project_id]
                marginal_map[p.project_id] = self.marginal_engine.calculate_marginal_impact(
                    project=p,
                    saturation_result=sat_res,
                    increment_paise=request.marginal_increment_paise,
                )

        # 3. Constraints feasibility validation
        self.constraint_engine.validate_constraints(request, matched_projects)

        # 4. Rank projects
        ranked_projects = self.rank_projects(
            projects=matched_projects,
            weights=request.weights,
            saturation_map=saturation_map,
            marginal_map=marginal_map,
            base_scores_map=base_scores_map,
        )

        # 5. Sequential budget allocation
        total_budget = request.budget_paise
        allocated_so_far = 0
        regional_allocations: dict[str, int] = {}
        allocations: list[Allocation] = []

        for rank_idx, ranked in enumerate(ranked_projects, start=1):
            p = ranked.project
            st = p.geographies[0].state if p.geographies else "UNKNOWN"

            budget_rem = self.constraint_engine.calculate_remaining_budget(
                total_budget, allocated_so_far
            )
            project_cap_rem = self.constraint_engine.apply_project_cap(
                p, request.constraints
            )
            region_cap_rem = self.constraint_engine.apply_region_cap(
                st, request.constraints, regional_allocations
            )

            # Max possible for this project under available budget, project cap, region cap
            candidate_amount = min(budget_rem, project_cap_rem, region_cap_rem)

            # Enforce minimum allocation floor
            allocated_amount = self.constraint_engine.apply_minimum_allocation(
                candidate_amount, request.constraints
            )

            # Commit allocation
            allocated_so_far += allocated_amount
            regional_allocations[st] = regional_allocations.get(st, 0) + allocated_amount

            # 6. Generate Reason Codes
            codes = self.generate_reason_codes(
                ranked=ranked,
                allocated_amount_paise=allocated_amount,
                project_cap_remaining=project_cap_rem,
                region_cap_remaining=region_cap_rem,
                budget_remaining=budget_rem,
                minimum_allocation_paise=request.constraints.minimum_allocation_per_project_paise,
            )

            # Build Allocation
            allocation = self.build_allocation(
                ranked=ranked,
                allocated_amount_paise=allocated_amount,
                rank=rank_idx,
                reason_codes=codes,
            )
            allocations.append(allocation)

        unallocated_paise = total_budget - allocated_so_far

        # Invariant check: require_full_budget_allocation
        if request.constraints.require_full_budget_allocation and unallocated_paise > 0:
            raise ConstraintViolationError(
                f"require_full_budget_allocation=True requires complete budget allocation, but {unallocated_paise} paise remains unallocated.",
                constraint_name="require_full_budget_allocation",
            )

        # 7. Portfolio metrics
        metrics = self.calculate_portfolio_metrics(
            allocations=allocations,
            total_budget_paise=total_budget,
            projects_map=projects_by_id,
            marginal_map=marginal_map,
        )

        # Deterministic run_id if not supplied
        if run_id is None:
            run_id = f"OPT-{total_budget}-{len(request.project_ids)}"

        return OptimizationResult(
            run_id=run_id,
            status=OptimizationStatus.COMPLETED,
            budget_paise=total_budget,
            allocated_paise=metrics["allocated_paise"],
            unallocated_paise=metrics["unallocated_paise"],
            allocations=allocations,
            total_predicted_impact=metrics["total_predicted_impact"],
            average_saturation=metrics["average_saturation"],
            underserved_region_allocation_share=metrics["underserved_region_allocation_share"],
            weights=request.weights,
            constraints=request.constraints,
            calculation_versions=CALCULATION_VERSIONS,
            created_at=created_at,
            portfolio_breakdown=metrics["portfolio_breakdown"],
            optimization_audit=metrics["optimization_audit"],
            pipeline_summary=metrics["pipeline_summary"],
        )

    def optimize(
        self,
        projects: list[Project],
        dna: list[ImpactDNA] | None,
        saturation: list[SaturationResult] | None,
        request: OptimizationRequest,
    ) -> OptimizationResult:
        """Contract compatibility alias delegating to calculate_optimal_allocation.

        Maintains exact interface compatibility with Technical Contract Section 51.
        """
        return self.calculate_optimal_allocation(
            request=request,
            projects=projects,
            saturation_results=saturation,
        )
