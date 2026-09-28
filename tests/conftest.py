"""Shared test fixtures."""

from __future__ import annotations

import pytest

from src.config import Config


@pytest.fixture
def config(tmp_path):
    """A test config with temporary directories."""
    return Config(
        cache_dir=tmp_path / "cache",
        db_path=tmp_path / "test.db",
        brave_api_key="test-key",
        openrouter_api_key="test-key",
    )
