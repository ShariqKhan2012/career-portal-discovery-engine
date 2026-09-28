"""Greenhouse ATS adapter."""

from __future__ import annotations

from .base import ATSAdapter, BoardVerification


class GreenhouseAdapter(ATSAdapter):
    """Adapter for Greenhouse (boards.greenhouse.io)."""

    @property
    def provider_id(self) -> str:
        return "greenhouse"

    def match(self, url: str) -> bool:
        return (
            "boards.greenhouse.io" in url
            or "job-boards.greenhouse.io" in url
            or "boards.eu.greenhouse.io" in url
        )

    def extract_slug(self, url: str) -> str | None:
        # boards.greenhouse.io/{slug}/jobs/123 → {slug}
        # boards.greenhouse.io/{slug} → {slug}
        parts = url.split("boards.greenhouse.io/")
        if len(parts) < 2:
            parts = url.split("job-boards.greenhouse.io/")
        if len(parts) < 2:
            parts = url.split("boards.eu.greenhouse.io/")
        if len(parts) < 2:
            return None
        slug = parts[1].split("/")[0]
        return slug or None

    async def verify_board(self, slug: str, http_client) -> BoardVerification:
        api_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
        try:
            result = await http_client.fetch(api_url)
            if result.status_code == 200:
                import json
                data = json.loads(result.text)
                jobs = data.get("jobs", [])
                return BoardVerification(
                    exists=True,
                    canonical_url=f"https://boards.greenhouse.io/{slug}",
                    company_name_shown=slug,
                    job_count=len(jobs),
                    evidence={"api_url": api_url, "job_count": len(jobs)},
                )
            else:
                return BoardVerification(
                    exists=False,
                    error=f"HTTP {result.status_code}",
                )
        except Exception as e:
            return BoardVerification(exists=False, error=str(e))
