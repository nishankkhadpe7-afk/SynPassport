"""Run management and monitoring endpoints for SynPassport API."""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Header,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from synpassport.api.config import APPROVER_TOKEN, MAX_UPLOAD_SIZE, RUNS_DIR
from synpassport.api.logging import get_logger, log_run_event
from synpassport.api.models import (
    ApproveRequest,
    ApproveResponse,
    BudgetUsed,
    EvidenceItem,
    RunCreatedResponse,
    RunStatusResponse,
    SubgroupSufficiencyItem,
    SufficiencyResponse,
)
from synpassport.api.store import (
    execute_run_pipeline,
    get_or_create_server_key,
    run_store,
)
from synpassport.checks.sufficiency import SufficiencyCheck
from synpassport.mission.schema import Mission
from synpassport.passport.builder import approve_passport
from synpassport.policy.engine import evaluate_policy_detailed
from synpassport.policy.loader import load_policy

__all__ = ["router"]

router = APIRouter(prefix="/runs", tags=["runs"])
logger = get_logger("synpassport.api.runs")


@router.post(
    "",
    response_model=RunCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule new assurance run",
)
async def create_run(
    background_tasks: BackgroundTasks,
    request: Request,
) -> RunCreatedResponse:
    """Validate mission, stage dataset file, and trigger background assurance pipeline."""
    form = await request.form()
    dataset_field = form.get("dataset") or form.get("file")
    if not isinstance(dataset_field, UploadFile):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Dataset file is required as multipart form field 'dataset'",
        )

    mission_field = form.get("mission")
    raw_mission_content: str | None = None
    if isinstance(mission_field, UploadFile):
        content_bytes = await mission_field.read()
        raw_mission_content = content_bytes.decode("utf-8")
    elif isinstance(mission_field, str):
        raw_mission_content = mission_field

    if not raw_mission_content or not raw_mission_content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mission specification is required and cannot be empty",
        )

    # Parse YAML / JSON
    try:
        parsed_mission = yaml.safe_load(raw_mission_content)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Malformed mission specification; unable to parse YAML/JSON: {exc}",
        ) from exc

    if not isinstance(parsed_mission, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mission specification must evaluate to a dictionary object",
        )

    # Validate mission schema
    try:
        validated_mission = Mission(**parsed_mission)
    except ValidationError as val_err:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Mission schema validation failure: {val_err}",
        ) from val_err

    # Check size before creating anything on disk; read at most limit + 1 bytes.
    dataset_bytes = await dataset_field.read(MAX_UPLOAD_SIZE + 1)
    if len(dataset_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum permitted limit of {MAX_UPLOAD_SIZE} bytes",
        )

    run_id = f"run_{uuid.uuid4().hex[:12]}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    staged_dataset_path = run_dir / "dataset.csv"
    staged_dataset_path.write_bytes(dataset_bytes)

    # Persist mission configuration
    mission_dict = validated_mission.to_dict()
    mission_file = run_dir / "mission.json"
    mission_file.write_text(json.dumps(mission_dict, indent=2), encoding="utf-8")

    # Register run in catalog
    run_store.create_run(
        run_id=run_id,
        dataset_path=staged_dataset_path,
        mission=mission_dict,
        run_dir=run_dir,
    )

    log_run_event(
        logger,
        logging.INFO,
        "Registered new assurance run",
        run_id=run_id,
        purpose=validated_mission.purpose,
    )

    # Dispatch to background task
    background_tasks.add_task(execute_run_pipeline, run_id)

    return RunCreatedResponse(
        run_id=run_id,
        status="QUEUED",
        message="Assurance run scheduled successfully",
    )


@router.get(
    "/{run_id}",
    response_model=RunStatusResponse,
    summary="Get run status and candidate evaluation overview",
)
def get_run_status(run_id: str) -> RunStatusResponse:
    """Retrieve execution status, evaluated candidates, budget, and verdicts."""
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )

    return RunStatusResponse(
        run_id=run.run_id,
        status=run.status,
        candidates=run.candidates,
        repairs=run.repairs,
        agent_rejections=run.agent_rejections,
        budget_used=BudgetUsed(**run.budget_used),
        verdicts=run.verdicts,
        best_candidate_id=run.best_candidate_id,
        error=run.error,
    )


@router.get(
    "/{run_id}/evidence",
    response_model=list[EvidenceItem],
    summary="Get empirical evidence rows",
)
def get_run_evidence(run_id: str) -> list[EvidenceItem]:
    """Retrieve empirical evidence measurements with confidence intervals and thresholds."""
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )

    # The policy engine, not the individual check, decides each check's state.
    # Re-run that pure, deterministic evaluation so the UI shows the engine's result.
    engine_states: dict[str, str] = {}
    try:
        policy = load_policy(str(run.mission.get("policy_id", "software-testing")))
        bundle = evaluate_policy_detailed(policy, run.evidence)
        engine_states = {cid: ev.state.value for cid, ev in bundle.check_evaluations.items()}
    except Exception:
        engine_states = {}

    items: list[EvidenceItem] = []
    for raw in run.evidence:
        rec = raw if isinstance(raw, dict) else (
            raw.to_dict() if hasattr(raw, "to_dict") else dict(raw.__dict__)
        )
        check_id = str(rec.get("check_id") or rec.get("check") or "unknown")
        items.append(
            EvidenceItem(
                check_id=check_id,
                value=rec.get("value"),
                ci_low=rec.get("ci_low"),
                ci_high=rec.get("ci_high"),
                n=rec.get("n"),
                seed=rec.get("seed"),
                state=engine_states.get(check_id) or rec.get("state"),
                threshold_ref=rec.get("threshold_ref") or rec.get("threshold"),
                extra=rec.get("extra", {}),
            )
        )
    return items


@router.get(
    "/{run_id}/events",
    summary="Subscribe to SSE stream of agent steps and candidate evaluations",
)
async def get_run_events(run_id: str) -> StreamingResponse:
    """Stream real-time server-sent events for agent actions, repairs, and rejections."""
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )

    existing_events, queue = run_store.subscribe_events(run_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Replay previously logged events
            for ev in existing_events:
                yield f"data: {json.dumps(ev)}\n\n"

            # If already terminal, close stream
            if run.status in ("COMPLETED", "FAILED"):
                return

            # Stream upcoming events
            while True:
                try:
                    ev = await asyncio.wait_for(queue.get(), timeout=2.0)
                    yield f"data: {json.dumps(ev)}\n\n"
                    if ev.get("type") in ("completed", "failed"):
                        break
                except TimeoutError:
                    if run.status in ("COMPLETED", "FAILED"):
                        break
                    yield ": ping\n\n"
        finally:
            run_store.unsubscribe_events(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/{run_id}/approve",
    response_model=ApproveResponse,
    summary="Authorize human release approval and re-sign passport",
)
def approve_run(
    run_id: str,
    payload: ApproveRequest,
    x_approver_token: str | None = Header(default=None),
) -> ApproveResponse:
    """Record human approver identifier and re-sign Evidence Passport."""
    # When SYNPASSPORT_APPROVER_TOKEN is configured, approvals require that shared secret.
    if APPROVER_TOKEN and not (
        x_approver_token and hmac.compare_digest(x_approver_token, APPROVER_TOKEN)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid X-Approver-Token header is required to approve releases",
        )

    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )

    if run.status != "COMPLETED" or not run.passport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Run must be in COMPLETED state before human approval can be granted",
        )

    current_approval = run.passport.get("human_approval")
    if isinstance(current_approval, dict) and current_approval.get("status") == "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Passport has already been approved",
        )

    verdict_values = set((run.passport.get("verdicts") or {}).values())
    if not verdict_values & {"PASS", "WARNING"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve a passport with no PASS or WARNING verdicts",
        )

    signing_key, _ = get_or_create_server_key()

    approved_passport = approve_passport(
        passport=run.passport,
        approver=payload.approver,
        signing_key=signing_key,
    )

    with run._lock:
        run.passport = approved_passport
        passport_file = run.run_dir / "passport.json"
        passport_file.write_text(
            json.dumps(approved_passport, indent=2),
            encoding="utf-8",
        )

    log_run_event(
        logger,
        logging.INFO,
        f"Recorded human approval by {payload.approver}",
        run_id=run_id,
        approver=payload.approver,
    )
    run_store.add_event(run_id, "approved", {"approver": payload.approver})

    return ApproveResponse(
        status="APPROVED",
        approver=payload.approver,
        passport=approved_passport,
    )


@router.get(
    "/{run_id}/passport",
    summary="Get signed Evidence Passport JSON",
)
def get_run_passport(run_id: str) -> JSONResponse:
    """Return signed Evidence Passport JSON document."""
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )

    if not run.passport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passport is not yet available for this run",
        )

    return JSONResponse(content=run.passport)


@router.get(
    "/{run_id}/dataset",
    summary="Download the exact synthetic dataset the passport is bound to",
    response_class=PlainTextResponse,
)
def get_run_dataset(run_id: str) -> PlainTextResponse:
    """Return the bound candidate CSV byte-for-byte, so clients can hash and verify it."""
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )
    if not run.passport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Passport is not yet available for this run",
        )

    bound_name = Path(str((run.passport.get("dataset") or {}).get("name", ""))).name
    dataset_file = run.run_dir / bound_name if bound_name else None
    if dataset_file is None or not dataset_file.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The dataset bound to this passport was not found on the server",
        )

    # Decode without newline translation so the client receives the exact signed bytes.
    content = dataset_file.read_bytes().decode("utf-8")
    return PlainTextResponse(content=content, media_type="text/csv; charset=utf-8")


@router.get(
    "/{run_id}/sufficiency",
    response_model=SufficiencyResponse,
    summary="Evaluate subgroup sample size sufficiency and CI width",
)
def get_run_sufficiency(run_id: str) -> SufficiencyResponse:
    """Return current sample size N, required min N, and projected CI width per subgroup."""
    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found",
        )

    if not run.dataset_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset file not found for sufficiency evaluation",
        )

    real_df = pd.read_csv(run.dataset_path)

    critical_subgroups = run.mission.get("critical_subgroups", [])
    if not critical_subgroups:
        critical_subgroups = ["age >= 65"]

    checker = SufficiencyCheck()
    subgroup_items: list[SubgroupSufficiencyItem] = []

    for query in critical_subgroups:
        res = checker.run(real_df, None, subgroup_query=query)
        meta = getattr(res, "metadata", {}) or {}
        subgroup_items.append(
            SubgroupSufficiencyItem(
                subgroup_query=query,
                current_n=int(res.n or 0),
                required_min_n=int(meta.get("min_n_required", 171)),
                projected_ci_width=float(meta.get("projected_ci_width", 1.0)),
                target_ci_width=float(meta.get("target_ci_width", 0.15)),
                state=str(res.state or "UNKNOWN"),
                reason=str(meta.get("reason", "")),
            )
        )

    first_item = subgroup_items[0] if subgroup_items else None
    return SufficiencyResponse(
        run_id=run.run_id,
        current_n=first_item.current_n if first_item else len(real_df),
        required_min_n=first_item.required_min_n if first_item else 171,
        ci_width=first_item.projected_ci_width if first_item else 0.0,
        subgroups=subgroup_items,
    )


DCR_BINS = 12


@router.get(
    "/{run_id}/dcr",
    summary="Distance-to-closest-record distributions for the signed candidate",
)
def get_run_dcr(run_id: str) -> dict[str, Any]:
    """Compute the DCR distributions the privacy check compares, from this run's files.

    For a sample of synthetic rows: the distance to the closest real *training* row and
    to the closest real *holdout* row. If synthetic rows sit much closer to training
    than to holdout rows, the generator may have memorised real records.
    """
    import numpy as np
    from scipy.spatial.distance import cdist

    from synpassport.checks.privacy import _encode_and_scale

    run = run_store.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found"
        )
    if not run.passport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Passport is not yet available"
        )

    bound_name = Path(str((run.passport.get("dataset") or {}).get("name", ""))).name
    synth_file = run.run_dir / bound_name
    train_file = run.run_dir / "train_partition.csv"
    holdout_file = run.run_dir / "holdout_partition.csv"
    files_ok = synth_file.is_file() and train_file.is_file() and holdout_file.is_file()
    if not (bound_name and files_ok):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run files needed for DCR are missing"
        )

    seed = int(run.mission.get("seed", 1234))
    train = pd.read_csv(train_file)
    holdout = pd.read_csv(holdout_file)
    synth = pd.read_csv(synth_file)
    n = min(len(train), len(holdout), len(synth), 500)
    if n < 2:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Too few rows")
    tr = train.sample(n=n, random_state=seed)
    ho = holdout.sample(n=n, random_state=seed)
    sy = synth.sample(n=n, random_state=seed)
    tr_m, ho_m, sy_m = _encode_and_scale(tr, ho, sy)
    d_train = np.min(cdist(sy_m, tr_m), axis=1)
    d_holdout = np.min(cdist(sy_m, ho_m), axis=1)

    top = float(np.quantile(np.concatenate([d_train, d_holdout]), 0.98)) or 1.0
    edges = np.linspace(0.0, top, DCR_BINS + 1)
    clipped_train = np.clip(d_train, 0.0, top)
    clipped_holdout = np.clip(d_holdout, 0.0, top)
    train_counts, _ = np.histogram(clipped_train, bins=edges)
    holdout_counts, _ = np.histogram(clipped_holdout, bins=edges)

    return {
        "candidate": bound_name,
        "sample_size": int(n),
        "seed": seed,
        "bins": [
            {"low": float(edges[i]), "high": float(edges[i + 1]),
             "to_training": int(train_counts[i]), "to_holdout": int(holdout_counts[i])}
            for i in range(DCR_BINS)
        ],
        "p5_to_training": float(np.percentile(d_train, 5)),
        "p5_to_holdout": float(np.percentile(d_holdout, 5)),
        "median_to_training": float(np.median(d_train)),
        "median_to_holdout": float(np.median(d_holdout)),
        "share_closer_to_training": float(np.mean(d_train < d_holdout - 1e-5)),
        "exact_copies_of_training": int(np.sum(d_train < 1e-5)),
    }
