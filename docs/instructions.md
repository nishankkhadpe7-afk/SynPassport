# SynPassport — Build & Run Instructions

Step-by-step guide to set up, build, test, and demo the MVP. Also usable as a briefing for an AI coding agent (see §9).

---

## 1. Prerequisites

- Python 3.11+
- Node.js 20+ (dashboard)
- Docker + Docker Compose
- Git
- LLM API key (only needed for the agent step; not for steps 1–4)

---

## 2. Setup

```bash
git clone <repo-url> synpassport && cd synpassport
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # set LLM_API_KEY, LLM_MODEL, SIGNING_KEY_PATH
python -m synpassport.passport.keygen   # creates Ed25519 keypair (private key chmod 600)
```

`.env`
```
LLM_API_KEY=...
LLM_MODEL=...
SIGNING_KEY_PATH=./keys/ed25519_private.pem
DB_PATH=./data/synpassport.db
GLOBAL_SEED=1234
```

Never commit `keys/`, `.env`, or datasets containing real sensitive data.

---

## 3. Build order (do not reorder)

Each step must have passing tests before the next begins.

### Step 1 — Policy engine
- [ ] `policies/*.yaml` for 5 profiles (start with `software-testing`, `ml-prototyping`, `ml-sensitive-v1`).
- [ ] Policy loader + canonical hash.
- [ ] Engine: `evaluate(policy, evidence) -> verdicts`.
- [ ] Property tests: deterministic, monotone, missing evidence never PASS.

**Done when:** engine turns hand-written evidence fixtures into correct per-use verdicts.

### Step 2 — Checks
- [ ] Implement 8 checks (`schema`, `marginal`, `correlation`, `tstr`, `subgroup_tstr`, `dcr`, `mia`, `sufficiency`).
- [ ] Bootstrap CI helper (≥1000 resamples, seeded).
- [ ] Train/holdout splitter; holdout stored separately, hash recorded.
- [ ] Known-answer tests (identical data, copied rows, shuffled columns).

**Done when:** `python -m synpassport.checks.run --data X --synth Y --policy Z` writes evidence rows to SQLite.

### Step 3 — Passport
- [ ] Canonical JSON serializer.
- [ ] Dataset SHA-256 (streamed).
- [ ] Ed25519 sign/verify.
- [ ] Passport builder from evidence + verdicts.
- [ ] Tamper tests: flip one byte in dataset → fail; flip one field in passport → fail.

### Step 4 — Verify SDK, CLI, loader guard, CI action
- [ ] `verify()`, `load_dataset()`, `PassportError` with reason codes.
- [ ] CLI: `passport verify|issue|approve|inspect`.
- [ ] Exit codes: 0 ok, 1 unsupported/tampered, 2 malformed.
- [ ] `.github/actions/verify/action.yml`.

**Checkpoint:** a scripted non-agent pipeline (fixed generator + fixed params → checks → engine → passport → verify) runs end-to-end. This is your demo safety net.

### Step 5 — Agent loop
- [ ] Tool registry + JSON schemas for actions.
- [ ] Dispatcher that rejects unknown tools/args; logs rejections.
- [ ] Repair whitelist validator; budget counters (3 candidates / 2 repairs).
- [ ] Holdout isolation (agent receives aggregates only).
- [ ] Mock-LLM tests for illegal actions and budget exhaustion.
- [ ] Explanation generator with evidence-id citations.
- [ ] Record `agent_rejections` and repairs into the passport.

### Step 6 — API + UI
- [ ] FastAPI endpoints (see `design.md` §8) + SSE event stream.
- [ ] Next.js screens: mission setup, run timeline, verdict board, evidence drill-down, sufficiency panel, passport, tamper demo.
- [ ] Replay mode (`--replay`) reading `replay/` cache.

---

## 4. Running

**Local (dev)**
```bash
uvicorn synpassport.api.main:app --reload      # backend :8000
cd web && npm install && npm run dev            # frontend :3000
```

**Docker (one command)**
```bash
docker compose up --build
```

**CLI quickstart**
```bash
passport issue --data data/hf_synth.csv --mission mission.yaml --policy ml-sensitive-v1
passport approve passport.json --approver "Name"
passport verify data/hf_synth.csv passport.json --purpose clinical_ml
```

**Replay mode (demo fallback)**
```bash
SYNPASSPORT_REPLAY=1 docker compose up
```

---

## 5. Testing

```bash
pytest -q                          # unit + property + integration
pytest -m e2e                      # replay-mode golden path
ruff check . && mypy src           # lint + types
```

Must-have tests before demo:
1. Policy engine determinism/monotonicity.
2. Missing evidence → never PASS.
3. One-byte dataset tamper → `DATASET_HASH_MISMATCH`.
4. One-field passport tamper → `SIGNATURE_INVALID`.
5. Mock agent proposing threshold change → rejected + in `agent_rejections`.
6. Payloads visible to agent contain no holdout rows.
7. Loader guard raises on missing/unsupported passport.

---

## 6. Demo runbook (90 seconds)

**Pre-demo checklist**
- [ ] Docker image built; `docker compose up` works offline in replay mode.
- [ ] Seeds fixed; Candidate 1 reproducibly fails privacy.
- [ ] Dataset copy + a pre-tampered copy ready.
- [ ] Browser tabs: dashboard, terminal.

**Script**
1. Upload heart-disease data; set mission = clinical ML, subgroup `age >= 65`. *(purpose first)*
2. Run: Candidate 1 fails DCR/MIA; agent explains likely memorization.
3. Agent applies one whitelisted repair; Candidate 2 passes privacy.
4. Verdict board: software_testing = PASS, clinical_ml = INSUFFICIENT_EVIDENCE (show "need ≥ N records 65+").
5. Issue passport. Edit one CSV cell → `passport verify` fails.
6. `load_dataset(..., purpose="clinical_ml")` on tampered file → blocked.

**If live run misbehaves:** switch to `--replay`; do not debug on stage.

---

## 7. Conventions

- **Determinism:** every stochastic call takes an explicit seed from config; record seeds in evidence.
- **Fail closed:** any error in a check or verification path → not PASS.
- **Language:** never "safe", "private", "compliant". Use "no unacceptable risk detected under the specified attacks" and "supports audit".
- **No `eval`/`exec`** anywhere, including subgroup expressions.
- **Secrets:** private key and API keys via env/file mounts only.
- **Commits:** small, one build step per PR; tests included.
- **Logging:** structured JSON logs with `run_id`; never log raw dataset rows.

---

## 8. Definition of done (MVP)

- [ ] 8 checks implemented, seeded, with CIs where required.
- [ ] Deterministic policy engine with property tests.
- [ ] Signed, hash-bound passport; tamper tests pass.
- [ ] `verify` CLI, SDK, loader guard, GitHub Action working.
- [ ] Agent limited to whitelist + budget; rejections logged in passport.
- [ ] Per-use verdicts displayed in UI, including INSUFFICIENT_EVIDENCE with min-N.
- [ ] One-command Docker run + replay mode.
- [ ] README states non-claims (no proof of privacy, no legal certification, human approval required).
- [ ] Impact statistics in the report backed by cited sources; vendor claims re-verified.

---

## 9. Briefing for an AI coding agent (paste as `CLAUDE.md` / `AGENTS.md`)

```
Project: SynPassport — purpose-bound assurance for synthetic data.
Read docs/architecture.md and docs/design.md first.

Hard rules:
1. The LLM never assigns verdicts. Only synpassport.policy.engine does.
2. Agent tools are limited to the registry; repairs limited to
   tune_hyperparameters | switch_generator | enable_dp_training.
3. Policy files are immutable at runtime; never add code that edits thresholds.
4. Holdout data never enters agent prompts or logs.
5. No eval/exec; no arbitrary code tools.
6. Missing/errored evidence => INSUFFICIENT_EVIDENCE, never PASS.
7. Follow build order: policy engine → checks → passport → SDK/guard → agent → UI.
8. Every change ships with tests; run `pytest -q && ruff check . && mypy src`.
9. Do not use the words "safe", "private", or "compliant" in UI copy or docs.
```

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Verification fails on unchanged file | Line endings / encoding changed dataset bytes | Hash raw bytes; avoid re-saving CSV |
| Signature invalid after re-issue | Canonicalization drift (float format, key order) | Fix serializer; add golden-file test |
| Candidate 1 doesn't fail privacy | Generator not over-fitted | Increase epochs / shrink train set; pin seed; re-cache |
| Subgroup CI narrow in demo | 65+ subgroup too large | Subsample the subgroup for the demo dataset |
| Agent loops or exceeds budget | Missing hard stop | Enforce counters in run-state, not prompt |
| Live LLM too slow | Network/latency | Use replay cache; lower max tokens |
