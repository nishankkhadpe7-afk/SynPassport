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

__all__ = [
    "BaseLLMClient",
    "GeminiLLMClient",
    "GroqLLMClient",
    "MockLLM",
    "RuleBasedPlanner",
    "create_llm_client",
    "describe_llm_client",
    "query_llm_structured",
]


class BaseLLMClient(ABC):
    """Abstract interface for LLM completion providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        """Generate text response from prompt and system instructions."""


class GeminiLLMClient(BaseLLMClient):
    """Google Gemini completion client via Generative Language REST API."""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key.strip()
        self.model = model.strip() if model and model.strip() else "gemini-1.5-flash"

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        import requests

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload: dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 600,
                "responseMimeType": "application/json",
            },
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }

        headers = {"Content-Type": "application/json"}
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini API returned no candidates: {data}")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError(f"Gemini API response content has no parts: {data}")
        return str(parts[0].get("text", ""))


def create_llm_client(
    api_key: str | None = None,
    model: str | None = None,
) -> BaseLLMClient:
    """Factory creating an LLM client from environment or explicitly provided parameters.

    Auto-detects provider from key prefix:
      - gsk_*  → Groq (OpenAI-compatible, qwen/qwen3.8-27b default)
      - AIza* or AQ.* → Google Gemini REST API
    """
    import os

    resolved_key = (
        api_key
        or os.environ.get("LLM_API_KEY")
        or os.environ.get("GROQ_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or ""
    ).strip()
    resolved_model = (model or os.environ.get("LLM_MODEL", "")).strip()

    if not resolved_key:
        # No key: the agent still repairs, using a fixed, auditable rule set.
        return RuleBasedPlanner()

    # Groq key detection (gsk_ prefix)
    if resolved_key.startswith("gsk_"):
        groq_model = resolved_model if resolved_model else "qwen/qwen3.8-27b"
        return GroqLLMClient(api_key=resolved_key, model=groq_model)

    # Gemini key (AIza or AQ. prefix, or unknown — default to Gemini)
    gemini_model = resolved_model if resolved_model else "gemini-1.5-flash"
    return GeminiLLMClient(api_key=resolved_key, model=gemini_model)


class GroqLLMClient(BaseLLMClient):
    """Groq completion client via OpenAI-compatible REST API."""

    def __init__(self, api_key: str, model: str = "qwen/qwen3.8-27b") -> None:
        self.api_key = api_key.strip()
        self.model = model.strip() if model and model.strip() else "qwen/qwen3.8-27b"

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        import requests

        url = "https://api.groq.com/openai/v1/chat/completions"
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.1,
            # A decision is a short JSON object; the cap stops runaway explanations.
            "max_tokens": 600,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError(f"Groq API returned no choices: {data}")
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise RuntimeError(f"Groq API response has empty content: {data}")
        return str(content)


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
    allowed_actions: set[str] | None = None,
) -> tuple[dict[str, Any] | None, list[str]]:
    """Query LLM with bounded retries on malformed JSON or schema rejections."""
    registry = tool_registry or AgentToolRegistry()
    retry_errors: list[str] = []
    current_prompt = prompt

    for attempt in range(max_retries):
        raw_output = client.generate(current_prompt, system_prompt)

        # 1. Parse JSON (stripping markdown code fences if present)
        clean_output = raw_output.strip()
        if clean_output.startswith("```"):
            lines = clean_output.split("\n")
            if len(lines) >= 2 and lines[0].startswith("```"):
                clean_output = "\n".join(lines[1:])
            if clean_output.endswith("```"):
                clean_output = clean_output[:-3]
            clean_output = clean_output.strip()

        try:
            parsed = json.loads(clean_output)
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

        if allowed_actions is not None and action not in allowed_actions:
            allowed = ", ".join(sorted(allowed_actions))
            retry_errors.append(
                f"Action '{action}' rejected: not permitted in this step (allowed: {allowed})"
            )
            current_prompt = (
                f"{prompt}\n\nERROR: Action '{action}' is not permitted in this step. "
                f"Choose one of: {allowed}."
            )
            continue

        # Successfully parsed and validated
        return parsed, retry_errors

    return None, retry_errors


class RuleBasedPlanner(BaseLLMClient):
    """Offline planner used when no LLM key is configured or the LLM call fails.

    It never calls a model. The agent loop asks it for a decision directly via
    :meth:`decide`, which follows a fixed, auditable repair order:
    switch GaussianCopula -> CTGAN, then double CTGAN's training epochs.
    """

    def generate(self, prompt: str, system_prompt: str | None = None) -> str:
        return json.dumps(
            {
                "thought_summary": "Rule-based planner does not use free-text prompts",
                "action": "finalize",
                "args": {"reason": "Rule-based planner"},
            }
        )

    @staticmethod
    def decide(
        current_generator: str,
        current_params: dict[str, Any],
        check_states: dict[str, str] | None = None,
        regenerating_identifiers: bool = False,
    ) -> dict[str, Any]:
        """Return the next whitelisted repair for the current generator settings."""
        states = check_states or {}
        if states.get("identifier_leakage") not in (None, "PASS") and not regenerating_identifiers:
            return {
                "thought_summary": (
                    "Real identifiers were copied into the synthetic data. Rule 0: "
                    "replace identifier columns with fresh values in the same format."
                ),
                "action": "propose_repair",
                "args": {"action": "regenerate_identifiers", "params": {}},
            }
        if current_generator != "CTGAN":
            return {
                "thought_summary": (
                    "Candidate missed the policy. Rule 1: switch from GaussianCopula to "
                    "CTGAN, which can model more complex distributions."
                ),
                "action": "propose_repair",
                "args": {
                    "action": "switch_generator",
                    "params": {"target_generator": "CTGAN"},
                },
            }
        epochs = int(current_params.get("epochs", 50))
        return {
            "thought_summary": (
                f"Still missing the policy after switching to CTGAN. Rule 2: train CTGAN longer "
                f"({epochs} -> {min(500, epochs * 2)} epochs)."
            ),
            "action": "propose_repair",
            "args": {
                "action": "tune_hyperparameters",
                "params": {"epochs": min(500, epochs * 2)},
            },
        }


def describe_llm_client(client: BaseLLMClient) -> str:
    """Human-readable name of the decision maker, shown on the run timeline."""
    if isinstance(client, GroqLLMClient):
        return f"Groq ({client.model})"
    if isinstance(client, GeminiLLMClient):
        return f"Gemini ({client.model})"
    if isinstance(client, RuleBasedPlanner):
        return "rule-based planner (no LLM key configured)"
    if isinstance(client, MockLLM):
        return "mock LLM (tests)"
    return type(client).__name__
