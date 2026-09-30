"""Configuration settings for SynPassport FastAPI backend."""

from __future__ import annotations

import os
from pathlib import Path

__all__ = [
    "CORS_ORIGINS",
    "DATA_DIR",
    "KEY_DIR",
    "MAX_UPLOAD_SIZE",
    "REPLAY_MODE",
    "RUNS_DIR",
]

# Base data directory for uploaded and generated artifacts
DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "./data")).resolve()
RUNS_DIR: Path = DATA_DIR / "runs"
KEY_DIR: Path = DATA_DIR / "keys"

# Max upload size: 50MB default
MAX_UPLOAD_SIZE: int = int(os.environ.get("MAX_UPLOAD_SIZE", 50 * 1024 * 1024))

# Permitted CORS origins
CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
_extra_origins = os.environ.get("CORS_ORIGINS")
if _extra_origins:
    CORS_ORIGINS.extend([origin.strip() for origin in _extra_origins.split(",") if origin.strip()])

# Replay mode flag
REPLAY_MODE: bool = os.environ.get("SYNPASSPORT_REPLAY", "0") == "1"
