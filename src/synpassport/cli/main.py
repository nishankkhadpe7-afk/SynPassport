"""Command-line interface for SynPassport operations.

Provides four subcommands per design.md §7:
- passport verify <data> <passport> --purpose <purpose> [--allow-warning] [--json]
- passport issue --data <data> --synth <synth> --policy <policy> [--output <p>] [--json]
- passport approve <passport> --approver <name> --key <key> [--output <path>] [--json]
- passport inspect <passport> [--json]

Exit codes:
- 0: OK (verified / operation succeeded)
- 1: Unsupported / tampered (SIGNATURE_INVALID, DATASET_HASH_MISMATCH, ...)
- 2: Malformed / usage error (PASSPORT_MALFORMED, PURPOSE_UNKNOWN, bad args, ...)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from synpassport.checks.run import run_checks_pipeline
from synpassport.passport.builder import approve_passport, build_passport
from synpassport.passport.keygen import generate_keypair
from synpassport.passport.trust import TrustedKeyRegistry
from synpassport.policy.engine import evaluate_policy
from synpassport.policy.loader import load_policy
from synpassport.sdk.verify import verify

__all__ = ["handle_approve", "handle_inspect", "handle_issue", "handle_keyreg", "handle_verify", "main"]


def _exit_code_for_reason(reason_code: str) -> int:
    """Map verification reason code to standard CLI exit code."""
    if reason_code == "OK":
        return 0
    if reason_code in (
        "SIGNATURE_INVALID",
        "KEY_UNTRUSTED",
        "PASSPORT_EXPIRED",
        "DATASET_HASH_MISMATCH",
        "PURPOSE_UNSUPPORTED",
        "APPROVAL_MISSING",
    ):
        return 1
    # PASSPORT_MALFORMED, PURPOSE_UNKNOWN, or other usage errors
    return 2


def handle_verify(args: argparse.Namespace) -> int:
    """Execute passport verification command."""
    data_path = Path(args.data)
    pass_path = Path(args.passport)

    if not data_path.is_file():
        if args.json:
            print(
                json.dumps(
                    {
                        "valid": False,
                        "reason_code": "DATASET_HASH_MISMATCH",
                        "details": {"error": f"Dataset file not found: {data_path}"},
                    }
                )
            )
        else:
            print(f"Error: Dataset file not found: {data_path}", file=sys.stderr)
        return 1

    if not pass_path.is_file():
        if args.json:
            print(
                json.dumps(
                    {
                        "valid": False,
                        "reason_code": "PASSPORT_MALFORMED",
                        "details": {"error": f"Passport file not found: {pass_path}"},
                    }
                )
            )
        else:
            print(f"Error: Passport file not found: {pass_path}", file=sys.stderr)
        return 2

    pub_key = args.public_key or getattr(args, "key", None)
    registry_path = getattr(args, "registry", None)
    max_age_days = getattr(args, "max_age_days", None)

    result = verify(
        dataset_path=data_path,
        passport_path=pass_path,
        purpose=args.purpose,
        allow_warning=args.allow_warning,
        public_key=pub_key,
        registry_path=registry_path,
        max_age_days=max_age_days,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        if result.valid:
            print(
                f"VERIFIED: Purpose '{args.purpose}' is supported and authentic. "
                f"[{result.reason_code}]"
            )
        else:
            err = result.details.get("error", "Verification condition not met")
            print(f"REJECTED: [{result.reason_code}] {err}", file=sys.stderr)

    return _exit_code_for_reason(result.reason_code)


def handle_issue(args: argparse.Namespace) -> int:
    """Execute checks and issue a signed Evidence Passport."""
    try:
        data_path = Path(args.data)
        synth_path = Path(args.synth)
        policy_ref = args.policy
        out_path = Path(args.output or "passport.json")

        if not data_path.is_file():
            print(f"Error: Real dataset file not found: {data_path}", file=sys.stderr)
            return 2
        if not synth_path.is_file():
            print(f"Error: Synthetic dataset file not found: {synth_path}", file=sys.stderr)
            return 2

        # 1. Run checks pipeline
        evidence_records = run_checks_pipeline(
            data_path=data_path,
            synth_path=synth_path,
            policy_id_or_path=policy_ref,
            holdout_path=args.holdout,
            candidate_id=args.candidate_id or "candidate_001",
            seed=args.seed or 1234,
        )

        # 2. Evaluate policy engine
        policy = load_policy(policy_ref)
        verdicts = evaluate_policy(policy, evidence_records)

        # 3. Resolve mission
        mission: dict[str, Any] = {
            "purpose": args.purpose or "assurance evaluation",
            "intended_uses": list(verdicts.keys()),
        }
        if args.mission and Path(args.mission).is_file():
            import yaml

            mission = yaml.safe_load(Path(args.mission).read_text(encoding="utf-8"))

        # 4. Build passport
        passport = build_passport(
            dataset_path=synth_path,
            mission=mission,
            policy=policy,
            evidence=evidence_records,
            verdicts=verdicts,
            signing_key=args.key,
            key_id=args.key_id,
        )

        out_path.write_text(passport.to_json(indent=2), encoding="utf-8")

        if args.json:
            print(passport.to_json(indent=2))
        else:
            print(f"Issued Evidence Passport written to: {out_path}")
            for use, v in verdicts.items():
                print(f"  - {use}: {v}")

        return 0
    except Exception as exc:
        print(f"Error during passport issuance: {exc}", file=sys.stderr)
        return 2


def handle_approve(args: argparse.Namespace) -> int:
    """Execute human approval and re-signing of an Evidence Passport."""
    try:
        pass_path = Path(args.passport)
        if not pass_path.is_file():
            print(f"Error: Passport file not found: {pass_path}", file=sys.stderr)
            return 2

        content = pass_path.read_text(encoding="utf-8")
        data = json.loads(content)

        out_path = Path(args.output) if args.output else pass_path

        updated_data = approve_passport(
            passport=data,
            approver=args.approver,
            signing_key=args.key,
            key_id=args.key_id,
        )

        out_path.write_text(json.dumps(updated_data, indent=2), encoding="utf-8")

        if args.json:
            print(json.dumps(updated_data, indent=2))
        else:
            print(f"Passport approved by {args.approver} and re-signed. Written to: {out_path}")

        return 0
    except Exception as exc:
        print(f"Error during passport approval: {exc}", file=sys.stderr)
        return 2


def handle_keyreg(args: argparse.Namespace) -> int:
    """Manage the trusted key registry (enroll, revoke, list)."""
    try:
        reg_path = Path(args.registry)
        registry = TrustedKeyRegistry.from_file(reg_path)

        if args.keyreg_command == "enroll":
            key_path = Path(args.public_key)
            if not key_path.is_file():
                print(f"Error: public key file not found: {key_path}", file=sys.stderr)
                return 2
            key_bytes = key_path.read_bytes()
            fp = registry.add_key(
                label=args.label,
                public_key=key_bytes,
                expires_at=getattr(args, "expires_at", None),
                comment=getattr(args, "comment", ""),
            )
            registry.save(reg_path)
            print(f"Enrolled key '{args.label}' with fingerprint: {fp}")
            print(f"Registry saved to: {reg_path}")

        elif args.keyreg_command == "revoke":
            reason = getattr(args, "reason", "")
            registry.revoke_key(args.label, reason=reason)
            registry.save(reg_path)
            print(f"Revoked key '{args.label}'. Registry saved to: {reg_path}")

        elif args.keyreg_command == "list":
            entries = registry.active_entries()
            if not entries:
                print("No active keys in registry.")
            else:
                print(f"Active keys in {reg_path}:")
                for label, entry in entries.items():
                    fp = str(entry.get("fingerprint", ""))[:16]
                    added = entry.get("added_at", "unknown")
                    expires = entry.get("expires_at") or "never"
                    comment = entry.get("comment", "")
                    print(f"  [{label}] fp={fp}... added={added} expires={expires} {comment}")

        elif args.keyreg_command == "generate":
            # Convenience: generate keypair AND enroll the public key
            out_dir = Path(getattr(args, "output_dir", "./keys"))
            priv_path, pub_path, key_id = generate_keypair(out_dir, key_name=args.label)
            pub_bytes = pub_path.read_bytes()
            fp = registry.add_key(
                label=args.label,
                public_key=pub_bytes,
                expires_at=getattr(args, "expires_at", None),
                comment=getattr(args, "comment", "auto-generated"),
            )
            registry.save(reg_path)
            print(f"Generated keypair for '{args.label}'.")
            print(f"  Private key: {priv_path}")
            print(f"  Public key:  {pub_path}")
            print(f"  Fingerprint: {fp}")
            print(f"  Registry:    {reg_path}")

        return 0
    except Exception as exc:
        print(f"Error in keyreg operation: {exc}", file=sys.stderr)
        return 2


def handle_inspect(args: argparse.Namespace) -> int:
    """Display contents and verification metrics of an Evidence Passport."""
    try:
        pass_path = Path(args.passport)
        if not pass_path.is_file():
            print(f"Error: Passport file not found: {pass_path}", file=sys.stderr)
            return 2

        content = pass_path.read_text(encoding="utf-8")
        data = json.loads(content)

        if args.json:
            print(json.dumps(data, indent=2))
            return 0

        print(f"--- Evidence Passport: {pass_path.name} ---")
        print(f"Passport Version: {data.get('passport_version', 'unknown')}")
        print(f"Issued At:        {data.get('issued_at', 'unknown')}")
        dataset = data.get("dataset", {})
        print(f"Dataset Name:     {dataset.get('name', 'unknown')}")
        print(f"Dataset SHA-256:  {dataset.get('sha256', 'unknown')}")
        policy = data.get("policy", {})
        pol_id = policy.get("id", "unknown")
        pol_sha = str(policy.get("sha256", "unknown"))[:16]
        print(f"Policy ID:        {pol_id} (SHA-256: {pol_sha}...)")

        print("\nVerdicts:")
        for purpose, verdict in data.get("verdicts", {}).items():
            print(f"  - {purpose:<20}: {verdict}")

        approval = data.get("human_approval", {})
        if isinstance(approval, dict):
            status = approval.get("status", "unknown")
            approver = approval.get("approver") or "None"
            print(f"\nHuman Approval:   {status} (Approver: {approver})")
        else:
            print(f"\nHuman Approval:   {approval}")

        signatures = data.get("audit_signatures", [])
        print(f"Prior Signatures: {len(signatures)} archived")

        sig = data.get("signature", {})
        sig_alg = sig.get("alg", "none")
        sig_kid = str(sig.get("key_id", ""))[:16]
        print(f"Current Sig Alg:  {sig_alg} (Key ID: {sig_kid}...)")

        return 0
    except Exception as exc:
        print(f"Error inspecting passport: {exc}", file=sys.stderr)
        return 2


def create_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="passport",
        description="SynPassport CLI: verify, issue, approve, inspect Evidence Passports.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: verify
    verify_p = subparsers.add_parser(
        "verify", help="Verify dataset and passport against intended purpose"
    )
    verify_p.add_argument("data", help="Path to synthetic dataset CSV")
    verify_p.add_argument("passport", help="Path to Evidence Passport JSON")
    verify_p.add_argument(
        "--purpose", required=True, help="Intended purpose (e.g. clinical_ml, software_testing)"
    )
    verify_p.add_argument(
        "--allow-warning", action="store_true", help="Permit WARNING verdicts as acceptable"
    )
    verify_p.add_argument(
        "--public-key", "--key", dest="public_key", help="Path to Ed25519 public key PEM"
    )
    verify_p.add_argument(
        "--registry",
        dest="registry",
        help="Path to trusted key registry JSON (preferred over --public-key for production)",
    )
    verify_p.add_argument(
        "--max-age-days",
        dest="max_age_days",
        type=int,
        default=None,
        help="Reject passports older than this many days",
    )
    verify_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # Subcommand: issue
    issue_p = subparsers.add_parser(
        "issue", help="Execute evaluation checks and issue signed passport"
    )
    issue_p.add_argument("--data", required=True, help="Path to real reference dataset CSV")
    issue_p.add_argument("--synth", required=True, help="Path to synthetic dataset CSV")
    issue_p.add_argument("--policy", required=True, help="Policy ID or path to policy YAML")
    issue_p.add_argument("--mission", help="Path to mission YAML declaration")
    issue_p.add_argument("--purpose", help="Primary mission purpose name")
    issue_p.add_argument("--holdout", help="Optional separate holdout CSV path")
    issue_p.add_argument(
        "--output", "-o", help="Output path for passport JSON (default: passport.json)"
    )
    issue_p.add_argument("--key", help="Path to Ed25519 private key PEM for signing")
    issue_p.add_argument("--key-id", help="Explicit public key ID")
    issue_p.add_argument("--candidate-id", help="Candidate identifier")
    issue_p.add_argument("--seed", type=int, default=1234, help="Evaluation random seed")
    issue_p.add_argument("--json", action="store_true", help="Output emitted passport as JSON")

    # Subcommand: approve
    approve_p = subparsers.add_parser(
        "approve", help="Execute human release approval and re-sign passport"
    )
    approve_p.add_argument("passport", help="Path to Evidence Passport JSON")
    approve_p.add_argument("--approver", required=True, help="Approver identity or email")
    approve_p.add_argument(
        "--key", required=True, help="Path to Ed25519 private key PEM for re-signing"
    )
    approve_p.add_argument("--key-id", help="Explicit public key ID")
    approve_p.add_argument(
        "--output", "-o", help="Optional output path (defaults to overwriting input passport)"
    )
    approve_p.add_argument("--json", action="store_true", help="Output updated passport as JSON")

    # Subcommand: inspect
    inspect_p = subparsers.add_parser(
        "inspect", help="Display summary metrics and verdicts of a passport"
    )
    inspect_p.add_argument("passport", help="Path to Evidence Passport JSON")
    inspect_p.add_argument("--json", action="store_true", help="Output raw passport JSON")

    # Subcommand: keyreg (trusted key registry management)
    keyreg_p = subparsers.add_parser(
        "keyreg", help="Manage the trusted issuer key registry"
    )
    keyreg_p.add_argument(
        "--registry", required=True, dest="registry",
        help="Path to trusted key registry JSON file"
    )
    keyreg_sub = keyreg_p.add_subparsers(dest="keyreg_command", required=True)

    enroll_p = keyreg_sub.add_parser("enroll", help="Enroll a public key into the registry")
    enroll_p.add_argument("--label", required=True, help="Unique label for this key")
    enroll_p.add_argument("--public-key", required=True, dest="public_key",
                          help="Path to Ed25519 public key PEM")
    enroll_p.add_argument("--expires-at", dest="expires_at",
                          help="Optional ISO-8601 expiry datetime")
    enroll_p.add_argument("--comment", default="", help="Audit comment")

    revoke_p = keyreg_sub.add_parser("revoke", help="Revoke a key in the registry")
    revoke_p.add_argument("--label", required=True, help="Label of the key to revoke")
    revoke_p.add_argument("--reason", default="", help="Revocation reason for audit")

    keyreg_sub.add_parser("list", help="List active keys in the registry")

    gen_p = keyreg_sub.add_parser(
        "generate", help="Generate a new Ed25519 keypair and enroll the public key"
    )
    gen_p.add_argument("--label", required=True, help="Unique label for this key")
    gen_p.add_argument("--output-dir", dest="output_dir", default="./keys",
                       help="Directory to write generated key files")
    gen_p.add_argument("--expires-at", dest="expires_at",
                       help="Optional ISO-8601 expiry datetime")
    gen_p.add_argument("--comment", default="auto-generated", help="Audit comment")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI main entrypoint."""
    parser = create_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code != 0 else 0

    if args.command == "verify":
        return handle_verify(args)
    if args.command == "issue":
        return handle_issue(args)
    if args.command == "approve":
        return handle_approve(args)
    if args.command == "inspect":
        return handle_inspect(args)
    if args.command == "keyreg":
        return handle_keyreg(args)

    return 2


if __name__ == "__main__":
    sys.exit(main())
