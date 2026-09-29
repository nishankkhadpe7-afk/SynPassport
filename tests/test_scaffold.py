"""Tests verifying repository scaffold integrity, module structure, and docstrings."""

import importlib
import inspect

import pytest

import synpassport
from synpassport.agent.repairs import validate_repair_action
from synpassport.agent.tools import AgentToolRegistry
from synpassport.cli.main import main as cli_main

MODULES_TO_VERIFY = [
    "synpassport",
    "synpassport.mission",
    "synpassport.mission.schema",
    "synpassport.policy",
    "synpassport.policy.models",
    "synpassport.policy.loader",
    "synpassport.policy.engine",
    "synpassport.checks",
    "synpassport.checks.base",
    "synpassport.checks.schema",
    "synpassport.checks.fidelity",
    "synpassport.checks.utility",
    "synpassport.checks.privacy",
    "synpassport.checks.sufficiency",
    "synpassport.evidence",
    "synpassport.evidence.models",
    "synpassport.evidence.store",
    "synpassport.generators",
    "synpassport.generators.base",
    "synpassport.generators.sdv_wrapper",
    "synpassport.agent",
    "synpassport.agent.loop",
    "synpassport.agent.tools",
    "synpassport.agent.repairs",
    "synpassport.agent.prompts",
    "synpassport.passport",
    "synpassport.passport.canonical",
    "synpassport.passport.signer",
    "synpassport.passport.builder",
    "synpassport.passport.keygen",
    "synpassport.sdk",
    "synpassport.sdk.verify",
    "synpassport.sdk.guard",
    "synpassport.cli",
    "synpassport.cli.main",
    "synpassport.api",
    "synpassport.api.main",
]


def test_package_version() -> None:
    """Verify package version is defined."""
    assert synpassport.__version__ == "0.1.0"


@pytest.mark.parametrize("mod_name", MODULES_TO_VERIFY)
def test_module_import_and_docstring(mod_name: str) -> None:
    """Verify each module can be imported and possesses an informative docstring."""
    mod = importlib.import_module(mod_name)
    assert mod is not None
    doc = inspect.getdoc(mod)
    assert doc is not None and len(doc.strip()) > 10, f"Module {mod_name} missing docstring"


def test_cli_help(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI help invocation exits cleanly."""
    exit_code = cli_main(["--help"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "SynPassport CLI" in captured.out


def test_agent_tool_whitelist_rejection() -> None:
    """Verify arbitrary tool actions are rejected by tool registry."""
    registry = AgentToolRegistry()
    assert registry.dispatch("generate_candidate", {})["status"] == "accepted"
    rejection = registry.dispatch("arbitrary_code_exec", {})
    assert rejection["status"] == "rejected"


def test_agent_repair_whitelist_rejection() -> None:
    """Verify invalid repair actions are rejected."""
    ok, _ = validate_repair_action("tune_hyperparameters", {})
    assert ok is True
    rejected, reason = validate_repair_action("edit_policy_threshold", {})
    assert rejected is False
    assert "not in permitted repair whitelist" in reason
