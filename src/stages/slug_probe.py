"""Stage 5: Slug probing.

Generates a bounded set of candidate slugs from the name and domain,
then queries the ATS adapters. Applies the collision guard.
"""

from __future__ import annotations

import re

from ..ats.greenhouse import GreenhouseAdapter
from ..ats.lever import LeverAdapter
from ..ats.ashby import AshbyAdapter
from .base import Stage, StageResult


class SlugProbeStage(Stage):
    """Stage 5: Probe ATS slugs."""

    @property
    def name(self) -> str:
        return "slug_probe"

    async def run(self, company, http_client, config, db) -> StageResult:
        """Probe ATS slugs for a company."""
        # Generate candidate slugs
        slugs = self._generate_slugs(company)
        if not slugs:
            return StageResult(
                outcome="not_found",
                error_message="no candidate slugs generated",
            )

        # Try each ATS provider
        adapters = [GreenhouseAdapter(), LeverAdapter(), AshbyAdapter()]
        for adapter in adapters:
            for slug in slugs:
                try:
                    result = await adapter.verify_board(slug, http_client)
                    if result.exists:
                        return StageResult(
                            outcome="verified",
                            candidate_url=result.canonical_url,
                            destination_type="ats_board",
                            ats_provider=adapter.provider_id,
                            ats_slug=slug,
                            job_count=result.job_count,
                            evidence={"stage": "slug_probe", "slug": slug},
                        )
                except Exception:
                    continue

        return StageResult(
            outcome="not_found",
            error_message="no ATS board found by slug probing",
        )

    def _generate_slugs(self, company) -> list[str]:
        """Generate candidate slugs from the company name and domain."""
        slugs = set()

        # From company name
        name = company.name.lower()
        name = re.sub(r"[^a-z0-9]", "", name)
        if name:
            slugs.add(name)

        # From domain
        if company.official_domain:
            domain = company.official_domain.split(".")[0].lower()
            domain = re.sub(r"[^a-z0-9]", "", domain)
            if domain:
                slugs.add(domain)

        return list(slugs)
