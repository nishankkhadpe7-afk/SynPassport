"""Configuration settings for SynPassport FastAPI backend."""

from __future__ import annotations

import os
from pathlib import Path

# Project root .env, found from this file so it loads whatever folder the API starts in.
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


def _load_env_file(path: Path) -> None:
    """Minimal KEY=VALUE loader used when python-dotenv is not installed.

    Existing environment variables always win, matching python-dotenv's default.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        if key and key not in os.environ:
            os.environ[key] = value


try:
    from dotenv import load_dotenv

    load_dotenv(_ENV_FILE if _ENV_FILE.is_file() else None)
except ImportError:
    _load_env_file(_ENV_FILE)

__all__ = [
    "APPROVER_TOKEN",
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
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3005",
    "http://127.0.0.1:3005",
]
_extra_origins = os.environ.get("CORS_ORIGINS")
if _extra_origins:
    CORS_ORIGINS.extend([origin.strip() for origin in _extra_origins.split(",") if origin.strip()])

# Replay mode flag
REPLAY_MODE: bool = os.environ.get("SYNPASSPORT_REPLAY", "0") == "1"

# Optional shared secret required (as X-Approver-Token header) to approve releases.
# Leave unset for local demos; set it whenever the API is reachable by others.
APPROVER_TOKEN: str = os.environ.get("SYNPASSPORT_APPROVER_TOKEN", "").strip()
