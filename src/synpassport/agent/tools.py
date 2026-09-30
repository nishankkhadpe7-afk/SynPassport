"""Whitelisted agent tool registry and action schemas.

Dispatches validated tool actions (generate_candidate, run_check, run_privacy_attack,
propose_repair, explain, finalize). Arbitrary code execution tools do not exist.
"""

from __future__ import annotations

from typing import Any

__all__ = ["AgentToolRegistry", "TOOL_SCHEMAS"]

TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "generate_candidate": {
        "type": "object",
        "properties": {
            "generator": {"type": "string", "enum": ["GaussianCopula", "CTGAN"]},
            "params": {"type": "object"},
            "seed": {"type": "integer"},
        },
    },
    "run_check": {
        "type": "object",
        "properties": {
            "check_id": {"type": "string"},
            "candidate_id": {"type": "string"},
        },
        "required": ["check_id"],
    },
    "run_privacy_attack": {
        "type": "object",
        "properties": {
            "attack_id": {
                "type": "string",
                "enum": ["privacy_dcr_vs_holdout", "membership_inference_auc"],
            },
            "candidate_id": {"type": "string"},
        },
        "required": ["attack_id"],
    },
    "propose_repair": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "tune_hyperparameters",
                    "switch_generator",
                    "enable_dp_training",
                ],
            },
            "params": {"type": "object"},
            "diagnosis": {"type": "string"},
        },
        "required": ["action"],
    },
    "explain": {
        "type": "object",
        "properties": {
            "evidence_ids": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["evidence_ids"],
    },
    "finalize": {
        "type": "object",
        "properties": {
            "candidate_id": {"type": "string"},
            "reason": {"type": "string"},
        },
    },
}


class AgentToolRegistry:
    """Registry of permitted tool calls with strict argument schema validation."""

    WHITELISTED_TOOLS = set(TOOL_SCHEMAS.keys())

    def validate_action(self, action: str, args: dict[str, Any]) -> tuple[bool, str]:
        """Validate action name and arguments against strict tool schemas."""
        # 1. Reject threshold modification proposals
        if "threshold" in action.lower() or any("threshold" in str(k).lower() for k in args):
            return (
                False,
                "Policy thresholds are locked and immutable; threshold changes are forbidden",
            )

        # 2. Reject unknown tools
        if action not in self.WHITELISTED_TOOLS:
            return False, f"Tool '{action}' is not in permitted tool registry"

        # 3. Validate required arguments
        schema = TOOL_SCHEMAS[action]
        required_keys = schema.get("required", [])
        for req in required_keys:
            if req not in args:
                return False, f"Action '{action}' missing required argument: '{req}'"

        # 4. Validate enum constraints
        properties = schema.get("properties", {})
        for param, val in args.items():
            if param in properties and "enum" in properties[param]:
                allowed = properties[param]["enum"]
                if val not in allowed:
                    return (
                        False,
                        f"Value '{val}' for parameter '{param}' is not permitted. "
                        f"Allowed: {allowed}",
                    )

        return True, "Accepted"

    def dispatch(self, action: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatch action if valid, otherwise return rejection description."""
        valid, reason = self.validate_action(action, args)
        if not valid:
            return {"status": "rejected", "action": action, "reason": reason}
        return {"status": "accepted", "action": action, "args": args}
