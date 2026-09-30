"""Whitelisted repair validator.

Validates that agent repair proposals match the strict whitelist:
- tune_hyperparameters
- switch_generator
- enable_dp_training

Any proposal attempting to alter policy thresholds or execute unauthorized actions
is immediately rejected and recorded.
"""

from __future__ import annotations

from typing import Any

__all__ = ["WHITELISTED_REPAIRS", "validate_repair_action"]

WHITELISTED_REPAIRS = {
    "tune_hyperparameters",
    "switch_generator",
    "enable_dp_training",
}


def validate_repair_action(action: str, params: dict[str, Any] | None = None) -> tuple[bool, str]:
    """Validate whether repair proposal is permitted under the locked policy."""
    params = params or {}

    # Reject non-whitelisted actions first
    if action not in WHITELISTED_REPAIRS:
        allowed = sorted(WHITELISTED_REPAIRS)
        return (
            False,
            f"Action '{action}' is not in permitted repair whitelist: {allowed}",
        )

    # Reject threshold modification attempts in action or params
    if "threshold" in action.lower() or any("threshold" in str(k).lower() for k in params):
        return (
            False,
            "Policy thresholds are locked and immutable; threshold changes are forbidden",
        )

    # Validate specific action parameters
    if action == "switch_generator":
        target = params.get("target_generator") or params.get("generator")
        if target and target not in ("CTGAN", "GaussianCopula"):
            return False, f"Generator '{target}' is not supported"

    return True, "Accepted"
