# Command-Line Interface (`synpassport.cli`)

The `synpassport.cli` module provides the `passport` (and `synpassport`) command-line interface powered by Click / Typer.

---

## Commands Summary

- [`main.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/cli/main.py): Subcommand implementations (`verify`, `issue`, `approve`, `inspect`, `keyreg`).

---

## 1. `passport verify`
Verifies a synthetic dataset against a signed Evidence Passport.

```bash
passport verify <dataset_path> <passport_path> \
  --purpose external_sharing \
  --registry keys/key_registry.json \
  --max-age-days 90 \
  --json
```

### Options
- `--purpose <text>`: Target use case to evaluate against policy verdicts (default: `analytics_internal`).
- `--allow-warning`: Allow execution if checks trigger policy warning bands.
- `--public-key <path>`: Explicit fallback Ed25519 public key PEM file.
- `--registry <path>`: Path to trusted key registry JSON file.
- `--max-age-days <int>`: Max allowable passport age in days.
- `--json`: Output machine-readable JSON verification report.

---

## 2. `passport issue`
Executes generation and assurance pipeline, issuing a signed Evidence Passport.

```bash
passport issue \
  --data data/real_train.csv \
  --synth data/train_synthetic.csv \
  --policy policies/policy_hipaa.yaml \
  --mission mission.yaml \
  --key keys/ed25519_signing_key.pem \
  --output data/passport.json
```

---

## 3. `passport approve`
Co-signs an existing passport with human approval credentials.

```bash
passport approve data/passport.json \
  --approver compliance-officer@company.com \
  --key keys/approver_ed25519_key.pem \
  --output data/passport_approved.json
```

---

## 4. `passport inspect`
Prints a formatted summary of evidence records, policy verdicts, and signature details.

```bash
passport inspect data/passport.json --json
```

---

## 5. `passport keyreg`
Manages the Trusted Key Registry.

```bash
# Enroll a new key
passport keyreg enroll --registry keys/key_registry.json \
  --label prod-issuer-1 \
  --public-key keys/ed25519_public.pem \
  --expires-at 2027-01-01T00:00:00Z \
  --comment "Production Signing Key"

# Revoke a key
passport keyreg revoke --registry keys/key_registry.json \
  --label prod-issuer-1 \
  --reason "Key compromised"

# List keys
passport keyreg list --registry keys/key_registry.json

# Generate new keypair & enroll
passport keyreg generate --label dev-key --output-dir keys/
```

---

## Exit Codes

- `0`: Success / Verified OK.
- `1`: Verification Failure / Unapproved / Hash Mismatch / Untrusted Key.
- `2`: Command Usage Error / File Not Found / Invalid Parameters.
