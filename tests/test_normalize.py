"""Tests for URL normalization — covers Appendix B cases."""

from src.normalize import (
    normalize_url,
    strip_trailing_punctuation,
    repair_broken_markdown,
    remove_tracking_params,
    upgrade_to_https,
    is_shortener,
)


# --- strip_trailing_punctuation ---

def test_strip_trailing_brackets():
    assert strip_trailing_punctuation("https://www.akamai.com/careers]]") == "https://www.akamai.com/careers"

def test_strip_trailing_comma():
    assert strip_trailing_punctuation("https://alley.co/careers/,") == "https://alley.co/careers/"

def test_strip_trailing_dot():
    assert strip_trailing_punctuation("https://www.carmatec.com/careers/.") == "https://www.carmatec.com/careers/"

def test_strip_trailing_mixed():
    assert strip_trailing_punctuation("https.com/path.,;!") == "https.com/path"

def test_no_trailing_punctuation():
    assert strip_trailing_punctuation("https://example.com/careers") == "https://example.com/careers"


# --- repair_broken_markdown ---

def test_repair_markdown_link():
    url = "https://aulaatcoventry.notion.site/career](https://…)"
    assert repair_broken_markdown(url) == "https://aulaatcoventry.notion.site/career"

def test_replain_url():
    assert repair_broken_markdown("https://example.com") == "https://example.com"


# --- remove_tracking_params ---

def test_remove_utm_params():
    url = "https://www.npmjs.com/jobs?utm_source=nodeweekly&utm_medium=email"
    assert remove_tracking_params(url) == "https://www.npmjs.com/jobs"

def test_remove_fbclid():
    url = "https://example.com/careers?fbclid=abc123"
    assert remove_tracking_params(url) == "https://example.com/careers"

def test_keep_non_tracking_params():
    url = "https://example.com/jobs?department=engineering"
    assert remove_tracking_params(url) == "https://example.com/jobs?department=engineering"

def test_no_params():
    url = "https://example.com/careers"
    assert remove_tracking_params(url) == "https://example.com/careers"


# --- upgrade_to_https ---

def test_upgrade_http():
    assert upgrade_to_https("http://jobs.ably.io") == "https://jobs.ably.io"

def test_already_https():
    assert upgrade_to_https("https://example.com") == "https://example.com"


# --- is_shortener ---

def test_is_shortener():
    assert is_shortener("https://bit.ly/3yz4YLc") is True

def test_is_not_shortener():
    assert is_shortener("https://example.com") is False


# --- normalize_url (full pipeline) ---

def test_normalize_full_pipeline():
    """Test the full normalization pipeline."""
    # Broken markdown + trailing punctuation
    assert normalize_url("https://aulaatcoventry.notion.site/career](https://…)") == "https://aulaatcoventry.notion.site/career"
    # Trailing comma
    assert normalize_url("https://alley.co/careers/,") == "https://alley.co/careers/"
    # Trailing dot
    assert normalize_url("https://www.carmatec.com/careers/.") == "https://www.carmatec.com/careers/"
    # Tracking params
    assert normalize_url("https://www.npmjs.com/jobs?utm_source=nodeweekly&utm_medium=email") == "https://www.npmjs.com/jobs"
    # HTTP upgrade
    assert normalize_url("http://jobs.ably.io") == "https://jobs.ably.io"
    # Combined: http + tracking
    assert normalize_url("http://example.com/jobs?utm_source=test") == "https://example.com/jobs"
