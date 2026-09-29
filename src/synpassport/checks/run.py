"""CLI entrypoint to execute evaluation checks and persist evidence records."""

import argparse
import sys
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from synpassport.checks.base import BaseCheck, CheckResult
from synpassport.checks.fidelity import CorrelationFidelityCheck, MarginalFidelityCheck
from synpassport.checks.privacy import DCRVsHoldoutCheck, MembershipInferenceCheck
from synpassport.checks.schema import SchemaValidityCheck
from synpassport.checks.splitter import split_train_holdout
from synpassport.checks.sufficiency import SufficiencyCheck
from synpassport.checks.utility import SubgroupUtilityCheck, UtilityTSTRCheck
from synpassport.evidence.models import EvidenceRecord
from synpassport.evidence.store import EvidenceStore
from synpassport.policy.loader import load_policy

__all__ = ["run_checks_pipeline", "main"]

CHECK_REGISTRY: dict[str, BaseCheck] = {
    "schema_validity": SchemaValidityCheck(),
    "marginal_fidelity": MarginalFidelityCheck(),
    "correlation_fidelity": CorrelationFidelityCheck(),
    "utility_tstr_ratio": UtilityTSTRCheck(),
    "subgroup_utility_ci": SubgroupUtilityCheck(),
    "subgroup_utility_ci_width": SubgroupUtilityCheck(),
    "privacy_dcr_vs_holdout": DCRVsHoldoutCheck(),
    "membership_inference_auc": MembershipInferenceCheck(),
    "sufficiency": SufficiencyCheck(),
}


def run_checks_pipeline(
    data_path: str | Path,
    synth_path: str | Path,
    policy_id_or_path: str | Path,
    holdout_path: str | Path | None = None,
    db_path: str | Path = "./data/synpassport.db",
    run_id: str | None = None,
    candidate_id: str = "candidate_001",
    seed: int = 1234,
    target_col: str | None = None,
    subgroup_query: str = "age >= 65",
) -> list[EvidenceRecord]:
    """Execute required evaluation checks and persist evidence rows into SQLite."""
    run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"

    # Load data
    real_df = pd.read_csv(data_path)
    synth_df = pd.read_csv(synth_path)

    # Resolve holdout
    if holdout_path and Path(holdout_path).is_file():
        train_df = real_df
        holdout_df = pd.read_csv(holdout_path)
    else:
        # Partition 50/50 deterministically
        split = split_train_holdout(real_df, train_ratio=0.5, seed=seed)
        train_df = split.train_df
        holdout_df = split.holdout_df

    # Load policy profile
    policy = load_policy(policy_id_or_path)
    requires: dict[str, Any] = policy.get("requires", {})

    # Execute checks
    evidence_records: list[EvidenceRecord] = []
    executed_check_ids: set[str] = set()

    for check_id, threshold_spec in requires.items():
        if check_id in executed_check_ids:
            continue

        check_instance = CHECK_REGISTRY.get(check_id)
        if not check_instance:
            continue

        check_kwargs: dict[str, Any] = {
            "seed": seed,
            "holdout_data": holdout_df,
            "target_col": target_col,
            "subgroup_query": subgroup_query,
        }

        if check_id in ("utility_tstr_ratio", "subgroup_utility_ci", "subgroup_utility_ci_width"):
            result: CheckResult = check_instance.run(train_df, synth_df, **check_kwargs)
        else:
            result = check_instance.run(real_df, synth_df, **check_kwargs)

        rec = EvidenceRecord(
            run_id=run_id,
            candidate_id=candidate_id,
            check_id=check_id,
            value=result.value,
            ci_low=result.ci_low,
            ci_high=result.ci_high,
            n=result.n,
            threshold_ref=str(threshold_spec),
            seed=seed,
            state=result.state,
            metadata=result.metadata,
        )
        evidence_records.append(rec)
        executed_check_ids.add(check_id)

    # Persist to SQLite evidence store
    store = EvidenceStore(db_path=db_path)
    store.record_batch(evidence_records)

    return evidence_records


def main(argv: list[str] | None = None) -> int:
    """CLI runner parsing arguments and executing checks pipeline."""
    parser = argparse.ArgumentParser(
        description="Run SynPassport assurance checks on synthetic dataset"
    )
    parser.add_argument("--data", required=True, help="Path to real dataset CSV")
    parser.add_argument("--synth", required=True, help="Path to synthetic dataset CSV")
    parser.add_argument("--policy", required=True, help="Policy ID or path to YAML")
    parser.add_argument("--holdout", default=None, help="Optional separate holdout CSV path")
    parser.add_argument("--db-path", default="./data/synpassport.db", help="SQLite DB path")
    parser.add_argument("--run-id", default=None, help="Assurance run ID")
    parser.add_argument("--candidate-id", default="candidate_001", help="Candidate identifier")
    parser.add_argument("--seed", type=int, default=1234, help="Deterministic seed")
    parser.add_argument("--target-col", default=None, help="Target column for downstream utility")
    parser.add_argument("--subgroup", default="age >= 65", help="Restricted subgroup expression")

    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    records = run_checks_pipeline(
        data_path=args.data,
        synth_path=args.synth,
        policy_id_or_path=args.policy,
        holdout_path=args.holdout,
        db_path=args.db_path,
        run_id=args.run_id,
        candidate_id=args.candidate_id,
        seed=args.seed,
        target_col=args.target_col,
        subgroup_query=args.subgroup,
    )

    print(f"Recorded {len(records)} evidence rows to SQLite at {args.db_path}:")
    for r in records:
        ci_str = f"[{r.ci_low:.3f}, {r.ci_high:.3f}]" if r.ci_low is not None else "None"
        print(f"  {r.check_id:<28} value={r.value:.4f}  CI={ci_str:<16} state={r.state}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
