"""FastAPI application entrypoint for SynPassport assurance workflows.

Exposes REST and SSE endpoints for run initialization, candidate evaluation monitoring,
evidence inspection, human release approval, and passport issuance/verification.
"""

from fastapi import FastAPI  # pyright: ignore [reportMissingImports, missing-import]

__all__ = ["app"]

app = FastAPI(
    title="SynPassport API",
    version="0.1.0",
    description="Assurance and verification API for synthetic data Evidence Passports.",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "synpassport"}


if __name__ == "__main__":
    import uvicorn  # pyright: ignore [reportMissingImports, missing-import]

    uvicorn.run(app, host="0.0.0.0", port=8000)
