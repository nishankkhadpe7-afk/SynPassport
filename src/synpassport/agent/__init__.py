"""Assurance agent loop, tools, and repair whitelists."""

from synpassport.agent.cache import ReplayCache, compute_replay_key
from synpassport.agent.explanation import (
    generate_explanation,
    verify_and_sanitize_explanation,
)
from synpassport.agent.llm import BaseLLMClient, MockLLM, query_llm_structured
from synpassport.agent.loop import AssuranceAgentLoop
from synpassport.agent.repairs import WHITELISTED_REPAIRS, validate_repair_action
from synpassport.agent.tools import TOOL_SCHEMAS, AgentToolRegistry

__all__ = [
    "AgentToolRegistry",
    "AssuranceAgentLoop",
    "BaseLLMClient",
    "MockLLM",
    "ReplayCache",
    "TOOL_SCHEMAS",
    "WHITELISTED_REPAIRS",
    "compute_replay_key",
    "generate_explanation",
    "query_llm_structured",
    "validate_repair_action",
    "verify_and_sanitize_explanation",
]
