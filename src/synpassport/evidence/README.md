# Evidence Store & Persistence (`synpassport.evidence`)

The `synpassport.evidence` module handles SQLite persistence, querying, and auditing of `EvidenceRecord` items generated during assurance runs.

---

## Submodule Architecture

- [`models.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/evidence/models.py): Pydantic data model for `EvidenceRecord`.
- [`store.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/evidence/store.py): SQLite-backed `EvidenceStore` persistence layer.

---

## Data Schema (`EvidenceRecord`)

Every statistical check execution generates an `EvidenceRecord`:

```python
class EvidenceRecord(BaseModel):
    run_id: str
    candidate_id: str
    check_id: str
    value: float
    ci_low: Optional[float] = None
    ci_high: Optional[float] = None
    n: int
    threshold_ref: float
    seed: int
    state: str  # "PASS", "FAIL", "INSUFFICIENT_EVIDENCE"
    metadata: dict = Field(default_factory=dict)
```

---

## SQLite Database Schema (`store.py`)

The SQLite database table `evidence_records` stores records for persistent auditing:

```sql
CREATE TABLE IF NOT EXISTS evidence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    check_id TEXT NOT NULL,
    value REAL NOT NULL,
    ci_low REAL,
    ci_high REAL,
    n INTEGER NOT NULL,
    threshold_ref REAL NOT NULL,
    seed INTEGER NOT NULL,
    state TEXT NOT NULL,
    metadata TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
