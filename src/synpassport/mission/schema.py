"""Mission specification schema and restricted subgroup expression parser.

Validates user-declared mission parameters using Pydantic models.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

__all__ = ["Mission"]


class Mission(BaseModel):
    """User-declared assurance mission specification."""

    purpose: str
    intended_uses: list[str] = Field(default_factory=list)
    critical_subgroups: list[str] = Field(default_factory=list)
    policy_id: str = "software-testing"
    privacy_level: str = "standard"
    target_column: str | None = None
    seed: int = 1234

    model_config = {"extra": "allow"}

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.intended_uses and self.purpose:
            self.intended_uses = [self.purpose]
        self.__dict__["data"] = self.model_dump()

    def to_dict(self) -> dict[str, Any]:
        """Return mission representation as a dictionary."""
        return self.model_dump()

