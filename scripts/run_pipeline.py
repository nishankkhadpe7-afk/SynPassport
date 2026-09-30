"""Scripted end-to-end non-agent assurance pipeline (Step 4 checkpoint).

Executes the full pipeline without LLM intervention:
Fixed generator + fixed parameters -> Evaluation checks -> Deterministic policy engine
-> Passport generation -> Human approval re-signing -> Verification & loader guard.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from synpassport.checks.run import run_checks_pipeline
from synpassport.generators.sdv_wrapper import GaussianCopulaGenerator
from synpassport.passport.builder import approve_passport, build_passport
from synpassport.passport.keygen import generate_keypair
from synpassport.policy.engine import evaluate_policy
from synpassport.policy.loader import load_policy
from synpassport.sdk.guard import load_dataset
from synpassport.sdk.verify import verify


def run_scripted_pipeline(output_dir: str | Path = "./data/scripted_pipeline") -> int:
    """Run full synthetic generation and assurance pipeline."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("==========================================================")
    print("SynPassport: Scripted End-to-End Assurance Pipeline")
    print("==========================================================")

    # 1. Synthesize reference dataset
    print("\n[Step 1] Creating baseline training dataset...")
    real_csv = out_dir / "real_training_data.csv"
    real_df = pd.DataFrame(
        {
            "age": [25, 45, 68, 72, 33, 58, 62, 77, 29, 51] * 10,
            "cholesterol": [180.0, 220.0, 240.0, 210.0, 195.0, 250.0, 230.0, 260.0, 190.0, 215.0]
            * 10,
            "resting_bp": [120, 135, 145, 130, 118, 140, 138, 150, 122, 128] * 10,
            "target": [0, 1, 1, 1, 0, 1, 0, 1, 0, 0] * 10,
        }
    )
    real_df.to_csv(real_csv, index=False)
    print(f"  Real data saved: {real_csv} (N={len(real_df)})")

    # 2. Fixed generator with fixed parameters and seed
    print("\n[Step 2] Training fixed generator (Gaussian Copula)...")
    generator = GaussianCopulaGenerator(seed=1234)
    generator.fit(real_df)
    synth_df = generator.sample(num_rows=len(real_df))
    synth_csv = out_dir / "synthetic_candidate.csv"
    synth_df.to_csv(synth_csv, index=False)
    print(f"  Synthetic data generated: {synth_csv} (N={len(synth_df)})")

    # 3. Cryptographic keypair generation
    print("\n[Step 3] Resolving cryptographic signing keys...")
    keys_dir = out_dir / "keys"
    priv_key_path, pub_key_path, key_id = generate_keypair(keys_dir, key_name="pipeline_key")
    print(f"  Signing Key: {priv_key_path.name}")
    print(f"  Public Key:  {pub_key_path.name} (Key ID: {key_id[:16]}...)")

    # 4. Evaluation checks execution
    print("\n[Step 4] Running 8 evaluation checks against policy 'software-testing'...")
    policy_id = "software-testing"
    evidence_records = run_checks_pipeline(
        data_path=real_csv,
        synth_path=synth_csv,
        policy_id_or_path=policy_id,
        db_path=out_dir / "evidence.db",
        candidate_id="fixed_candidate_001",
        seed=1234,
        target_col="target",
    )
    print(f"  Executed checks, recorded {len(evidence_records)} evidence items into SQLite")

    # 5. Deterministic policy engine evaluation
    print("\n[Step 5] Evaluating policy engine verdicts...")
    policy = load_policy(policy_id)
    verdicts = evaluate_policy(policy, evidence_records)
    for purpose, state in verdicts.items():
        print(f"  Verdict [{purpose}]: {state}")

    # 6. Build Evidence Passport
    print("\n[Step 6] Building and signing initial Evidence Passport...")
    passport_path = out_dir / "synthetic_candidate.passport.json"
    mission = {
        "purpose": "software testing validation",
        "intended_uses": list(verdicts.keys()),
        "privacy_level": "medium",
    }
    passport = build_passport(
        dataset_path=synth_csv,
        mission=mission,
        policy=policy,
        evidence=evidence_records,
        verdicts=verdicts,
        signing_key=priv_key_path,
        key_id=key_id,
    )
    passport_path.write_text(passport.to_json(indent=2), encoding="utf-8")
    print(f"  Initial passport written to: {passport_path}")
    print(f"  Human approval status: {passport['human_approval']['status']}")

    # 7. Human approval flow
    print("\n[Step 7] Executing human release approval flow...")
    approve_passport(
        passport=passport,
        approver="lead_engineer@example.org",
        signing_key=priv_key_path,
        key_id=key_id,
    )
    passport_path.write_text(passport.to_json(indent=2), encoding="utf-8")
    print(f"  Approval status flipped to: {passport['human_approval']['status']}")
    print(f"  Approver recorded: {passport['human_approval']['approver']}")
    print(f"  Prior signatures in audit trail: {len(passport['audit_signatures'])}")

    # 8. Verification SDK
    print("\n[Step 8] Verifying Evidence Passport via SDK verify()...")
    res = verify(
        dataset_path=synth_csv,
        passport_path=passport_path,
        purpose="software_testing",
        public_key=pub_key_path,
    )
    print(f"  Verification Result: valid={res.valid}, reason={res.reason_code}")
    if not res.valid:
        print(f"  Error details: {res.details}")
        return 1

    # 9. Protected dataset loader guard
    print("\n[Step 9] Testing dataset loader guard load_dataset()...")
    loaded_df = load_dataset(
        dataset_path=synth_csv,
        passport_path=passport_path,
        purpose="software_testing",
        public_key=pub_key_path,
    )
    print(
        f"  Loader guard returned DataFrame (N={len(loaded_df)}, "
        f"cols={list(loaded_df.columns)})"
    )

    print("\n==========================================================")
    print("SUCCESS: End-to-end assurance pipeline verified completely!")
    print("==========================================================")
    return 0


def main() -> None:
    """CLI runner for scripted pipeline."""
    code = run_scripted_pipeline()
    sys.exit(code)


if __name__ == "__main__":
    main()
