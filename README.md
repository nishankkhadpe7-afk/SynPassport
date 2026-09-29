# SynPassport

> Purpose-bound assurance agent for synthetic data that issues signed, hash-bound Evidence Passports.

Question answered: *given this purpose and this policy, is there enough evidence to trust this dataset for this use — and can we enforce that decision?*

---

## Core Guarantees & Non-Claims

1. **Separation of Powers**:
   - The LLM agent explores, diagnoses, and suggests whitelisted parameter repairs.
   - The deterministic policy engine computes and issues all per-use verdicts. The LLM never assigns verdicts.
   - Missing or errored evidence resolves to `INSUFFICIENT_EVIDENCE`, never `PASS`.

2. **Enforceability**:
   - Every Evidence Passport is canonicalized, hashed with SHA-256, and signed with Ed25519.
   - Datasets are bound by the SHA-256 hash of raw file bytes.

3. **Explicit Non-Claims**:
   - Does not provide absolute mathematical proof of secrecy or confidentiality.
   - Does not certify statutory regulatory adherence.
   - Does not replace human release approval when required by policy.
   - Evaluates empirical evidence under specified attacks and pre-registered statistical checks.

---

## Repository Layout

- `policies/`: Versioned policy profiles (YAML).
- `src/synpassport/`: Core assurance packages:
  - `mission/`: Mission schema declaration and restricted expression parsing.
  - `policy/`: Policy profile models, hashing, and deterministic evaluation engine.
  - `checks/`: Evaluation checks and adversarial attack implementations.
  - `evidence/`: SQLite append-only evidence store and models.
  - `generators/`: Synthetic data generator wrappers.
  - `agent/`: Assurance agent orchestration loop with strict tool and repair whitelists.
  - `passport/`: Canonical JSON serialization, Ed25519 signing, and schema verification.
  - `sdk/`: Programmatic verification SDK and dataset loader guard.
  - `cli/`: `passport` command-line interface.
  - `api/`: FastAPI service.
- `web/`: Next.js web dashboard.
- `.github/actions/verify/`: CI gate composite action.
- `replay/`: Deterministic cached runs for demonstration.
- `tests/`: Unit, property, and integration tests.
- `docker/`: Docker and container configurations.

---

## Development

```bash
pip install -e ".[dev]"
cp .env.example .env
pytest -q
ruff check .
mypy src
```
