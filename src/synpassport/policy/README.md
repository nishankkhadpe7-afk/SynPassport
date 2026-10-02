# Immutable Policy Engine (`synpassport.policy`)

The `synpassport.policy` module defines the specification, canonical hashing, and multi-purpose evaluation matrix for assurance policies.

---

## Submodule Architecture

- [`models.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/models.py): Pydantic data models (`PolicyDefinition`, `CheckThreshold`, `PurposePolicy`, `BudgetConfig`).
- [`loader.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/loader.py): YAML loader (`load_policy`), policy canonical hashing (`canonical_hash`), and policy binding verification.
- [`engine.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/policy/engine.py): Multi-purpose verdict decision engine (`evaluate_policy`).

---

## 1. YAML Policy Specification

Policies are declared in human-readable YAML files stored in `policies/`:

```yaml
id: policy_hipaa_v1
version: 1.0.0
description: HIPAA-compliant privacy and fidelity standards for healthcare data sharing.

requires:
  schema_validity:
    threshold: 0.0
    operator: "<="
  marginal_fidelity:
    threshold: 0.15
    operator: "<="
  correlation_fidelity:
    threshold: 0.20
    operator: "<="
  privacy_dcr_vs_holdout:
    threshold: 0.60
    operator: "<="
  membership_inference_auc:
    threshold: 0.55
    operator: "<="

warning_bands:
  privacy_dcr_vs_holdout: 0.55
  marginal_fidelity: 0.12

uses:
  analytics_internal:
    required_checks:
      - schema_validity
      - marginal_fidelity
      - correlation_fidelity
  external_sharing:
    required_checks:
      - schema_validity
      - marginal_fidelity
      - correlation_fidelity
      - privacy_dcr_vs_holdout
      - membership_inference_auc

budget:
  max_candidates: 3
  max_repairs: 2

human_approval:
  required: true
```

---

## 2. Policy Canonical Hashing (`sha256`)

To guarantee policy immutability and prevent unauthorized threshold relaxation:
1. The policy file YAML is loaded into a Python dictionary.
2. The `sha256` key (if present) is excluded.
3. The dictionary is canonicalized via RFC 8785 JSON canonicalization.
4. The SHA-256 hex digest of the canonical string is computed and assigned to `policy.sha256`.
5. The `policy.sha256` digest is embedded in the signed Evidence Passport.

If a dataset creator modifies a threshold in the YAML, the resulting passport will carry a different `policy.sha256` hash, causing verifiers to detect policy tampering.

---

## 3. Multi-Purpose Verdict Matrix (`engine.py`)

A single pipeline execution produces a set of evidence records. `evaluate_policy()` evaluates these records against the requirements of multiple intended use cases (`uses`):

```python
from synpassport.policy.engine import evaluate_policy

verdicts = evaluate_policy(policy, evidence_records)
# Returns:
# {
#   "analytics_internal": "APPROVED",
#   "external_sharing": "REJECTED"
# }
```

### Evaluation Logic
For each purpose defined under `uses`:
1. All checks listed under `required_checks` must have `state == "PASS"`.
2. If any required check has `state == "FAIL"` or `state == "INSUFFICIENT_EVIDENCE"`, the purpose is marked **`REJECTED`**.
3. If all required checks pass, the purpose is marked **`APPROVED`**.
