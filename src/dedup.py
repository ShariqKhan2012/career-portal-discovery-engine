"""Deduplication by domain identity plus source evidence.

Concept note — why domain identity: the same company may appear in both
directories with slightly different names. The registrable domain is the
stable identity key. Fuzzy name matches never auto-merge — they go to review.
"""

from __future__ import annotations

from .domains import registrable_domain


def find_duplicates(companies: list[dict]) -> list[tuple[dict, dict]]:
    """Find duplicate companies by registrable domain.

    Returns pairs of (kept, merged) where kept is the one with more source
    evidence. Fuzzy name matches are NOT auto-merged.

    Each company dict must have: id, name, urls (list of URL strings).
    """
    # Group by registrable domain
    by_domain: dict[str, list[dict]] = {}
    for company in companies:
        urls = company.get("urls", [])
        for url in urls:
            domain = registrable_domain(url)
            if domain:
                by_domain.setdefault(domain, []).append(company)
                break  # One domain per company is enough for grouping

    # Find duplicates within each domain group
    duplicates = []
    for domain, group in by_domain.items():
        if len(group) < 2:
            continue
        # Sort by number of sources (descending), then by name for stability
        group.sort(key=lambda c: (-len(c.get("sources", [])), c.get("name", "")))
        kept = group[0]
        for merged in group[1:]:
            # Only auto-merge if names are similar enough
            if _names_similar(kept["name"], merged["name"]):
                duplicates.append((kept, merged))
            # Otherwise, leave for review (fuzzy match, never auto-merge)

    return duplicates


def _names_similar(name1: str, name2: str) -> bool:
    """Check if two names are similar enough for auto-merge.

    Only exact matches after normalization are auto-merged. Fuzzy matches
    (e.g. "Example Corp" vs "Example Corporation") go to review.
    """
    n1 = _normalize(name1)
    n2 = _normalize(name2)
    if not n1 or not n2:
        return False
    return n1 == n2


def _normalize(name: str) -> str:
    """Normalize a name for comparison."""
    import re
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "", name)
    return name.strip()
