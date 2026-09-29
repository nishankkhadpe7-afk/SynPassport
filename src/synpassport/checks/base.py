"""Base definitions and interfaces for evaluation checks."""

from abc import ABC, abstractmethod
from typing import Any

__all__ = ["BaseCheck", "CheckResult"]


class CheckResult:
    """Outcome and metrics produced by an evaluation check."""

    def __init__(
        self,
        check_id: str,
        value: float,
        ci_low: float | None = None,
        ci_high: float | None = None,
        n: int | None = None,
        seed: int | None = None,
        state: str | None = None,
        threshold_ref: str | None = None,
        error: str | None = None,
        **metadata: Any,
    ) -> None:
        self.check_id = check_id
        self.value = value
        self.ci_low = ci_low
        self.ci_high = ci_high
        self.n = n
        self.seed = seed
        self.state = state
        self.threshold_ref = threshold_ref
        self.error = error
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert check result to dictionary for evidence records."""
        data: dict[str, Any] = {
            "check_id": self.check_id,
            "value": self.value,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "n": self.n,
            "seed": self.seed,
            "state": self.state,
            "threshold_ref": self.threshold_ref,
            "error": self.error,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        return data


class BaseCheck(ABC):
    """Abstract base class for all synthetic data evaluation checks."""

    check_id: str

    @abstractmethod
    def run(self, real_data: Any, synth_data: Any, **kwargs: Any) -> CheckResult:
        """Execute check evaluation returning structured result metrics."""
        raise NotImplementedError
