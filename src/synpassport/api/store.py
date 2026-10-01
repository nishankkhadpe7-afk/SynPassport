"""In-memory and file-backed run state management for SynPassport API."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from synpassport.agent.llm import create_llm_client
from synpassport.agent.loop import AssuranceAgentLoop
from synpassport.api.config import KEY_DIR, REPLAY_MODE
from synpassport.api.logging import get_logger, log_run_event
from synpassport.passport.keygen import generate_keypair
from synpassport.passport.signer import load_private_key

__all__ = [
    "RunRecord",
    "RunStore",
    "execute_run_pipeline",
    "get_or_create_server_key",
    "run_store",
]

logger = get_logger("synpassport.api.store")


class RunRecord:
    """Encapsulates execution state, artifacts, and event subscribers for a single run."""

    def __init__(
        self,
        run_id: str,
        dataset_path: Path,
        mission: dict[str, Any],
        run_dir: Path,
    ) -> None:
        self.run_id = run_id
        self.dataset_path = dataset_path
        self.mission = mission
        self.run_dir = run_dir
        self.status = "QUEUED"
        self.created_at = datetime.now(UTC).isoformat()
        self.completed_at: str | None = None
        self.candidates: list[dict[str, Any]] = []
        self.repairs: list[dict[str, Any]] = []
        self.agent_rejections: list[dict[str, Any]] = []
        self.budget_used: dict[str, int] = {
            "candidates_evaluated": 0,
            "max_candidates": 3,
            "repairs_attempted": 0,
            "max_repairs": 2,
        }
        self.verdicts: dict[str, str] = {}
        self.explanation: dict[str, Any] | None = None
        self.passport: dict[str, Any] | None = None
        self.evidence: list[dict[str, Any]] = []
        self.error: str | None = None
        self.events: list[dict[str, Any]] = []
        self.subscribers: list[asyncio.Queue[dict[str, Any]]] = []
        self._lock = threading.Lock()


class RunStore:
    """Concurrent catalog of active and historical runs."""

    def __init__(self) -> None:
        self._runs: dict[str, RunRecord] = {}
        self._lock = threading.Lock()

    def create_run(
        self,
        run_id: str,
        dataset_path: Path,
        mission: dict[str, Any],
        run_dir: Path,
    ) -> RunRecord:
        """Create and register a new run record."""
        with self._lock:
            record = RunRecord(
                run_id=run_id,
                dataset_path=dataset_path,
                mission=mission,
                run_dir=run_dir,
            )
            self._runs[run_id] = record
            return record

    def get_run(self, run_id: str) -> RunRecord | None:
        """Retrieve run record by id if found."""
        with self._lock:
            return self._runs.get(run_id)

    def add_event(self, run_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Record event and push to active SSE subscribers."""
        run = self.get_run(run_id)
        if not run:
            return

        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        with run._lock:
            run.events.append(event)
            for queue in list(run.subscribers):
                try:
                    queue.put_nowait(event)
                except Exception:
                    pass

    def subscribe_events(
        self, run_id: str
    ) -> tuple[list[dict[str, Any]], asyncio.Queue[dict[str, Any]]]:
        """Subscribe to real-time events for run, returning existing events and listener queue."""
        run = self.get_run(run_id)
        if not run:
            raise KeyError(f"Run {run_id} not found")

        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        with run._lock:
            existing = list(run.events)
            run.subscribers.append(queue)

        return existing, queue

    def unsubscribe_events(self, run_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        """Remove subscriber queue from run listener list."""
        run = self.get_run(run_id)
        if not run:
            return
        with run._lock:
            if queue in run.subscribers:
                run.subscribers.remove(queue)


run_store = RunStore()


def get_or_create_server_key() -> tuple[Any, Path]:
    """Retrieve or generate Ed25519 signing keypair for server passport issuance."""
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    priv_path = KEY_DIR / "api_private.pem"
    pub_path = KEY_DIR / "api_public.pem"

    if priv_path.is_file() and pub_path.is_file():
        priv_key = load_private_key(priv_path)
        return priv_key, pub_path

    # Generate fresh keypair
    priv_file, pub_file, _ = generate_keypair(output_dir=KEY_DIR, key_name="api")
    priv_key = load_private_key(priv_file)
    return priv_key, pub_file


def execute_run_pipeline(run_id: str) -> None:
    """Execute assurance cycle in background task and update run record."""
    run = run_store.get_run(run_id)
    if not run:
        return

    run.status = "RUNNING"
    log_run_event(logger, logging.INFO, "Starting assurance run execution", run_id=run_id)
    run_store.add_event(run_id, "status", {"status": "RUNNING"})

    def on_event(event_type: str, data: dict[str, Any]) -> None:
        run_store.add_event(run_id, event_type, data)

    try:
        # Determine replay mode flag from env or config
        is_replay = REPLAY_MODE or (os.environ.get("SYNPASSPORT_REPLAY") == "1")

        signing_key, _ = get_or_create_server_key()

        # Instantiate agent loop with event listener and configured LLM client
        llm_client = create_llm_client()
        loop = AssuranceAgentLoop(
            llm_client=llm_client,
            event_listener=on_event,
            replay_mode=is_replay,
        )

        policy_id = str(run.mission.get("policy_id", "software-testing"))
        target_col = run.mission.get("target_column")
        seed = int(run.mission.get("seed", 1234))

        final_bundle = loop.run(
            real_data_path=run.dataset_path,
            mission=run.mission,
            policy_id_or_path=policy_id,
            output_dir=run.run_dir,
            signing_key=signing_key,
            seed=seed,
            target_col=target_col,
        )

        with run._lock:
            run.status = "COMPLETED"
            run.completed_at = datetime.now(UTC).isoformat()
            run.candidates = final_bundle.get("candidates", [])
            run.repairs = final_bundle.get("repairs", [])
            run.agent_rejections = final_bundle.get("agent_rejections", [])
            run.verdicts = final_bundle.get("verdicts", {})
            run.explanation = final_bundle.get("explanation")
            run.passport = final_bundle.get("passport")

            if run.passport:
                run.evidence = run.passport.get("evidence", [])
                # Persist passport JSON to disk
                passport_file = run.run_dir / "passport.json"
                passport_file.write_text(
                    json.dumps(run.passport, indent=2),
                    encoding="utf-8",
                )

            run.budget_used = {
                "candidates_evaluated": final_bundle.get("candidates_evaluated", 1),
                "max_candidates": loop.max_candidates,
                "repairs_attempted": final_bundle.get("repairs_attempted", 0),
                "max_repairs": loop.max_repairs,
            }

        log_run_event(
            logger,
            logging.INFO,
            f"Assurance run completed. Best candidate: {final_bundle.get('best_candidate_id')}",
            run_id=run_id,
            verdicts=final_bundle.get("verdicts", {}),
        )
        run_store.add_event(run_id, "completed", {"status": "COMPLETED"})

    except Exception as exc:
        with run._lock:
            run.status = "FAILED"
            run.error = str(exc)
            run.completed_at = datetime.now(UTC).isoformat()

        log_run_event(
            logger,
            logging.ERROR,
            f"Assurance run failed with error: {exc}",
            run_id=run_id,
        )
        run_store.add_event(run_id, "failed", {"status": "FAILED", "error": str(exc)})
