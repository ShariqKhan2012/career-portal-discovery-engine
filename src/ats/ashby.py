"""Ashby ATS adapter."""

from __future__ import annotations

from .base import ATSAdapter, BoardVerification


class AshbyAdapter(ATSAdapter):
    """Adapter for Ashby (jobs.ashbyhq.com)."""

    @property
    def provider_id(self) -> str:
        return "ashby"

    def match(self, url: str) -> bool:
        return "jobs.ashbyhq.com" in url

    def extract_slug(self, url: str) -> str | None:
        # jobs.ashbyhq.com/{slug} → {slug}
        if "jobs.ashbyhq.com/" in url:
            slug = url.split("jobs.ashbyhq.com/")[1].split("/")[0]
            return slug or None
        return None

    async def verify_board(self, slug: str, http_client) -> BoardVerification:
        api_url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
        try:
            result = await http_client.fetch(api_url)
            if result.status_code == 200:
                import json
                data = json.loads(result.text)
                jobs = data.get("jobPosts", [])
                return BoardVerification(
                    exists=True,
                    canonical_url=f"https://jobs.ashbyhq.com/{slug}",
                    company_name_shown=data.get("companyName", slug),
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
