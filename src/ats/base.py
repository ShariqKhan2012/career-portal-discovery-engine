"""ATS adapter interface.

Each ATS provider implements: match, extract_slug, verify_board.
Concept note — why a common interface: the discovery ladder calls these
methods without knowing which provider it's dealing with. Adding a new
ATS provider means writing one adapter and nothing else.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BoardVerification:
    """Result of verifying an ATS board."""

    exists: bool
    canonical_url: str = ""
    company_name_shown: str = ""
    job_count: int = 0
    evidence: dict = field(default_factory=dict)
    error: Optional[str] = None


class ATSAdapter(ABC):
    """Base class for all ATS provider adapters."""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique provider identifier (e.g. 'greenhouse', 'lever')."""
        ...

    @abstractmethod
    def match(self, url: str) -> bool:
        """Check if a URL belongs to this ATS provider."""
        ...

    @abstractmethod
    def extract_slug(self, url: str) -> Optional[str]:
        """Extract the company slug from a URL.

        Returns None if no slug can be extracted.
        """
        ...

    @abstractmethod
    async def verify_board(self, slug: str, http_client) -> BoardVerification:
        """Verify that a board exists and belongs to the company.

        Returns BoardVerification with exists=True if the board is valid.
        """
        ...
