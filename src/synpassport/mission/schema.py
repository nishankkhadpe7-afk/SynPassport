"""Mission specification schema and restricted subgroup expression parser.

Validates user-declared mission parameters using Pydantic models.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from synpassport.checks.subgroups import parse_subgroup_expression

__all__ = ["Mission"]

_POLICY_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


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

    @field_validator("policy_id")
    @classmethod
    def _policy_id_is_profile_name(cls, value: str) -> str:
        # Missions name a bundled policy profile; file paths are not accepted here.
        if not _POLICY_ID_RE.match(value):
            raise ValueError(
                "policy_id must be a policy profile name (letters, digits, '-' or '_')"
            )
        return value

    @field_validator("critical_subgroups")
    @classmethod
    def _subgroups_parse(cls, value: list[str]) -> list[str]:
        for expr in value:
            parse_subgroup_expression(expr)
        return value

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if not self.intended_uses and self.purpose:
            self.intended_uses = [self.purpose]
        self.__dict__["data"] = self.model_dump()

    def to_dict(self) -> dict[str, Any]:
        """Return mission representation as a dictionary."""
        return dict(self.model_dump())

