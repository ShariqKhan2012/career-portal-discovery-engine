"""Name/domain mismatch detection.

Concept note — why detect mismatches: a directory entry for "addstructure"
listing "bazaarvoice.com" is either a data error or a company that was
acquired. Either way, it needs investigation, not silent acceptance.
"""

from __future__ import annotations

import re

from .domains import registrable_domain


def _normalize_name(name: str) -> str:
    """Normalize a company name for comparison."""
    name = name.lower()
    # Remove common suffixes
    for suffix in [" inc", " llc", " ltd", " gmbh", " corp", " co", " company", " technologies", " technology"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    # Remove non-alphanumeric
    name = re.sub(r"[^a-z0-9]", "", name)
    return name.strip()


def _domain_to_name(domain: str) -> str:
    """Convert a domain to a comparable name string.

    Example: "bazaarvoice.com" → "bazaarvoice"
    """
    if not domain:
        return ""
    parts = domain.split(".")
    if len(parts) >= 2:
        return parts[-2]
    return parts[0] if parts else ""


def is_mismatch(company_name: str, urls: list[str]) -> bool:
    """Check if a company name doesn't match any of its URLs.

    A mismatch is when the company name shares no significant token
    with any of the URL domains.
    """
    if not urls:
        return False

    name_norm = _normalize_name(company_name)
    if not name_norm:
        return False

    for url in urls:
        domain = registrable_domain(url)
        if not domain:
            continue
        domain_name = _domain_to_name(domain)
        if not domain_name:
            continue
        # Check if the domain name appears in the company name or vice versa
        if domain_name in name_norm or name_norm in domain_name:
            return False
        # Check for partial matches (at least 3 chars)
        if len(domain_name) >= 3 and domain_name[:3] in name_norm:
            return False
        if len(name_norm) >= 3 and name_norm[:3] in domain_name:
            return False

    return True
