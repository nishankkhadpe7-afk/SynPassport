# SynPassport — Architecture

> An assurance and enforcement layer between synthetic-data generation and real-world use.
> Question answered: *given this purpose and this policy, is there enough evidence to trust this dataset for this use — and can we enforce that decision?*

---

## 1. Goals and non-goals

**Goals**
- Purpose-scoped verdicts: one verdict per intended use, not one quality score.
- Agentic, adversarial assurance inside a locked policy.
- Enforceable output: hash-bound, Ed25519-signed Evidence Passport + verify SDK + loader guard + CI gate.

**Non-goals**
- Not a synthetic-data generator (sits on top of SDV/CTGAN).
- Does not prove privacy or certify legal compliance (DPDP, etc.).
- Does not replace human release approval.
- MVP scope: tabular data, one generator, one mission type.

---

## 2. Core principle: separation of powers

| Actor | May | May NOT |
|---|---|---|
| **LLM agent** | Interpret mission, pick a *predefined* policy profile, plan checks, choose whitelisted repairs, diagnose, explain | Write/edit thresholds, assign states, run arbitrary code, see holdout records |
| **Policy engine (deterministic)** | Convert evidence → PASS / WARNING / FAIL / INSUFFICIENT_EVIDENCE per use | Consult the LLM for a verdict |
| **Human** | Approve final release | — |

Any disallowed LLM proposal is rejected by the engine and logged into the passport (`agent_rejections`).

---

## 3. System overview

```
DATA MISSION (purpose, subgroups, privacy level, intended uses)
        │
        ▼
POLICY PROFILE (versioned YAML; policy hash locked BEFORE testing)
        │
        ▼
FEASIBILITY + SUFFICIENCY CHECK (size, schema, subgroup power analysis)
        │
        ▼
ASSURANCE AGENT (LLM, structured outputs, whitelisted tools)
   plan → generate candidate → run checks + attacks → diagnose → repair
        │
        ▼
EVIDENCE STORE (metrics, CIs, seeds, code version)
        │
        ▼
DETERMINISTIC POLICY ENGINE → per-use verdicts
        │
        ▼
EVIDENCE PASSPORT (canonical JSON, SHA-256, Ed25519)
        │
        ▼
HUMAN APPROVAL → verify() SDK / loader guard / CI gate
```

---

## 4. Components

### 4.1 Mission & Policy layer
- **Mission** (user-declared): `purpose`, `critical_subgroups`, `privacy_level`, `intended_uses`.
- **Policy profiles** (fixed, versioned YAML): `software-testing`, `ml-prototyping`, `ml-development` (`ml-sensitive-v1` in the report), `sensitive-research`, `public-release`.
- **Policy hash**: SHA-256 of canonical policy YAML, locked and recorded before any run.
- **Budget** (in policy): `max_candidates: 3`, `max_repairs: 2`.

### 4.2 Feasibility & sufficiency gate
- Validates schema, row count, subgroup sizes.
- Power analysis: minimum subgroup N required to meet `subgroup_utility_ci_width`.
- Short-circuits to `INSUFFICIENT_EVIDENCE` with an actionable "need ≥ N records" message when data can't support the claim.

### 4.3 Assurance agent
- LLM with tool-calling + structured (schema-validated) outputs.
- **Tool registry** (only these exist):
  - `generate_candidate(generator, params, seed)`
  - `run_check(check_id, candidate_id)`
  - `run_privacy_attack(attack_id, candidate_id)`
  - `propose_repair(action, params)` — whitelist: `tune_hyperparameters`, `switch_generator`, `enable_dp_training`
  - `explain(evidence_ids)` — reads the evidence store only
- **Loop**: plan → generate → evaluate → diagnose → repair (≤ budget) → finalize.
- Agent sees aggregate outputs only; the final holdout never enters its context.

### 4.4 Evaluation engine (8 pre-registered checks)

| # | Check | Method | Dimension |
|---|---|---|---|
| 1 | Schema validity | types, ranges, required fields, categorical domains | Validity |
| 2 | Marginal fidelity | KS / TV distance per feature | Fidelity |
| 3 | Correlation fidelity | pairwise correlation/association matrix distance | Fidelity |
| 4 | Downstream utility | TSTR vs train-on-real baseline | Utility |
| 5 | Subgroup utility | TSTR on critical subgroup + bootstrap CI | Subgroup |
| 6 | DCR vs holdout | synth→train vs synth→holdout distance distributions | Privacy |
| 7 | Membership inference | attack model, train vs holdout | Privacy |
| 8 | Sufficiency | subgroup N and CI width vs policy | Evidence strength |

### 4.5 Evidence store
- SQLite. Every metric stored with: value, CI, seed, candidate id, code version (git SHA), timestamp.
- Append-only from the checks' perspective; the explanation layer is read-only.

### 4.6 Deterministic policy engine
- Pure function: `(policy, evidence) → verdicts{use → state}`.
- No network, no LLM, no randomness. Same inputs → same verdicts (unit-testable, property-testable).
- State semantics:
  - **PASS**: all required checks meet thresholds.
  - **WARNING**: limitation that may be acceptable for the use (e.g., borderline subgroup utility).
  - **FAIL**: sufficient evidence that a required condition is violated.
  - **INSUFFICIENT_EVIDENCE**: evidence cannot support a conclusion either way (missing check or CI too wide). Missing evidence is never converted to PASS.

### 4.7 Passport service
- Canonical JSON (sorted keys, stable number format, UTF-8) → SHA-256 → Ed25519 signature.
- Dataset bound by SHA-256 of the exact file bytes.
- `human_approval`: `PENDING | APPROVED | REJECTED` (recorded, signed on approval).

### 4.8 Enforcement layer
- **verify SDK/CLI**: `passport verify data.csv passport.json --purpose clinical_ml` → checks signature, dataset hash, purpose support, human approval where policy requires it.
- **Loader guard**: `load_dataset(path, purpose=...)` raises if passport missing/tampered/unsupported.
- **CI gate**: GitHub Action wrapping the CLI; fails pipeline on invalid/unsupported passport.

### 4.9 API & UI
- FastAPI backend; Next.js dashboard with per-use verdict view, evidence drill-down, repair timeline, passport download, tamper-demo.

---

## 5. Data flow (single run)

1. User submits dataset + mission → API creates `run_id`.
2. Policy profile selected (agent picks from existing list; user may override) → policy hash locked.
3. Data split: **train / holdout (locked)**. Holdout is accessible only to the evaluation engine.
4. Feasibility/sufficiency gate runs.
5. Agent loop generates candidates and calls check/attack tools; results land in the evidence store.
6. On failure, agent proposes repair → engine validates against whitelist + budget → applied or rejected (logged).
7. Final candidate selected (best by policy-defined ordering, not by LLM opinion).
8. Policy engine computes per-use verdicts.
9. Passport built, canonicalized, signed.
10. Human approves/rejects; passport updated and re-signed.
11. Consumers verify via SDK / loader guard / CI.

---

## 6. Trust boundaries and threat model

| Threat | Mitigation |
|---|---|
| LLM weakens its own bar | Thresholds only in locked, hashed policy files; agent can't write them |
| Test-until-pass / p-hacking | Pre-registered checks, candidate cap (3), repair cap (2), counts recorded in passport |
| Holdout leakage to repair agent | Agent receives aggregates only; holdout access confined to eval engine process |
| Dataset tampering after issuance | SHA-256 binding; verification fails on 1-cell change |
| Passport tampering | Ed25519 signature over canonical JSON |
| Prompt injection via dataset values/column names | Column names/values never placed raw into agent prompts without sanitization; agent has no code exec; tool args schema-validated |
| Forged issuer | **Out of MVP scope** — key distribution / trust roots are Phase 4 (documented, not oversold) |
| Non-determinism | Fixed seeds, pinned deps, Docker, recorded code version |

---

## 7. Passport schema (v0)

```json
{
  "passport_version": "0.1",
  "dataset": {"name": "...", "sha256": "..."},
  "mission": {"purpose": "...", "subgroups": ["age>=65"], "privacy_level": "high"},
  "policy": {"id": "ml-sensitive-v1", "sha256": "..."},
  "run": {"code_version": "git:...", "seeds": [1234, 5678],
          "candidates_evaluated": 3, "repairs_attempted": 1},
  "evidence": [{"check": "dcr_vs_holdout", "state": "PASS", "value": 0.0, "ci": [0, 0], "threshold": "..."}],
  "repairs": [{"action": "tune_hyperparameters", "params": {}, "outcome": "..."}],
  "agent_rejections": [{"proposal": "raise privacy threshold", "reason": "policy locked"}],
  "verdicts": {"software_testing": "PASS", "ml_prototyping": "PASS", "clinical_ml": "INSUFFICIENT_EVIDENCE"},
  "human_approval": "PENDING",
  "issued_at": "ISO-8601",
  "signature": {"alg": "Ed25519", "key_id": "...", "value": "..."}
}
```

Signing input = canonical JSON of everything except `signature`.

---

## 8. Repository layout

```
synpassport/
├─ policies/                 # versioned YAML profiles
├─ src/synpassport/
│  ├─ mission/               # mission schema, validation
│  ├─ policy/                # loader, hasher, deterministic engine
│  ├─ checks/                # 8 checks + privacy attacks
│  ├─ evidence/              # SQLite store, models
│  ├─ generators/            # SDV wrappers (CTGAN, Gaussian Copula, DP option)
│  ├─ agent/                 # loop, tool registry, whitelist, prompts
│  ├─ passport/              # canonicalize, hash, sign, verify
│  ├─ sdk/                   # verify(), load_dataset()
│  ├─ cli/                   # `passport` command
│  └─ api/                   # FastAPI app
├─ web/                      # Next.js dashboard
├─ .github/actions/verify/   # CI gate
├─ replay/                   # cached candidates + LLM responses for demo
├─ tests/
├─ docker/ + docker-compose.yml
└─ docs/ (architecture.md, design.md, instructions.md)
```

---

## 9. Technology stack

| Layer | Choice |
|---|---|
| Frontend | React / Next.js |
| Backend | Python, FastAPI |
| Agent | LLM API, tool-calling, structured outputs |
| Synthetic data | SDV (CTGAN or Gaussian Copula) |
| Evaluation | SDMetrics, scikit-learn, custom bootstrap + privacy checks (Anonymeter optional) |
| Storage | SQLite |
| Security | SHA-256, Ed25519, canonical JSON |
| Deployment | Docker, seeded runs, public repo |

---

## 10. Build order (dependency-driven)

1. Policy engine (+ policy YAML, hashing)
2. Checks (8)
3. Passport: canonical JSON, hash, signature
4. Verify SDK + loader guard (+ CLI, CI action)
5. Agent loop
6. UI

A working non-agent pipeline (steps 1–4 driven by a fixed script) is the fallback if the live agent misbehaves.

---

## 11. Extension points (post-MVP)

- More generators / time-series; stronger attacks; better uncertainty estimation (Phase 2).
- RBAC, on-prem, audit history (Phase 3).
- Third-party auditors, remote verification, key distribution and trust roots (Phase 4).
- TEE-based confidential assurance (Phase 5).
