"""Typed exceptions for AllocateAI Decision Engine.

Authoritative source: Software Contract v1.0 & Technical Contract v1.0.
All exceptions are structured, descriptive, and deterministic.
"""


class DecisionEngineError(Exception):
    """Base exception class for all AllocateAI Decision Engine errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConstraintViolationError(DecisionEngineError):
    """Raised when an optimization constraint cannot be satisfied or is violated."""

    def __init__(
        self,
        message: str = "Optimization constraint violated",
        constraint_name: str | None = None,
        details: dict | None = None,
    ) -> None:
        merged_details = details or {}
        if constraint_name:
            merged_details["constraint_name"] = constraint_name
        super().__init__(message, merged_details)
        self.constraint_name = constraint_name


class WeightValidationError(DecisionEngineError):
    """Raised when priority weights fail validation (e.g. out of [0, 1] bounds or sum != 1.0)."""

    def __init__(
        self,
        message: str = "Optimization weights validation failed",
        weight_sum: float | None = None,
        invalid_weights: dict | None = None,
        details: dict | None = None,
    ) -> None:
        merged_details = details or {}
        if weight_sum is not None:
            merged_details["weight_sum"] = weight_sum
        if invalid_weights:
            merged_details["invalid_weights"] = invalid_weights
        super().__init__(message, merged_details)
        self.weight_sum = weight_sum
        self.invalid_weights = invalid_weights


class InvalidProjectDataError(DecisionEngineError):
    """Raised when project data is malformed, missing required values, or out of valid ranges."""

    def __init__(
        self,
        message: str = "Project data validation failed",
        project_id: str | None = None,
        field_name: str | None = None,
        details: dict | None = None,
    ) -> None:
        merged_details = details or {}
        if project_id:
            merged_details["project_id"] = project_id
        if field_name:
            merged_details["field_name"] = field_name
        super().__init__(message, merged_details)
        self.project_id = project_id
        self.field_name = field_name


class BudgetValidationError(DecisionEngineError):
    """Raised when budget amounts or paise values are invalid (e.g., negative, non-integer, zero budget)."""

    def __init__(
        self,
        message: str = "Budget validation failed",
        amount_paise: int | None = None,
        details: dict | None = None,
    ) -> None:
        merged_details = details or {}
        if amount_paise is not None:
            merged_details["amount_paise"] = amount_paise
        super().__init__(message, merged_details)
        self.amount_paise = amount_paise


class CalculationVersionError(DecisionEngineError):
    """Raised when a calculation version is unsupported, mismatched, or invalid."""

    def __init__(
        self,
        message: str = "Calculation version error",
        provided_version: str | None = None,
        expected_version: str | None = None,
        details: dict | None = None,
    ) -> None:
        merged_details = details or {}
        if provided_version:
            merged_details["provided_version"] = provided_version
        if expected_version:
            merged_details["expected_version"] = expected_version
        super().__init__(message, merged_details)
        self.provided_version = provided_version
        self.expected_version = expected_version
