"""Tests for registrable domain computation."""

from src.domains import registrable_domain, full_domain, is_subdomain


def test_simple_domain():
    assert registrable_domain("https://www.example.com/path") == "example.com"

def test_domain_with_subdomain():
    assert registrable_domain("https://api.example.com") == "example.com"

def test_co_uk():
    assert registrable_domain("https://www.example.co.uk") == "example.co.uk"

def test_no_scheme():
    assert registrable_domain("example.com") == "example.com"

def test_invalid_url():
    assert registrable_domain("not-a-url") is None

def test_empty():
    assert registrable_domain("") is None


def test_full_domain_with_subdomain():
    assert full_domain("https://www.example.com/path") == "www.example.com"

def test_full_domain_without_subdomain():
    assert full_domain("https://example.com") == "example.com"

def test_is_subdomain_match():
    assert is_subdomain("https://api.example.com", "example.com") is True

def test_is_subdomain_no_match():
    assert is_subdomain("https://other.com", "example.com") is False
