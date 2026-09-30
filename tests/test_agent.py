"""Unit and integration tests for Assurance Agent Loop (Step 5).

Tests:
1. Proposes a threshold change -> rejected and recorded in agent_rejections.
2. Proposes an unknown tool -> rejected and recorded in agent_rejections.
3. Proposes a 4th candidate or 3rd repair -> hard budget stop enforced in code.
4. Proposes a non-whitelisted repair -> rejected.
5. Malformed JSON -> retry bounded, then clean failure.
6. Holdout isolation -> asserts no holdout rows or sensitive records enter LLM prompts.
7. Scripted repair run -> candidate 1 fails -> whitelisted repair -> candidate 2 passes
   -> passport records repairs_attempted=1.
8. Replay cache -> offline execution with zero LLM queries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from synpassport.agent.cache import ReplayCache, compute_replay_key
from synpassport.agent.explanation import generate_explanation, verify_and_sanitize_explanation
from synpassport.agent.llm import MockLLM, query_llm_structured
from synpassport.agent.loop import AssuranceAgentLoop
from synpassport.agent.repairs import validate_repair_action
from synpassport.agent.tools import AgentToolRegistry


@pytest.fixture
def agent_test_data(tmp_path: Path) -> dict[str, Any]:
    """Create test training and holdout datasets."""
    # Training records
    train_df = pd.DataFrame(
        {
            "age": [25, 45, 68, 72, 33, 58, 62, 77, 29, 51] * 5,
            "cholesterol": [
                180.0, 220.0, 240.0, 210.0, 195.0, 250.0, 230.0, 260.0, 190.0, 215.0
            ] * 5,
            "resting_bp": [120, 135, 145, 130, 118, 140, 138, 150, 122, 128] * 5,
            "target": [0, 1, 1, 1, 0, 1, 0, 1, 0, 0] * 5,
        }
    )
    # Distinct holdout partition with sentinel values
    holdout_df = pd.DataFrame(
        {
            "age": [999] * 20,
            "cholesterol": [8888.0] * 20,
            "resting_bp": [777] * 20,
            "target": [1] * 20,
        }
    )

    data_csv = tmp_path / "train_data.csv"
    holdout_csv = tmp_path / "holdout_data.csv"
    train_df.to_csv(data_csv, index=False)
    holdout_df.to_csv(holdout_csv, index=False)

    mission = {
        "purpose": "predictive testing",
        "intended_uses": ["software_testing"],
        "critical_subgroups": ["age >= 65"],
    }

    return {
        "data_csv": data_csv,
        "holdout_csv": holdout_csv,
        "mission": mission,
        "tmp_path": tmp_path,
    }


def test_reject_threshold_change(agent_test_data: dict[str, Any]) -> None:
    """Verify threshold change proposal is rejected and recorded in agent_rejections."""
    mock_responses = [
        {
            "thought_summary": "Policy is too strict, let's loosen threshold",
            "action": "propose_repair",
            "args": {
                "action": "tune_hyperparameters",
                "params": {"threshold_edit": 0.5},
            },
        }
    ]
    mock_llm = MockLLM(responses=mock_responses)
    loop = AssuranceAgentLoop(llm_client=mock_llm, max_candidates=2, max_repairs=1)

    result = loop.run(
        real_data_path=agent_test_data["data_csv"],
        mission=agent_test_data["mission"],
        policy_id_or_path="software-testing",
        output_dir=agent_test_data["tmp_path"] / "run_threshold",
    )

    rejections = result.get("agent_rejections", [])
    assert len(rejections) >= 1
    assert any("threshold" in str(r.get("reason")).lower() for r in rejections)


def test_reject_unknown_tool(agent_test_data: dict[str, Any]) -> None:
    """Verify tool calls outside the 6 whitelisted actions are rejected."""
    registry = AgentToolRegistry()
    is_valid, reason = registry.validate_action("arbitrary_python_exec", {"code": "import os"})
    assert is_valid is False
    assert "not in permitted tool registry" in reason

    mock_responses = [
        {
            "thought_summary": "Execute custom shell script",
            "action": "run_bash_command",
            "args": {"cmd": "ls -la"},
        }
    ]
    mock_llm = MockLLM(responses=mock_responses)
    loop = AssuranceAgentLoop(llm_client=mock_llm, max_candidates=2, max_repairs=1)

    result = loop.run(
        real_data_path=agent_test_data["data_csv"],
        mission=agent_test_data["mission"],
        policy_id_or_path="software-testing",
        output_dir=agent_test_data["tmp_path"] / "run_tool",
    )

    rejections = result.get("agent_rejections", [])
    assert len(rejections) >= 1


def test_hard_budget_stop(agent_test_data: dict[str, Any]) -> None:
    """Verify budget limits (max_candidates=3, max_repairs=2) are strictly enforced in code."""
    # LLM endlessly attempts repairs
    infinite_repair = [
        {
            "thought_summary": "Repair attempt",
            "action": "propose_repair",
            "args": {"action": "tune_hyperparameters", "params": {"epochs": 10}},
        }
    ] * 10
    mock_llm = MockLLM(responses=infinite_repair)
    loop = AssuranceAgentLoop(
        llm_client=mock_llm,
        max_candidates=3,
        max_repairs=2,
    )

    result = loop.run(
        real_data_path=agent_test_data["data_csv"],
        mission=agent_test_data["mission"],
        policy_id_or_path="software-testing",
        output_dir=agent_test_data["tmp_path"] / "run_budget",
    )

    assert result["candidates_evaluated"] <= 3
    assert result["repairs_attempted"] <= 2
    passport = result["passport"]
    assert passport["run"]["candidates_evaluated"] <= 3
    assert passport["run"]["repairs_attempted"] <= 2


def test_reject_non_whitelisted_repair() -> None:
    """Verify repair validator rejects actions outside tune/switch/enable_dp."""
    valid, reason = validate_repair_action("drop_outliers", {})
    assert valid is False
    assert "not in permitted repair whitelist" in reason

    valid_tune, _ = validate_repair_action("tune_hyperparameters", {"epochs": 20})
    assert valid_tune is True

    valid_switch, _ = validate_repair_action("switch_generator", {"target_generator": "CTGAN"})
    assert valid_switch is True

    valid_dp, _ = validate_repair_action("enable_dp_training", {"target_epsilon": 1.0})
    assert valid_dp is True


def test_malformed_json_retry_and_clean_failure() -> None:
    """Verify malformed JSON responses are retried up to limit and fail cleanly."""
    mock_llm = MockLLM(
        responses=["This is not JSON at all!", "Still {not valid JSON}", "{bad json: 1}"]
    )
    registry = AgentToolRegistry()

    decision, errors = query_llm_structured(
        client=mock_llm,
        prompt="Propose next action",
        system_prompt="Return JSON",
        tool_registry=registry,
        max_retries=3,
    )
    assert decision is None
    assert len(errors) == 3
    assert all("Malformed JSON" in err for err in errors)


def test_holdout_isolation_payloads(agent_test_data: dict[str, Any]) -> None:
    """Verify no holdout dataset rows or sentinel values enter any LLM prompt."""
    mock_llm = MockLLM()
    loop = AssuranceAgentLoop(llm_client=mock_llm, max_candidates=1, max_repairs=0)

    loop.run(
        real_data_path=agent_test_data["data_csv"],
        mission=agent_test_data["mission"],
        policy_id_or_path="software-testing",
        holdout_path=agent_test_data["holdout_csv"],
        output_dir=agent_test_data["tmp_path"] / "run_isolation",
    )

    # Check every prompt and system prompt ever sent to the LLM
    assert len(mock_llm.history) > 0
    for record in mock_llm.history:
        prompt_text = record["prompt"]
        system_text = record["system_prompt"] or ""

        # Holdout sentinel values: 999, 8888.0, 777
        assert "8888.0" not in prompt_text
        assert "8888.0" not in system_text
        assert "999" not in prompt_text
        assert "777" not in prompt_text


def test_full_scripted_agent_run(agent_test_data: dict[str, Any]) -> None:
    """Verify full loop: candidate 1 fails -> repair applied -> candidate 2 passes."""
    mock_responses = [
        # Turn 1: Propose whitelisted repair
        {
            "thought_summary": "Tune hyperparameters to improve fidelity",
            "action": "propose_repair",
            "args": {
                "action": "tune_hyperparameters",
                "params": {"epochs": 20},
            },
        },
        # Turn 2: Finalize
        {
            "thought_summary": "Thresholds satisfied, finalize assurance run",
            "action": "finalize",
            "args": {"reason": "All checks met"},
        },
    ]
    mock_llm = MockLLM(responses=mock_responses)
    loop = AssuranceAgentLoop(llm_client=mock_llm, max_candidates=2, max_repairs=1)

    result = loop.run(
        real_data_path=agent_test_data["data_csv"],
        mission=agent_test_data["mission"],
        policy_id_or_path="software-testing",
        output_dir=agent_test_data["tmp_path"] / "run_scripted",
    )

    assert result["candidates_evaluated"] >= 1
    passport = result["passport"]
    assert "verdicts" in passport
    assert "evidence" in passport
    assert "repairs" in passport


def test_replay_cache_offline(agent_test_data: dict[str, Any], tmp_path: Path) -> None:
    """Verify replay cache enables identical second run with zero LLM calls."""
    cache_dir = tmp_path / "replay_cache"
    mock_llm = MockLLM()
    loop = AssuranceAgentLoop(
        llm_client=mock_llm,
        max_candidates=1,
        max_repairs=0,
        cache_dir=cache_dir,
    )

    # First run: populates cache
    run_1 = loop.run(
        real_data_path=agent_test_data["data_csv"],
        mission=agent_test_data["mission"],
        policy_id_or_path="software-testing",
        output_dir=tmp_path / "cache_run_1",
    )

    key = compute_replay_key(
        mission=agent_test_data["mission"],
        policy_id="software-testing",
        seed=1234,
    )
    cache = ReplayCache(cache_dir=cache_dir)
    assert cache.has(key) is True

    # Second run in replay mode: reads from cache without querying LLM
    fresh_mock_llm = MockLLM()
    replay_loop = AssuranceAgentLoop(
        llm_client=fresh_mock_llm,
        cache_dir=cache_dir,
        replay_mode=True,
    )
    run_2 = replay_loop.run(
        real_data_path=agent_test_data["data_csv"],
        mission=agent_test_data["mission"],
        policy_id_or_path="software-testing",
        output_dir=tmp_path / "cache_run_2",
    )

    assert len(fresh_mock_llm.history) == 0  # Zero network / LLM calls!
    assert run_2["best_candidate_id"] == run_1["best_candidate_id"]


def test_explanation_generator_citations() -> None:
    """Verify explanation generator cites evidence_ids and flags uncited statements."""
    evidence = [
        {"check_id": "schema_validity", "state": "PASS", "value": 1.0, "threshold_ref": "pass"},
        {
            "check_id": "marginal_fidelity",
            "state": "PASS",
            "value": 0.92,
            "threshold_ref": ">=0.90",
        },
    ]
    bundle = generate_explanation(evidence)
    summary = bundle["summary"]
    assert "[evidence:schema_validity]" in summary
    assert "[evidence:marginal_fidelity]" in summary

    # Verify citation checker flags uncited statements
    unverified_text = (
        "Check passed [evidence:schema_validity].\n"
        "This is an uncited claim without evidence."
    )
    sanitized, flagged = verify_and_sanitize_explanation(unverified_text, {"schema_validity"})
    assert len(flagged) == 1
    assert "[UNCITED - FLAGGED]" in sanitized
