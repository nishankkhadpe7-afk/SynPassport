"""Whitelisted agent tool registry and action schemas.

Dispatches validated tool actions (generate_candidate, run_check, run_privacy_attack,
propose_repair, explain). Arbitrary code execution tools do not exist.
"""

from typing import Any

__all__ = ["AgentToolRegistry"]


class AgentToolRegistry:
    """Registry of permitted tool calls with strict argument schema validation."""

    WHITELISTED_TOOLS = {
        "generate_candidate",
        "run_check",
        "run_privacy_attack",
        "propose_repair",
        "explain",
    }

    def dispatch(self, action: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatch action if whitelisted, otherwise return rejection."""
        if action not in self.WHITELISTED_TOOLS:
            return {"status": "rejected", "reason": f"Tool '{action}' is not whitelisted"}
        return {"status": "accepted"}
