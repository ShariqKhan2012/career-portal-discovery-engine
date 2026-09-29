"""Configuration with all limits from the master prompt §5 and §6."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field
from dotenv import load_dotenv


class Config(BaseModel):
    """Application configuration. All limits are configurable via .env.

    Environment variables are read at instantiation time (not import time)
    so tests can override them with monkeypatch.
    """

    # --- Rate limiting (§6) ---
    requests_per_second_per_domain: float = Field(
        default=1.0, description="Max requests per second per domain"
    )
    global_concurrency: int = Field(
        default=8, description="Global concurrent request limit"
    )
    # Per-domain overrides for CDNs and APIs with different limits
    per_domain_rate_limits: dict[str, float] = Field(
        default={"raw.githubusercontent.com": 10.0, "api.github.com": 0.5},
        description="Per-domain rate limit overrides (requests/sec)",
    )

    # --- Timeouts (§5) ---
    default_timeout_seconds: float = Field(default=30.0)
    per_stage_timeout_seconds: float = Field(default=60.0)

    # --- Retries (§5) ---
    max_retries: int = Field(default=3)
    retry_backoff_base_seconds: float = Field(default=1.0)

    # --- Per-company limits (§5) ---
    max_fetches_per_company: int = Field(default=50)
    max_research_tool_calls_per_company: int = Field(default=20)
    max_research_tokens_per_company: int = Field(default=10_000)

    # --- Cost cap (§5) ---
    monthly_cost_cap_usd: float = Field(default=0.0)

    # --- Cache (§6: "Cache every HTTP response on disk") ---
    cache_dir: Path = Field(default=Path(".cache"))

    # --- Database ---
    db_path: Path = Field(default=Path("data/career_discovery.db"))

    # --- User agent (§6: "honest User-Agent with a contact placeholder") ---
    user_agent: str = Field(
        default="CareerPortalDiscovery/0.1 (+contact@example.com)"
    )

    # --- Logging ---
    log_level: str = Field(default="INFO")

    # --- API keys (loaded from .env, never hardcoded) ---
    serper_api_key: str = Field(default="")
    openrouter_api_key: str = Field(default="")
    openrouter_model: str = Field(default="anthropic/claude-3-haiku")

    def __init__(self, **data):
        # Load .env file if it exists (does not override real env vars)
        load_dotenv()
        # For fields not explicitly passed, check environment
        for field_name in type(self).model_fields:
            if field_name not in data:
                env_val = os.environ.get(field_name.upper())
                if env_val is not None:
                    data[field_name] = env_val  # Pydantic handles type coercion
        super().__init__(**data)

    def ensure_dirs(self) -> None:
        """Create cache and data directories if they don't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
