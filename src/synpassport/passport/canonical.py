"""Canonical JSON serialization and cryptographic hashing.

Produces deterministic, byte-stable JSON representations (sorted keys, stable floats,
no extraneous whitespace, UTF-8 encoded) for SHA-256 digests and cryptographic signatures.
"""

import hashlib
import json
import math
from enum import Enum
from pathlib import Path
from typing import Any

__all__ = [
    "canonical_json_dumps",
    "canonical_hash",
    "hash_canonical_csv",
    "hash_dataset_file",
    "normalize_for_canonical",
]


def normalize_for_canonical(obj: Any, float_precision: int = 6) -> Any:
    """Recursively normalize data structure for deterministic canonical serialization."""
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            raise ValueError("Cannot canonicalize NaN or infinite float values")
        rounded = round(obj, float_precision)
        return 0.0 if rounded == 0.0 else rounded
    if isinstance(obj, Enum):
        return str(obj.value)
    if isinstance(obj, str) or obj is None:
        return obj
    if isinstance(obj, dict):
        return {str(k): normalize_for_canonical(v, float_precision) for k, v in sorted(obj.items())}
    if isinstance(obj, (list, tuple)):
        return [normalize_for_canonical(item, float_precision) for item in obj]

    # Handle Pydantic models or custom objects with dict conversions
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        return normalize_for_canonical(obj.model_dump(), float_precision)
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return normalize_for_canonical(obj.to_dict(), float_precision)

    raise TypeError(f"Object of type {type(obj).__name__} cannot be canonicalized to JSON")


def canonical_json_dumps(data: Any, float_precision: int = 6) -> bytes:
    """Serialize data structure to canonical UTF-8 JSON bytes."""
    normalized = normalize_for_canonical(data, float_precision=float_precision)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def canonical_hash(data: Any, float_precision: int = 6) -> str:
    """Compute SHA-256 digest of canonicalized JSON object."""
    return hashlib.sha256(canonical_json_dumps(data, float_precision=float_precision)).hexdigest()


def hash_dataset_file(file_path: str | Path, chunk_size: int = 65536) -> str:
    """Compute SHA-256 hex digest streamed over raw dataset file bytes."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Dataset file does not exist: {path}")

    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def hash_canonical_csv(source: str | Path | bytes) -> str:
    """Compute normalized canonical SHA-256 hash of CSV content.

    Normalizes Windows/Unix line endings (CRLF -> LF), trims trailing whitespace
    per line, and strips trailing blank lines so re-saving or transferring across OS
    does not break verification.
    """
    if isinstance(source, bytes):
        raw_text = source.decode("utf-8", errors="replace")
    else:
        path = Path(source)
        if not path.is_file():
            raise FileNotFoundError(f"Dataset file does not exist: {path}")
        raw_text = path.read_text(encoding="utf-8", errors="replace")

    normalized_lines = [line.rstrip() for line in raw_text.replace("\r\n", "\n").split("\n")]
    while normalized_lines and not normalized_lines[-1]:
        normalized_lines.pop()

    canonical_content = "\n".join(normalized_lines) + "\n"
    return hashlib.sha256(canonical_content.encode("utf-8")).hexdigest()
