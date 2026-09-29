"""Stage 6: Headless rendering.

Uses Playwright to render JavaScript-heavy pages that can't be parsed
with BeautifulSoup alone. Blocks unnecessary resources, uses bounded
waits, and re-runs detectors on the rendered DOM.

Concept note — why bounded waits: an indefinite network-idle wait can
hang forever on pages with long-polling or analytics. We wait for a
selector or a fixed timeout, never indefinite.
"""

from __future__ import annotations

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page, Browser

from .base import Stage, StageResult

# Multilingual career terms (same as crawl stage)
CAREER_TERMS = [
    "careers", "jobs", "join us", "work with us", "hiring", "open positions",
    "karriere", "carreiras", "trabalhe conosco", "empleo", "emprego",
    "emplois", "vacatures", "lavora con noi", "kariera",
]

# Resources to block for faster rendering
BLOCKED_RESOURCE_TYPES = {"image", "stylesheet", "font", "media"}


class RenderStage(Stage):
    """Stage 6: Headless rendering for JS-shell pages."""

    @property
    def name(self) -> str:
        return "render"

    async def run(self, company, http_client, config, db) -> StageResult:
        """Render the page with Playwright and detect careers content."""
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

        try:
            result = await self._render_and_detect(listed_url)
            if result:
                return result
        except Exception as e:
            return StageResult(
                outcome="failed",
                error_message=f"render failed: {e}",
            )

        return StageResult(
            outcome="not_found",
            error_message="no careers content found after rendering",
        )

    async def _render_and_detect(self, url: str) -> StageResult | None:
        """Render the page and detect careers content."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    user_agent="CareerPortalDiscovery/0.1 (+contact@example.com)",
                )
                page = await context.new_page()

                # Block unnecessary resources for faster rendering
                await page.route(
                    "**/*",
                    lambda route: route.abort()
                    if route.request.resource_type in BLOCKED_RESOURCE_TYPES
                    else route.continue_(),
                )

                # Navigate with a bounded timeout
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")

                # Wait a bit for JS to render (bounded)
                await page.wait_for_timeout(2000)

                # Get the rendered HTML
                html = await page.content()
                soup = BeautifulSoup(html, "lxml")

                # Scan for career terms in links
                for link in soup.find_all("a", href=True):
                    text = link.get_text(strip=True).lower()
                    href = link["href"]
                    if any(term in text for term in CAREER_TERMS):
                        return StageResult(
                            outcome="verified",
                            candidate_url=href,
                            destination_type="custom_page",
                            evidence={"stage": "render", "link_text": text},
                        )

                # Check for ATS embeds
                ats_evidence = self._detect_ats_embeds(soup)
                if ats_evidence:
                    return StageResult(
                        outcome="verified",
                        candidate_url=url,
                        destination_type="ats_board",
                        ats_provider=ats_evidence["provider"],
                        ats_slug=ats_evidence["slug"],
                        evidence={"stage": "render", "ats_embed": ats_evidence},
                    )

                return None
            finally:
                await browser.close()

    def _detect_ats_embeds(self, soup: BeautifulSoup) -> dict | None:
        """Detect ATS embeds in the rendered DOM."""
        # Check for Greenhouse embeds
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            if "greenhouse.io/embed" in src:
                # Extract slug from embed URL
                if "for=" in src:
                    slug = src.split("for=")[1].split("&")[0]
                    return {"provider": "greenhouse", "slug": slug}

        # Check for Lever embeds
        for script in soup.find_all("script"):
            src = script.get("src", "")
            if "lever.co" in src:
                return {"provider": "lever", "slug": ""}

        return None
