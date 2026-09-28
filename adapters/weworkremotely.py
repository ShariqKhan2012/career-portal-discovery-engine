"""We Work Remotely source adapter.

WWR's top-remote-companies page lists 100 companies in server-rendered
HTML. Each company has a profile page at /company/{slug}.

Concept note — why HTML parsing: WWR has no public API or structured data
feed. The HTML is server-rendered (not a JS shell), so BeautifulSoup
can parse it directly.
"""

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .base import SourceAdapter

TOP_COMPANIES_URL = "https://weworkremotely.com/top-remote-companies"
COMPANY_PROFILE_URL = "https://weworkremotely.com/company/{slug}"


class WeWorkRemotelyAdapter(SourceAdapter):
    """Adapter for weworkremotely.com/top-remote-companies."""

    @property
    def name(self) -> str:
        return "weworkremotely"

    async def fetch_companies(self, http_client) -> list[dict[str, Any]]:
        """Fetch all companies from the WWR top-remote-companies page.

        1. Fetch the top-remote-companies page (1 request, cached).
        2. Parse HTML to extract company names and slugs.
        3. For each company, fetch the profile page (concurrent, cached).
        4. Parse the profile page to extract the company website URL.
        """
        # Step 1: Fetch the listing page
        result = await http_client.fetch(TOP_COMPANIES_URL)
        soup = BeautifulSoup(result.text, "lxml")

        # Step 2: Extract company entries
        # Each company is in a list item with a link to /company/{slug}
        # The company name is in a heading (h2/h3/h4) or strong text near the link
        companies = []
        seen_slugs = set()

        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("/company/") and href != "/company/":
                slug = href.split("/company/")[1].strip("/")
                if slug in seen_slugs:
                    continue

                # Try to get the company name from a heading near the link
                name = None
                parent = link.find_parent(["li", "div"])
                if parent:
                    heading = parent.find(["h2", "h3", "h4", "strong"])
                    if heading:
                        name = heading.get_text(strip=True)

                # Skip if no name found or name is a generic label
                if not name or name.lower() in ("view company profile", "view profile", ""):
                    continue

                seen_slugs.add(slug)
                companies.append({
                    "slug": slug,
                    "name": name,
                    "listed_url_raw": "",
                    "profile_url": COMPANY_PROFILE_URL.format(slug=slug),
                    "raw_metadata": {},
                })

        # Step 3: Fetch each company profile page to get the website URL
        for company in companies:
            try:
                profile_result = await http_client.fetch(company["profile_url"])
                profile_soup = BeautifulSoup(profile_result.text, "lxml")
                website = _extract_website(profile_soup)
                if website:
                    company["listed_url_raw"] = website
            except Exception:
                continue  # Skip if profile page can't be fetched

        return companies


def _extract_website(soup: BeautifulSoup) -> str:
    """Extract the company website URL from a WWR profile page.

    The profile page typically has a link to the company's own site.
    """
    # Look for a link to the company website (not WWR itself)
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if href.startswith("http") and "weworkremotely.com" not in href:
            return href
    return ""
