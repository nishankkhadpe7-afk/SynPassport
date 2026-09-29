"""Command-line interface for SynPassport operations.

Provides commands for passport verification, issuance, approval, and inspection:
- passport verify <data> <passport> --purpose <purpose>
- passport issue --data <data> --mission <mission> --policy <policy>
- passport approve <passport> --approver <name>
- passport inspect <passport>
"""

import sys

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint function."""
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("SynPassport CLI: verify, issue, approve, inspect")
        return 0
    cmd = args[0]
    if cmd == "verify":
        print("Verification command stub")
        return 0
    elif cmd == "issue":
        print("Issue command stub")
        return 0
    elif cmd == "approve":
        print("Approval command stub")
        return 0
    elif cmd == "inspect":
        print("Inspect command stub")
        return 0
    else:
        print(f"Unknown command: {cmd}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
