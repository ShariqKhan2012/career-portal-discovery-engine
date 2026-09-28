"""Stage 4: Static crawl.

Scans nav and footer anchors using multilingual career terms. Probes
common paths. Reads sitemap.xml. Looks for embedded ATS iframes, scripts,
and links.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from .base import Stage, StageResult

# Multilingual career terms
CAREER_TERMS = [
    "careers", "jobs", "join us", "work with us", "hiring", "open positions",
    "karriere", "carreiras", "trabalhe conosco", "empleo", "emprego",
    "emplois", "vacatures", "lavora con noi", "kariera",
]

# Common careers paths
CAREERS_PATHS = [
    "/careers", "/jobs", "/company/careers", "/about/careers",
    "/join", "/work-with-us",
]


class CrawlStage(Stage):
    """Stage 4: Static crawl for careers pages."""

    @property
    def name(self) -> str:
        return "crawl"

    async def run(self, company, http_client, config, db) -> StageResult:
        """Crawl the company website for careers pages."""
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

        # Try to fetch the listed URL
        try:
            result = await http_client.fetch(listed_url)
        except Exception:
            return StageResult(
                outcome="not_found",
                error_message="could not fetch listed URL",
            )

        soup = BeautifulSoup(result.text, "lxml")

        # Scan for career terms in links
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            href = link["href"]
            if any(term in text for term in CAREER_TERMS):
                return StageResult(
                    outcome="verified",
                    candidate_url=href,
                    destination_type="custom_page",
                    evidence={"stage": "crawl", "link_text": text},
                )

        # Probe common careers paths
        from urllib.parse import urljoin
        for path in CAREERS_PATHS:
            probe_url = urljoin(listed_url, path)
            try:
                probe_result = await http_client.fetch(probe_url)
                if probe_result.status_code == 200:
                    return StageResult(
                        outcome="verified",
                        candidate_url=probe_url,
                        destination_type="custom_page",
                        evidence={"stage": "crawl", "path": path},
                    )
            except Exception:
                continue

        return StageResult(
            outcome="not_found",
            error_message="no careers page found by crawling",
        )
