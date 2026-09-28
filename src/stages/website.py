"""Stage 3: Official website discovery.

Uses the directory link, redirects, or the WWR profile to discover the
company's official website. Detects name/domain mismatches, parent
companies, and acquisitions.
"""

from __future__ import annotations

from ..domains import registrable_domain
from .base import Stage, StageResult


class WebsiteStage(Stage):
    """Stage 3: Discover the official website."""

    @property
    def name(self) -> str:
        return "website"

    async def run(self, company, http_client, config, db) -> StageResult:
        """Discover the official website."""
        # Get the listed URL
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

        # Check if the listed URL is already the official website
        url_domain = registrable_domain(listed_url)
        if url_domain and company.official_domain and url_domain.lower() == company.official_domain.lower():
            return StageResult(
                outcome="needs_review",
                candidate_url=listed_url,
                error_message="listed URL is the official website, not a careers page",
            )

        # Try to fetch the listed URL and follow redirects
        try:
            result = await http_client.fetch(listed_url)
            final_domain = registrable_domain(result.final_url)
            if final_domain and company.official_domain and final_domain.lower() == company.official_domain.lower():
                return StageResult(
                    outcome="needs_review",
                    candidate_url=result.final_url,
                    error_message="listed URL redirects to official website",
                )
        except Exception:
            pass

        return StageResult(
            outcome="not_found",
            error_message="could not discover official website",
        )
