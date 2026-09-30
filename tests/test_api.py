"""Integration tests for SynPassport FastAPI backend service (Step 6a).

Tests:
1. Replay mode full run: POST /runs -> GET /runs/{id} with candidates, repairs, budget, verdicts.
2. GET /runs/{id}/evidence: empirical evidence rows with CIs and thresholds.
3. GET /runs/{id}/events: SSE stream of agent execution steps.
4. POST /runs/{id}/approve: human approval flow, audit signatures, and re-signing.
5. GET /runs/{id}/passport: signed Evidence Passport JSON.
6. GET /runs/{id}/sufficiency: current N, required min N, projected CI width.
7. POST /verify:
   - verify pass with genuine synthetic data and passport
   - verify fail on tampered dataset (DATASET_HASH_MISMATCH)
   - verify fail on undeclared purpose (PURPOSE_UNKNOWN)
8. Mission validation error handling (422 Unprocessable Entity).
9. Size limit enforcement (413 Request Entity Too Large).
10. 404 for unknown run IDs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from synpassport.api.main import app
from synpassport.api.store import run_store


@pytest.fixture
def client() -> TestClient:
    """Provide FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_csv_bytes(tmp_path: Path) -> bytes:
    """Generate sample training dataset CSV bytes."""
    df = pd.DataFrame(
        {
            "age": [25, 45, 68, 72, 33, 58, 62, 77, 29, 51] * 5,
            "cholesterol": [
                180.0, 220.0, 240.0, 210.0, 195.0, 250.0, 230.0, 260.0, 190.0, 215.0
            ] * 5,
            "resting_bp": [120, 135, 145, 130, 118, 140, 138, 150, 122, 128] * 5,
            "target": [0, 1, 1, 1, 0, 1, 0, 1, 0, 0] * 5,
        }
    )
    csv_file = tmp_path / "sample_real.csv"
    df.to_csv(csv_file, index=False)
    return csv_file.read_bytes()


@pytest.fixture
def valid_mission_dict() -> dict[str, Any]:
    """Valid assurance mission specification."""
    return {
        "purpose": "software_testing",
        "intended_uses": ["software_testing"],
        "critical_subgroups": ["age >= 65"],
        "policy_id": "software-testing",
        "seed": 1234,
    }


def test_health_check(client: TestClient) -> None:
    """Verify health endpoint."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "synpassport"}


def test_malformed_mission_returns_422(
    client: TestClient,
    sample_csv_bytes: bytes,
) -> None:
    """Verify malformed mission YAML/JSON returns 422 Unprocessable Entity."""
    # 1. Empty mission
    resp1 = client.post(
        "/runs",
        files={"dataset": ("data.csv", sample_csv_bytes, "text/csv")},
        data={"mission": ""},
    )
    assert resp1.status_code == 422

    # 2. Syntax error YAML/JSON
    resp2 = client.post(
        "/runs",
        files={"dataset": ("data.csv", sample_csv_bytes, "text/csv")},
        data={"mission": "invalid: yaml: [broken"},
    )
    assert resp2.status_code == 422

    # 3. Missing required purpose field
    resp3 = client.post(
        "/runs",
        files={"dataset": ("data.csv", sample_csv_bytes, "text/csv")},
        data={"mission": json.dumps({"intended_uses": ["testing"]})},
    )
    assert resp3.status_code == 422


def test_upload_size_limit_returns_413(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    valid_mission_dict: dict[str, Any],
) -> None:
    """Verify upload exceeding MAX_UPLOAD_SIZE returns 413."""
    monkeypatch.setattr("synpassport.api.routers.runs.MAX_UPLOAD_SIZE", 50)
    oversized_bytes = b"age,target\n" + b"25,0\n" * 10

    resp = client.post(
        "/runs",
        files={"dataset": ("data.csv", oversized_bytes, "text/csv")},
        data={"mission": json.dumps(valid_mission_dict)},
    )
    assert resp.status_code == 413
    assert "exceeds maximum permitted limit" in resp.json()["detail"]


def test_full_run_in_replay_mode_and_lifecycle(
    client: TestClient,
    sample_csv_bytes: bytes,
    valid_mission_dict: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify complete run lifecycle under SYNPASSPORT_REPLAY=1."""
    monkeypatch.setenv("SYNPASSPORT_REPLAY", "1")

    # 1. POST /runs: schedule assurance run
    create_resp = client.post(
        "/runs",
        files={"dataset": ("train.csv", sample_csv_bytes, "text/csv")},
        data={"mission": json.dumps(valid_mission_dict)},
    )
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    run_id = created_data["run_id"]
    assert run_id.startswith("run_")

    # 2. GET /runs/{id}: retrieve execution status, candidates, budget
    status_resp = client.get(f"/runs/{run_id}")
    assert status_resp.status_code == 200
    run_info = status_resp.json()
    assert run_info["run_id"] == run_id
    assert run_info["status"] == "COMPLETED"
    assert len(run_info["candidates"]) >= 1
    assert "software_testing" in run_info["verdicts"]
    assert run_info["budget_used"]["candidates_evaluated"] >= 1

    # 3. GET /runs/{id}/evidence: inspect empirical measurements
    evidence_resp = client.get(f"/runs/{run_id}/evidence")
    assert evidence_resp.status_code == 200
    evidence_rows = evidence_resp.json()
    assert len(evidence_rows) >= 1
    check_ids = [row["check_id"] for row in evidence_rows]
    assert "schema_validity" in check_ids

    # 4. GET /runs/{id}/events: SSE event streaming
    events_resp = client.get(f"/runs/{run_id}/events")
    assert events_resp.status_code == 200
    assert "text/event-stream" in events_resp.headers["content-type"]
    sse_text = events_resp.text
    assert "data: " in sse_text
    assert "finalized" in sse_text or "status" in sse_text or "candidate" in sse_text

    # 5. GET /runs/{id}/sufficiency: verify sample size power metrics
    suff_resp = client.get(f"/runs/{run_id}/sufficiency")
    assert suff_resp.status_code == 200
    suff_data = suff_resp.json()
    assert suff_data["run_id"] == run_id
    assert suff_data["current_n"] > 0
    assert suff_data["required_min_n"] > 0
    assert len(suff_data["subgroups"]) >= 1

    # 6. GET /runs/{id}/passport: verify initial unapproved passport
    pass_resp = client.get(f"/runs/{run_id}/passport")
    assert pass_resp.status_code == 200
    passport_data = pass_resp.json()
    assert passport_data["human_approval"]["status"] == "PENDING"
    assert "signature" in passport_data

    # 7. POST /runs/{id}/approve: human approval flow
    approver_email = "auditor_lead@example.org"
    appr_resp = client.post(
        f"/runs/{run_id}/approve",
        json={"approver": approver_email},
    )
    assert appr_resp.status_code == 200
    appr_data = appr_resp.json()
    assert appr_data["status"] == "APPROVED"
    assert appr_data["approver"] == approver_email
    approved_passport = appr_data["passport"]
    assert approved_passport["human_approval"]["status"] == "APPROVED"
    assert approved_passport["human_approval"]["approver"] == approver_email
    assert len(approved_passport["audit_signatures"]) >= 1

    # 8. POST /verify: verify authentic dataset and approved passport
    run_record = run_store.get_run(run_id)
    assert run_record is not None
    # Locate candidate synthetic data CSV
    cand_csv_path = run_record.run_dir / "candidate_001.csv"
    assert cand_csv_path.is_file()
    cand_bytes = cand_csv_path.read_bytes()
    passport_str = json.dumps(approved_passport)

    verify_pass_resp = client.post(
        "/verify",
        files={
            "dataset": ("candidate_001.csv", cand_bytes, "text/csv"),
            "passport": ("passport.json", passport_str.encode("utf-8"), "application/json"),
        },
        data={"purpose": "software_testing", "allow_warning": "true"},
    )
    assert verify_pass_resp.status_code == 200
    v_pass_data = verify_pass_resp.json()
    assert v_pass_data["valid"] is True
    assert v_pass_data["reason_code"] == "OK"

    # 9. POST /verify: tamper dataset bytes -> fail with DATASET_HASH_MISMATCH
    tampered_bytes = cand_bytes + b"\n999,999,999,1\n"
    verify_tamper_resp = client.post(
        "/verify",
        files={
            "dataset": ("tampered.csv", tampered_bytes, "text/csv"),
            "passport": ("passport.json", passport_str.encode("utf-8"), "application/json"),
        },
        data={"purpose": "software_testing", "allow_warning": "true"},
    )
    assert verify_tamper_resp.status_code == 200
    v_tamper_data = verify_tamper_resp.json()
    assert v_tamper_data["valid"] is False
    assert v_tamper_data["reason_code"] == "DATASET_HASH_MISMATCH"

    # 10. POST /verify: undeclared purpose -> fail with PURPOSE_UNKNOWN
    verify_purpose_resp = client.post(
        "/verify",
        files={
            "dataset": ("candidate_001.csv", cand_bytes, "text/csv"),
            "passport": ("passport.json", passport_str.encode("utf-8"), "application/json"),
        },
        data={"purpose": "undeclared_clinical_ml", "allow_warning": "true"},
    )
    assert verify_purpose_resp.status_code == 200
    v_purp_data = verify_purpose_resp.json()
    assert v_purp_data["valid"] is False
    assert v_purp_data["reason_code"] == "PURPOSE_UNKNOWN"

    # 11. POST /verify: JSON payload verification
    verify_json_resp = client.post(
        "/verify",
        json={
            "dataset_path": str(cand_csv_path),
            "passport": approved_passport,
            "purpose": "software_testing",
            "allow_warning": True,
        },
    )
    assert verify_json_resp.status_code == 200
    assert verify_json_resp.json()["valid"] is True


def test_unknown_run_id_returns_404(client: TestClient) -> None:
    """Verify unknown run_id returns 404 for all run endpoints."""
    non_existent = "run_nonexistent_000"
    assert client.get(f"/runs/{non_existent}").status_code == 404
    assert client.get(f"/runs/{non_existent}/evidence").status_code == 404
    assert client.get(f"/runs/{non_existent}/events").status_code == 404
    assert client.get(f"/runs/{non_existent}/passport").status_code == 404
    assert client.get(f"/runs/{non_existent}/sufficiency").status_code == 404
    assert (
        client.post(f"/runs/{non_existent}/approve", json={"approver": "test"}).status_code == 404
    )
