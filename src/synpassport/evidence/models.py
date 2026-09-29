"""Evidence record models.

Defines schemas for storing check metrics, confidence intervals, sample counts,
random seeds, and code revision hashes.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

__all__ = ["EvidenceRecord"]


class EvidenceRecord(BaseModel):
    """Represents an individual metric observation recorded during evaluation."""

    run_id: str
    candidate_id: str
    check_id: str
    value: float
    ci_low: float | None = None
    ci_high: float | None = None
    n: int | None = None
    threshold_ref: str = ""
    seed: int | None = None
    code_version: str = "git:0.1.0"
    state: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize evidence record to dictionary."""
        return {
            "run_id": self.run_id,
            "candidate_id": self.candidate_id,
            "check_id": self.check_id,
            "value": self.value,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "n": self.n,
            "threshold_ref": self.threshold_ref,
            "seed": self.seed,
            "code_version": self.code_version,
            "state": self.state,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
