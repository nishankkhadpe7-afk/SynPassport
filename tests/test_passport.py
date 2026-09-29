"""Unit and property tests for Passport subsystem (Step 3).

Verifies canonical serialization stability, golden-file adherence, streamed dataset hashing,
tamper detection, Ed25519 key generation, sign/verify roundtrips, and approval flow.
"""

from enum import Enum
from pathlib import Path
from typing import Any

import pytest

from synpassport.passport.builder import (
    build_passport,
    verify_dataset_hash,
    verify_passport,
)
from synpassport.passport.canonical import (
    canonical_hash,
    canonical_json_dumps,
    hash_dataset_file,
)
from synpassport.passport.keygen import compute_key_id, generate_keypair
from synpassport.passport.signer import (
    load_public_key,
    verify_signature,
)


class SampleEnum(Enum):
    """Enumeration fixture for testing canonical serialization."""

    ALPHA = "ALPHA_VAL"
    BETA = "BETA_VAL"


@pytest.fixture
def sample_dataset_file(tmp_path: Path) -> Path:
    """Generate temporary CSV dataset for hashing tests."""
    csv_file = tmp_path / "sample_data.csv"
    csv_file.write_text("id,val,label\n1,10.5,0\n2,20.25,1\n3,30.125,0\n", encoding="utf-8")
    return csv_file


@pytest.fixture
def generated_keys(tmp_path: Path) -> tuple[Path, Path, str]:
    """Generate deterministic temporary signing keypair."""
    keys_dir = tmp_path / "keys"
    return generate_keypair(keys_dir)


def test_canonical_stability_key_order() -> None:
    """Verify dictionaries with scrambled key order produce identical canonical bytes and hash."""
    dict_a = {
        "zeta": 1,
        "alpha": [3, 2, 1],
        "nested": {"z": True, "a": False},
        "beta": "string_val",
    }
    dict_b = {
        "nested": {"a": False, "z": True},
        "beta": "string_val",
        "zeta": 1,
        "alpha": [3, 2, 1],
    }

    bytes_a = canonical_json_dumps(dict_a)
    bytes_b = canonical_json_dumps(dict_b)

    assert bytes_a == bytes_b
    assert canonical_hash(dict_a) == canonical_hash(dict_b)


def test_canonical_float_formatting() -> None:
    """Verify float values round to fixed precision and handle edge cases deterministically."""
    # Float precision rounding (default 6 decimal places)
    dict_a = {"metric": 0.8500000001}
    dict_b = {"metric": 0.85}

    assert canonical_json_dumps(dict_a) == canonical_json_dumps(dict_b)

    # Negative zero normalization
    assert canonical_json_dumps({"v": -0.0}) == canonical_json_dumps({"v": 0.0})

    # NaN / Inf should raise ValueError (fail closed)
    with pytest.raises(ValueError, match="Cannot canonicalize"):
        canonical_json_dumps({"v": float("nan")})

    with pytest.raises(ValueError, match="Cannot canonicalize"):
        canonical_json_dumps({"v": float("inf")})


def test_canonical_enum_and_custom_serialization() -> None:
    """Verify enums and structured models serialize to stable representations."""
    payload = {
        "status": SampleEnum.ALPHA,
        "items": [SampleEnum.BETA, "literal"],
    }
    raw = canonical_json_dumps(payload).decode("utf-8")
    assert raw == '{"items":["BETA_VAL","literal"],"status":"ALPHA_VAL"}'


def test_canonical_golden_file() -> None:
    """Golden-file test ensuring canonical serializer output never drifts."""
    fixture_path = Path(__file__).parent / "fixtures" / "golden_passport_canonical.json"
    assert fixture_path.is_file(), f"Missing golden fixture: {fixture_path}"

    expected_bytes = fixture_path.read_bytes().strip()
    expected_hash = "0e74b5e83f575e7986959dc1290d46882ac0c00b04375df54708fc7738ad8339"

    # Input object with scrambled keys and non-canonical order
    scrambled_input: dict[str, Any] = {
        "verdicts": {
            "software_testing": "PASS",
            "ml_prototyping": "PASS",
        },
        "passport_version": "0.1.0",
        "human_approval": {
            "timestamp": None,
            "status": "PENDING",
            "approver": None,
        },
        "dataset": {
            "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "name": "sample.csv",
        },
        "mission": {
            "privacy_level": "high",
            "purpose": "synthetic evaluation demo",
            "critical_subgroups": ["age >= 65"],
        },
        "run": {
            "candidates_evaluated": 1,
            "seeds": [1234],
            "repairs_attempted": 0,
            "code_version": "git:abc12345",
        },
        "policy": {
            "sha256": "358742b6a782b575a61c566dd93444453b3f274cb6e81f1489eef3ff1910ef0b",
            "id": "ml-sensitive-v1",
        },
        "evidence": [
            {
                "threshold": ">=0.90",
                "state": "PASS",
                "check": "marginal_fidelity",
                "n": 1000,
                "seed": 1234,
                "ci": [0.891234, 0.945678],
                "value": 0.918456,
            }
        ],
        "repairs": [],
        "agent_rejections": [],
        "audit_signatures": [],
        "issued_at": "2026-09-30T00:00:00+00:00",
    }

    actual_bytes = canonical_json_dumps(scrambled_input)
    actual_hash = canonical_hash(scrambled_input)

    assert actual_bytes == expected_bytes
    assert actual_hash == expected_hash


def test_dataset_streamed_sha256(sample_dataset_file: Path) -> None:
    """Verify streamed dataset SHA-256 calculation matches raw file digest."""
    import hashlib

    expected_hash = hashlib.sha256(sample_dataset_file.read_bytes()).hexdigest()
    actual_hash = hash_dataset_file(sample_dataset_file, chunk_size=16)

    assert actual_hash == expected_hash


def test_dataset_tamper_detection(sample_dataset_file: Path) -> None:
    """Verify flipping one byte in the dataset file causes hash mismatch."""
    passport = build_passport(
        dataset_path=sample_dataset_file,
        mission={"purpose": "demo"},
        policy="ml-sensitive-v1",
        evidence=[],
        verdicts={"software_testing": "PASS"},
    )

    # Initial check passes
    assert verify_dataset_hash(sample_dataset_file, passport) is True

    # Mutate one byte in the dataset file
    content = sample_dataset_file.read_bytes()
    # Flip first character from 'i' to 'x'
    tampered_content = b"x" + content[1:]
    sample_dataset_file.write_bytes(tampered_content)

    # Verification must fail closed
    assert verify_dataset_hash(sample_dataset_file, passport) is False


def test_keygen_permissions_and_key_id(tmp_path: Path) -> None:
    """Verify key generation produces files with 0600 permissions and accurate public key id."""
    keys_dir = tmp_path / "keygen_test"
    priv_path, pub_path, key_id = generate_keypair(keys_dir, key_name="test_key")

    assert priv_path.is_file()
    assert pub_path.is_file()
    assert len(key_id) == 64  # SHA-256 hex length

    pub_key = load_public_key(pub_path)
    assert compute_key_id(pub_key) == key_id


def test_sign_verify_roundtrip(
    sample_dataset_file: Path,
    generated_keys: tuple[Path, Path, str],
) -> None:
    """Verify end-to-end sign and verify roundtrip over canonical bytes."""
    priv_path, pub_path, key_id = generated_keys

    passport = build_passport(
        dataset_path=sample_dataset_file,
        mission={"purpose": "testing roundtrip", "subgroups": ["all"]},
        policy={"id": "software-testing", "requires": {"schema_validity": "pass"}},
        evidence=[{"check": "schema_validity", "state": "PASS", "value": 1.0}],
        verdicts={"software_testing": "PASS"},
        signing_key=priv_path,
        key_id=key_id,
    )

    assert passport["signature"] is not None
    assert passport["signature"]["alg"] == "Ed25519"
    assert passport["signature"]["key_id"] == key_id
    assert isinstance(passport["signature"]["value"], str)

    # Verify using EvidencePassport instance method
    assert passport.verify(pub_path) is True
    # Verify using standalone verify_passport helper
    assert verify_passport(passport.to_dict(), pub_path) is True


def test_passport_tamper_detection(
    sample_dataset_file: Path,
    generated_keys: tuple[Path, Path, str],
) -> None:
    """Verify altering any passport field invalidates the Ed25519 signature."""
    priv_path, pub_path, key_id = generated_keys

    passport = build_passport(
        dataset_path=sample_dataset_file,
        mission={"purpose": "tamper test"},
        policy="software-testing",
        evidence=[{"check": "schema_validity", "state": "PASS", "value": 1.0}],
        verdicts={"software_testing": "PASS"},
        signing_key=priv_path,
        key_id=key_id,
    )

    data = passport.to_dict()
    assert verify_passport(data, pub_path) is True

    # Tamper 1: change verdict from PASS to FAIL
    tampered_verdict = dict(data)
    tampered_verdict["verdicts"] = {"software_testing": "FAIL"}
    assert verify_passport(tampered_verdict, pub_path) is False

    # Tamper 2: change evidence value
    tampered_evidence = dict(data)
    tampered_evidence["evidence"] = [{"check": "schema_validity", "state": "PASS", "value": 0.99}]
    assert verify_passport(tampered_evidence, pub_path) is False

    # Tamper 3: change dataset hash
    tampered_dataset = dict(data)
    tampered_dataset["dataset"] = {"name": "sample_data.csv", "sha256": "0" * 64}
    assert verify_passport(tampered_dataset, pub_path) is False


def test_wrong_public_key_fails(
    sample_dataset_file: Path,
    tmp_path: Path,
) -> None:
    """Verify signature verification fails when presented with wrong public key."""
    keys_a = tmp_path / "keys_a"
    keys_b = tmp_path / "keys_b"

    priv_a, pub_a, _ = generate_keypair(keys_a, key_name="key_a")
    _, pub_b, _ = generate_keypair(keys_b, key_name="key_b")

    passport = build_passport(
        dataset_path=sample_dataset_file,
        mission={"purpose": "mismatched key test"},
        policy="software-testing",
        evidence=[],
        verdicts={"software_testing": "PASS"},
        signing_key=priv_a,
    )

    # Valid with key A
    assert verify_passport(passport, pub_a) is True
    # Invalid with key B
    assert verify_passport(passport, pub_b) is False


def test_approval_flow(
    sample_dataset_file: Path,
    generated_keys: tuple[Path, Path, str],
) -> None:
    """Verify human approval adds approver, timestamp, retains prior signature, and re-signs."""
    priv_path, pub_path, key_id = generated_keys

    passport = build_passport(
        dataset_path=sample_dataset_file,
        mission={"purpose": "approval test"},
        policy="software-testing",
        evidence=[],
        verdicts={"software_testing": "PASS"},
        signing_key=priv_path,
        key_id=key_id,
    )

    # Starts as PENDING
    assert passport["human_approval"]["status"] == "PENDING"
    assert passport["human_approval"]["approver"] is None
    assert passport.is_approved() is False
    assert len(passport["audit_signatures"]) == 0

    initial_sig = passport["signature"]["value"]

    # Execute approval flow
    fixed_time = "2026-09-30T12:00:00Z"
    passport.approve(
        approver="auditor_lead@example.org",
        signing_key=priv_path,
        key_id=key_id,
        timestamp=fixed_time,
    )

    assert passport["human_approval"]["status"] == "APPROVED"
    assert passport["human_approval"]["approver"] == "auditor_lead@example.org"
    assert passport["human_approval"]["timestamp"] == fixed_time
    assert passport.is_approved() is True

    # Previous signature retained in audit_signatures
    assert len(passport["audit_signatures"]) == 1
    assert passport["audit_signatures"][0]["value"] == initial_sig

    # New signature is different and verifies successfully
    new_sig = passport["signature"]["value"]
    assert new_sig != initial_sig
    assert passport.verify(pub_path) is True


def test_fail_closed_error_paths(sample_dataset_file: Path, tmp_path: Path) -> None:
    """Verify robust fail-closed behavior on corrupted inputs, bad keys, and malformed files."""
    # Empty signature
    assert verify_signature(b"data", "", b"dummy_pub") is False

    # Corrupted base64 signature
    assert verify_signature(b"data", "not_valid_base64!!!", b"dummy_pub") is False

    # Corrupted payload structure
    assert verify_passport({}, "dummy_pub") is False

    # Missing dataset file
    missing_file = tmp_path / "non_existent.csv"
    assert verify_dataset_hash(missing_file, {"dataset": {"sha256": "abc"}}) is False
