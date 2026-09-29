"""Dataset loader guard enforcing purpose-bound passport verification.

Prevents unauthorized, unsupported, or tampered datasets from being loaded into
downstream training or analytics pipelines.
"""

from typing import Any

__all__ = ["PassportError", "load_dataset"]


class PassportError(Exception):
    """Raised when dataset loading is blocked due to missing or invalid assurance verification."""

    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def load_dataset(
    dataset_path: str,
    purpose: str,
    passport_path: str | None = None,
    allow_warning: bool = False,
) -> Any:
    """Load dataset after strictly validating Evidence Passport against declared purpose."""
    raise NotImplementedError("Feature implementation pending")
