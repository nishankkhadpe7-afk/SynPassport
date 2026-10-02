"""Trusted key registry for passport signature verification.

Addresses the core trust model gap: without a pinned trust anchor the verifier
cannot distinguish a legitimate passport from a forgery signed with an
attacker-controlled key.

Provides:
- TrustedKeyRegistry: allowlist of authorized issuer public-key fingerprints.
- validate_passport_expiry: check issued_at against a max_age_days policy.
- resolve_trusted_key: high-level helper used by the verify pipeline.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from synpassport.passport.signer import load_public_key

__all__ = [
    "TrustedKeyRegistry",
    "compute_key_fingerprint",
    "resolve_trusted_key",
    "validate_passport_expiry",
]


def compute_key_fingerprint(public_key: Any) -> str:
    """Return SHA-256 hex of raw Ed25519 public key bytes (matches passport key_id)."""
    pub = load_public_key(public_key)
    raw = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return hashlib.sha256(raw).hexdigest()


def _pub_key_to_pem(public_key: Any) -> str:
    pub = load_public_key(public_key)
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")


def _pem_to_pub_key(pem: str) -> ed25519.Ed25519PublicKey:
    pub = serialization.load_pem_public_key(pem.encode("ascii"))
    if not isinstance(pub, ed25519.Ed25519PublicKey):
        raise TypeError("PEM does not encode an Ed25519 public key")
    return pub


class TrustedKeyRegistry:
    """Allowlist of authorized issuer public-key fingerprints.

    Each entry (keyed by label) stores:
    - fingerprint: SHA-256 hex of raw public key bytes (== passport key_id)
    - public_key_pem: PEM-encoded public key
    - added_at, expires_at: enrollment and optional expiry ISO timestamps
    - revoked: bool – revoked keys are always rejected
    - comment: audit note
    """

    def __init__(self, entries: dict[str, dict[str, Any]] | None = None) -> None:
        self._entries: dict[str, dict[str, Any]] = entries or {}

    # ── Mutation ──────────────────────────────────────────

    def add_key(
        self,
        label: str,
        public_key: Any,
        *,
        expires_at: str | None = None,
        comment: str = "",
    ) -> str:
        """Register a trusted public key under label. Returns fingerprint."""
        fp = compute_key_fingerprint(public_key)
        pem = _pub_key_to_pem(public_key)
        self._entries[label] = {
            "fingerprint": fp,
            "public_key_pem": pem,
            "added_at": datetime.now(UTC).isoformat(),
            "expires_at": expires_at,
            "revoked": False,
            "comment": comment,
        }
        return fp

    def revoke_key(self, label: str, *, reason: str = "") -> None:
        """Mark key as revoked. Raises KeyError if label unknown."""
        if label not in self._entries:
            raise KeyError(f"Key label {label!r} not found in registry")
        self._entries[label]["revoked"] = True
        self._entries[label]["revoked_at"] = datetime.now(UTC).isoformat()
        self._entries[label]["revocation_reason"] = reason

    def remove_key(self, label: str) -> None:
        """Permanently remove a key entry."""
        self._entries.pop(label, None)

    # ── Lookup ────────────────────────────────────────────

    def get_entry_by_label(self, label: str) -> dict[str, Any] | None:
        return self._entries.get(label)

    def get_entry_by_fingerprint(self, fingerprint: str) -> dict[str, Any] | None:
        fp_lower = fingerprint.lower()
        for entry in self._entries.values():
            if entry.get("fingerprint", "").lower() == fp_lower:
                return entry
        return None

    def resolve_public_key(self, fingerprint: str) -> ed25519.Ed25519PublicKey:
        """Return live public key for fingerprint, enforcing revocation and expiry.

        Raises KeyError, PermissionError, or ValueError as appropriate.
        """
        entry = self.get_entry_by_fingerprint(fingerprint)
        if entry is None:
            raise KeyError(
                f"Fingerprint {fingerprint!r} is not in the trusted key registry. "
                "Only pre-registered issuer keys are accepted."
            )
        if entry.get("revoked"):
            reason = entry.get("revocation_reason", "no reason given")
            raise PermissionError(f"Key {fingerprint!r} has been revoked: {reason}")
        expires = entry.get("expires_at")
        if expires:
            exp_dt = datetime.fromisoformat(expires)
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=UTC)
            if datetime.now(UTC) > exp_dt:
                raise ValueError(
                    f"Key {fingerprint!r} expired at {expires}. Rotate before verifying."
                )
        return _pem_to_pub_key(entry["public_key_pem"])

    def is_empty(self) -> bool:
        return len(self._entries) == 0

    def active_entries(self) -> dict[str, dict[str, Any]]:
        """Return non-revoked, non-expired entries keyed by label."""
        now = datetime.now(UTC)
        result = {}
        for label, entry in self._entries.items():
            if entry.get("revoked"):
                continue
            expires = entry.get("expires_at")
            if expires:
                exp_dt = datetime.fromisoformat(expires)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=UTC)
                if now > exp_dt:
                    continue
            result[label] = entry
        return result

    # ── Serialization ─────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {"version": 1, "entries": self._entries}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrustedKeyRegistry":
        return cls(entries=data.get("entries", {}))

    def save(self, path: str | Path) -> None:
        """Write registry JSON with restricted permissions (0600)."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        try:
            os.chmod(p, 0o600)
        except OSError:
            pass

    @classmethod
    def from_file(cls, path: str | Path) -> "TrustedKeyRegistry":
        """Load from JSON; returns empty registry if file absent."""
        p = Path(path)
        if not p.is_file():
            return cls()
        return cls.from_dict(json.loads(p.read_text(encoding="utf-8")))


def validate_passport_expiry(
    passport_data: dict[str, Any],
    max_age_days: int | None = None,
) -> tuple[bool, str]:
    """Validate passport issued_at is within max_age_days.

    Returns (ok: bool, reason: str). ok=True means still fresh.
    """
    if max_age_days is None:
        return True, "No expiry policy configured"
    issued_raw = passport_data.get("issued_at")
    if not issued_raw:
        return False, "Passport missing issued_at; cannot validate expiry"
    try:
        issued = datetime.fromisoformat(str(issued_raw))
        if issued.tzinfo is None:
            issued = issued.replace(tzinfo=UTC)
    except ValueError:
        return False, f"Cannot parse issued_at: {issued_raw!r}"
    age = datetime.now(UTC) - issued
    if age > timedelta(days=max_age_days):
        return False, (
            f"Passport is {age.days}d old; max allowed is {max_age_days}d. "
            "Issue a new passport."
        )
    return True, f"Passport age {age.days}d is within {max_age_days}-day window"


def resolve_trusted_key(
    passport_data: dict[str, Any],
    registry: TrustedKeyRegistry | None = None,
    registry_path: str | Path | None = None,
    fallback_public_key: Any | None = None,
) -> ed25519.Ed25519PublicKey:
    """Resolve the verification public key for passport_data.

    Resolution order:
    1. registry (or loaded from registry_path) lookup by signature.key_id.
    2. If registry is empty and fallback_public_key provided: use it (dev/test only).
    3. Raise KeyError.
    """
    if registry is None and registry_path is not None:
        registry = TrustedKeyRegistry.from_file(registry_path)

    sig_block = passport_data.get("signature", {})
    key_id = sig_block.get("key_id", "") if isinstance(sig_block, dict) else ""

    if registry is not None and not registry.is_empty():
        if key_id:
            return registry.resolve_public_key(key_id)
        active = registry.active_entries()
        if len(active) == 1:
            return _pem_to_pub_key(next(iter(active.values()))["public_key_pem"])
        raise KeyError(
            "Passport signature.key_id is missing and registry has multiple active keys."
        )

    if fallback_public_key is not None:
        return load_public_key(fallback_public_key)

    raise KeyError(
        "No trusted key registry provided and no fallback_public_key supplied. "
        "Configure a TrustedKeyRegistry with at least one enrolled issuer key."
    )
