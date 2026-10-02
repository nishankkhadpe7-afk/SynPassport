"""Regression tests for verification, policy and API issues found in code review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from synpassport.agent.llm import MockLLM
from synpassport.agent.loop import AssuranceAgentLoop
from synpassport.agent.repairs import validate_repair_action
from synpassport.api.main import app
from synpassport.api.store import get_or_create_server_key, run_store
from synpassport.cli.main import main
from synpassport.generators.sdv_wrapper import CTGANGenerator
from synpassport.passport.builder import approve_passport, build_passport
from synpassport.passport.canonical import canonical_json_dumps
from synpassport.passport.keygen import generate_keypair
from synpassport.policy.engine import evaluate_check
from synpassport.sdk.verify import verify


@pytest.fixture
def signed(tmp_path: Path) -> dict[str, Any]:
    """A dataset, issuer keypair and signed passport with float evidence values."""
    data = tmp_path / "synth.csv"
    pd.DataFrame({"a": [1.5, 2.25, 3.0] * 4, "y": [0, 1, 0] * 4}).to_csv(data, index=False)
    priv, pub, _ = generate_keypair(tmp_path / "issuer", "issuer")
    passport = build_passport(
        dataset_path=data,
        mission={"purpose": "software_testing"},
        policy="software-testing",
        evidence=[
            {"check_id": "schema_validity", "value": 1.0, "state": "PASS"},
            {"check_id": "marginal_fidelity", "value": 0.918456123, "state": "PASS"},
        ],
        verdicts={"software_testing": "PASS", "clinical_ml": "PASS"},
        signing_key=priv,
    )
    passport_file = tmp_path / "passport.json"
    passport_file.write_text(passport.to_json(), encoding="utf-8")
    return {"data": data, "priv": priv, "pub": pub, "passport_file": passport_file}


# --- Signature trust -------------------------------------------------------------------


def test_key_next_to_passport_is_not_trusted(signed: dict[str, Any], tmp_path: Path) -> None:
    """An attacker-supplied key beside a forged passport must not make it verify."""
    evil_dir = tmp_path / "evil"
    attacker_priv, _, _ = generate_keypair(evil_dir, "ed25519")  # writes ed25519_public.pem
    forged = build_passport(
        dataset_path=signed["data"],
        mission={"purpose": "x"},
        policy="ml-sensitive-v1",
        evidence=[],
        verdicts={"clinical_ml": "PASS"},
        signing_key=attacker_priv,
    ).to_dict()
    forged = approve_passport(forged, "ceo@example.com", attacker_priv)
    forged_file = evil_dir / "passport.json"
    forged_file.write_text(json.dumps(forged), encoding="utf-8")

    no_key = verify(signed["data"], forged_file, "clinical_ml")
    assert no_key.valid is False
    assert no_key.reason_code == "SIGNATURE_INVALID"

    real_key = verify(signed["data"], forged_file, "clinical_ml", public_key=signed["pub"])
    assert real_key.valid is False


def test_env_var_supplies_trusted_key(
    signed: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SYNPASSPORT_PUBLIC_KEY", str(signed["pub"]))
    assert verify(signed["data"], signed["passport_file"], "software_testing").valid is True


def test_passport_survives_javascript_style_round_trip(
    signed: dict[str, Any], tmp_path: Path
) -> None:
    """JSON.stringify turns 1.0 into 1; the signature must still verify."""
    data = json.loads(signed["passport_file"].read_text(encoding="utf-8"))

    def js_like(obj: Any) -> Any:
        if isinstance(obj, float) and obj.is_integer():
            return int(obj)
        if isinstance(obj, dict):
            return {k: js_like(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [js_like(v) for v in obj]
        return obj

    round_tripped = tmp_path / "rt.json"
    round_tripped.write_text(json.dumps(js_like(data)), encoding="utf-8")
    res = verify(signed["data"], round_tripped, "software_testing", public_key=signed["pub"])
    assert res.valid is True, res.details
    assert canonical_json_dumps({"v": 1.0}) == canonical_json_dumps({"v": 1})


def test_unsigned_float_precision_is_rejected(signed: dict[str, Any], tmp_path: Path) -> None:
    """Edits hidden below the 6-decimal canonical precision must not keep a valid signature."""
    data = json.loads(signed["passport_file"].read_text(encoding="utf-8"))
    stored = data["evidence"][1]["value"]
    assert stored == round(stored, 6)  # builder stores exactly what it signs
    data["evidence"][1]["value"] = stored + 4e-7
    tweaked = tmp_path / "tweaked.json"
    tweaked.write_text(json.dumps(data), encoding="utf-8")
    res = verify(signed["data"], tweaked, "software_testing", public_key=signed["pub"])
    assert res.valid is False
    assert res.reason_code == "SIGNATURE_INVALID"


# --- CLI ------------------------------------------------------------------------------


def test_cli_verify_without_key_does_not_crash(signed: dict[str, Any]) -> None:
    code = main(["verify", str(signed["data"]), str(signed["passport_file"]), "--purpose", "x"])
    assert code == 1  # SIGNATURE_INVALID: no trusted key, but no AttributeError


def test_cli_issue_requires_key(signed: dict[str, Any], tmp_path: Path) -> None:
    out = tmp_path / "issued.json"
    args = ["issue", "--data", str(signed["data"]), "--synth", str(signed["data"])]
    args += ["--policy", "software-testing", "-o", str(out)]
    assert main(args) == 2
    assert not out.exists()


# --- Policy engine ---------------------------------------------------------------------


def test_ci_width_requirement_uses_interval_width() -> None:
    """A narrow CI around a ~1.0 utility ratio satisfies max CI width 0.15."""
    res = evaluate_check(
        check_id="subgroup_utility_ci_width",
        threshold_spec={"max": 0.15},
        warning_band_spec=None,
        evidence_record={
            "check_id": "subgroup_utility_ci_width",
            "value": 1.0,
            "ci_low": 0.977,
            "ci_high": 1.018,
        },
    )
    assert res.state.value == "PASS"
    assert res.value == pytest.approx(0.041)


def test_errored_check_is_never_pass() -> None:
    """Errors carried in metadata (as the pipeline stores them) block PASS."""
    res = evaluate_check(
        check_id="subgroup_utility_ci_width",
        threshold_spec={"max": 0.15},
        warning_band_spec=None,
        evidence_record={
            "check_id": "subgroup_utility_ci_width",
            "value": 0.0,
            "state": "INSUFFICIENT_EVIDENCE",
            "metadata": {"error": "Subgroup utility evaluation error: boom"},
        },
    )
    assert res.state.value == "INSUFFICIENT_EVIDENCE"


def test_agent_evaluates_mission_subgroup(tmp_path: Path) -> None:
    """The mission's critical subgroup (not a hardcoded 'age >= 65') is evaluated."""
    df = pd.DataFrame(
        {"age": list(range(20, 80)) * 4, "bp": list(range(100, 160)) * 4, "y": [0, 1] * 120}
    )
    real = tmp_path / "real.csv"
    df.to_csv(real, index=False)
    result = AssuranceAgentLoop(llm_client=MockLLM(), cache_dir=tmp_path / "replay").run(
        real_data_path=real,
        mission={"purpose": "clinical_ml", "critical_subgroups": ["bp >= 150"]},
        policy_id_or_path="ml-sensitive-v1",
        output_dir=tmp_path / "run",
        target_col="y",
    )
    sub = next(
        e for e in result["passport"]["evidence"] if e["check_id"] == "subgroup_utility_ci_width"
    )
    assert sub["metadata"].get("subgroup_query") == "bp >= 150"


# --- Agent repairs / generators ---------------------------------------------------------


def test_repair_params_are_validated() -> None:
    assert validate_repair_action("tune_hyperparameters", {"epochs": "abc"})[0] is False
    assert validate_repair_action("tune_hyperparameters", {"epochs": 10**9})[0] is False
    assert validate_repair_action("tune_hyperparameters", {"lr": 0.1})[0] is False
    assert validate_repair_action("tune_hyperparameters", {"epochs": 50})[0] is True
    assert validate_repair_action("enable_dp_training", {})[0] is False


def test_ctgan_fallback_is_recorded(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "ctgan":
            raise ImportError("ctgan not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    gen = CTGANGenerator(epochs=1, seed=1)
    gen.fit(pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": ["x", "y", "x", "y"]}))
    assert gen.backend == "GaussianCopula"
    assert gen.fallback_reason and "CTGAN unavailable" in gen.fallback_reason


# --- API ---------------------------------------------------------------------------------


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _server_signed_run(run_id: str, verdicts: dict[str, str]) -> Path:
    """Create a run directory whose passport binds candidate_001 while a newer
    candidate_002 also exists."""
    from synpassport.api.routers import verify as verify_router

    run_dir = verify_router.RUNS_DIR / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "candidate_001.csv").write_text("a,y\n1,0\n2,1\n", encoding="utf-8")
    (run_dir / "candidate_002.csv").write_text("a,y\n9,9\n", encoding="utf-8")
    key, _ = get_or_create_server_key()
    passport = build_passport(
        dataset_path=run_dir / "candidate_001.csv",
        mission={"purpose": "software_testing"},
        policy="software-testing",
        evidence=[],
        verdicts=verdicts,
        signing_key=key,
    )
    (run_dir / "passport.json").write_text(passport.to_json(), encoding="utf-8")
    run_store.create_run(run_id, run_dir / "dataset.csv", {"purpose": "x"}, run_dir)
    record = run_store.get_run(run_id)
    assert record is not None
    record.status = "COMPLETED"
    record.passport = passport.to_dict()
    return run_dir


def test_verify_by_run_id_uses_bound_candidate(client: TestClient) -> None:
    _server_signed_run("run_aaaaaaaaaaaa", {"software_testing": "PASS"})
    resp = client.post(
        "/verify", json={"run_id": "run_aaaaaaaaaaaa", "purpose": "software_testing"}
    )
    assert resp.status_code == 200
    assert resp.json()["reason_code"] == "OK", resp.json()


def test_verify_rejects_paths_outside_runs(client: TestClient) -> None:
    traversal = client.post(
        "/verify", json={"run_id": "../../etc", "purpose": "x", "dataset_content": "a"}
    )
    assert traversal.status_code == 422
    outside = client.post(
        "/verify",
        json={"dataset_path": "/etc/hostname", "passport": {}, "purpose": "x"},
    )
    assert outside.status_code == 422


def test_verify_cleans_up_staging(client: TestClient) -> None:
    from synpassport.api.routers import verify as verify_router

    client.post(
        "/verify",
        files={"dataset": ("d.csv", b"a\n1\n"), "passport": ("p.json", b"{}")},
        data={"purpose": "x"},
    )
    staging = verify_router.RUNS_DIR / "staging"
    assert not staging.exists() or not any(staging.iterdir())


def test_approve_twice_and_token(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    _server_signed_run("run_bbbbbbbbbbbb", {"software_testing": "PASS"})
    monkeypatch.setattr("synpassport.api.routers.runs.APPROVER_TOKEN", "s3cret")
    url = "/runs/run_bbbbbbbbbbbb/approve"
    assert client.post(url, json={"approver": "a"}).status_code == 401
    bad = client.post(url, json={"approver": "a"}, headers={"X-Approver-Token": "nope"})
    assert bad.status_code == 401
    ok = client.post(url, json={"approver": "a"}, headers={"X-Approver-Token": "s3cret"})
    assert ok.status_code == 200
    again = client.post(url, json={"approver": "b"}, headers={"X-Approver-Token": "s3cret"})
    assert again.status_code == 409


def test_cannot_approve_all_failed_passport(client: TestClient) -> None:
    _server_signed_run("run_cccccccccccc", {"software_testing": "FAIL"})
    resp = client.post("/runs/run_cccccccccccc/approve", json={"approver": "a"})
    assert resp.status_code == 400


def test_mission_policy_id_must_be_profile_name(client: TestClient) -> None:
    from synpassport.api.routers import runs as runs_router

    before = set(runs_router.RUNS_DIR.glob("run_*")) if runs_router.RUNS_DIR.exists() else set()
    resp = client.post(
        "/runs",
        files={"dataset": ("d.csv", b"a,y\n1,0\n2,1\n")},
        data={"mission": json.dumps({"purpose": "x", "policy_id": "../../etc/passwd"})},
    )
    assert resp.status_code == 422
    after = set(runs_router.RUNS_DIR.glob("run_*")) if runs_router.RUNS_DIR.exists() else set()
    assert after == before


def test_dataset_endpoint_round_trip_verifies(client: TestClient) -> None:
    """The bound dataset served by the API verifies untouched and fails with one changed byte."""
    _server_signed_run("run_dddddddddddd", {"software_testing": "PASS"})
    resp = client.get("/runs/run_dddddddddddd/dataset")
    assert resp.status_code == 200
    content = resp.text

    passport = client.get("/runs/run_dddddddddddd/passport").json()
    ok = client.post(
        "/verify",
        json={"passport": passport, "dataset_content": content, "purpose": "software_testing"},
    ).json()
    assert ok["reason_code"] == "OK", ok

    tampered = content.replace("1,0", "1.1,0", 1)
    bad = client.post(
        "/verify",
        json={"passport": passport, "dataset_content": tampered, "purpose": "software_testing"},
    ).json()
    assert bad["reason_code"] == "DATASET_HASH_MISMATCH"


def test_dataset_endpoint_unknown_run(client: TestClient) -> None:
    assert client.get("/runs/run_000000000000/dataset").status_code == 404


# --- Agent decision maker ------------------------------------------------------------


def test_no_llm_key_uses_rule_based_planner(monkeypatch):
    from synpassport.agent.llm import RuleBasedPlanner, create_llm_client

    for name in ("LLM_API_KEY", "GROQ_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    assert isinstance(create_llm_client(), RuleBasedPlanner)


def test_rule_based_planner_proposes_whitelisted_repairs():
    from synpassport.agent.llm import RuleBasedPlanner
    from synpassport.agent.repairs import validate_repair_action

    first = RuleBasedPlanner.decide("GaussianCopula", {})
    second = RuleBasedPlanner.decide("CTGAN", {"epochs": 50})
    for decision in (first, second):
        assert decision["action"] == "propose_repair"
        ok, _ = validate_repair_action(decision["args"]["action"], decision["args"]["params"])
        assert ok
    assert first["args"]["action"] == "switch_generator"
    assert second["args"]["params"] == {"epochs": 100}


def test_llm_failure_falls_back_instead_of_failing_run():
    from synpassport.agent.llm import BaseLLMClient
    from synpassport.agent.loop import AssuranceAgentLoop

    class BrokenLLM(BaseLLMClient):
        def generate(self, prompt, system_prompt=None):
            raise ConnectionError("rate limited")

    events: list[tuple[str, dict]] = []
    loop = AssuranceAgentLoop(
        llm_client=BrokenLLM(), event_listener=lambda t, d: events.append((t, d))
    )
    ok_text = "\n".join(
        ["id,code"] + [f"ID-{i:05d},{i % 3}" for i in range(400)]
    )
    data = Path("ids.csv")
    data.write_text(ok_text + "\n")
    loop.run(
        real_data_path=data,
        mission={"purpose": "software_testing"},
        policy_id_or_path="software-testing",
    )
    assert loop.repairs_attempted >= 1
    assert any(d.get("phase") == "fallback" for t, d in events if t == "step")


def test_env_file_loads_without_python_dotenv(tmp_path, monkeypatch):
    from synpassport.api.config import _load_env_file

    env = tmp_path / ".env"
    env.write_bytes(b"LLM_API_KEY=gsk_test123\r\nLLM_MODEL='m'\r\n# c\r\nX=1 # note\r\n")
    for k in ("LLM_API_KEY", "LLM_MODEL", "X"):
        monkeypatch.delenv(k, raising=False)
    _load_env_file(env)
    import os

    assert os.environ["LLM_API_KEY"] == "gsk_test123"
    assert os.environ["LLM_MODEL"] == "m"
    assert os.environ["X"] == "1"


def test_repair_step_retries_when_llm_picks_a_non_repair_tool():
    from synpassport.agent.llm import MockLLM, query_llm_structured

    llm = MockLLM(
        responses=[
            {"thought_summary": "x", "action": "run_check", "args": {"check_id": "a"}},
            {
                "thought_summary": "y",
                "action": "propose_repair",
                "args": {"action": "switch_generator", "params": {"target_generator": "CTGAN"}},
            },
        ]
    )
    decision, errors = query_llm_structured(
        client=llm, prompt="p", system_prompt="s", allowed_actions={"propose_repair", "finalize"}
    )
    assert decision is not None and decision["action"] == "propose_repair"
    assert any("not permitted in this step" in e for e in errors)


def test_switch_generator_rejects_unsupported_and_accepts_aliases():
    from synpassport.agent.repairs import normalize_target_generator, validate_repair_action

    assert not validate_repair_action("switch_generator", {"generator_name": "TVAE"})[0]
    assert not validate_repair_action("switch_generator", {})[0]
    assert not validate_repair_action("switch_generator", {"target_generator": "CTGAN", "x": 1})[0]
    ok, _ = validate_repair_action("switch_generator", {"generator_name": "CTGAN"})
    assert ok
    assert normalize_target_generator({"generator_name": "CTGAN"}) == "CTGAN"


def test_invalid_llm_repair_is_replaced_by_rule_based_repair():
    from synpassport.agent.llm import MockLLM
    from synpassport.agent.loop import AssuranceAgentLoop

    llm = MockLLM(
        responses=[
            {
                "thought_summary": "try TVAE",
                "action": "propose_repair",
                "args": {"action": "switch_generator", "params": {"generator_name": "TVAE"}},
            }
        ]
    )
    loop = AssuranceAgentLoop(llm_client=llm)
    data = Path("ids2.csv")
    data.write_text("\n".join(["id,code"] + [f"ID-{i:05d},{i % 3}" for i in range(400)]) + "\n")
    loop.run(
        real_data_path=data,
        mission={"purpose": "software_testing"},
        policy_id_or_path="software-testing",
    )
    # The ID column leaks, so the rule-based replacement is to regenerate identifiers.
    assert loop.repairs_log[0]["action"] == "regenerate_identifiers"
    assert any("TVAE" in r["reason"] or "TVAE" in r["proposal"] for r in loop.agent_rejections)


def test_schema_check_rejects_negative_values_in_non_negative_column():
    from synpassport.checks.schema import SchemaValidityCheck

    real = pd.DataFrame({"amount": [1.0, 5.0, 300.0, 20.0, 7.5] * 20})
    synth = real.copy()
    synth.loc[0, "amount"] = -5.0
    result = SchemaValidityCheck().run(real, synth)
    assert result.value < 1.0


def test_identifier_leak_is_detected_and_repaired(tmp_path):
    from synpassport.agent.llm import RuleBasedPlanner
    from synpassport.agent.loop import AssuranceAgentLoop

    rows = ["txn_id,amount,kind"] + [
        f"TXN-{i:06X},{(i * 37) % 500 + 1.5},{'abc'[i % 3]}" for i in range(600)
    ]
    data = Path("txns.csv")
    data.write_text("\n".join(rows) + "\n")
    loop = AssuranceAgentLoop(llm_client=RuleBasedPlanner())
    result = loop.run(
        real_data_path=data,
        mission={"purpose": "software_testing"},
        policy_id_or_path="software-testing",
    )
    by_id = {c["candidate_id"]: c for c in result["candidates"]}
    assert by_id["candidate_001"]["check_states"]["identifier_leakage"] == "FAIL"
    assert by_id["candidate_002"]["check_states"]["identifier_leakage"] == "PASS"
    assert loop.repairs_log[0]["action"] == "regenerate_identifiers"
    assert result["verdicts"]["software_testing"] == "PASS"


def test_fresh_identifiers_keep_format_and_never_copy():
    import numpy as np

    from synpassport.checks.identifiers import fresh_identifiers, identifier_format_mask

    real = pd.Series([f"TXN-{i:08X}" for i in range(0, 5000, 7)])
    fresh = fresh_identifiers(real, 300, np.random.default_rng(1))
    assert fresh.is_unique
    assert not fresh.isin(set(real)).any()
    assert fresh.str.startswith("TXN-").all()
    assert identifier_format_mask(real, fresh).all()
    ips = pd.Series([f"10.{i % 250}.{i % 7}.{i % 200 + 1}" for i in range(300)])
    assert identifier_format_mask(ips, fresh_identifiers(ips, 50, np.random.default_rng(2))).all()


def test_policy_endpoint_hash_matches_passport_and_dcr_endpoint(tmp_path):
    import time

    from fastapi.testclient import TestClient

    from synpassport.api.main import app

    client = TestClient(app)
    pol = client.get("/policies/software-testing").json()
    assert "identifier_leakage" in pol["uses"]["software_testing"]
    assert client.get("/policies/..%2Fetc").status_code in (400, 404)

    rows = ["age,amount,kind"] + [
        f"{20 + i % 60},{(i * 13) % 300 + 0.5},{'xy'[i % 2]}" for i in range(300)
    ]
    mission = {"purpose": "software_testing", "policy_id": "software-testing", "seed": 1234}
    run_id = client.post(
        "/runs",
        files={"dataset": ("d.csv", ("\n".join(rows) + "\n").encode(), "text/csv")},
        data={"mission": json.dumps(mission)},
    ).json()["run_id"]
    for _ in range(100):
        state = client.get(f"/runs/{run_id}").json()
        if state["status"] in ("COMPLETED", "FAILED"):
            break
        time.sleep(0.2)
    assert state["status"] == "COMPLETED"
    assert state["best_candidate_id"]
    passport = client.get(f"/runs/{run_id}/passport").json()
    assert passport["policy"]["sha256"] == pol["sha256"]
    dcr = client.get(f"/runs/{run_id}/dcr").json()
    assert len(dcr["bins"]) == 12
    assert sum(b["to_training"] for b in dcr["bins"]) == dcr["sample_size"]
