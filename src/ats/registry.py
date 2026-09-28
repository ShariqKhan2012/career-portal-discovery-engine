"""ATS registry loader — loads provider configs from ats_patterns.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_registry(path: str | Path = "ats_patterns.json") -> dict[str, Any]:
    """Load the ATS pattern registry from JSON."""
    with open(path) as f:
        return json.load(f)


def get_provider_config(registry: dict, provider_id: str) -> dict | None:
    """Get a specific provider's config from the registry."""
    for provider in registry.get("providers", []):
        if provider["id"] == provider_id:
            return provider
    return None


def get_aggregator_hosts(registry: dict) -> set[str]:
    """Get the set of aggregator/social hosts."""
    return set(registry.get("aggregator_hosts", []))
