"""Replay cache for recording and replaying LLM responses and candidate runs.

Keys records by (mission, policy_id, seed) and persists artifacts into replay/.
Enables completely deterministic offline replay mode with zero network calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from synpassport.passport.canonical import canonical_hash

__all__ = ["ReplayCache", "compute_replay_key"]


def compute_replay_key(mission: dict[str, Any], policy_id: str, seed: int) -> str:
    """Compute deterministic SHA-256 cache key from mission, policy, and seed."""
    key_payload = {
        "mission": mission,
        "policy_id": policy_id,
        "seed": seed,
    }
    return canonical_hash(key_payload)


class ReplayCache:
    """Read/write cache for deterministic offline execution in replay mode."""

    def __init__(self, cache_dir: str | Path = "./replay") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}.json"

    def has(self, cache_key: str) -> bool:
        """Return True if cache entry exists."""
        return self._file_path(cache_key).is_file()

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """Retrieve cached run entry if present."""
        path = self._file_path(cache_key)
        if not path.is_file():
            return None
        try:
            res = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(res, dict):
                return res
            return None
        except Exception:
            return None

    def save(self, cache_key: str, data: dict[str, Any]) -> None:
        """Persist execution record to cache file."""
        path = self._file_path(cache_key)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
