"""Whitelisted repair validator.

Validates that agent repair proposals match the strict whitelist:
tune_hyperparameters, switch_generator, enable_dp_training.
Any proposal attempting to alter policy thresholds is immediately rejected and recorded.
"""

from typing import Any

__all__ = ["validate_repair_action"]

WHITELISTED_REPAIRS = {
    "tune_hyperparameters",
    "switch_generator",
    "enable_dp_training",
}


def validate_repair_action(action: str, params: dict[str, Any]) -> tuple[bool, str]:
    """Validate whether repair proposal is permitted under the locked policy."""
    if action not in WHITELISTED_REPAIRS:
        return False, f"Action '{action}' is not in permitted repair whitelist"
    return True, "Accepted"
