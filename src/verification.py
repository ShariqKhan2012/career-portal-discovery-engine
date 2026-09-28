"""Verification service — implements the §7 acceptance rules.

A candidate is `verified` only if ALL of the following hold:
1. Observed this run
2. Belongs to the company
3. Shows careers content
4. Not an aggregator or social network
5. ATS details recorded (for ATS destinations)

Concept note — why a separate service: verification rules are the core
trust boundary of the system. Keeping them in one place makes them
testable and auditable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .ats.registry import get_aggregator_hosts, load_registry


@dataclass
class VerificationResult:
    """Result of verifying a candidate."""

    verified: bool
    failed_check: Optional[str] = None
    confidence: float = 0.0
    evidence: dict = field(default_factory=dict)


def verify_candidate(
    url: str,
    company_name: str,
    company_domain: str | None,
    observed_this_run: bool,
    shows_careers_content: bool,
    ats_provider: str | None = None,
    ats_slug: str | None = None,
    job_count: int | None = None,
) -> VerificationResult:
    """Verify a candidate against the §7 acceptance rules.

    Returns VerificationResult with verified=True only if all checks pass.
    """
    # Check 1: Observed this run
    if not observed_this_run:
        return VerificationResult(
            verified=False,
            failed_check="not_observed_this_run",
            confidence=0.0,
        )

    # Check 2: Not an aggregator or social network (check before company check)
    if _is_aggregator(url):
        return VerificationResult(
            verified=False,
            failed_check="is_aggregator",
            confidence=0.0,
        )

    # Check 3: Belongs to the company
    if not _belongs_to_company(url, company_name, company_domain):
        return VerificationResult(
            verified=False,
            failed_check="does_not_belong_to_company",
            confidence=0.0,
        )

    # Check 4: Shows careers content
    if not shows_careers_content:
        return VerificationResult(
            verified=False,
            failed_check="no_careers_content",
            confidence=0.0,
        )

    # Check 5: ATS details recorded (for ATS destinations)
    if ats_provider and not ats_slug:
        return VerificationResult(
            verified=False,
            failed_check="ats_details_missing",
            confidence=0.0,
        )

    # All checks passed
    confidence = _compute_confidence(ats_provider, job_count)
    return VerificationResult(
        verified=True,
        confidence=confidence,
        evidence={
            "url": url,
            "ats_provider": ats_provider,
            "ats_slug": ats_slug,
            "job_count": job_count,
        },
    )


def _belongs_to_company(url: str, company_name: str, company_domain: str | None) -> bool:
    """Check if the URL belongs to the company.

    The host is either the company's official domain (or a subdomain),
    or a recognized ATS host whose slug matches the company name
    (slug-collision guard).
    """
    from .domains import registrable_domain, full_domain

    url_domain = registrable_domain(url)
    if not url_domain:
        return False

    # Check against company domain
    if company_domain and url_domain.lower() == company_domain.lower():
        return True

    # Check if it's a known ATS host
    ats_hosts = {
        "boards.greenhouse.io", "job-boards.greenhouse.io", "boards.eu.greenhouse.io",
        "jobs.lever.co", "jobs.eu.lever.co",
        "jobs.ashbyhq.com",
        "apply.workable.com",
        "jobs.smartrecruiters.com", "careers.smartrecruiters.com",
    }
    url_full = full_domain(url)
    if url_full and url_full.lower() in ats_hosts:
        # Slug-collision guard: the slug must match the company name
        slug = _extract_ats_slug(url)
        if slug and _name_matches_slug(company_name, slug):
            return True
        return False

    return False


def _extract_ats_slug(url: str) -> str | None:
    """Extract the ATS slug from a URL."""
    for prefix in [
        "boards.greenhouse.io/", "job-boards.greenhouse.io/", "boards.eu.greenhouse.io/",
        "jobs.lever.co/", "jobs.eu.lever.co/",
        "jobs.ashbyhq.com/",
    ]:
        if prefix in url:
            slug = url.split(prefix)[1].split("/")[0]
            return slug or None
    return None


def _name_matches_slug(company_name: str, slug: str) -> bool:
    """Check if the company name matches the ATS slug.

    Normalizes both and checks for a match. This is the slug-collision
    guard: a matching slug alone is never enough.
    """
    name_norm = re.sub(r"[^a-z0-9]", "", company_name.lower())
    slug_norm = re.sub(r"[^a-z0-9]", "", slug.lower())
    if not name_norm or not slug_norm:
        return False
    return name_norm == slug_norm or name_norm in slug_norm or slug_norm in name_norm


def _is_aggregator(url: str) -> bool:
    """Check if the URL is an aggregator or social network."""
    registry = load_registry()
    aggregator_hosts = get_aggregator_hosts(registry)

    from .domains import full_domain
    url_domain = full_domain(url)
    if not url_domain:
        return False

    # Check exact match and parent domain
    for host in aggregator_hosts:
        if url_domain.lower() == host or url_domain.lower().endswith("." + host):
            return True

    return False


def _compute_confidence(ats_provider: str | None, job_count: int | None) -> float:
    """Compute a confidence score based on the evidence.

    API-verified board with name match scores higher than a page found
    by crawling alone, which scores higher than a single agent observation.
    """
    if ats_provider:
        # API-verified ATS board
        base = 0.9
        if job_count is not None and job_count > 0:
            base += 0.05  # Has active job postings
        return min(base, 1.0)
    else:
        # Page found by crawling
        return 0.7
