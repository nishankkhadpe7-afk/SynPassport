"""Provider-agnostic LLM interface with structured-output validation.

Validates that LLM responses conform strictly to the action schema:
{ "thought_summary": "...", "action": "...", "args": { ... } }
Invalid JSON, unknown tools, or schema mismatches are rejected, logged, and retried.
Provides MockLLM for unit and integration testing.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from synpassport.agent.tools import AgentToolRegistry

__all__ = ["BaseLLMClient", "MockLLM", "query_llm_structured"]


class BaseLLMClient(ABC):
    """Abstract interface for LLM completion providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text response from prompt and system instructions."""


class MockLLM(BaseLLMClient):
    """Deterministic Mock LLM for unit tests, tracking prompt history for isolation verification."""

    def __init__(
        self,
        responses: list[str | dict[str, Any]] | None = None,
        generator_fn: Callable[[str], str] | None = None,
    ) -> None:
        self.responses: list[str] = []
        if responses:
            for r in responses:
                if isinstance(r, dict):
                    self.responses.append(json.dumps(r))
                else:
                    self.responses.append(str(r))
        self.generator_fn = generator_fn
        self.history: list[dict[str, Any]] = []

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Return next mocked response and record payload history for holdout verification."""
        self.history.append({
            "prompt": prompt,
            "system_prompt": system_prompt,
        })
        if self.generator_fn is not None:
            return self.generator_fn(prompt)
        if self.responses:
            return self.responses.pop(0)
        # Default fallback to finalize action
        return json.dumps({
            "thought_summary": "Default mock completion",
            "action": "finalize",
            "args": {"reason": "Mock completion finished"},
        })


def query_llm_structured(
    client: BaseLLMClient,
    prompt: str,
    system_prompt: str,
    tool_registry: AgentToolRegistry | None = None,
    max_retries: int = 3,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Query LLM with bounded retries on malformed JSON or schema rejections."""
    registry = tool_registry or AgentToolRegistry()
    retry_errors: list[str] = []
    current_prompt = prompt

    for attempt in range(max_retries):
        raw_output = client.generate(current_prompt, system_prompt)

        # 1. Parse JSON
        try:
            parsed = json.loads(raw_output.strip())
        except Exception as exc:
            err = f"Malformed JSON on attempt {attempt + 1}: {exc}"
            retry_errors.append(err)
            current_prompt = (
                f"{prompt}\n\nERROR: Previous response was not valid JSON ({exc}). "
                "Please return strictly valid JSON."
            )
            continue

        if not isinstance(parsed, dict):
            err = f"Response must be a JSON object, got {type(parsed).__name__}"
            retry_errors.append(err)
            current_prompt = f"{prompt}\n\nERROR: {err}. Please return a JSON object."
            continue

        # 2. Check required schema fields
        if "action" not in parsed:
            err = "Response missing required key 'action'"
            retry_errors.append(err)
            current_prompt = f"{prompt}\n\nERROR: {err}."
            continue

        action = str(parsed.get("action"))
        args = parsed.get("args") or {}
        if not isinstance(args, dict):
            err = "Field 'args' must be a dictionary"
            retry_errors.append(err)
            current_prompt = f"{prompt}\n\nERROR: {err}."
            continue

        # 3. Validate against tool registry
        valid, reason = registry.validate_action(action, args)
        if not valid:
            retry_errors.append(f"Action '{action}' rejected: {reason}")
            # If proposing a forbidden action like threshold changes, do not retry blindly
            if "threshold" in action.lower():
                return None, retry_errors
            current_prompt = (
                f"{prompt}\n\nERROR: Action '{action}' was rejected ({reason}). "
                "Please select a permitted action."
            )
            continue

        # Successfully parsed and validated
        return parsed, retry_errors

    return None, retry_errors
