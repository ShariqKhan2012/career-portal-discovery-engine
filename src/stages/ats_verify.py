"""Stage 2: ATS verification.

Calls the provider adapter's verify_board method to confirm the board
exists and belongs to the company.
"""

from __future__ import annotations

from ..ats.greenhouse import GreenhouseAdapter
from ..ats.lever import LeverAdapter
from ..ats.ashby import AshbyAdapter
from .base import Stage, StageResult


class ATSVerifyStage(Stage):
    """Stage 2: Verify ATS boards."""

    @property
    def name(self) -> str:
        return "ats_verify"

    async def run(self, company, http_client, config, db) -> StageResult:
        """Verify the ATS board for a company."""
        # Get the ATS provider and slug from the company's source
        conn = db.connect()
        row = conn.execute(
            "SELECT listed_url_clean FROM company_sources WHERE company_id = ?",
            (company.id,),
        ).fetchone()
        listed_url = row[0] if row and row[0] else ""

        if not listed_url:
            return StageResult(
                outcome="not_found",
                error_message="no listed URL",
            )

        # Check if it's an ATS board
        from ..ats.greenhouse import GreenhouseAdapter
        from ..ats.lever import LeverAdapter
        from ..ats.ashby import AshbyAdapter

        adapters = [GreenhouseAdapter(), LeverAdapter(), AshbyAdapter()]
        for adapter in adapters:
            if adapter.match(listed_url):
                slug = adapter.extract_slug(listed_url)
                if slug:
                    result = await adapter.verify_board(slug, http_client)
                    if result.exists:
                        return StageResult(
                            outcome="verified",
                            candidate_url=result.canonical_url,
                            destination_type="ats_board",
                            ats_provider=adapter.provider_id,
                            ats_slug=slug,
                            job_count=result.job_count,
                            evidence={"stage": "ats_verify", "slug": slug},
                        )
                    else:
                        return StageResult(
                            outcome="not_found",
                            error_message=f"ATS board not found: {adapter.provider_id}/{slug}",
                        )

        return StageResult(
            outcome="not_found",
            error_message="not an ATS board",
        )
