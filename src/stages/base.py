"""Stage interface for the discovery ladder.

Concept note — why a common interface: the orchestrator calls each stage
without knowing which stage it's dealing with. Each stage returns a
StageResult with the outcome and evidence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from ..models import ErrorClass


@dataclass
class StageResult:
    """Result of running a discovery stage."""

    outcome: str  # "verified", "needs_review", "not_found", "blocked", "failed"
    candidate_url: str = ""
    destination_type: str = ""
    ats_provider: str = ""
    ats_slug: str = ""
    job_count: int = 0
    evidence: dict = field(default_factory=dict)
    error_class: Optional[ErrorClass] = None
    error_message: str = ""


class Stage(ABC):
    """Base class for all discovery stages."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage name (e.g. "seed", "ats_verify", "website", "crawl", "slug_probe")."""
        ...

    @abstractmethod
    async def run(self, company, http_client, config, db) -> StageResult:
        """Run the stage for a company.

        Returns a StageResult with the outcome and evidence.
        """
        ...
