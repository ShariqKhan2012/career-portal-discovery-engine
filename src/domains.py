"""Registrable domain computation using a public-suffix library.

Concept note — why registrable domains: "example.co.uk" and "example.com"
are different companies, but "www.example.com" and "api.example.com" are
the same. The registrable domain (eTLD+1) is the identity key.
"""

from __future__ import annotations

import tldextract


def registrable_domain(url: str) -> str | None:
    """Extract the registrable domain (eTLD+1) from a URL.

    Returns None if the domain cannot be determined.
    Examples:
        https://www.example.com/path  →  example.com
        https://api.example.co.uk    →  example.co.uk
        not-a-url                    →  None
    """
    if not url:
        return None
    # Ensure URL has a scheme for tldextract
    if "://" not in url:
        url = "https://" + url
    extracted = tldextract.extract(url)
    if not extracted.domain or not extracted.suffix:
        return None
    return f"{extracted.domain}.{extracted.suffix}"


def full_domain(url: str) -> str | None:
    """Extract the full domain (including subdomain) from a URL.

    Examples:
        https://www.example.com/path  →  www.example.com
        https://api.example.co.uk    →  api.example.co.uk
    """
    if not url:
        return None
    if "://" not in url:
        url = "https://" + url
    extracted = tldextract.extract(url)
    if not extracted.domain or not extracted.suffix:
        return None
    parts = []
    if extracted.subdomain:
        parts.append(extracted.subdomain)
    parts.append(extracted.domain)
    parts.append(extracted.suffix)
    return ".".join(parts)


def is_subdomain(url: str, parent_domain: str) -> bool:
    """Check if the URL's registrable domain matches the parent domain."""
    reg = registrable_domain(url)
    return reg is not None and reg.lower() == parent_domain.lower()
