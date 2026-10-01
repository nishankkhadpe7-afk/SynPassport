"""Dataset and Evidence Passport verification endpoints."""

from __future__ import annotations

import json
import logging
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

        resolved_purpose = body.get("purpose")
        resolved_allow_warning = bool(body.get("allow_warning", False))

        # Preferred path: run_id provided — read passport and dataset directly from disk,
        # bypassing JS JSON round-trip that mutates float values and breaks the signature.
        run_id_val = body.get("run_id")
        if run_id_val:
            run_dir = RUNS_DIR / str(run_id_val)
            passport_on_disk = run_dir / "passport.json"
            # Use the candidate CSV that was actually signed (candidate_001.csv or latest)
            candidate_csvs = sorted(run_dir.glob("candidate_*.csv"))
            dataset_on_disk = candidate_csvs[-1] if candidate_csvs else None

            if passport_on_disk.is_file():
                pass_file_path = passport_on_disk
            if dataset_on_disk and dataset_on_disk.is_file():
                data_file_path = dataset_on_disk

        if "dataset_path" in body and Path(body["dataset_path"]).is_file():
            data_file_path = Path(body["dataset_path"])
        elif "dataset_content" in body and data_file_path is None:
            data_file_path = staging_dir / "dataset.csv"
            data_file_path.write_text(str(body["dataset_content"]), encoding="utf-8")

        if "passport_path" in body and Path(body["passport_path"]).is_file():
            pass_file_path = Path(body["passport_path"])
        elif "passport" in body and pass_file_path is None:
            # Last resort: write the passport from the JS object — may fail sig check
            # due to float mutation, but kept as fallback for external callers.
            pass_file_path = staging_dir / "passport.json"
            p_val = body["passport"]
            pass_file_path.write_text(
                json.dumps(p_val) if isinstance(p_val, dict) else str(p_val),
                encoding="utf-8",
            )

    # 2. Parse Multipart form fields if multipart/form-data
    if "multipart/form-data" in content_type:
        form = await request.form()

        d_val = form.get("dataset")
        if isinstance(d_val, UploadFile):
            d_bytes = await d_val.read()
            if len(d_bytes) > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Uploaded dataset exceeds max limit of {MAX_UPLOAD_SIZE} bytes",
                )
            data_file_path = staging_dir / "dataset.csv"
            data_file_path.write_bytes(d_bytes)
        elif isinstance(d_val, str) and d_val.strip():
            data_file_path = staging_dir / "dataset.csv"
            data_file_path.write_text(d_val, encoding="utf-8")

        p_val = form.get("passport")
        if isinstance(p_val, UploadFile):
            p_bytes = await p_val.read()
            pass_file_path = staging_dir / "passport.json"
            pass_file_path.write_bytes(p_bytes)
        elif isinstance(p_val, str) and p_val.strip():
            pass_file_path = staging_dir / "passport.json"
            pass_file_path.write_text(p_val, encoding="utf-8")

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

    # Resolve candidate public key from server keypair if available
    _, server_pub_path = get_or_create_server_key()

    result = verify(
        dataset_path=data_file_path,
        passport_path=pass_file_path,
        purpose=resolved_purpose,
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
