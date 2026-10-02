# Mission Profile & Intent Specification (`synpassport.mission`)

The `synpassport.mission` module defines domain intent specifications and task constraints.

---

## Submodule Architecture

- [`schema.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/mission/schema.py): Pydantic data model for `MissionProfile`.

---

## `MissionProfile` Schema

```yaml
name: Clinical Trial Analysis
domain: healthcare
intended_use: external_sharing
target_columns:
  - mortality
  - readmission_30d
sensitive_columns:
  - ssn
  - patient_name
  - zip_code
utility_min_acceptable: 0.85
```
