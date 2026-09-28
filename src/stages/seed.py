"""Stage 1: Seed classification.

Classifies the listed URL from the directory as one of:
- official website
- ATS board
- careers page
- aggregator
- social profile
- short URL
- invalid

If it's an ATS board, extracts the provider and slug.
"""

from __future__ import annotations

from urllib.parse import urlparse

from ..ats.greenhouse import GreenhouseAdapter
from ..ats.lever import LeverAdapter
from ..ats.ashby import AshbyAdapter
from ..models import ErrorClass
from .base import Stage, StageResult


class SeedStage(Stage):
    """Stage 1: Classify the listed URL."""

    @property
    def name(self) -> str:
        return "seed"

    async def run(self, company, http_client, config, db) -> StageResult:
        """Classify the listed URL."""
        # Get the listed URL from the company's source
        listed_url = self._get_listed_url(company, db)
        if not listed_url:
            return StageResult(
                outcome="failed",
                error_class=ErrorClass.SCHEMA,
                error_message="no listed URL",
            )

        # Check if it's a short URL
        from ..normalize import is_shortener
        if is_shortener(listed_url):
            return StageResult(
                outcome="needs_review",
                candidate_url=listed_url,
                error_message="short URL needs expansion",
            )

        # Check if it's an ATS board
        ats_adapters = [GreenhouseAdapter(), LeverAdapter(), AshbyAdapter()]
        for adapter in ats_adapters:
            if adapter.match(listed_url):
                slug = adapter.extract_slug(listed_url)
                if slug:
                    return StageResult(
                        outcome="verified",
                        candidate_url=listed_url,
                        destination_type="ats_board",
                        ats_provider=adapter.provider_id,
                        ats_slug=slug,
                        evidence={"stage": "seed", "ats_provider": adapter.provider_id},
                    )

        # Check if it's an aggregator or social network
        if self._is_aggregator(listed_url):
            return StageResult(
                outcome="needs_review",
                candidate_url=listed_url,
                error_message="aggregator URL",
            )

        # Check if it's a careers page
        if self._is_careers_page(listed_url):
            return StageResult(
                outcome="verified",
                candidate_url=listed_url,
                destination_type="custom_page",
                evidence={"stage": "seed"},
            )

        # Check if it's an official website
        if self._is_official_website(listed_url, company):
            return StageResult(
                outcome="needs_review",
                candidate_url=listed_url,
                error_message="official website, not careers page",
            )

        # Unknown
        return StageResult(
            outcome="needs_review",
            candidate_url=listed_url,
            error_message="unclassified URL",
        )

    def _get_listed_url(self, company, db) -> str:
        """Get the listed URL from the company's source."""
        conn = db.connect()
        row = conn.execute(
            "SELECT listed_url_clean FROM company_sources WHERE company_id = ?",
            (company.id,),
        ).fetchone()
        return row[0] if row and row[0] else ""

    def _is_aggregator(self, url: str) -> bool:
        """Check if the URL is an aggregator or social network."""
        aggregators = {
            "linkedin.com", "glassdoor.com", "angel.co", "wellfound.com",
            "x.com", "twitter.com", "ycombinator.com", "remoteok.io",
            "remoteok.com", "weworkremotely.com", "remoters.net",
            "weloveremotejobs.com", "welcometothejungle.com",
        }
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain in aggregators

    def _is_careers_page(self, url: str) -> bool:
        """Check if the URL looks like a careers page."""
        careers_paths = ["/careers", "/jobs", "/join", "/work-with-us", "/hiring", "/about/careers"]
        parsed = urlparse(url)
        path = parsed.path.lower()
        return any(path.startswith(cp) for cp in careers_paths)

    def _is_official_website(self, url: str, company) -> bool:
        """Check if the URL is the company's official website."""
        from ..domains import registrable_domain
        url_domain = registrable_domain(url)
        if not url_domain or not company.official_domain:
            return False
        return url_domain.lower() == company.official_domain.lower()
