"""Pydantic request and response schemas for SynPassport API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

__all__ = [
    "ApproveRequest",
    "ApproveResponse",
    "BudgetUsed",
    "EvidenceItem",
    "RunCreatedResponse",
    "RunStatusResponse",
    "SubgroupSufficiencyItem",
    "SufficiencyResponse",
    "VerifyResponse",
]


class RunCreatedResponse(BaseModel):
    """Response returned upon successful run scheduling."""

    run_id: str
    status: str
    message: str


class BudgetUsed(BaseModel):
    """Run budget consumption metrics."""

    candidates_evaluated: int = 0
    max_candidates: int = 3
    repairs_attempted: int = 0
    max_repairs: int = 2


class RunStatusResponse(BaseModel):
    """Detailed status and candidate overview for a run."""

    run_id: str
    status: str
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    repairs: list[dict[str, Any]] = Field(default_factory=list)
    agent_rejections: list[dict[str, Any]] = Field(default_factory=list)
    budget_used: BudgetUsed = Field(default_factory=BudgetUsed)
    verdicts: dict[str, str] = Field(default_factory=dict)
    error: str | None = None


class EvidenceItem(BaseModel):
    """Empirical evidence measurement record."""

    check_id: str
    value: float | None = None
    ci_low: float | None = None
    ci_high: float | None = None
    n: int | None = None
    seed: int | None = None
    state: str | None = None
    threshold_ref: Any = None
    extra: dict[str, Any] = Field(default_factory=dict)


class ApproveRequest(BaseModel):
    """Human approval request payload."""

    approver: str = Field(..., description="Email or identifier of authorized approver")


class ApproveResponse(BaseModel):
    """Response returned after human approval and re-signing."""

    status: str
    approver: str
    passport: dict[str, Any]


class SubgroupSufficiencyItem(BaseModel):
    """Subgroup power analysis and projected confidence interval width."""

    subgroup_query: str
    current_n: int
    required_min_n: int
    projected_ci_width: float
    target_ci_width: float
    state: str
    reason: str


class SufficiencyResponse(BaseModel):
    """Subgroup sufficiency analysis overview for a run."""

    run_id: str
    current_n: int = 0
    required_min_n: int = 0
    ci_width: float = 0.0
    subgroups: list[SubgroupSufficiencyItem] = Field(default_factory=list)


class VerifyResponse(BaseModel):
    """Structured dataset and passport verification result."""

    valid: bool
    reason_code: str
    description: str
    details: dict[str, Any] = Field(default_factory=dict)
