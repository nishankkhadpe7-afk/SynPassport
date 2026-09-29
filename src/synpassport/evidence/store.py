"""SQLite append-only evidence store.

Provides durable, append-only persistence of evaluation metrics, confidence intervals,
and execution metadata for transparent verification and auditing.
"""

import json
import sqlite3
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from synpassport.evidence.models import EvidenceRecord

__all__ = ["EvidenceStore"]


class EvidenceStore:
    """Append-only SQLite repository for check observations and evaluation logs."""

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Create and yield a sqlite connection, ensuring proper closure on Windows."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create append-only evidence records table and indexes."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    check_id TEXT NOT NULL,
                    value REAL NOT NULL,
                    ci_low REAL,
                    ci_high REAL,
                    n INTEGER,
                    threshold_ref TEXT,
                    seed INTEGER,
                    code_version TEXT NOT NULL,
                    state TEXT,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_run ON evidence_records(run_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_evidence_candidate "
                "ON evidence_records(run_id, candidate_id)"
            )
            conn.commit()

    def record_evidence(self, record: EvidenceRecord | dict[str, Any]) -> int:
        """Append an individual evidence record to the store."""
        rec = record if isinstance(record, EvidenceRecord) else EvidenceRecord(**record)
        meta_json = json.dumps(rec.metadata) if rec.metadata else "{}"

        query = """
            INSERT INTO evidence_records (
                run_id, candidate_id, check_id, value, ci_low, ci_high,
                n, threshold_ref, seed, code_version, state, metadata_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            rec.run_id,
            rec.candidate_id,
            rec.check_id,
            rec.value,
            rec.ci_low,
            rec.ci_high,
            rec.n,
            rec.threshold_ref,
            rec.seed,
            rec.code_version,
            rec.state,
            meta_json,
            rec.created_at,
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return int(cursor.lastrowid or 0)

    def record_batch(self, records: Sequence[EvidenceRecord | dict[str, Any]]) -> list[int]:
        """Append a batch of evidence records inside a single transaction."""
        ids: list[int] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO evidence_records (
                    run_id, candidate_id, check_id, value, ci_low, ci_high,
                    n, threshold_ref, seed, code_version, state, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for record in records:
                rec = record if isinstance(record, EvidenceRecord) else EvidenceRecord(**record)
                meta_json = json.dumps(rec.metadata) if rec.metadata else "{}"
                params = (
                    rec.run_id,
                    rec.candidate_id,
                    rec.check_id,
                    rec.value,
                    rec.ci_low,
                    rec.ci_high,
                    rec.n,
                    rec.threshold_ref,
                    rec.seed,
                    rec.code_version,
                    rec.state,
                    meta_json,
                    rec.created_at,
                )
                cursor.execute(query, params)
                ids.append(int(cursor.lastrowid or 0))
            conn.commit()
        return ids

    def get_run_evidence(
        self,
        run_id: str,
        candidate_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve recorded evidence records for a run, optionally filtered by candidate."""
        if candidate_id:
            query = """
                SELECT * FROM evidence_records
                WHERE run_id = ? AND candidate_id = ?
                ORDER BY id ASC
            """
            params: tuple[Any, ...] = (run_id, candidate_id)
        else:
            query = """
                SELECT * FROM evidence_records
                WHERE run_id = ?
                ORDER BY id ASC
            """
            params = (run_id,)

        results: list[dict[str, Any]] = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for row in cursor.execute(query, params):
                row_dict = dict(row)
                meta_raw = row_dict.pop("metadata_json", "{}")
                try:
                    row_dict["metadata"] = json.loads(meta_raw) if meta_raw else {}
                except Exception:
                    row_dict["metadata"] = {}
                results.append(row_dict)
        return results
