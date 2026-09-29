# SynPassport — Design

Detailed design decisions for each subsystem. Companion to `architecture.md`.

---

## 1. Design principles

1. **No LLM-issued pass.** Verdicts come from a deterministic engine.
2. **Purpose first.** Every check exists because a purpose requires it.
3. **Explicit uncertainty.** Every subgroup metric has a CI; wide CI → `INSUFFICIENT_EVIDENCE`, never a weak pass.
4. **Evidence, not proof.** Privacy results are phrased as risk evidence.
5. **Pre-registration.** Policy hash + check list locked before any run.
6. **Actionable refusals.** Insufficient evidence always says how much more is needed.
7. **Human accountable.** Final release approval is a person.

---

## 2. Data models

### 2.1 Mission
```yaml
mission:
  purpose: train heart-failure prediction model
  target: hf_event                 # label column for TSTR
  critical_subgroups: ["age >= 65"]
  privacy_level: high              # low | medium | high
  intended_uses: [software_testing, ml_prototyping, clinical_ml]
```
Validation: subgroup expressions parsed with a restricted grammar (column, comparator, literal) — **no `eval`**.

### 2.2 Policy profile
```yaml
id: ml-sensitive-v1
version: 1
requires:
  schema_validity: pass
  marginal_fidelity:        {min: 0.90}
  correlation_fidelity:     {min: 0.85}
  utility_tstr_ratio:       {min: 0.90}
  subgroup_utility_ci_width: {max: 0.15}
  privacy_dcr_vs_holdout:   not_closer_than_holdout
  membership_inference_auc: {max: 0.55}
budget: {max_candidates: 3, max_repairs: 2}
uses:                       # which checks each use needs + warning bands
  software_testing: [schema_validity, marginal_fidelity]
  ml_prototyping:   [schema_validity, marginal_fidelity, correlation_fidelity, utility_tstr_ratio]
  clinical_ml:      [all]
warning_bands:
  utility_tstr_ratio: {min: 0.85}      # 0.85–0.90 → WARNING
human_approval: required
```
Hash = SHA-256 over canonical (sorted-key, normalized) serialization.

### 2.3 Evidence record
```
{ run_id, candidate_id, check_id, value, ci_low, ci_high, n, threshold_ref,
  seed, code_version, created_at }
```

---

## 3. Policy engine design

### 3.1 Per-check state function
For each check `c` with threshold `t` and evidence `e`:

| Condition | State |
|---|---|
| Evidence missing / check not run / error | `INSUFFICIENT_EVIDENCE` |
| Metric CI width > policy CI limit | `INSUFFICIENT_EVIDENCE` |
| Metric (by CI) clearly violates `t` | `FAIL` |
| Metric within `warning_bands` | `WARNING` |
| Metric meets `t` with adequate CI | `PASS` |

Decision rule on CIs: use the bound, not the point estimate, for FAIL/PASS claims where the policy says so (e.g., pass only if the lower CI bound ≥ threshold; fail only if the upper bound < threshold; otherwise insufficient).

### 3.2 Aggregation per use
`use_state = worst(check_states for required checks)` with severity order:
`FAIL > INSUFFICIENT_EVIDENCE > WARNING > PASS`.

### 3.3 Properties (to test)
- Deterministic and pure.
- Monotone: worsening any metric never improves a verdict.
- Missing evidence never yields PASS.
- Adding a check to a use's requirements can only worsen or keep its verdict.

---

## 4. Check designs

### 4.1 Schema validity
Types, ranges, nullability, categorical domains, key/relationship integrity. Score = fraction of rows valid; requirement is `pass` only at 100% (policy-configurable).

### 4.2 Marginal fidelity
Per-feature: KS complement (numeric), TV complement (categorical). Aggregate = mean; also report worst feature.

### 4.3 Correlation fidelity
Pearson (numeric), Cramér's V / correlation ratio (mixed). Score = `1 − normalized_distance(corr_real, corr_synth)`.

### 4.4 Downstream utility (TSTR)
- Train model A on synthetic, model B on real train; both evaluated on **real holdout**.
- `tstr_ratio = metric(A) / metric(B)` (AUROC or task-appropriate metric).
- Fixed model family and hyperparameters (e.g., logistic regression + gradient boosting) declared in policy.

### 4.5 Subgroup utility
Same as TSTR, restricted to subgroup rows of holdout. **Bootstrap** (≥1000 resamples, fixed seed) → 95% CI. Report `ci_width`.

### 4.6 DCR vs holdout (baseline-corrected)
- Compute distance-to-closest-record: synth→train and synth→holdout.
- Compare distributions (e.g., fraction of synth records closer to train than to holdout, and a one-sided test / effect size).
- `FAIL` if synthetic is systematically closer to train than holdout beyond tolerance.
- Holdout must be the same size as train sample used (or subsampled) to avoid bias.

### 4.7 Membership inference
- Attack model trained (on shadow data) to distinguish train vs holdout using synthetic data as reference.
- Report AUC with bootstrap CI; `FAIL` if lower CI bound > 0.55 threshold, `INSUFFICIENT_EVIDENCE` if CI spans threshold.

### 4.8 Sufficiency check
- Subgroup N and projected CI width vs policy.
- Power analysis output: `min_N_required` for the policy's tolerance. Surfaced in UI and passport.

---

## 5. Agent design

### 5.1 Interaction pattern
Structured-output loop. Each turn the LLM returns JSON validated against a schema:
```json
{ "thought_summary": "...", "action": "run_check|generate_candidate|propose_repair|finalize",
  "args": { ... } }
```
Invalid JSON, unknown tool, or schema mismatch → rejected, logged, retried (bounded).

### 5.2 Guardrail enforcement (in code, not prompts)
| Rule | Enforcement point |
|---|---|
| Tool registry only | dispatcher rejects unknown `action` |
| Repair whitelist (3 actions) | `propose_repair` validator |
| Budget (3 candidates / 2 repairs) | run-state counter; exceeding → hard stop |
| No threshold edits | policy files read-only to agent; any "change threshold" intent logged as rejection |
| Holdout isolation | eval engine runs in separate module/process; returns aggregates only |
| No arbitrary code | no code-exec tool exists |

### 5.3 Prompts
- **System prompt**: role, tool list, hard rules, output schema. Guardrail wording is defense-in-depth only.
- **Context given**: mission, policy *summary* (thresholds visible, immutable), aggregate results, prior repairs.
- **Never given**: raw holdout rows, signing keys, raw dataset values beyond schema/aggregates.

### 5.4 Diagnosis → repair mapping (heuristic starting point)
| Symptom | Likely cause | Candidate repair |
|---|---|---|
| DCR closer to train, high MIA AUC | memorization | `tune_hyperparameters` (fewer epochs / larger noise), then `enable_dp_training` |
| Low correlation fidelity | generator can't capture dependencies | `switch_generator` (CTGAN ↔ Gaussian Copula) |
| Low subgroup utility, small N | insufficient data, not repairable | no repair; report `INSUFFICIENT_EVIDENCE` + min N |

### 5.5 Candidate selection
Selection among candidates is done by the engine using a fixed ordering (fewest FAILs → fewest INSUFFICIENT → highest aggregate), not by the LLM.

### 5.6 Explanation
Generated from evidence-store rows only; every claim in the explanation must cite an `evidence_id`. Post-check: strip/flag statements without citations.

---

## 6. Passport design

- **Canonicalization**: JSON with sorted keys, no whitespace, UTF-8, floats rounded to fixed precision, stable enum strings.
- **Signing**: Ed25519 over canonical bytes of the passport minus `signature`.
- **Key handling (MVP)**: local keypair generated on first run, `key_id` = hash of public key; private key file `0600`, never in repo or image. Public key shipped alongside passport for verification. *No trust-root claims.*
- **Human approval**: approval adds `{approver, timestamp}`, flips status, re-signs (previous signature retained in an audit array).
- **Verification steps** (in order, fail-closed):
  1. Parse + schema-validate passport.
  2. Recompute canonical hash; verify signature.
  3. Hash dataset file; compare to `dataset.sha256`.
  4. Check `verdicts[purpose]` ∈ {PASS} (WARNING allowed only if caller opts in).
  5. Check `human_approval == APPROVED` when policy requires it.
  6. Return structured result with reason codes.

Reason codes: `OK`, `SIGNATURE_INVALID`, `DATASET_HASH_MISMATCH`, `PURPOSE_UNSUPPORTED`, `PURPOSE_UNKNOWN`, `APPROVAL_MISSING`, `PASSPORT_MALFORMED`.

---

## 7. SDK / CLI / CI design

```python
from synpassport import verify, load_dataset

result = verify("data.csv", "passport.json", purpose="clinical_ml")
df = load_dataset("data.csv", purpose="clinical_ml")  # raises PassportError
```
```
passport verify data.csv passport.json --purpose clinical_ml [--allow-warning] [--json]
passport issue  ... | passport approve ... | passport inspect passport.json
```
Exit codes: `0` verified, `1` unsupported/tampered, `2` malformed/usage error.
GitHub Action: inputs `dataset`, `passport`, `purpose`; fails job on non-zero.

---

## 8. API design (FastAPI)

| Method | Path | Purpose |
|---|---|---|
| POST | `/runs` | upload dataset + mission, start run |
| GET | `/runs/{id}` | status, candidates, verdicts |
| GET | `/runs/{id}/evidence` | evidence rows |
| GET | `/runs/{id}/events` | SSE stream: agent steps, repairs, rejections |
| POST | `/runs/{id}/approve` | human approval |
| GET | `/runs/{id}/passport` | signed passport JSON |
| POST | `/verify` | verify dataset + passport (demo) |

---

## 9. UI design

**Screens**
1. **Mission setup** — upload, purpose, subgroup, privacy level, intended uses; shows chosen policy + hash.
2. **Run view** — live agent timeline (plan → candidate → checks → diagnosis → repair), budget meter (candidates/repairs used).
3. **Verdict board** — one card per intended use with state badge, required checks, and the blocking reason.
4. **Evidence drill-down** — metric, CI plot, threshold line, baseline comparison (DCR histograms).
5. **Sufficiency panel** — "need ≥ N records aged 65+" with current N.
6. **Passport panel** — JSON view, download, approve, verify.
7. **Tamper demo** — edit-a-cell → verification fails → loader guard blocks.

**State colors** (also distinguished by icon + label, not color alone): PASS green, WARNING amber, FAIL red, INSUFFICIENT_EVIDENCE grey/blue with "?" icon.

**Copy rules**: never say "safe" or "private"; use "no unacceptable risk detected under the specified attacks".

---

## 10. Demo design (90-second golden path)

| Step | Action | Proves |
|---|---|---|
| 1 | Upload public heart-disease dataset; mission = clinical ML, 65+ | Purpose first |
| 2 | Candidate 1 fails privacy; agent explains memorization | Adversarial testing + diagnosis |
| 3 | One whitelisted repair; Candidate 2 passes privacy | Bounded repair loop |
| 4 | Subgroup CI wide → clinical = INSUFFICIENT_EVIDENCE, testing = PASS | Purpose-scoped verdicts + sufficiency |
| 5 | Issue passport; edit one CSV cell; verify fails | Tamper evidence |
| 6 | Loader guard blocks tampered file | Enforceability |

**Reliability**: cached generators/candidates/LLM responses in `replay/`; live target < 60 s; `--replay` fallback; fixed seeds; one-command Docker.

To make step 2 deterministic, choose seed/params so Candidate 1 is reproducibly over-fitted (e.g., CTGAN with many epochs, small training set), and pre-verify the outcome.

---

## 11. Testing strategy

| Layer | Tests |
|---|---|
| Policy engine | unit + property tests (monotonicity, missing→never PASS) |
| Checks | known-answer tests on toy data (identical data → fidelity 1.0; copied rows → DCR FAIL) |
| Passport | round-trip sign/verify; single-byte tamper on dataset and passport; canonicalization stability |
| Agent | mock LLM emitting illegal actions → all rejected + logged; budget exhaustion → hard stop |
| Holdout isolation | test asserting agent-visible payloads contain no holdout rows |
| SDK/CLI | exit codes, reason codes, loader guard raises |
| E2E | replay-mode golden path in CI |

---

## 12. Open decisions

- Which public dataset (e.g., UCI heart disease) and whether size supports a meaningful 65+ subgroup — determines whether step 4 naturally yields INSUFFICIENT_EVIDENCE.
- WARNING policy for consumers: block by default or opt-in via `--allow-warning`.
- Multiple-testing adjustment method for candidate count (record in passport; e.g., Bonferroni over candidates).
- LLM provider/model and structured-output mechanism.
- Verified statistics for the impact section (report flags these as TODO before submission).
