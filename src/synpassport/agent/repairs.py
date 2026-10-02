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

__all__ = [
    "SUPPORTED_GENERATORS",
    "TUNABLE_PARAMS",
    "WHITELISTED_REPAIRS",
    "normalize_target_generator",
    "validate_repair_action",
]

SUPPORTED_GENERATORS = ("GaussianCopula", "CTGAN")
# LLMs name this argument inconsistently; all spellings mean the same thing.
GENERATOR_PARAM_ALIASES = ("target_generator", "generator", "generator_name")


def normalize_target_generator(params: dict[str, Any]) -> str | None:
    """Return the requested generator from any accepted argument spelling."""
    for key in GENERATOR_PARAM_ALIASES:
        if params.get(key):
            return str(params[key])
    return None

# Hyperparameters the bundled generators actually consume, with safe integer ranges.
TUNABLE_PARAMS: dict[str, tuple[int, int]] = {
    "epochs": (1, 500),
    "batch_size": (10, 10_000),
}

WHITELISTED_REPAIRS = {
    "tune_hyperparameters",
    "switch_generator",
    "regenerate_identifiers",
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
    if action == "enable_dp_training":
        # No differentially private generator ships with SynPassport, so accepting this
        # would record a privacy repair in the passport that never actually happened.
        return (
            False,
            "enable_dp_training is not supported: no differentially private generator "
            "is installed",
        )

    if action == "tune_hyperparameters":
        unknown = sorted(set(params) - set(TUNABLE_PARAMS))
        if unknown:
            allowed = sorted(TUNABLE_PARAMS)
            return False, f"Unsupported hyperparameters {unknown}; allowed: {allowed}"
        for name, (low, high) in TUNABLE_PARAMS.items():
            if name not in params:
                continue
            val = params[name]
            if isinstance(val, bool) or not isinstance(val, int) or not low <= val <= high:
                return False, f"Hyperparameter '{name}' must be an integer in [{low}, {high}]"

    if action == "regenerate_identifiers":
        # Which columns count as identifiers is decided by code from the real data,
        # never by the agent, so this repair takes no parameters.
        extra = sorted(k for k in params if k != "diagnosis")
        if extra:
            return False, (
                f"regenerate_identifiers takes no parameters (got {extra}); identifier "
                "columns are detected automatically"
            )

    if action == "switch_generator":
        unknown = sorted(set(params) - set(GENERATOR_PARAM_ALIASES))
        if unknown:
            return False, f"Unsupported switch_generator params {unknown}; use target_generator"
        target = normalize_target_generator(params)
        if target is None:
            return False, "switch_generator requires target_generator"
        if target not in SUPPORTED_GENERATORS:
            return (
                False,
                f"Generator '{target}' is not supported; "
                f"choose one of {list(SUPPORTED_GENERATORS)}",
            )

    return True, "Accepted"
