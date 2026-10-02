# Verification SDK & Data Guard (`synpassport.sdk`)

The `synpassport.sdk` module provides the client-side library for verifying Evidence Passports and securely loading dataset files while mitigating Time-of-Check to Time-of-Use (TOCTOU) race conditions.

---

## Submodules

- [`verify.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/verify.py): 7-step fail-closed verification pipeline (`verify`, `verify_bytes`).
- [`guard.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/guard.py): TOCTOU-safe dataset loader (`load_dataset`).

---

## 1. 7-Step Fail-Closed Verification Pipeline ([`verify.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/verify.py))

Verification returns `(is_valid: bool, reason: str, details: dict)`. If any step fails, verification halts immediately and returns an explicit error reason code.

```
Step 1: JSON & Schema Parsing
   └── Step 2: Passport Expiration Validation (max_age_days)
          └── Step 3: Public Key Resolution (TrustedKeyRegistry lookup)
                 └── Step 4: Cryptographic Signature Verification (Ed25519 over Canonical JSON)
                        └── Step 5: Dataset Hash Verification (Raw SHA-256 or Canonical CSV SHA-256)
                               └── Step 6: Purpose Verdict Verification (Target Purpose == "APPROVED")
                                      └── Step 7: Human Approval Verification (Co-signature requirement)
```

### Complete Reason Codes (`REASON_CODES`)

| Reason Code | Description |
| :--- | :--- |
| `OK` | Verification succeeded completely. |
| `PASSPORT_MALFORMED` | Invalid JSON or missing required top-level passport schema fields. |
| `PASSPORT_EXPIRED` | Passport `issued_at` exceeds `max_age_days` constraint. |
| `KEY_UNTRUSTED` | Signing key is not present in registry, is revoked, or is expired. |
| `SIGNATURE_INVALID` | Ed25519 signature check failed against canonical payload bytes. |
| `DATASET_HASH_MISMATCH` | Neither raw file SHA-256 nor canonical CSV SHA-256 match `dataset.sha256`. |
| `PURPOSE_UNKNOWN` | Requested `purpose` is not defined in the policy verdicts. |
| `PURPOSE_UNSUPPORTED` | Requested `purpose` verdict is `REJECTED` instead of `APPROVED`. |
| `APPROVAL_MISSING` | Policy mandates `human_approval.required: true` but approval is missing/unapproved. |

### SDK Usage Example

```python
from synpassport.sdk import verify

valid, reason, details = verify(
    dataset_path="data/train_synthetic.csv",
    passport_path="data/passport.json",
    purpose="external_sharing",
    registry_path="keys/key_registry.json",
    max_age_days=90
)

if not valid:
    raise ValueError(f"Passport verification failed: {reason} ({details})")
```

---

## 2. TOCTOU-Safe Dataset Guard ([`guard.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/sdk/guard.py))

Traditional verification opens a Time-of-Check to Time-of-Use (TOCTOU) vulnerability where a file is verified on disk and subsequently re-read by an analytics engine, allowing an attacker to swap the verified file on disk between check and use.

`synpassport.sdk.guard.load_dataset()` eliminates this attack vector:

```python
from synpassport.sdk.guard import load_dataset

# 1. Reads file bytes ONCE into memory.
# 2. Performs verification against in-memory bytes.
# 3. Parses Pandas DataFrame directly from in-memory buffer.
df = load_dataset(
    dataset_path="data/train_synthetic.csv",
    passport_path="data/passport.json",
    purpose="analytics_internal"
)
```
