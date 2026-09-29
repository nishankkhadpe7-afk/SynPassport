"""Pytest configuration and test fixtures."""

import pytest


@pytest.fixture
def sample_run_id() -> str:
    """Fixture providing a mock run identifier."""
    return "test-run-001"
