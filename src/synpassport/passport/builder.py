"""Evidence Passport data models, builder, and approval flow.

Constructs signed Evidence Passports combining dataset hashes, mission declarations,
locked policy hashes, empirical evidence, repair logs, deterministic verdicts,
and human approval status.
"""

from __future__ import annotations

import copy
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from synpassport.passport.canonical import (
    canonical_hash,
    canonical_json_dumps,
    hash_dataset_file,
)
from synpassport.passport.keygen import compute_key_id
from synpassport.passport.signer import load_public_key, sign_payload, verify_signature

__all__ = [
    "EvidencePassport",
    "approve_passport",
    "build_passport",
    "get_code_version",
    "verify_dataset_hash",
    "verify_passport",
]


def get_code_version() -> str:
    """Retrieve current git commit hash or fallback identifier."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        )
        sha = res.stdout.strip()
        if sha:
            return f"git:{sha[:12]}"
    except Exception:
        pass
    return "git:unknown"


class EvidencePassport:
    """Structured representation of an Evidence Passport."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.data: dict[str, Any] = copy.deepcopy(data)

    def to_dict(self) -> dict[str, Any]:
        """Return passport dictionary copy."""
        return copy.deepcopy(self.data)

    def to_canonical_json(self) -> bytes:
        """Serialize passport dictionary to canonical UTF-8 JSON bytes."""
        return canonical_json_dumps(self.data)

    def to_json(self, indent: int = 2) -> str:
        """Serialize passport dictionary to formatted JSON string."""
        return json.dumps(self.data, indent=indent)

    def sign(self, signing_key: Any, key_id: str | None = None) -> str:
        """Sign canonical bytes of the passport minus 'signature' and attach signature block."""
        if key_id is None:
            try:
                pub_key = load_public_key(signing_key)
                key_id = compute_key_id(pub_key)
            except Exception:
                key_id = "unknown"

        sig_b64 = sign_payload(self.data, signing_key)
        self.data["signature"] = {
            "alg": "Ed25519",
            "key_id": key_id,
            "value": sig_b64,
        }
        return sig_b64

    def verify(self, public_key: Any) -> bool:
        """Verify attached signature against public key."""
        return verify_passport(self.data, public_key)

    def approve(
        self,
        approver: str,
        signing_key: Any,
        key_id: str | None = None,
        timestamp: str | None = None,
    ) -> None:
        """Execute human approval flow: add approver/timestamp, retain prior sig, and re-sign."""
        self.data = approve_passport(
            self.data,
            approver=approver,
            signing_key=signing_key,
            key_id=key_id,
            timestamp=timestamp,
        )

    def is_approved(self) -> bool:
        """Return True if human approval status is APPROVED."""
        approval = self.data.get("human_approval")
        if isinstance(approval, dict):
            return approval.get("status") == "APPROVED"
        return approval == "APPROVED"

    def __getitem__(self, item: str) -> Any:
        return self.data[item]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def __contains__(self, item: str) -> bool:
        return item in self.data

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)


def build_passport(
    dataset_path: str | Path,
    mission: dict[str, Any],
    policy: dict[str, Any] | str,
    evidence: list[dict[str, Any]] | list[Any],
    verdicts: dict[str, str],
    run_info: dict[str, Any] | None = None,
    repairs: list[dict[str, Any]] | None = None,
    agent_rejections: list[dict[str, Any]] | None = None,
    dataset_name: str | None = None,
    dataset_sha256: str | None = None,
    policy_hash: str | None = None,
    code_version: str | None = None,
    seeds: list[int] | None = None,
    candidates_evaluated: int = 1,
    repairs_attempted: int = 0,
    signing_key: Any = None,
    key_id: str | None = None,
    issued_at: str | None = None,
) -> EvidencePassport:
    """Construct an Evidence Passport dictionary and optional signature."""
    path = Path(dataset_path)
    d_name = dataset_name or path.name

    if dataset_sha256 is None:
        d_sha256 = hash_dataset_file(path)
    else:
        d_sha256 = dataset_sha256

    if isinstance(policy, dict):
        pol_id = str(policy.get("id", "custom-policy"))
        pol_sha = policy_hash or canonical_hash(policy)
    else:
        pol_id = str(policy)
        pol_sha = policy_hash or canonical_hash({"id": pol_id})

    # Normalize evidence records
    normalized_evidence: list[dict[str, Any]] = []
    for item in evidence:
        if hasattr(item, "to_dict") and callable(item.to_dict):
            normalized_evidence.append(item.to_dict())
        elif hasattr(item, "__dict__"):
            d = dict(item.__dict__)
            normalized_evidence.append(d)
        elif isinstance(item, dict):
            normalized_evidence.append(copy.deepcopy(item))
        else:
            normalized_evidence.append({"raw": str(item)})

    # Resolve run metadata
    resolved_code_version = code_version
    if resolved_code_version is None and run_info:
        resolved_code_version = run_info.get("code_version")
    if resolved_code_version is None:
        resolved_code_version = get_code_version()

    run_dict: dict[str, Any] = {
        "code_version": resolved_code_version,
        "seeds": seeds if seeds is not None else (run_info.get("seeds") if run_info else [1234]),
        "candidates_evaluated": (
            run_info.get("candidates_evaluated", candidates_evaluated)
            if run_info
            else candidates_evaluated
        ),
        "repairs_attempted": (
            run_info.get("repairs_attempted", repairs_attempted) if run_info else repairs_attempted
        ),
    }

    now_iso = issued_at or datetime.now(UTC).isoformat()

    passport_dict: dict[str, Any] = {
        "passport_version": "0.1.0",
        "dataset": {
            "name": d_name,
            "sha256": d_sha256,
        },
        "mission": copy.deepcopy(mission),
        "policy": {
            "id": pol_id,
            "sha256": pol_sha,
        },
        "run": run_dict,
        "evidence": normalized_evidence,
        "repairs": copy.deepcopy(repairs or []),
        "agent_rejections": copy.deepcopy(agent_rejections or []),
        "verdicts": copy.deepcopy(verdicts),
        "human_approval": {
            "status": "PENDING",
            "approver": None,
            "timestamp": None,
        },
        "audit_signatures": [],
        "issued_at": now_iso,
    }

    passport = EvidencePassport(passport_dict)
    if signing_key is not None:
        passport.sign(signing_key, key_id=key_id)

    return passport


def approve_passport(
    passport: EvidencePassport | dict[str, Any],
    approver: str,
    signing_key: Any,
    key_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Execute approval flow on passport: add approver/timestamp, retain prior sig, and re-sign."""
    data = passport.to_dict() if isinstance(passport, EvidencePassport) else copy.deepcopy(passport)

    # Retain prior signature in audit array
    current_sig = data.get("signature")
    if current_sig and isinstance(current_sig, dict) and current_sig.get("value"):
        audit_list = data.setdefault("audit_signatures", [])
        prior_record = copy.deepcopy(current_sig)
        prior_record["archived_at"] = datetime.now(UTC).isoformat()
        audit_list.append(prior_record)

    # Update human approval status
    appr_time = timestamp or datetime.now(UTC).isoformat()
    data["human_approval"] = {
        "status": "APPROVED",
        "approver": approver,
        "timestamp": appr_time,
    }

    # Re-sign over canonical bytes minus 'signature'
    if key_id is None:
        try:
            pub_key = load_public_key(signing_key)
            key_id = compute_key_id(pub_key)
        except Exception:
            key_id = (
                current_sig.get("key_id", "unknown") if isinstance(current_sig, dict) else "unknown"
            )

    new_sig_b64 = sign_payload(data, signing_key)
    data["signature"] = {
        "alg": "Ed25519",
        "key_id": key_id,
        "value": new_sig_b64,
    }

    if isinstance(passport, EvidencePassport):
        passport.data = data

    return data


def verify_passport(
    passport: EvidencePassport | dict[str, Any],
    public_key: Any,
) -> bool:
    """Verify passport signature against canonical bytes excluding 'signature'."""
    try:
        data = passport.data if isinstance(passport, EvidencePassport) else passport
        sig_block = data.get("signature")
        if not sig_block or not isinstance(sig_block, dict):
            return False

        sig_b64 = sig_block.get("value")
        if not sig_b64 or not isinstance(sig_b64, str):
            return False

        return verify_signature(data, sig_b64, public_key)
    except Exception:
        return False


def verify_dataset_hash(
    dataset_path: str | Path,
    passport: EvidencePassport | dict[str, Any],
) -> bool:
    """Verify dataset file SHA-256 against the recorded hash in passport."""
    try:
        data = passport.data if isinstance(passport, EvidencePassport) else passport
        expected_sha = data.get("dataset", {}).get("sha256")
        if not expected_sha or not isinstance(expected_sha, str):
            return False

        actual_sha = hash_dataset_file(dataset_path)
        return actual_sha.lower() == expected_sha.lower()
    except Exception:
        return False
