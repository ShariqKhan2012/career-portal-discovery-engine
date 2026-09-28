"""Tests for name/domain mismatch detection."""

from src.mismatch import is_mismatch


def test_mismatch_addstructure_bazaarvoice():
    """addstructure → bazaarvoice.com is a mismatch."""
    assert is_mismatch("addstructure", ["https://www.bazaarvoice.com"]) is True

def test_match_10up():
    """10up → 10up.com is a match."""
    assert is_mismatch("10up", ["https://10up.com"]) is False

def test_match_ably():
    """Ably → ably.io is a match."""
    assert is_mismatch("Ably", ["https://www.ably.io"]) is False

def test_match_with_suffix():
    """Company name with Inc suffix still matches."""
    assert is_mismatch("Acme Inc", ["https://acme.com"]) is False

def test_no_urls():
    """No URLs to compare against — not a mismatch."""
    assert is_mismatch("anything", []) is False

def test_mismatch_completely_different():
    """Completely different name and domain."""
    assert is_mismatch("Totally Different", ["https://example.com"]) is True
