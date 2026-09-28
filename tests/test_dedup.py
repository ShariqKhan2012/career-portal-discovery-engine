"""Tests for deduplication."""

from src.dedup import find_duplicates


def test_same_domain_duplicates():
    """Two companies with the same registrable domain are duplicates."""
    companies = [
        {"id": "a", "name": "Example Corp", "urls": ["https://example.com"], "sources": ["s1"]},
        {"id": "b", "name": "Example Corp", "urls": ["https://www.example.com"], "sources": ["s2"]},
    ]
    dups = find_duplicates(companies)
    assert len(dups) == 1
    kept, merged = dups[0]
    assert kept["id"] == "a"
    assert merged["id"] == "b"


def test_different_domains_no_duplicates():
    """Companies with different domains are not duplicates."""
    companies = [
        {"id": "a", "name": "Example", "urls": ["https://example.com"], "sources": ["s1"]},
        {"id": "b", "name": "Other", "urls": ["https://other.com"], "sources": ["s2"]},
    ]
    dups = find_duplicates(companies)
    assert len(dups) == 0


def test_fuzzy_name_no_auto_merge():
    """Fuzzy name matches never auto-merge — they go to review."""
    companies = [
        {"id": "a", "name": "Example Corp", "urls": ["https://example.com"], "sources": ["s1"]},
        {"id": "b", "name": "Example Corporation", "urls": ["https://www.example.com"], "sources": ["s2"]},
    ]
    dups = find_duplicates(companies)
    # "examplecorp" vs "examplecorporation" — not similar enough
    assert len(dups) == 0


def test_more_sources_wins():
    """The company with more sources is kept."""
    companies = [
        {"id": "a", "name": "Example", "urls": ["https://example.com"], "sources": ["s1"]},
        {"id": "b", "name": "Example", "urls": ["https://www.example.com"], "sources": ["s1", "s2"]},
    ]
    dups = find_duplicates(companies)
    assert len(dups) == 1
    kept, merged = dups[0]
    assert kept["id"] == "b"  # More sources
    assert merged["id"] == "a"
