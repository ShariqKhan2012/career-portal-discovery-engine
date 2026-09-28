"""Source adapter interface.

Concept note — why adapters: adding a new directory means writing one
adapter and nothing else. The adapter converts source-specific data into
the common CompanySource format.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.models import CompanySource


class SourceAdapter(ABC):
    """Base class for all source adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique source name."""
        ...

    @abstractmethod
    async def fetch_companies(self, http_client) -> list[dict[str, Any]]:
        """Fetch raw company data from the source.

        Returns a list of dicts with at least: name, listed_url, profile_url.
        """
        ...

    def to_company_source(self, company_id: str, raw: dict[str, Any]) -> CompanySource:
        """Convert raw source data to a CompanySource model."""
        return CompanySource(
            company_id=company_id,
            source_name=self.name,
            profile_url=raw.get("profile_url"),
            listed_url_raw=raw.get("listed_url_raw"),
            listed_url_clean=raw.get("listed_url_clean"),
            raw_metadata=raw.get("raw_metadata"),
        )
