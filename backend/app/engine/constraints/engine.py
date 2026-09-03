"""Constraint Engine for AllocateAI Decision Engine (Member C Phase 5).

Responsible for evaluating and enforcing policy constraints:
- Project allocation caps
- Regional allocation caps
- Minimum project allocation floors
- Regional equity policy enforcement
- Total budget exhaustion feasibility verification

Authoritative contracts: Software Contract v1.0 & Technical Contract v1.0.
Strictly deterministic: zero randomness, zero external APIs, zero temporal dependencies.
All monetary amounts represented in integer paise.
"""

import sys
from typing import Final

from backend.app.engine.exceptions import (
    ConstraintViolationError,
)
from backend.app.engine.schemas import (
    OptimizationConstraints,
    OptimizationRequest,
    Project,
)


class ConstraintEngine:
    """Deterministic constraint engine enforcing financial, project, and regional rules."""

    def validate_constraints(
        self,
        request: OptimizationRequest,
        projects: list[Project],
    ) -> None:
        """Validate mathematical feasibility of constraints against candidate projects and total budget.

        Args:
            request: Optimization request containing constraints and total budget.
            projects: List of candidate projects.

        Raises:
            ConstraintViolationError: If constraints are mathematically impossible to satisfy.
        """
        constraints = request.constraints
        budget = request.budget_paise

        # 1. Validate minimum allocation per project against total budget
        if constraints.minimum_allocation_per_project_paise is not None:
            min_alloc = constraints.minimum_allocation_per_project_paise
            if min_alloc > budget:
                raise ConstraintViolationError(
                    f"Minimum allocation per project ({min_alloc} paise) exceeds total budget ({budget} paise)",
                    constraint_name="minimum_allocation_per_project_paise",
                )
            if constraints.max_allocation_per_project_paise is not None:
                if min_alloc > constraints.max_allocation_per_project_paise:
                    raise ConstraintViolationError(
                        f"Minimum allocation ({min_alloc} paise) exceeds maximum project cap ({constraints.max_allocation_per_project_paise} paise)",
                        constraint_name="minimum_allocation_per_project_paise",
                    )

        # 2. Feasibility check for require_full_budget_allocation
        if constraints.require_full_budget_allocation:
            # Maximum absorbable capacity across all projects under project caps
            max_absorbable_total = 0
            for p in projects:
                remaining_need = max(
                    0,
                    p.financials.requested_amount_paise - p.financials.current_funding_paise,
                )
                if constraints.max_allocation_per_project_paise is not None:
                    max_p = min(remaining_need, constraints.max_allocation_per_project_paise)
                else:
                    max_p = remaining_need
                max_absorbable_total += max_p

            if max_absorbable_total < budget:
                raise ConstraintViolationError(
                    f"Full budget allocation required ({budget} paise), but candidate projects can absorb at most {max_absorbable_total} paise",
                    constraint_name="require_full_budget_allocation",
                )

            # Regional caps feasibility check
            if constraints.max_allocation_per_region_paise is not None and constraints.regional_equity_enabled:
                states = {p.geographies[0].state for p in projects if p.geographies}
                max_regional_total = len(states) * constraints.max_allocation_per_region_paise
                if max_regional_total < budget:
                    raise ConstraintViolationError(
                        f"Full budget allocation required ({budget} paise), but regional caps across {len(states)} regions allow at most {max_regional_total} paise",
                        constraint_name="max_allocation_per_region_paise",
                    )

    def apply_project_cap(
        self,
        project: Project,
        constraints: OptimizationConstraints,
        already_allocated_to_project: int = 0,
    ) -> int:
        """Calculate maximum allowable additional allocation to a project under project need and caps.

        Args:
            project: Project entity.
            constraints: Optimization constraints.
            already_allocated_to_project: Amount already committed in current run in paise.

        Returns:
            Allowable additional allocation in integer paise.
        """
        remaining_project_need = max(
            0,
            project.financials.requested_amount_paise
            - project.financials.current_funding_paise
            - already_allocated_to_project,
        )

        if constraints.max_allocation_per_project_paise is not None:
            cap_remaining = max(
                0,
                constraints.max_allocation_per_project_paise - already_allocated_to_project,
            )
            return min(remaining_project_need, cap_remaining)

        return remaining_project_need

    def apply_region_cap(
        self,
        state: str,
        constraints: OptimizationConstraints,
        regional_allocations: dict[str, int],
    ) -> int:
        """Calculate maximum allowable additional allocation into a region under regional caps.

        Args:
            state: Geographic state name.
            constraints: Optimization constraints.
            regional_allocations: Current cumulative allocations by state in paise.

        Returns:
            Allowable additional regional allocation in integer paise.
        """
        if constraints.max_allocation_per_region_paise is not None and constraints.regional_equity_enabled:
            current_allocated = regional_allocations.get(state, 0)
            return max(0, constraints.max_allocation_per_region_paise - current_allocated)

        return sys.maxsize

    def apply_minimum_allocation(
        self,
        candidate_amount_paise: int,
        constraints: OptimizationConstraints,
    ) -> int:
        """Enforce minimum allocation threshold floor.

        Args:
            candidate_amount_paise: Candidate allocation amount in paise.
            constraints: Optimization constraints.

        Returns:
            candidate_amount_paise if >= minimum, else 0.
        """
        if constraints.minimum_allocation_per_project_paise is not None:
            if candidate_amount_paise < constraints.minimum_allocation_per_project_paise:
                return 0
        return candidate_amount_paise

    def calculate_remaining_budget(
        self,
        total_budget_paise: int,
        allocated_so_far_paise: int,
    ) -> int:
        """Calculate unallocated remaining budget in integer paise.

        Args:
            total_budget_paise: Initial total budget in paise.
            allocated_so_far_paise: Cumulative allocations committed so far.

        Returns:
            Remaining budget in integer paise (never negative).
        """
        return max(0, total_budget_paise - allocated_so_far_paise)
