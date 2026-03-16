from dataclasses import dataclass


@dataclass(frozen=True)
class Error:
    """
    Standard error model.
    'details' provides extra context for programmatic handling.
    """

    status_code: int
    error_code: str
    message: str
    details: dict | None = None
