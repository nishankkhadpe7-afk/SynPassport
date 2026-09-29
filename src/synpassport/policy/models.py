"""Policy profile data models and threshold specifications.

Defines threshold requirements, evaluation budgets, and purpose-specific check lists.
"""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

__all__ = [
    "CheckState",
    "SEVERITY_ORDER",
    "BudgetConfig",
    "PolicyProfile",
]


class CheckState(StrEnum):
    """Evaluation verdict states for checks and intended uses."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


# Severity ordering: FAIL > INSUFFICIENT_EVIDENCE > WARNING > PASS
SEVERITY_ORDER: dict[CheckState, int] = {
    CheckState.FAIL: 4,
    CheckState.INSUFFICIENT_EVIDENCE: 3,
    CheckState.WARNING: 2,
    CheckState.PASS: 1,
}


class BudgetConfig(BaseModel):
    """Execution budget constraints for candidate evaluation and repairs."""

    max_candidates: int = Field(default=3, ge=1)
    max_repairs: int = Field(default=2, ge=0)


class PolicyProfile(BaseModel):
    """Locked, versioned policy profile specifying thresholds and purpose bindings."""

    id: str
    version: int = 1
    name: str | None = None
    description: str | None = None
    requires: dict[str, Any] = Field(default_factory=dict)
    budget: BudgetConfig = Field(default_factory=BudgetConfig)
    uses: dict[str, list[str]] = Field(default_factory=dict)
    warning_bands: dict[str, dict[str, float]] = Field(default_factory=dict)
    human_approval: str = "optional"
    sha256: str | None = None

    def get_required_checks_for_use(self, use: str) -> list[str]:
        """Resolve list of required check IDs for a given intended use.

        If the use declares ['all'], expands to all check IDs in requires.
        """
        declared = self.uses.get(use, [])
        if "all" in declared:
            return list(self.requires.keys())
        return list(declared)
