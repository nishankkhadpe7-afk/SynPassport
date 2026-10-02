"""FastAPI application entrypoint for SynPassport assurance workflows.

Exposes REST and SSE endpoints for run initialization, candidate evaluation monitoring,
evidence inspection, human release approval, and passport issuance/verification.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from synpassport.api.config import CORS_ORIGINS, REPLAY_MODE
from synpassport.api.routers import policies, runs, verify

__all__ = ["app"]

app = FastAPI(
    title="SynPassport API",
    version="0.1.0",
    description="Assurance and verification API for synthetic data Evidence Passports.",
)

# CORS configuration for development and UI dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers split by concern
app.include_router(runs.router)
app.include_router(verify.router)
app.include_router(policies.router)


@app.get("/health", summary="Service health status")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "synpassport"}


@app.get("/config", summary="Service configuration status")
def service_config() -> dict[str, object]:
    """Retrieve service runtime flags."""
    return {
        "replay_mode": REPLAY_MODE,
        "service": "synpassport",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
