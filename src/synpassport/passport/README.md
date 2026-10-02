# Cryptographic Passport Engine (`synpassport.passport`)

The `synpassport.passport` module is the core cryptographic attestation engine of SynPassport. It is responsible for assembling, canonicalizing, signing, verifying, and co-signing **Evidence Passports** for synthetic datasets, as well as managing trusted public key registries and expiration policies.

---

## Component Overview

The package comprises five modules:

- [`builder.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/builder.py): `EvidencePassport` wrapper class, passport construction (`build_passport`), human co-signing (`approve_passport`), verification (`verify_passport`), dataset hash validation (`verify_dataset_hash`), and standard attestation format exports (in-toto, DSSE).
- [`canonical.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/canonical.py): RFC 8785 compliant JSON canonicalization (`canonical_json_dumps`), payload SHA-256 digest (`canonical_hash`), and line-ending invariant CSV byte hashing (`hash_canonical_csv`).
- [`trust.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/trust.py): Trusted Key Registry management (`TrustedKeyRegistry`), key enrollment/revocation/expiration, trust anchor resolution (`resolve_trusted_key`), and passport lifetime validation (`validate_passport_expiry`).
- [`signer.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/signer.py): Low-level Ed25519 signature generation (`sign_passport_data`) and signature verification (`verify_passport_signature`).
- [`keygen.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/passport/keygen.py): Ed25519 keypair generation (`generate_ed25519_keypair`), PEM serialization (`load_private_key`, `load_public_key`), and Key ID calculation (`compute_key_id`).

---

## 1. Data Structure (`builder.py`)

### `EvidencePassport` Wrapper Class
`EvidencePassport` wraps a standard Python `dict` containing execution, policy, evidence, and signature metadata.

```python
from synpassport.passport.builder import EvidencePassport, build_passport

passport_dict = build_passport(...)
passport = EvidencePassport(passport_dict)

# Verify self-contained signature
is_valid = passport.verify(public_key=pub_key)

# Export to standard formats
dsse_envelope = passport.to_dsse_envelope()
intoto_statement = passport.to_intoto_statement()
```

### Full Passport JSON Schema

```json
{
  "passport_version": "1.0.0",
  "mode": "live",
  "dataset": {
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "name": "train_synthetic.csv",
    "canonical_sha256": "f4c9a8..."
  },
  "mission": {
    "name": "Clinical Trial Analysis",
    "domain": "healthcare"
  },
  "policy": {
    "id": "policy_hipaa_v1",
    "sha256": "a1b2c3d4e5f6..."
  },
  "run": {
    "code_version": "0.1.0",
    "seeds": {"numpy": 42, "torch": 42},
    "candidates_evaluated": 3,
    "repairs_attempted": 1,
    "hypotheses_evaluated": ["tune_hyperparameters"],
    "mode": "live"
  },
  "evidence": [
    {
      "check_id": "privacy_dcr_vs_holdout",
      "value": 0.45,
      "ci_low": 0.38,
      "ci_high": 0.52,
      "n": 1000,
      "threshold_ref": 0.60,
      "seed": 42,
      "state": "PASS",
      "metadata": {}
    }
  ],
  "repairs": [],
  "agent_rejections": [],
  "verdicts": {
    "analytics_internal": "APPROVED",
    "external_sharing": "REJECTED"
  },
  "human_approval": {
    "approved": true,
    "approver": "compliance-officer@company.com",
    "timestamp": "2026-10-02T23:00:00Z"
  },
  "audit_signatures": [],
  "issued_at": "2026-10-02T22:55:00Z",
  "signature": {
    "algorithm": "ed25519",
    "public_key_pem": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----",
    "signature": "3a7b9c...",
    "key_id": "8f3e2a1b9c0d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f"
  }
}
```

---

## 2. Cryptography & Canonicalization

### Key Generation & Key ID (`keygen.py`)
- **Algorithm**: Ed25519 (Edwards-curve Digital Signature Algorithm over Curve25519).
- **Key ID Derivation**: The `key_id` is computed as the SHA-256 hex digest of the raw 32-byte public key:
  ```python
  raw_bytes = public_key.public_bytes(
      encoding=serialization.Encoding.Raw,
      format=serialization.PublicFormat.Raw
  )
  key_id = hashlib.sha256(raw_bytes).hexdigest()
  ```

### Canonical Serialization (`canonical.py`)
To prevent signature verification failures across platforms or key orders, all payload digests use RFC 8785 JSON canonicalization:
- Dictionary keys are sorted lexicographically.
- No whitespace around separators (`separators=(',', ':')`).
- `ensure_ascii=False` for standard UTF-8 text formatting.
- The `signature` block is stripped before digest calculation.

### Dataset Hash Verification (`verify_dataset_hash`)
The dataset hash check supports two modes:
1. **Raw Byte SHA-256**: Exact byte match of the target dataset file (`dataset.sha256`).
2. **Canonical CSV SHA-256**: Line-ending invariant match (`dataset.canonical_sha256`), stripping `
` to `
` and omitting trailing empty lines.

---

## 3. Trust Model & Key Governance (`trust.py`)

The `TrustedKeyRegistry` maintains a persistent registry of authorized signing keys:

```json
{
  "keys": {
    "prod-key-1": {
      "fingerprint": "8f3e2a1b9c0d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f",
      "public_key_pem": "-----BEGIN PUBLIC KEY-----
...",
      "added_at": "2026-01-01T00:00:00Z",
      "expires_at": "2027-01-01T00:00:00Z",
      "revoked": false,
      "revocation_reason": null,
      "comment": "Production Signing Key"
    }
  }
}
```

### Key Resolution Algorithm (`resolve_trusted_key`)
When verifying a passport:
1. `signature.key_id` is looked up in `TrustedKeyRegistry`.
2. Verifies `revoked == False` (otherwise returns `KEY_UNTRUSTED`).
3. Verifies `now < expires_at` (otherwise returns `KEY_UNTRUSTED`).
4. If registry is empty (development mode), falls back to embedded `public_key_pem` or explicitly passed key.

### Passport Expiration Validation (`validate_passport_expiry`)
Passport `issued_at` timestamp is checked against `max_age_days`. If expired, returns `PASSPORT_EXPIRED`.

---

## 4. Human Co-Signing & Approval (`approve_passport`)

When policy requires human sign-off:
1. Former signature block is moved into `audit_signatures`.
2. `human_approval` field is updated (`approved: true`, `approver: "<email>"`, `timestamp: "<iso>"`).
3. Entire payload is re-canonicalized and signed by the approver's Ed25519 key.

---

## 5. Attestation Export Formats

- **DSSE (Dead Simple Signing Envelope)**: `to_dsse_envelope()` outputs base64 payload and signature blocks conforming to the DSSE v1.0 specification.
- **In-Toto Statement**: `to_intoto_statement()` formats evidence as an in-toto v0.1 Statement predicate.
