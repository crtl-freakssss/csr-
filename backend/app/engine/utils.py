"""Reusable deterministic utility functions for AllocateAI Decision Engine.

Authoritative source: Software Contract v1.0 & Technical Contract v1.0.
These functions only perform validation, normalization, and bounds enforcement.
They do not perform business calculations.
"""

import math
from typing import Any

from backend.app.engine.constants import (
    SCORE_MAX,
    SCORE_MIN,
    WEIGHT_MAX,
    WEIGHT_MIN,
    WEIGHT_SUM_TARGET,
    WEIGHT_SUM_TOLERANCE,
)
from backend.app.engine.exceptions import (
    BudgetValidationError,
    CalculationVersionError,
    InvalidProjectDataError,
    WeightValidationError,
)


def validate_score(score: float, name: str = "score") -> float:
    """Validate that a score is a finite real number within [0.0, 1.0].

    Args:
        score: The numerical score to validate.
        name: The name of the field for error reporting.

    Returns:
        The validated float score.

    Raises:
        InvalidProjectDataError: If score is non-numeric, NaN, infinite, or outside [0.0, 1.0].
    """
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise InvalidProjectDataError(
            f"{name} must be a numeric value, got {type(score).__name__}",
            field_name=name,
        )
    if math.isnan(score) or math.isinf(score):
        raise InvalidProjectDataError(
            f"{name} cannot be NaN or Infinite",
            field_name=name,
        )
    if not (SCORE_MIN <= score <= SCORE_MAX):
        raise InvalidProjectDataError(
            f"{name} must be in range [{SCORE_MIN}, {SCORE_MAX}], got {score}",
            field_name=name,
        )
    return float(score)


def clip_score(
    score: float,
    min_val: float = SCORE_MIN,
    max_val: float = SCORE_MAX,
) -> float:
    """Deterministically clip a score to [min_val, max_val].

    Args:
        score: The raw numerical score.
        min_val: Lower bound (defaults to 0.0).
        max_val: Upper bound (defaults to 1.0).

    Returns:
        The clipped float score.
    """
    if not isinstance(score, (int, float)) or isinstance(score, bool):
        raise InvalidProjectDataError(
            f"score must be numeric to clip, got {type(score).__name__}"
        )
    if math.isnan(score):
        return min_val
    if math.isinf(score):
        return max_val if score > 0 else min_val
    return float(max(min_val, min(score, max_val)))


def safe_division(
    numerator: float,
    denominator: float,
    default: float = 0.0,
    tolerance: float = 1e-12,
) -> float:
    """Perform deterministic division guarded against zero or negligible denominators.

    Args:
        numerator: Dividend.
        denominator: Divisor.
        default: Fallback value returned if denominator is near zero.
        tolerance: Threshold below which denominator is treated as zero.

    Returns:
        The result of numerator / denominator or default.
    """
    if not isinstance(numerator, (int, float)) or not isinstance(denominator, (int, float)):
        raise InvalidProjectDataError("Numerator and denominator must be numeric")
    if math.isnan(numerator) or math.isnan(denominator):
        return default
    if abs(denominator) < tolerance:
        return default
    result = numerator / denominator
    return default if (math.isnan(result) or math.isinf(result)) else float(result)


def validate_paise(
    amount: Any,
    name: str = "amount_paise",
    allow_zero: bool = True,
) -> int:
    """Validate that an amount represents monetary value in integer paise.

    Never accepts float rupees or negative paise.

    Args:
        amount: The monetary value to check.
        name: Name of the field for error reporting.
        allow_zero: Whether 0 is accepted.

    Returns:
        The validated integer paise amount.

    Raises:
        BudgetValidationError: If amount is a float, boolean, negative, or fails zero condition.
    """
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise BudgetValidationError(
            f"{name} must be an integer paise count, never float or non-integer. Got {type(amount).__name__}",
            details={"field_name": name, "received_value": str(amount)},
        )
    if allow_zero and amount < 0:
        raise BudgetValidationError(
            f"{name} must be non-negative (>= 0 paise), got {amount}",
            amount_paise=amount,
            details={"field_name": name},
        )
    if not allow_zero and amount <= 0:
        raise BudgetValidationError(
            f"{name} must be strictly positive (> 0 paise), got {amount}",
            amount_paise=amount,
            details={"field_name": name},
        )
    return amount


def validate_budget(budget_paise: Any) -> int:
    """Validate an optimization or allocation total budget.

    Budget must be an integer strictly greater than 0 paise.

    Args:
        budget_paise: Total budget in paise.

    Returns:
        The validated integer paise amount.

    Raises:
        BudgetValidationError: If budget is not an integer or <= 0.
    """
    return validate_paise(budget_paise, name="budget_paise", allow_zero=False)


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Deterministically normalize a dictionary of weights so they sum to 1.0.

    Args:
        weights: Mapping of weight names to float values.

    Returns:
        New mapping of weight names to normalized float values.

    Raises:
        WeightValidationError: If any weight is negative or total weight sum is <= 0.
    """
    if not weights:
        raise WeightValidationError("Cannot normalize empty weights dictionary")

    invalid = {k: v for k, v in weights.items() if not isinstance(v, (int, float)) or v < WEIGHT_MIN}
    if invalid:
        raise WeightValidationError(
            f"All weights must be non-negative numbers: {invalid}",
            invalid_weights=invalid,
        )

    total_sum = sum(weights.values())
    if total_sum <= 0:
        raise WeightValidationError(
            f"Weight sum must be strictly positive to normalize, got {total_sum}",
            weight_sum=total_sum,
        )

    return {k: float(v / total_sum) for k, v in weights.items()}


def validate_weights(
    weights: dict[str, float],
    tolerance: float = WEIGHT_SUM_TOLERANCE,
) -> None:
    """Validate that weights are individually bounded in [0, 1] and sum to 1.0.

    Args:
        weights: Mapping of weight names to float values.
        tolerance: Allowed deviation from 1.0.

    Raises:
        WeightValidationError: If any weight is out of bounds or sum deviation exceeds tolerance.
    """
    if not weights:
        raise WeightValidationError("Weights dictionary cannot be empty")

    invalid_bounds = {}
    for name, val in weights.items():
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            invalid_bounds[name] = val
        elif not (WEIGHT_MIN <= val <= WEIGHT_MAX):
            invalid_bounds[name] = val

    if invalid_bounds:
        raise WeightValidationError(
            f"Weights out of bounds [{WEIGHT_MIN}, {WEIGHT_MAX}]: {invalid_bounds}",
            invalid_weights=invalid_bounds,
        )

    total = sum(weights.values())
    if abs(total - WEIGHT_SUM_TARGET) > tolerance:
        raise WeightValidationError(
            f"Weights must sum to {WEIGHT_SUM_TARGET} (±{tolerance}), got {total:.6f}",
            weight_sum=total,
            details={"weights": weights},
        )


def validate_calculation_version(version: str, expected_version: str) -> None:
    """Validate that a calculation/schema version matches the required version contract.

    Args:
        version: Version string to validate.
        expected_version: Required contract version.

    Raises:
        CalculationVersionError: If versions do not match.
    """
    if version != expected_version:
        raise CalculationVersionError(
            f"Calculation version mismatch: expected '{expected_version}', got '{version}'",
            provided_version=version,
            expected_version=expected_version,
        )
