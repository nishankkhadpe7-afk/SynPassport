"""Explanation generator grounded in evidence-store rows.

Builds post-run explanations strictly citing evidence_ids.
Uncited claims are stripped or flagged as [UNCITED - FLAGGED].
"""

from __future__ import annotations

import re
from typing import Any

__all__ = ["generate_explanation", "verify_and_sanitize_explanation"]

CITATION_REGEX = re.compile(r"\[evidence:([a-zA-Z0-9_\-]+)\]")


def generate_explanation(evidence_records: list[dict[str, Any]] | list[Any]) -> dict[str, Any]:
    """Generate structured explanation statements citing evidence records directly."""
    claims: list[dict[str, Any]] = []
    lines: list[str] = []

    for item in evidence_records:
        if isinstance(item, dict):
            rec = item
        elif hasattr(item, "to_dict"):
            rec = item.to_dict()
        else:
            rec = dict(item.__dict__)
        cid = rec.get("check_id") or rec.get("check") or "unknown"
        state = rec.get("state", "UNKNOWN")
        val = rec.get("value")
        th = rec.get("threshold_ref") or rec.get("threshold") or "policy"
        ci_l = rec.get("ci_low")
        ci_h = rec.get("ci_high")

        if ci_l is not None and ci_h is not None:
            stmt = (
                f"Check '{cid}' scored {val:.4f} with 95% CI "
                f"[{ci_l:.4f}, {ci_h:.4f}] vs threshold {th} -> {state}"
            )
        elif val is not None:
            stmt = f"Check '{cid}' evaluated to {val:.4f} vs threshold {th} -> {state}"
        else:
            stmt = f"Check '{cid}' reached state {state} under threshold {th}"

        cited_stmt = f"{stmt} [evidence:{cid}]"
        lines.append(cited_stmt)
        claims.append(
            {
                "statement": stmt,
                "evidence_id": cid,
                "state": state,
                "cited": True,
            }
        )

    summary_text = "\n".join(lines)
    return {
        "summary": summary_text,
        "claims": claims,
        "flagged_claims": [],
    }


def verify_and_sanitize_explanation(
    explanation_text: str,
    valid_evidence_ids: set[str],
) -> tuple[str, list[str]]:
    """Verify that every sentence or claim cites an evidence_id; strip or flag uncited claims."""
    lines = [line.strip() for line in explanation_text.splitlines() if line.strip()]
    sanitized_lines: list[str] = []
    flagged: list[str] = []

    for line in lines:
        citations = CITATION_REGEX.findall(line)
        valid_citations = [c for c in citations if c in valid_evidence_ids]

        if not valid_citations:
            flagged_line = f"[UNCITED - FLAGGED] {line}"
            flagged.append(line)
            sanitized_lines.append(flagged_line)
        else:
            sanitized_lines.append(line)

    return "\n".join(sanitized_lines), flagged
