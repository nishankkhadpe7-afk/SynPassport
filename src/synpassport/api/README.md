# REST API & Async Server (`synpassport.api`)

The `synpassport.api` module implements an asynchronous FastAPI web service providing HTTP REST endpoints for dataset verification, asynchronous synthesis & assurance job runs, Server-Sent Events (SSE) progress streaming, and human approval co-signing.

---

## Module Layout

- [`main.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/main.py): FastAPI application lifecycle, startup key initialization (`get_or_create_server_key`), router inclusion.
- [`config.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/config.py): Environment settings (`SYNPASSPORT_APPROVAL_TOKEN`, key paths, storage dirs).
- [`models.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/models.py): Pydantic API request & response payload schemas.
- [`store.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/store.py): Thread-safe in-memory and SQLite run state store.
- [`logging.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/logging.py): Structured JSON logging.
- [`routers/verify.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/routers/verify.py): `POST /verify` endpoint handler.
- [`routers/runs.py`](file:///Users/vanshjain/Desktop/SynPassport/src/synpassport/api/routers/runs.py): `POST /runs`, `GET /runs/{id}`, SSE, evidence, sufficiency & approval endpoints.

---

## API Endpoints Reference

### 1. `POST /verify`
Verifies synthetic dataset bytes against passport JSON.
- **Request**: Multipart form data containing `dataset` (file) and `passport` (JSON file), or JSON body with raw bytes.
- **Security**: In-memory byte verification (no disk temp files created).
- **Response**:
```json
{
  "valid": true,
  "reason": "OK",
  "details": {
    "key_id": "8f3e2a1b...",
    "purpose": "analytics_internal"
  }
}
```

### 2. `POST /runs`
Submits background synthesis and assurance job.
- **Response**: `202 Accepted` returning `{"run_id": "run_12345", "status": "PENDING"}`.

### 3. `GET /runs/{id}`
Polls current execution status, candidate iterations, and policy verdicts.

### 4. `GET /runs/{id}/events`
Server-Sent Events (SSE) endpoint emitting real-time event logs (`text/event-stream`).

### 5. `GET /runs/{id}/passport`
Returns final signed Evidence Passport JSON upon completion.

### 6. `POST /runs/{id}/approve`
Co-signs passport with human approval.
- **Authentication**: Requires `X-Approval-Token` header matching `SYNPASSPORT_APPROVAL_TOKEN` environment variable if configured.

---

## Running Server

```bash
uvicorn synpassport.api.main:app --host 0.0.0.0 --port 8000
```
