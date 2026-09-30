"""Run management and monitoring endpoints for SynPassport API."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncGenerator

import pandas as pd
import yaml
from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from starlette.datastructures import UploadFile

from synpassport.api.config import MAX_UPLOAD_SIZE, RUNS_DIR
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

    # Stage dataset file with size checking
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    staged_dataset_path = run_dir / "dataset.csv"

    dataset_bytes = await dataset_field.read()
    if len(dataset_bytes) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum permitted limit of {MAX_UPLOAD_SIZE} bytes",
        )

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

    items: list[EvidenceItem] = []
    for raw in run.evidence:
        rec = raw if isinstance(raw, dict) else (
            raw.to_dict() if hasattr(raw, "to_dict") else dict(raw.__dict__)
        )
        items.append(
            EvidenceItem(
                check_id=str(rec.get("check_id") or rec.get("check") or "unknown"),
                value=rec.get("value"),
                ci_low=rec.get("ci_low"),
                ci_high=rec.get("ci_high"),
                n=rec.get("n"),
                seed=rec.get("seed"),
                state=rec.get("state"),
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
def approve_run(run_id: str, payload: ApproveRequest) -> ApproveResponse:
    """Record human approver identifier and re-sign Evidence Passport."""
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
