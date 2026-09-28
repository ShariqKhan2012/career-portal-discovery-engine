"""Tests for configuration."""

from src.config import Config


def test_default_config():
    config = Config()
    assert config.requests_per_second_per_domain == 1.0
    assert config.global_concurrency == 8
    assert config.max_retries == 3
    assert config.monthly_cost_cap_usd == 0.0


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("REQUESTS_PER_SECOND_PER_DOMAIN", "2.0")
    monkeypatch.setenv("GLOBAL_CONCURRENCY", "4")
    config = Config()
    assert config.requests_per_second_per_domain == 2.0
    assert config.global_concurrency == 4


def test_ensure_dirs(tmp_path):
    config = Config(
        cache_dir=tmp_path / "new_cache",
        db_path=tmp_path / "new_data" / "test.db",
    )
    config.ensure_dirs()
    assert config.cache_dir.exists()
    assert config.db_path.parent.exists()
