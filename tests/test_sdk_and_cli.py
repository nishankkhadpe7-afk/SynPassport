"""Comprehensive unit and integration tests for Verify SDK, Guard, and CLI (Step 4).

Tests every verification reason code:
- OK
- SIGNATURE_INVALID
- DATASET_HASH_MISMATCH
- PURPOSE_UNSUPPORTED
- PURPOSE_UNKNOWN
- APPROVAL_MISSING
- PASSPORT_MALFORMED

Tests exit codes:
- 0: OK
- 1: Unsupported / tampered
- 2: Malformed / usage error

Tests loader guard load_dataset() raising PassportError.
Tests CLI subcommands: verify, issue, approve, inspect.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from synpassport.cli.main import main
from synpassport.passport.builder import approve_passport, build_passport
from synpassport.passport.keygen import generate_keypair
from synpassport.sdk.guard import PassportError, load_dataset
from synpassport.sdk.verify import verify


@pytest.fixture
def test_env(tmp_path: Path) -> dict[str, Any]:
    """Create test dataset, keypair, and baseline passports."""
    # Real & synthetic datasets
    df = pd.DataFrame(
        {
            "feat_a": [1.0, 2.0, 3.0, 4.0, 5.0] * 5,
            "feat_b": [10.0, 20.0, 30.0, 40.0, 50.0] * 5,
            "label": [0, 1, 0, 1, 0] * 5,
        }
    )
    data_csv = tmp_path / "synthetic_data.csv"
    df.to_csv(data_csv, index=False)

    # Keys
    keys_dir = tmp_path / "keys"
    priv_key, pub_key, key_id = generate_keypair(keys_dir, key_name="test_key")

    # Baseline passport data
    mission = {
        "purpose": "model training",
        "intended_uses": ["software_testing", "ml_prototyping", "clinical_ml"],
    }
    policy_spec = {
        "id": "software-testing",
        "human_approval": "optional",
        "requires": {"schema_validity": "pass"},
    }
    evidence = [{"check": "schema_validity", "state": "PASS", "value": 1.0}]
    verdicts = {
        "software_testing": "PASS",
        "ml_prototyping": "WARNING",
        "clinical_ml": "FAIL",
    }

    passport_obj = build_passport(
        dataset_path=data_csv,
        mission=mission,
        policy=policy_spec,
        evidence=evidence,
        verdicts=verdicts,
        signing_key=priv_key,
        key_id=key_id,
    )
    passport_file = tmp_path / "valid.passport.json"
    passport_file.write_text(passport_obj.to_json(indent=2), encoding="utf-8")

    return {
        "tmp_path": tmp_path,
        "data_csv": data_csv,
        "priv_key": priv_key,
        "pub_key": pub_key,
        "key_id": key_id,
        "passport_file": passport_file,
        "passport_obj": passport_obj,
    }


# =========================================================================
# Tests: Reason Codes
# =========================================================================


def test_reason_code_ok(test_env: dict[str, Any]) -> None:
    """Verify reason code OK on authentic dataset and PASS verdict."""
    res = verify(
        dataset_path=test_env["data_csv"],
        passport_path=test_env["passport_file"],
        purpose="software_testing",
        public_key=test_env["pub_key"],
    )
    assert res.valid is True
    assert res.reason_code == "OK"
    assert bool(res) is True


def test_reason_code_warning_handling(test_env: dict[str, Any]) -> None:
    """Verify WARNING requires allow_warning=True to yield OK, else PURPOSE_UNSUPPORTED."""
    # Without opt-in
    res_blocked = verify(
        dataset_path=test_env["data_csv"],
        passport_path=test_env["passport_file"],
        purpose="ml_prototyping",
        allow_warning=False,
        public_key=test_env["pub_key"],
    )
    assert res_blocked.valid is False
    assert res_blocked.reason_code == "PURPOSE_UNSUPPORTED"

    # With opt-in
    res_allowed = verify(
        dataset_path=test_env["data_csv"],
        passport_path=test_env["passport_file"],
        purpose="ml_prototyping",
        allow_warning=True,
        public_key=test_env["pub_key"],
    )
    assert res_allowed.valid is True
    assert res_allowed.reason_code == "OK"


def test_reason_code_signature_invalid(test_env: dict[str, Any]) -> None:
    """Verify reason code SIGNATURE_INVALID when passport content is tampered."""
    tampered_file = test_env["tmp_path"] / "tampered_sig.passport.json"
    content = json.loads(test_env["passport_file"].read_text(encoding="utf-8"))

    # Tamper mission purpose without re-signing
    content["mission"]["purpose"] = "malicious alteration"
    tampered_file.write_text(json.dumps(content), encoding="utf-8")

    res = verify(
        dataset_path=test_env["data_csv"],
        passport_path=tampered_file,
        purpose="software_testing",
        public_key=test_env["pub_key"],
    )
    assert res.valid is False
    assert res.reason_code == "SIGNATURE_INVALID"


def test_reason_code_dataset_hash_mismatch(test_env: dict[str, Any]) -> None:
    """Verify reason code DATASET_HASH_MISMATCH when dataset bytes are altered."""
    # Create corrupted dataset
    corrupt_csv = test_env["tmp_path"] / "tampered_dataset.csv"
    raw_bytes = test_env["data_csv"].read_bytes()
    # Flip first character
    corrupt_csv.write_bytes(b"Z" + raw_bytes[1:])

    res = verify(
        dataset_path=corrupt_csv,
        passport_path=test_env["passport_file"],
        purpose="software_testing",
        public_key=test_env["pub_key"],
    )
    assert res.valid is False
    assert res.reason_code == "DATASET_HASH_MISMATCH"


def test_reason_code_purpose_unsupported(test_env: dict[str, Any]) -> None:
    """Verify reason code PURPOSE_UNSUPPORTED on FAIL verdict."""
    res = verify(
        dataset_path=test_env["data_csv"],
        passport_path=test_env["passport_file"],
        purpose="clinical_ml",  # verdict is FAIL
        public_key=test_env["pub_key"],
    )
    assert res.valid is False
    assert res.reason_code == "PURPOSE_UNSUPPORTED"


def test_reason_code_purpose_unknown(test_env: dict[str, Any]) -> None:
    """Verify reason code PURPOSE_UNKNOWN when queried purpose is not declared."""
    res = verify(
        dataset_path=test_env["data_csv"],
        passport_path=test_env["passport_file"],
        purpose="non_existent_purpose_xyz",
        public_key=test_env["pub_key"],
    )
    assert res.valid is False
    assert res.reason_code == "PURPOSE_UNKNOWN"


def test_reason_code_approval_missing(test_env: dict[str, Any]) -> None:
    """Verify reason code APPROVAL_MISSING when required approval is PENDING."""
    appr_file = test_env["tmp_path"] / "approval_required.passport.json"

    # Build passport with ml-sensitive-v1 which requires human approval
    passport_obj = build_passport(
        dataset_path=test_env["data_csv"],
        mission={"purpose": "sensitive ml"},
        policy="ml-sensitive-v1",
        evidence=[],
        verdicts={"software_testing": "PASS"},
        signing_key=test_env["priv_key"],
        key_id=test_env["key_id"],
    )
    appr_file.write_text(passport_obj.to_json(indent=2), encoding="utf-8")

    # Before approval -> APPROVAL_MISSING
    res_before = verify(
        dataset_path=test_env["data_csv"],
        passport_path=appr_file,
        purpose="software_testing",
        public_key=test_env["pub_key"],
    )
    assert res_before.valid is False
    assert res_before.reason_code == "APPROVAL_MISSING"

    # After approval -> OK
    approve_passport(
        passport=passport_obj,
        approver="reviewer_auditor@example.org",
        signing_key=test_env["priv_key"],
        key_id=test_env["key_id"],
    )
    appr_file.write_text(passport_obj.to_json(indent=2), encoding="utf-8")

    res_after = verify(
        dataset_path=test_env["data_csv"],
        passport_path=appr_file,
        purpose="software_testing",
        public_key=test_env["pub_key"],
    )
    assert res_after.valid is True
    assert res_after.reason_code == "OK"


def test_reason_code_passport_malformed(test_env: dict[str, Any]) -> None:
    """Verify reason code PASSPORT_MALFORMED on missing file, corrupted JSON, or invalid schema."""
    # Non-existent file
    missing = test_env["tmp_path"] / "non_existent.passport.json"
    res_missing = verify(
        dataset_path=test_env["data_csv"],
        passport_path=missing,
        purpose="software_testing",
    )
    assert res_missing.valid is False
    assert res_missing.reason_code == "PASSPORT_MALFORMED"

    # Corrupt JSON
    corrupt_json = test_env["tmp_path"] / "corrupt.json"
    corrupt_json.write_text("{this is not valid json!}", encoding="utf-8")
    res_corrupt = verify(
        dataset_path=test_env["data_csv"],
        passport_path=corrupt_json,
        purpose="software_testing",
    )
    assert res_corrupt.valid is False
    assert res_corrupt.reason_code == "PASSPORT_MALFORMED"

    # Schema missing required block
    bad_schema = test_env["tmp_path"] / "bad_schema.json"
    bad_schema.write_text(json.dumps({"passport_version": "0.1.0"}), encoding="utf-8")
    res_schema = verify(
        dataset_path=test_env["data_csv"],
        passport_path=bad_schema,
        purpose="software_testing",
    )
    assert res_schema.valid is False
    assert res_schema.reason_code == "PASSPORT_MALFORMED"


# =========================================================================
# Tests: Loader Guard load_dataset()
# =========================================================================


def test_guard_load_dataset_success(test_env: dict[str, Any]) -> None:
    """Verify load_dataset returns DataFrame when assurance checks pass."""
    df = load_dataset(
        dataset_path=test_env["data_csv"],
        passport_path=test_env["passport_file"],
        purpose="software_testing",
        public_key=test_env["pub_key"],
    )
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 25
    assert "feat_a" in df.columns


def test_guard_raises_on_unsupported_purpose(test_env: dict[str, Any]) -> None:
    """Verify load_dataset raises PassportError with PURPOSE_UNSUPPORTED on rejected verdict."""
    with pytest.raises(PassportError) as exc_info:
        load_dataset(
            dataset_path=test_env["data_csv"],
            passport_path=test_env["passport_file"],
            purpose="clinical_ml",  # FAIL
            public_key=test_env["pub_key"],
        )
    assert exc_info.value.reason_code == "PURPOSE_UNSUPPORTED"


def test_guard_raises_on_tampered_dataset(test_env: dict[str, Any]) -> None:
    """Verify load_dataset raises PassportError with DATASET_HASH_MISMATCH on modified file."""
    corrupt_csv = test_env["tmp_path"] / "guard_tampered.csv"
    raw_bytes = test_env["data_csv"].read_bytes()
    corrupt_csv.write_bytes(b"A" + raw_bytes[1:])

    with pytest.raises(PassportError) as exc_info:
        load_dataset(
            dataset_path=corrupt_csv,
            passport_path=test_env["passport_file"],
            purpose="software_testing",
            public_key=test_env["pub_key"],
        )
    assert exc_info.value.reason_code == "DATASET_HASH_MISMATCH"


def test_guard_raises_on_missing_passport(test_env: dict[str, Any]) -> None:
    """Verify load_dataset raises PassportError when no passport can be located."""
    orphan_csv = test_env["tmp_path"] / "isolated_data.csv"
    orphan_csv.write_text("a,b\n1,2\n", encoding="utf-8")

    with pytest.raises(PassportError) as exc_info:
        load_dataset(
            dataset_path=orphan_csv,
            purpose="software_testing",
        )
    assert exc_info.value.reason_code == "PASSPORT_MALFORMED"


# =========================================================================
# Tests: CLI Commands & Exit Codes
# =========================================================================


def test_cli_verify_exit_code_0(
    test_env: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify CLI exit code 0 on valid passport verification."""
    code = main(
        [
            "verify",
            str(test_env["data_csv"]),
            str(test_env["passport_file"]),
            "--purpose",
            "software_testing",
            "--public-key",
            str(test_env["pub_key"]),
        ]
    )
    out, err = capsys.readouterr()
    assert code == 0
    assert "VERIFIED" in out


def test_cli_verify_exit_code_1_unsupported(
    test_env: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify CLI exit code 1 on unsupported purpose."""
    code = main(
        [
            "verify",
            str(test_env["data_csv"]),
            str(test_env["passport_file"]),
            "--purpose",
            "clinical_ml",  # FAIL
            "--public-key",
            str(test_env["pub_key"]),
        ]
    )
    assert code == 1


def test_cli_verify_exit_code_2_malformed(
    test_env: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify CLI exit code 2 on missing or malformed passport file."""
    code = main(
        [
            "verify",
            str(test_env["data_csv"]),
            str(test_env["tmp_path"] / "ghost.json"),
            "--purpose",
            "software_testing",
        ]
    )
    assert code == 2


def test_cli_verify_json_output(
    test_env: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify CLI --json outputs valid JSON with reason_code."""
    code = main(
        [
            "verify",
            str(test_env["data_csv"]),
            str(test_env["passport_file"]),
            "--purpose",
            "software_testing",
            "--public-key",
            str(test_env["pub_key"]),
            "--json",
        ]
    )
    out, _ = capsys.readouterr()
    assert code == 0
    data = json.loads(out)
    assert data["valid"] is True
    assert data["reason_code"] == "OK"


def test_cli_inspect_command(test_env: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI inspect command prints passport summary."""
    code = main(["inspect", str(test_env["passport_file"])])
    out, _ = capsys.readouterr()
    assert code == 0
    assert "Evidence Passport" in out
    assert "software_testing" in out


def test_cli_approve_command(test_env: dict[str, Any], capsys: pytest.CaptureFixture[str]) -> None:
    """Verify CLI approve command re-signs passport with approval status."""
    approved_out = test_env["tmp_path"] / "cli_approved.passport.json"
    code = main(
        [
            "approve",
            str(test_env["passport_file"]),
            "--approver",
            "auditor_chief@example.org",
            "--key",
            str(test_env["priv_key"]),
            "--output",
            str(approved_out),
        ]
    )
    assert code == 0
    data = json.loads(approved_out.read_text(encoding="utf-8"))
    assert data["human_approval"]["status"] == "APPROVED"
    assert data["human_approval"]["approver"] == "auditor_chief@example.org"
    assert len(data["audit_signatures"]) == 1
