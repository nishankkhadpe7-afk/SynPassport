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
2. Tools are strictly limited to: generate_candidate, run_check, run_privacy_attack,
   propose_repair, explain, finalize.
3. Repairs are strictly limited to: tune_hyperparameters, switch_generator, enable_dp_training.
4. Policy thresholds are LOCKED and IMMUTABLE. Proposing threshold changes is forbidden.
5. Holdout datasets are completely isolated and inaccessible.
6. No arbitrary code execution exists.

RESPONSE FORMAT:
You must respond ONLY with a single valid JSON object formatted as follows:
{
  "thought_summary": "<brief reasoning on checks, metrics, or diagnosis>",
  "action": "<one of the 6 permitted tool actions>",
  "args": { <valid schema arguments for the action> }
}
"""

DIAGNOSIS_PROMPT = """Analyze the evaluation metrics below and propose one whitelisted repair.
Permitted repairs:
- tune_hyperparameters (params: {epochs, lr, noise})
- switch_generator (params: {target_generator})
- enable_dp_training (params: {target_epsilon, target_delta})
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
            metrics = cand.get("metrics", {})
            verdicts = cand.get("verdicts", {})
            lines.append(f"Candidate [{cid}]:")
            lines.append(f"  Verdicts: {verdicts}")
            lines.append(f"  Aggregates: {metrics}")

    if agent_rejections:
        lines.append("")
        lines.append("=== RECENT REJECTIONS (FORBIDDEN ACTIONS LOGGED) ===")
        for rej in agent_rejections[-5:]:
            prop = rej.get("proposal")
            rsn = rej.get("reason")
            lines.append(f"  - Rejected proposal: '{prop}' | Reason: {rsn}")

    lines.append("")
    lines.append("Determine next action (run_check, run_privacy_attack, propose_repair, finalize).")
    return "\n".join(lines)
