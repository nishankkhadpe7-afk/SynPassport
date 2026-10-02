"""Verification SDK function for synthetic datasets and Evidence Passports.

Executes sequential, fail-closed verification checks per design.md §6:
1. Parse and schema-validate the passport.
2. Recompute canonical hash and verify the Ed25519 signature.
3. Stream dataset file bytes to verify the SHA-256 digest.
4. Verify purpose-scoped verdicts (PASS, or WARNING if allowed).
5. Verify required human approval status.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from synpassport.passport.builder import verify_passport
from synpassport.passport.canonical import hash_canonical_csv, hash_dataset_file
from synpassport.passport.trust import (
    TrustedKeyRegistry,
    resolve_trusted_key,
    validate_passport_expiry,
)
from synpassport.policy.loader import load_policy

__all__ = ["REASON_CODES", "VerificationResult", "verify"]

REASON_CODES = {
    "OK": "Verification successful and purpose supported.",
    "SIGNATURE_INVALID": "Cryptographic signature missing, invalid, or tampered.",
    "KEY_UNTRUSTED": "Signing key is not in the trusted issuer registry, is revoked, or has expired.",
    "PASSPORT_EXPIRED": "Passport has exceeded the maximum age allowed by policy.",
    "DATASET_HASH_MISMATCH": "Dataset file SHA-256 does not match passport binding.",
    "PURPOSE_UNSUPPORTED": "Purpose verdict does not meet acceptance thresholds.",
    "PURPOSE_UNKNOWN": "Purpose is not declared or evaluated in passport verdicts.",
    "APPROVAL_MISSING": "Human release approval is required by policy but missing.",
    "PASSPORT_MALFORMED": "Passport file is missing, invalid JSON, or schema non-conformant.",
}


class VerificationResult:
    """Structured result of dataset and passport verification checks."""

    def __init__(
        self,
        valid: bool,
        reason_code: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.valid = valid
        self.reason_code = reason_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert verification result to dictionary."""
        return {
            "valid": self.valid,
            "reason_code": self.reason_code,
            "description": REASON_CODES.get(self.reason_code, "Unknown status"),
            "details": self.details,
        }

    def __bool__(self) -> bool:
        """Allow boolean evaluation of result."""
        return self.valid

    def __repr__(self) -> str:
        return f"VerificationResult(valid={self.valid}, reason_code='{self.reason_code}')"


def _resolve_public_key(
    passport_path: str | Path,
    public_key: Any | None,
) -> Any | None:
    """Locate candidate public key from argument or standard locations."""
    if public_key is not None:
        return public_key

    p_path = Path(passport_path)

    # Check next to passport: <passport_dir>/ed25519_public.pem or <passport>.pub.pem
    sibling_pub = p_path.parent / "ed25519_public.pem"
    if sibling_pub.is_file():
        return sibling_pub

    dot_pub = p_path.with_suffix(p_path.suffix + ".pub.pem")
    if dot_pub.is_file():
        return dot_pub

    # Check project-level keys/
    project_pub = Path("./keys/ed25519_public.pem")
    if project_pub.is_file():
        return project_pub

    return None


def verify(
    dataset_path: str | Path | None = None,
    passport_path: str | Path | None = None,
    purpose: str = "",
    allow_warning: bool = False,
    public_key: Any | None = None,
    *,
    dataset_bytes: bytes | None = None,
    passport_data: dict[str, Any] | None = None,
    verify_evidence: bool = False,
    registry: TrustedKeyRegistry | None = None,
    registry_path: str | Path | None = None,
    max_age_days: int | None = None,
) -> VerificationResult:
    """Verify dataset against its Evidence Passport for a specific purpose.

    Executes verification steps in order with fail-closed semantics:
    1. Parse + schema-validate passport -> PASSPORT_MALFORMED
    2. Validate passport age against max_age_days -> PASSPORT_EXPIRED
    3. Resolve trusted signing key from registry (if provided) -> KEY_UNTRUSTED
    4. Recompute canonical hash; verify signature -> SIGNATURE_INVALID
    5. Hash dataset bytes/file; compare to dataset.sha256 (or canonical_sha256) -> DATASET_HASH_MISMATCH
    6. Check verdicts[purpose] in {PASS, WARNING (opt-in)} -> PURPOSE_UNSUPPORTED / PURPOSE_UNKNOWN
    7. Check human_approval == APPROVED when policy requires -> APPROVAL_MISSING

    Args:
        registry: Pre-loaded TrustedKeyRegistry. When provided, the passport's
            ``signature.key_id`` is looked up in the allowlist and the resolved
            key is used for signature verification.  Revoked/expired keys are
            rejected with KEY_UNTRUSTED.
        registry_path: Path to a JSON TrustedKeyRegistry file. Loaded lazily
            when ``registry`` is None.
        max_age_days: If set, passports older than this number of days are
            rejected with PASSPORT_EXPIRED.
    """
    # -------------------------------------------------------------
    # Step 1: Parse and schema-validate passport
    # -------------------------------------------------------------
    pass_file = Path(passport_path) if passport_path else None
    if passport_data is None:
        if pass_file is None or not pass_file.is_file():
            return VerificationResult(
                valid=False,
                reason_code="PASSPORT_MALFORMED",
                details={"error": f"Passport file not found: {pass_file}"},
            )

        try:
            content = pass_file.read_text(encoding="utf-8")
            passport_data = json.loads(content)
        except Exception as exc:
            return VerificationResult(
                valid=False,
                reason_code="PASSPORT_MALFORMED",
                details={"error": f"Failed to parse passport JSON: {exc}"},
            )

    if not isinstance(passport_data, dict):
        return VerificationResult(
            valid=False,
            reason_code="PASSPORT_MALFORMED",
            details={"error": "Passport JSON root must be an object"},
        )

    # Validate essential schema elements
    required_fields = ["dataset", "policy", "verdicts", "human_approval", "signature"]
    for req in required_fields:
        if req not in passport_data:
            return VerificationResult(
                valid=False,
                reason_code="PASSPORT_MALFORMED",
                details={"error": f"Missing required top-level field: '{req}'"},
            )

    dataset_block = passport_data.get("dataset")
    if not isinstance(dataset_block, dict) or "sha256" not in dataset_block:
        return VerificationResult(
            valid=False,
            reason_code="PASSPORT_MALFORMED",
            details={"error": "Passport 'dataset' block must contain 'sha256'"},
        )

    policy_block = passport_data.get("policy")
    if not isinstance(policy_block, dict) or "id" not in policy_block:
        return VerificationResult(
            valid=False,
            reason_code="PASSPORT_MALFORMED",
            details={"error": "Passport 'policy' block must contain 'id'"},
        )

    verdicts_block = passport_data.get("verdicts")
    if not isinstance(verdicts_block, dict):
        return VerificationResult(
            valid=False,
            reason_code="PASSPORT_MALFORMED",
            details={"error": "Passport 'verdicts' must be a dictionary"},
        )

    sig_block = passport_data.get("signature")
    if not isinstance(sig_block, dict) or "value" not in sig_block:
        return VerificationResult(
            valid=False,
            reason_code="PASSPORT_MALFORMED",
            details={"error": "Passport 'signature' block must contain 'value'"},
        )

    # -------------------------------------------------------------
    # Step 2: Validate passport expiry (optional)
    # -------------------------------------------------------------
    ok_exp, exp_reason = validate_passport_expiry(passport_data, max_age_days=max_age_days)
    if not ok_exp:
        return VerificationResult(
            valid=False,
            reason_code="PASSPORT_EXPIRED",
            details={"error": exp_reason},
        )

    # -------------------------------------------------------------
    # Step 3: Resolve trusted signing key
    # -------------------------------------------------------------
    resolved_key: Any = None
    if registry is not None or registry_path is not None:
        # Registry-based trust anchor — preferred path
        try:
            resolved_key = resolve_trusted_key(
                passport_data,
                registry=registry,
                registry_path=registry_path,
                fallback_public_key=None,  # no fallback when registry explicitly provided
            )
        except (KeyError, PermissionError, ValueError) as exc:
            return VerificationResult(
                valid=False,
                reason_code="KEY_UNTRUSTED",
                details={"error": str(exc)},
            )
    else:
        # Legacy path: caller supplies public_key directly (dev/CI use)
        resolved_key = _resolve_public_key(
            pass_file if pass_file else Path("./passport.json"), public_key
        )
        if resolved_key is None:
            return VerificationResult(
                valid=False,
                reason_code="SIGNATURE_INVALID",
                details={
                    "error": (
                        "Public key not provided and could not be resolved from standard paths. "
                        "Supply a TrustedKeyRegistry for production use."
                    )
                },
            )

    # -------------------------------------------------------------
    # Step 4: Recompute canonical hash; verify signature
    # -------------------------------------------------------------
    if sig_block.get("alg") != "Ed25519":
        return VerificationResult(
            valid=False,
            reason_code="SIGNATURE_INVALID",
            details={"error": f"Unsupported signature algorithm: {sig_block.get('alg')}"},
        )

    if not verify_passport(passport_data, resolved_key):
        return VerificationResult(
            valid=False,
            reason_code="SIGNATURE_INVALID",
            details={
                "error": "Ed25519 signature verification failed over canonical passport bytes"
            },
        )

    # -------------------------------------------------------------
    # Step 5: Hash dataset bytes or file; compare to dataset.sha256 (or canonical_sha256)
    # -------------------------------------------------------------
    expected_sha256 = str(dataset_block.get("sha256", "")).lower()
    expected_canon = dataset_block.get("canonical_sha256")
    if expected_canon:
        expected_canon = str(expected_canon).lower()

    if dataset_bytes is not None:
        computed_sha256 = hashlib.sha256(dataset_bytes).hexdigest().lower()
        if computed_sha256 != expected_sha256:
            # Fallback to canonical CSV content hash if recorded
            if expected_canon:
                try:
                    canon_hash = hash_canonical_csv(dataset_bytes).lower()
                    if canon_hash != expected_canon:
                        return VerificationResult(
                            valid=False,
                            reason_code="DATASET_HASH_MISMATCH",
                            details={
                                "expected": expected_sha256,
                                "actual": computed_sha256,
                                "canonical_expected": expected_canon,
                                "canonical_actual": canon_hash,
                                "error": "Dataset SHA-256 does not match passport binding",
                            },
                        )
                except Exception:
                    return VerificationResult(
                        valid=False,
                        reason_code="DATASET_HASH_MISMATCH",
                        details={
                            "expected": expected_sha256,
                            "actual": computed_sha256,
                            "error": "Dataset SHA-256 does not match passport binding",
                        },
                    )
            else:
                return VerificationResult(
                    valid=False,
                    reason_code="DATASET_HASH_MISMATCH",
                    details={
                        "expected": expected_sha256,
                        "actual": computed_sha256,
                        "error": "Dataset SHA-256 does not match passport binding",
                    },
                )
    else:
        if dataset_path is None:
            return VerificationResult(
                valid=False,
                reason_code="DATASET_HASH_MISMATCH",
                details={"error": "Neither dataset_path nor dataset_bytes provided"},
            )
        d_path = Path(dataset_path)
        if not d_path.is_file():
            return VerificationResult(
                valid=False,
                reason_code="DATASET_HASH_MISMATCH",
                details={"error": f"Dataset file not found: {d_path}"},
            )

        try:
            computed_sha256 = hash_dataset_file(d_path).lower()
        except Exception as exc:
            return VerificationResult(
                valid=False,
                reason_code="DATASET_HASH_MISMATCH",
                details={"error": f"Error computing dataset SHA-256: {exc}"},
            )

        if computed_sha256 != expected_sha256:
            # Fallback to canonical CSV content hash if recorded
            if expected_canon:
                try:
                    canon_hash = hash_canonical_csv(d_path).lower()
                    if canon_hash != expected_canon:
                        return VerificationResult(
                            valid=False,
                            reason_code="DATASET_HASH_MISMATCH",
                            details={
                                "expected": expected_sha256,
                                "actual": computed_sha256,
                                "canonical_expected": expected_canon,
                                "canonical_actual": canon_hash,
                                "error": "Dataset SHA-256 does not match passport binding",
                            },
                        )
                except Exception:
                    return VerificationResult(
                        valid=False,
                        reason_code="DATASET_HASH_MISMATCH",
                        details={
                            "expected": expected_sha256,
                            "actual": computed_sha256,
                            "error": "Dataset SHA-256 does not match passport binding",
                        },
                    )
            else:
                return VerificationResult(
                    valid=False,
                    reason_code="DATASET_HASH_MISMATCH",
                    details={
                        "expected": expected_sha256,
                        "actual": computed_sha256,
                        "error": "Dataset SHA-256 does not match passport binding",
                    },
                )

    # -------------------------------------------------------------
    # Step 4: Check verdicts[purpose] in {PASS} (WARNING if allow_warning)
    # -------------------------------------------------------------
    if purpose not in verdicts_block:
        return VerificationResult(
            valid=False,
            reason_code="PURPOSE_UNKNOWN",
            details={
                "purpose": purpose,
                "available_purposes": sorted(verdicts_block.keys()),
                "error": f"Purpose '{purpose}' not found in passport verdicts",
                "mode": passport_data.get("mode", "live"),
            },
        )

    verdict_state = str(verdicts_block[purpose])
    if verdict_state == "PASS":
        pass
    elif verdict_state == "WARNING":
        if not allow_warning:
            return VerificationResult(
                valid=False,
                reason_code="PURPOSE_UNSUPPORTED",
                details={
                    "purpose": purpose,
                    "verdict": verdict_state,
                    "mode": passport_data.get("mode", "live"),
                    "error": (
                        "Purpose has WARNING verdict; allow_warning must be enabled to proceed"
                    ),
                },
            )
    else:
        return VerificationResult(
            valid=False,
            reason_code="PURPOSE_UNSUPPORTED",
            details={
                "purpose": purpose,
                "verdict": verdict_state,
                "mode": passport_data.get("mode", "live"),
                "error": f"Purpose verdict '{verdict_state}' does not meet required threshold",
            },
        )

    # Independent policy re-evaluation: verify that evidence rows support the verdict
    evidence_rows = passport_data.get("evidence", [])
    if verify_evidence and evidence_rows:
        try:
            from synpassport.policy.engine import evaluate_policy
            pol_id = str(policy_block.get("id"))
            loaded_pol = None
            try:
                loaded_pol = load_policy(pol_id)
            except Exception:
                pass
            if loaded_pol:
                recomputed_verdicts = evaluate_policy(loaded_pol, evidence_rows)
                recomputed_state = recomputed_verdicts.get(purpose)
                if recomputed_state and recomputed_state != verdict_state:
                    return VerificationResult(
                        valid=False,
                        reason_code="PURPOSE_UNSUPPORTED",
                        details={
                            "purpose": purpose,
                            "declared_verdict": verdict_state,
                            "recomputed_verdict": recomputed_state,
                            "error": f"Independent policy evaluation yielded '{recomputed_state}', contradicting declared verdict '{verdict_state}'",
                        },
                    )
        except Exception:
            pass

    # -------------------------------------------------------------
    # Step 5: Check human_approval == APPROVED when policy requires it
    # -------------------------------------------------------------
    policy_id = str(policy_block.get("id"))
    req_human_approval = False
    try:
        policy_def = load_policy(policy_id)
        req_human_approval = policy_def.get("human_approval") == "required"
    except Exception:
        # Fallback to passport policy block if local policy file absent
        req_human_approval = policy_block.get("human_approval") == "required"

    ha = passport_data.get("human_approval")
    is_approved = False
    if isinstance(ha, dict):
        status = ha.get("status")
        is_approved = status == "APPROVED"
        if status == "REJECTED":
            return VerificationResult(
                valid=False,
                reason_code="APPROVAL_MISSING",
                details={"status": status, "error": "Release approval was explicitly rejected"},
            )
    elif isinstance(ha, str):
        is_approved = ha == "APPROVED"
        if ha == "REJECTED":
            return VerificationResult(
                valid=False,
                reason_code="APPROVAL_MISSING",
                details={"status": ha, "error": "Release approval was explicitly rejected"},
            )

    if req_human_approval and not is_approved:
        return VerificationResult(
            valid=False,
            reason_code="APPROVAL_MISSING",
            details={
                "policy_id": policy_id,
                "human_approval": ha,
                "error": "Policy requires human release approval before use",
            },
        )

    # -------------------------------------------------------------
    # Step 6: Return structured OK result
    # -------------------------------------------------------------
    return VerificationResult(
        valid=True,
        reason_code="OK",
        details={
            "purpose": purpose,
            "verdict": verdict_state,
            "dataset_sha256": computed_sha256,
            "policy_id": policy_id,
        },
    )
