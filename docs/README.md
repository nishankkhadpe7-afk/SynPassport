# SynPassport Technical Documentation

Welcome to the technical documentation for **SynPassport** — the verifiable cryptographic assurance and passport system for tabular synthetic data.

---

## Component Documentation Index

Each core component of SynPassport features dedicated technical documentation:

- 🛡️ **[Cryptographic Passport Engine (`synpassport.passport`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/README.md)**
  - Ed25519 signing, RFC 8785 canonical JSON serialization, dataset SHA-256 byte hashing, DSSE / In-toto interop formats.
- 🔑 **[Trust Model & Governance Guide](file:///Users/vanshjain/Desktop/SynPassport/docs/TRUST_MODEL.md)**
  - Trusted Key Registry, Key ID derivation, key revocation, key expiration, and threat model analysis.
- 📊 **[Assurance & Statistical Checks Pipeline (`synpassport.checks`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/checks/README.md)**
  - All 8 statistical checks: schema validity, marginal distance, correlation Frobenius norm, TSTR utility ratio, subgroup CIs, DCR vs holdout, MIA AUC, and sample sufficiency.
- 📜 **[Immutable Policy Engine (`synpassport.policy`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/README.md)**
  - Policy YAML schema, canonical policy hashing, purpose-based multi-use verdict matrix.
- 🤖 **[Autonomous Assurance Agent (`synpassport.agent`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/agent/README.md)**
  - Plan-Generate-Evaluate-Repair state machine, LLM diagnosis, whitelisted repairs, replay caching, and prompt injection defenses.
- 🔒 **[Verification SDK & Data Guard (`synpassport.sdk`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/README.md)**
  - 7-step fail-closed verification pipeline, TOCTOU-safe dataset loader (`guard.py`), and error reason codes.
- 💻 **[Command-Line Interface (`synpassport.cli`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/cli/README.md)**
  - `passport verify`, `issue`, `approve`, `inspect`, and `keyreg` subcommands.
- 🌐 **[REST API & Async Server (`synpassport.api`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/README.md)**
  - FastAPI web server, background runs, SSE event streaming, zero-disk verification, and approval auth.
- 🗄️ **[Evidence Store (`synpassport.evidence`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/evidence/README.md)**
  - SQLite persistence layer for structured audit records.
- ⚙️ **[Synthetic Data Generators (`synpassport.generators`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/generators/README.md)**
  - GaussianCopula, CTGAN, and Differential Privacy (DP) training integrations.
- 🎯 **[Mission Profile (`synpassport.mission`)](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/mission/README.md)**
  - Domain intent specification.
- 🔐 **[Security Architecture & Defenses](file:///Users/vanshjain/Desktop/SynPassport/docs/SECURITY.md)**
  - Complete security model covering TOCTOU mitigations, prompt sanitization, cryptographically locked policies, and token authentication.
- 📜 **[Detailed Changelog & Commit Log](file:///Users/vanshjain/Desktop/SynPassport/CHANGELOG.md)**
  - Full history of all commits, features, and file modifications over time. Auto-updates on every commit.

