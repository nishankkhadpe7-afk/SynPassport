"""Dataset and Evidence Passport verification endpoints."""

from __future__ import annotations

import json
import logging
import re
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    status,
)
from starlette.datastructures import UploadFile

from synpassport.api.config import MAX_UPLOAD_SIZE, RUNS_DIR
from synpassport.api.logging import get_logger, log_run_event
from synpassport.api.models import VerifyResponse
from synpassport.api.store import get_or_create_server_key
from synpassport.sdk.verify import verify

__all__ = ["router"]

router = APIRouter(tags=["verify"])
logger = get_logger("synpassport.api.verify")


RUN_ID_PATTERN = re.compile(r"^run_[0-9a-f]{12}$")


def _path_inside_runs_dir(raw: Any) -> Path | None:
    """Resolve a client-supplied server path, accepting it only inside RUNS_DIR."""
    try:
        candidate = Path(str(raw)).resolve()
    except (OSError, ValueError):
        return None
    runs_root = RUNS_DIR.resolve()
    if not candidate.is_relative_to(runs_root) or not candidate.is_file():
        return None
    return candidate


def _run_artifacts(run_id: str) -> tuple[Path | None, Path | None]:
    """Locate a run's signed passport and the exact dataset file it is bound to."""
    if not RUN_ID_PATTERN.match(run_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid run_id format",
        )
    run_dir = RUNS_DIR / run_id
    passport_file = run_dir / "passport.json"
    if not passport_file.is_file():
        return None, None

    # Use the dataset named inside the passport (the best candidate actually signed),
    # not simply the most recent candidate file in the directory.
    try:
        passport_data = json.loads(passport_file.read_text(encoding="utf-8"))
        bound_name = Path(str(passport_data.get("dataset", {}).get("name", ""))).name
    except (OSError, ValueError, AttributeError):
        bound_name = ""
    dataset_file = run_dir / bound_name if bound_name else None
    if dataset_file is None or not dataset_file.is_file():
        dataset_file = None
    return passport_file, dataset_file


def _check_size(num_bytes: int, label: str) -> None:
    if num_bytes > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded {label} exceeds max limit of {MAX_UPLOAD_SIZE} bytes",
        )


@router.post(
    "/verify",
    response_model=VerifyResponse,
    summary="Cryptographically verify dataset against its Evidence Passport",
)
async def verify_dataset_passport(
    request: Request,
) -> VerifyResponse:
    """Verify Ed25519 signature, dataset SHA-256 hash, purpose verdicts, and human approval."""
    verify_id = f"verify_{uuid.uuid4().hex[:8]}"
    staging_dir = RUNS_DIR / "staging" / verify_id
    staging_dir.mkdir(parents=True, exist_ok=True)
    try:
        return await _verify_impl(request, staging_dir)
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)


async def _verify_impl(request: Request, staging_dir: Path) -> VerifyResponse:
    # Text from the client is written as raw UTF-8 bytes, never in text mode: on Windows,
    # text mode turns "\n" into "\r\n" and the SHA-256 would never match the passport.
    data_file_path: Path | None = None
    pass_file_path: Path | None = None
    resolved_purpose: str | None = None
    resolved_allow_warning: bool = False

    # 1. Parse JSON body if Content-Type is application/json
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            body: dict[str, Any] = await request.json()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Malformed JSON request body: {exc}",
            ) from exc
        if not isinstance(body, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="JSON request body must be an object",
            )

        resolved_purpose = body.get("purpose")
        resolved_allow_warning = bool(body.get("allow_warning", False))

        # Preferred path: run_id provided — read the signed passport and the dataset it
        # is bound to directly from disk.
        run_id_val = body.get("run_id")
        if run_id_val:
            pass_file_path, data_file_path = _run_artifacts(str(run_id_val))

        # Server-side paths are only honoured inside the runs directory.
        if "dataset_path" in body:
            safe = _path_inside_runs_dir(body["dataset_path"])
            if safe is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="dataset_path must point to a file inside the runs directory",
                )
            data_file_path = safe
        elif "dataset_content" in body and data_file_path is None:
            content = str(body["dataset_content"])
            _check_size(len(content.encode("utf-8")), "dataset")
            data_file_path = staging_dir / "dataset.csv"
            data_file_path.write_bytes(content.encode("utf-8"))

        if "passport_path" in body:
            safe = _path_inside_runs_dir(body["passport_path"])
            if safe is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="passport_path must point to a file inside the runs directory",
                )
            pass_file_path = safe
        elif "passport" in body and pass_file_path is None:
            p_val = body["passport"]
            p_text = json.dumps(p_val) if isinstance(p_val, dict) else str(p_val)
            _check_size(len(p_text.encode("utf-8")), "passport")
            pass_file_path = staging_dir / "passport.json"
            pass_file_path.write_bytes(p_text.encode("utf-8"))

    # 2. Parse Multipart form fields if multipart/form-data
    if "multipart/form-data" in content_type:
        form = await request.form()

        d_val = form.get("dataset")
        if isinstance(d_val, UploadFile):
            d_bytes = await d_val.read(MAX_UPLOAD_SIZE + 1)
            _check_size(len(d_bytes), "dataset")
            data_file_path = staging_dir / "dataset.csv"
            data_file_path.write_bytes(d_bytes)
        elif isinstance(d_val, str) and d_val.strip():
            _check_size(len(d_val.encode("utf-8")), "dataset")
            data_file_path = staging_dir / "dataset.csv"
            data_file_path.write_bytes(d_val.encode("utf-8"))

        p_val = form.get("passport")
        if isinstance(p_val, UploadFile):
            p_bytes = await p_val.read(MAX_UPLOAD_SIZE + 1)
            _check_size(len(p_bytes), "passport")
            pass_file_path = staging_dir / "passport.json"
            pass_file_path.write_bytes(p_bytes)
        elif isinstance(p_val, str) and p_val.strip():
            pass_file_path = staging_dir / "passport.json"
            pass_file_path.write_bytes(p_val.encode("utf-8"))

        if form.get("purpose"):
            resolved_purpose = str(form.get("purpose"))

        if form.get("allow_warning") is not None:
            resolved_allow_warning = str(form.get("allow_warning")).lower() in (
                "true",
                "1",
                "yes",
            )

    if not data_file_path or not pass_file_path or not resolved_purpose:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Fields 'dataset', 'passport', and 'purpose' are strictly required",
        )

    # The server only trusts its own signing key.
    _, server_pub_path = get_or_create_server_key()

    result = verify(
        dataset_path=data_file_path,
        passport_path=pass_file_path,
        purpose=str(resolved_purpose),
        allow_warning=resolved_allow_warning,
        public_key=server_pub_path,
    )

    log_run_event(
        logger,
        logging.INFO,
        f"Executed passport verification: valid={result.valid}, reason={result.reason_code}",
        purpose=resolved_purpose,
        reason_code=result.reason_code,
    )

    res_dict = result.to_dict()
    return VerifyResponse(
        valid=result.valid,
        reason_code=result.reason_code,
        description=res_dict.get("description", ""),
        details=result.details,
    )
