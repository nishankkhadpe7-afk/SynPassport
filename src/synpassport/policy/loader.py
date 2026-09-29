"""Policy profile loader and canonical SHA-256 policy hasher.

Loads versioned YAML policy files and locks policy hashes prior to assurance runs.
"""

from pathlib import Path
from typing import Any

import yaml

from synpassport.passport.canonical import canonical_hash
from synpassport.policy.models import PolicyProfile

__all__ = ["load_policy", "compute_policy_hash", "load_policy_profile"]

# Default directory where policy profiles reside
DEFAULT_POLICIES_DIR = Path(__file__).resolve().parents[3] / "policies"


def compute_policy_hash(policy_data: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 digest of canonicalized policy content.

    Excludes any existing 'sha256' key so hashing is reproducible.
    """
    clean_data = {k: v for k, v in policy_data.items() if k != "sha256"}
    return canonical_hash(clean_data)


def resolve_policy_path(path_or_id: str | Path) -> Path:
    """Locate policy YAML file from exact path or profile identifier."""
    candidate = Path(path_or_id)
    if candidate.is_file():
        return candidate

    # Search in default policies directory
    for ext in (".yaml", ".yml"):
        file_path = DEFAULT_POLICIES_DIR / f"{path_or_id}{ext}"
        if file_path.is_file():
            return file_path

    msg = f"Policy profile not found: '{path_or_id}' (searched {DEFAULT_POLICIES_DIR})"
    raise FileNotFoundError(msg)


def load_policy(path_or_id: str | Path) -> dict[str, Any]:
    """Load and parse a policy profile from YAML with canonical SHA-256 hash attached."""
    policy_path = resolve_policy_path(path_or_id)
    with open(policy_path, encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)

    if not isinstance(raw_data, dict):
        raise ValueError(f"Invalid policy format in {policy_path}: expected dictionary")

    policy_dict = dict(raw_data)
    policy_dict["sha256"] = compute_policy_hash(policy_dict)
    return policy_dict


def load_policy_profile(path_or_id: str | Path) -> PolicyProfile:
    """Load policy profile into a validated PolicyProfile data model."""
    data = load_policy(path_or_id)
    return PolicyProfile(**data)
