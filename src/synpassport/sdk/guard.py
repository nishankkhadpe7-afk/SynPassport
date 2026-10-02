"""Dataset loader guard enforcing purpose-bound passport verification.

Prevents unauthorized, unsupported, or tampered datasets from being loaded into
downstream training or analytics pipelines.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pandas as pd

from synpassport.sdk.verify import verify

__all__ = ["PassportError", "load_dataset"]


class PassportError(Exception):
    """Raised when dataset loading is blocked due to missing or invalid assurance verification."""

    def __init__(self, message: str, reason_code: str = "PASSPORT_MALFORMED") -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.message = message


def _locate_default_passport(dataset_path: Path) -> Path | None:
    """Locate associated passport file by conventional naming patterns."""
    candidates = [
        dataset_path.with_name(f"{dataset_path.name}.passport.json"),
        dataset_path.with_suffix(".passport.json"),
        dataset_path.parent / "passport.json",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_dataset(
    dataset_path: str | Path,
    purpose: str,
    passport_path: str | Path | None = None,
    allow_warning: bool = False,
    public_key: Any | None = None,
) -> pd.DataFrame:
    """Load dataset after strictly validating Evidence Passport against declared purpose.

    Eliminates TOCTOU race conditions by reading raw bytes once, verifying cryptographic
    digest against those bytes, and parsing the dataframe directly from the in-memory buffer.
    Raises PassportError on any non-OK verification result.
    """
    d_path = Path(dataset_path)
    if not d_path.is_file():
        raise PassportError(
            f"Dataset file does not exist: {d_path}", reason_code="DATASET_HASH_MISMATCH"
        )

    # Read bytes once to avoid TOCTOU file-swapping between verification and ingestion
    try:
        raw_bytes = d_path.read_bytes()
    except Exception as exc:
        raise PassportError(
            f"Failed to read dataset file bytes: {exc}", reason_code="DATASET_HASH_MISMATCH"
        ) from exc

    if passport_path is not None:
        p_path = Path(passport_path)
    else:
        found = _locate_default_passport(d_path)
        if found is None:
            raise PassportError(
                f"No Evidence Passport specified or found for dataset: {d_path}",
                reason_code="PASSPORT_MALFORMED",
            )
        p_path = found

    result = verify(
        dataset_path=d_path,
        passport_path=p_path,
        purpose=purpose,
        allow_warning=allow_warning,
        public_key=public_key,
        dataset_bytes=raw_bytes,
    )

    if not result.valid:
        error_msg = result.details.get("error", "Assurance check rejected")
        raise PassportError(
            f"Dataset loading blocked for purpose '{purpose}': [{result.reason_code}] {error_msg}",
            reason_code=result.reason_code,
        )

    # Parse dataframe directly from verified memory buffer (TOCTOU-safe)
    suffix = d_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(io.BytesIO(raw_bytes))
    elif suffix in (".parquet", ".pq"):
        return pd.read_parquet(io.BytesIO(raw_bytes))
    else:
        raise PassportError(
            f"Unsupported dataset file format '{suffix}' for path: {d_path}. "
            "Supported formats: .csv, .parquet, .pq",
            reason_code="PASSPORT_MALFORMED",
        )
