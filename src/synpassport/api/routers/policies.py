"""Read-only access to the locked policy profiles."""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, HTTPException, status

from synpassport.passport.canonical import canonical_hash
from synpassport.policy.loader import DEFAULT_POLICIES_DIR, load_policy

__all__ = ["router"]

router = APIRouter(prefix="/policies", tags=["Policies"])

_POLICY_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def _summary(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": policy.get("id"),
        "version": policy.get("version"),
        "name": policy.get("name"),
        "description": policy.get("description"),
        # Same hash the passport records for the policy it was judged against.
        "sha256": canonical_hash(policy),
        "uses": policy.get("uses", {}),
        "requires": policy.get("requires", {}),
        "budget": policy.get("budget", {}),
        "human_approval": policy.get("human_approval"),
    }


@router.get("", summary="List policy profiles")
def list_policies() -> list[dict[str, Any]]:
    out = []
    for path in sorted(DEFAULT_POLICIES_DIR.glob("*.yaml")):
        try:
            out.append(_summary(load_policy(path.stem)))
        except Exception:
            continue
    return out


@router.get("/{policy_id}", summary="Get one policy profile with its hash")
def get_policy(policy_id: str) -> dict[str, Any]:
    if not _POLICY_ID.match(policy_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid policy id")
    try:
        return _summary(load_policy(policy_id))
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Policy '{policy_id}' not found"
        ) from exc
