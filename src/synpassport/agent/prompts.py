"""System and context prompts for the SynPassport Assurance Agent.

Enforces prompt-injection hygiene and holdout isolation:
- Raw dataset records and holdout rows NEVER enter prompts.
- Column identifiers and types are sanitized.
- Policy thresholds are presented strictly as locked and read-only.
- Structured JSON output schema is mandated.
"""

from __future__ import annotations

import re
from typing import Any

__all__ = [
    "DIAGNOSIS_PROMPT",
    "SYSTEM_PROMPT",
    "format_agent_context",
    "format_policy_summary",
    "sanitize_column_name",
    "sanitize_schema_summary",
]

SYSTEM_PROMPT = """You are SynPassport Assurance Agent.
Your role is to plan evaluation checks, diagnose empirical failures, and propose repairs.

HARD RULES:
1. You NEVER assign verdicts. Only the policy engine assigns
   PASS/WARNING/FAIL/INSUFFICIENT_EVIDENCE.
2. All pre-registered checks have already run; their results are in the context.
   In the repair step the only permitted actions are propose_repair and finalize.
3. Repairs are strictly limited to these three, with exactly these params:
   - regenerate_identifiers: {} (no params). Replaces identifier columns, which code
     detects from the real data, with fresh values in the same format so no real
     identifier is copied. Use it when identifier_leakage is not PASS.
   - switch_generator: {"target_generator": "CTGAN" or "GaussianCopula"}
     (no other generators exist; TVAE, DP and others are unavailable)
   - tune_hyperparameters: {"epochs": int 1-500, "batch_size": int 10-10000}
     (only affects CTGAN)
   If no permitted repair can plausibly fix the failing check, choose finalize.
4. Policy thresholds are LOCKED and IMMUTABLE. Proposing threshold changes is forbidden.
5. Holdout datasets are completely isolated and inaccessible.
6. No arbitrary code execution exists.

Keep thought_summary to at most 2 short sentences (under 60 words). State the
decision, not your deliberation. Do not think out loud.

RESPONSE FORMAT:
You must respond ONLY with a single valid JSON object formatted as follows:
{
  "thought_summary": "<at most 2 short sentences: the failing check and why this action>",
  "action": "propose_repair" or "finalize",
  "args": { <valid schema arguments for the action> }
}
"""

DIAGNOSIS_PROMPT = """Analyze the evaluation metrics below and propose one whitelisted repair.
Permitted repairs:
- tune_hyperparameters (params: {epochs, batch_size}; integers; only affect CTGAN)
- switch_generator (params: {target_generator}: "CTGAN" or "GaussianCopula")
"""


def sanitize_column_name(col: str) -> str:
    """Sanitize column name to alphanumeric characters and underscores to prevent injection."""
    cleaned = re.sub(r"[^\w\s-]", "", str(col)).strip()
    return re.sub(r"[-\s]+", "_", cleaned)[:64]


def sanitize_schema_summary(
    columns: list[str],
    dtypes: dict[str, str] | None = None,
    row_count: int | None = None,
) -> dict[str, Any]:
    """Build sanitized tabular schema representation without raw dataset records."""
    dtypes = dtypes or {}
    sanitized_cols = [
        {
            "name": sanitize_column_name(c),
            "type": str(dtypes.get(c, "unknown")),
        }
        for c in columns
    ]
    return {
        "num_columns": len(columns),
        "num_rows": row_count if row_count is not None else "unknown",
        "columns": sanitized_cols,
    }


def format_policy_summary(policy: dict[str, Any]) -> str:
    """Format read-only policy profile summary with immutable constraints."""
    pid = policy.get("id", "custom-policy")
    pver = policy.get("version", 1)
    requires = policy.get("requires", {})
    warning_bands = policy.get("warning_bands", {})
    uses = policy.get("uses", {})

    lines = [
        f"POLICY: {pid} (version {pver}) [STATUS: LOCKED, READ-ONLY]",
        "Mandatory Thresholds:",
    ]
    for cid, th in requires.items():
        lines.append(f"  - {cid}: {th}")

    if warning_bands:
        lines.append("Warning Bands:")
        for cid, wb in warning_bands.items():
            lines.append(f"  - {cid}: {wb}")

    if uses:
        lines.append("Intended Uses Evaluated:")
        for use, checks in uses.items():
            lines.append(f"  - {use}: {checks}")

    return "\n".join(lines)


def _format_evidence(evidence: list[Any], states: dict[str, str] | None = None) -> list[str]:
    """Aggregate per-check results for the prompt (values only, never raw records)."""
    out: list[str] = []
    for rec in evidence:
        data = rec if isinstance(rec, dict) else getattr(rec, "__dict__", {})
        if hasattr(rec, "model_dump"):
            data = rec.model_dump()
        check_id = data.get("check_id", "?")
        value = data.get("value")
        # 4 decimals so a near-miss such as 0.9995 against "pass" is not shown as 1.000
        val = f"{value:.4f}" if isinstance(value, (int, float)) else str(value)
        parts = [f"Check {check_id}: value={val}", f"threshold={data.get('threshold_ref')}"]
        if states and check_id in states:
            parts.append(f"state={states[check_id]}")
        if data.get("ci_low") is not None and data.get("ci_high") is not None:
            parts.append(f"ci=[{data['ci_low']:.3f}, {data['ci_high']:.3f}]")
        meta = data.get("metadata") or {}
        if meta.get("error"):
            parts.append(f"error={str(meta['error'])[:120]}")
        out.append(", ".join(parts))
        reports = meta.get("column_reports")
        if isinstance(reports, dict):
            bad = {
                sanitize_column_name(k): v.get("valid_fraction")
                for k, v in reports.items()
                if isinstance(v, dict) and (v.get("valid_fraction") or 0) < 1.0
            }
            if bad:
                out.append(
                    "  columns with out-of-range or invalid values (valid fraction): "
                    + ", ".join(f"{k}={v:.4f}" for k, v in list(bad.items())[:8])
                )
        per_feature = meta.get("per_feature")
        if isinstance(per_feature, dict) and per_feature:
            worst = sorted(per_feature.items(), key=lambda kv: kv[1])[:8]
            out.append(
                "  lowest-scoring columns: "
                + ", ".join(f"{sanitize_column_name(k)}={v:.2f}" for k, v in worst)
            )
    return out


def format_agent_context(
    mission: dict[str, Any],
    policy: dict[str, Any],
    schema_summary: dict[str, Any],
    candidate_history: list[dict[str, Any]],
    budget_state: dict[str, int],
    agent_rejections: list[dict[str, str]] | None = None,
) -> str:
    """Assemble structured agent context using aggregate statistics only."""
    lines = [
        "=== MISSION DECLARATION ===",
        f"Purpose:        {mission.get('purpose', 'Evaluation')}",
        f"Subgroups:      {mission.get('critical_subgroups', ['all'])}",
        f"Intended Uses:  {mission.get('intended_uses', [])}",
        "",
        "=== LOCKED POLICY CONSTRAINTS ===",
        format_policy_summary(policy),
        "",
        "=== DATASET SCHEMA (SANITIZED SUMMARY) ===",
        f"Columns ({schema_summary.get('num_columns', 0)}): "
        + ", ".join(c["name"] for c in schema_summary.get("columns", [])[:20]),
        "",
        "=== RUN BUDGET STATE (HARD LIMITS ENFORCED IN CODE) ===",
        (
            f"Candidates Evaluated: {budget_state.get('candidates_evaluated', 0)} / "
            f"{budget_state.get('max_candidates', 3)}"
        ),
        (
            f"Repairs Attempted:    {budget_state.get('repairs_attempted', 0)} / "
            f"{budget_state.get('max_repairs', 2)}"
        ),
    ]

    if candidate_history:
        lines.append("")
        lines.append("=== CANDIDATE EVALUATION AGGREGATES ===")
        for cand in candidate_history:
            cid = cand.get("candidate_id", "unknown")
            verdicts = cand.get("verdicts", {})
            actual = cand.get("generator", "unknown")
            requested = cand.get("requested_generator") or actual
            gen_text = str(actual)
            if requested != actual:
                gen_text = (
                    f"{actual} (requested {requested}, which is NOT available in this "
                    "environment, so it fell back; do not request it again)"
                )
            lines.append(f"Candidate [{cid}] (generator: {gen_text}):")
            lines.append(f"  Verdicts: {verdicts}")
            if cand.get("params"):
                lines.append(f"  Generator params: {cand.get('params')}")
            for line in _format_evidence(cand.get("evidence", []), cand.get("check_states")):
                lines.append(f"  {line}")

    if agent_rejections:
        lines.append("")
        lines.append("=== RECENT REJECTIONS (FORBIDDEN ACTIONS LOGGED) ===")
        for rej in agent_rejections[-5:]:
            prop = rej.get("proposal")
            rsn = rej.get("reason")
            lines.append(f"  - Rejected proposal: '{prop}' | Reason: {rsn}")

    lines.append("")
    lines.append(
        "REPAIR STEP: every check above has already been run. Respond with action "
        "'propose_repair' (args: action, params, diagnosis) or 'finalize'. "
        "Other actions are rejected here."
    )
    return "\n".join(lines)
