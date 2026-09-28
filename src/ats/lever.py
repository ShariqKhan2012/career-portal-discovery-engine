"""Lever ATS adapter."""

from __future__ import annotations

from .base import ATSAdapter, BoardVerification


class LeverAdapter(ATSAdapter):
    """Adapter for Lever (jobs.lever.co)."""

    @property
    def provider_id(self) -> str:
        return "lever"

    def match(self, url: str) -> bool:
        return "jobs.lever.co" in url or "jobs.eu.lever.co" in url

    def extract_slug(self, url: str) -> str | None:
        # jobs.lever.co/{slug} → {slug}
        for prefix in ["jobs.lever.co/", "jobs.eu.lever.co/"]:
            if prefix in url:
                slug = url.split(prefix)[1].split("/")[0]
                return slug or None
        return None

    async def verify_board(self, slug: str, http_client) -> BoardVerification:
        api_url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        try:
            result = await http_client.fetch(api_url)
            if result.status_code == 200:
                import json
                data = json.loads(result.text)
                if isinstance(data, list):
                    return BoardVerification(
                        exists=True,
                        canonical_url=f"https://jobs.lever.co/{slug}",
                        company_name_shown=slug,
                        job_count=len(data),
                        evidence={"api_url": api_url, "job_count": len(data)},
                    )
                else:
                    return BoardVerification(exists=False, error="Unexpected API response format")
            else:
                return BoardVerification(
                    exists=False,
                    error=f"HTTP {result.status_code}",
                )
        except Exception as e:
            return BoardVerification(exists=False, error=str(e))
