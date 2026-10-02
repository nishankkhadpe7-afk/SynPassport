"""Pytest configuration and test fixtures."""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Keep every test out of the project's real data/, keys/ and replay/ folders.

    The API and agent default to relative paths (./data, ./replay); without this the
    suite writes runs, staging folders, signing keys and replay entries into the repo.
    """
    workdir = tmp_path / "workspace"
    workdir.mkdir()
    monkeypatch.chdir(workdir)

    data_dir = workdir / "data"
    runs_dir = data_dir / "runs"
    key_dir = data_dir / "keys"
    monkeypatch.setattr("synpassport.api.config.DATA_DIR", data_dir)
    monkeypatch.setattr("synpassport.api.config.RUNS_DIR", runs_dir)
    monkeypatch.setattr("synpassport.api.config.KEY_DIR", key_dir)
    monkeypatch.setattr("synpassport.api.routers.runs.RUNS_DIR", runs_dir)
    monkeypatch.setattr("synpassport.api.routers.verify.RUNS_DIR", runs_dir)
    monkeypatch.setattr("synpassport.api.store.KEY_DIR", key_dir)
    monkeypatch.delenv("SYNPASSPORT_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("SYNPASSPORT_APPROVER_TOKEN", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    return workdir


@pytest.fixture
def sample_run_id() -> str:
    """Fixture providing a mock run identifier."""
    return "test-run-001"
