"""Remote In Tech source adapter.

Uses the GitHub repo (remoteintech/remote-jobs) as the structured data
source instead of scraping HTML. Each company is a markdown file with
YAML frontmatter in src/companies/{slug}.md.

Concept note — why the GitHub repo: the site is generated from this repo.
Using the repo directly gives structured data (frontmatter) instead of
parsing HTML, and is more reliable.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from .base import SourceAdapter

REPO_API = "https://api.github.com/repos/remoteintech/remote-jobs"
RAW_BASE = "https://raw.githubusercontent.com/remoteintech/remote-jobs/main"


class RemoteInTechAdapter(SourceAdapter):
    """Adapter for remoteintech.company via its GitHub repo."""

    @property
    def name(self) -> str:
        return "remoteintech"

    async def fetch_companies(self, http_client) -> list[dict[str, Any]]:
        """Fetch all companies from the GitHub repo.

        1. Get the file tree from the GitHub API (1 request, cached).
        2. Filter for src/companies/*.md files.
        3. Fetch each file's raw content (concurrent, cached on disk).
        4. Parse YAML frontmatter.
        """
        # Step 1: Get the file tree
        tree_url = f"{REPO_API}/git/trees/main?recursive=1"
        try:
            result = await http_client.fetch(tree_url)
        except Exception:
            # Fallback: try the master branch
            tree_url = f"{REPO_API}/git/trees/master?recursive=1"
            result = await http_client.fetch(tree_url)

        tree_data = json.loads(result.text)
        company_files = [
            item["path"] for item in tree_data.get("tree", [])
            if item["path"].startswith("src/companies/") and item["path"].endswith(".md")
        ]

        # Step 2: Fetch each file's raw content concurrently
        import asyncio

        async def fetch_one(path: str) -> dict[str, Any] | None:
            slug = path.split("/")[-1].replace(".md", "")
            raw_url = f"{RAW_BASE}/{path}"
            try:
                raw_result = await http_client.fetch(raw_url)
                raw_text = raw_result.text
            except Exception:
                return None

            frontmatter = _parse_frontmatter(raw_text)
            if not frontmatter:
                return None

            return {
                "slug": slug,
                "name": frontmatter.get("title", slug),
                "listed_url_raw": frontmatter.get("careers_url", ""),
                "profile_url": f"https://remoteintech.company/companies/{slug}/",
                "raw_metadata": {
                    "website": frontmatter.get("website", ""),
                    "region": frontmatter.get("region", ""),
                    "remote_policy": frontmatter.get("remote_policy", ""),
                    "company_size": frontmatter.get("company_size", ""),
                    "technologies": frontmatter.get("technologies", []),
                    "added_at": frontmatter.get("addedAt", ""),
                    "updated_at": frontmatter.get("updatedAt", ""),
                },
            }

        # Fetch all files concurrently (HTTP client handles rate limiting)
        tasks = [fetch_one(path) for path in company_files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        companies = []
        for result in results:
            if isinstance(result, dict):
                companies.append(result)
            # Skip exceptions and None results

        return companies


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a markdown file.

    Simple parser for the specific format used by remote-jobs.
    Handles: strings, lists, and basic types.
    """
    if not text.startswith("---"):
        return {}

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}

    frontmatter_text = parts[1]
    result: dict[str, Any] = {}
    current_key = None
    current_list = None

    for line in frontmatter_text.strip().split("\n"):
        line = line.rstrip()
        if not line:
            continue

        # List item
        if line.strip().startswith("- ") and current_key:
            if current_list is None:
                current_list = []
            value = line.strip()[2:].strip().strip('"').strip("'")
            current_list.append(value)
            result[current_key] = current_list
            continue

        # Key-value pair
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            current_key = key
            current_list = None

            if value:
                # Remove quotes
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]
                result[key] = value
            else:
                result[key] = ""

    return result
