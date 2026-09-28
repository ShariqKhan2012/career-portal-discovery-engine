"""Tests for ATS adapters."""

from src.ats.greenhouse import GreenhouseAdapter
from src.ats.lever import LeverAdapter
from src.ats.ashby import AshbyAdapter


# --- Greenhouse ---

def test_greenhouse_match():
    adapter = GreenhouseAdapter()
    assert adapter.match("https://boards.greenhouse.io/acme") is True
    assert adapter.match("https://job-boards.greenhouse.io/acme") is True
    assert adapter.match("https://boards.eu.greenhouse.io/acme") is True
    assert adapter.match("https://jobs.lever.co/acme") is False

def test_greenhouse_extract_slug():
    adapter = GreenhouseAdapter()
    assert adapter.extract_slug("https://boards.greenhouse.io/acme") == "acme"
    assert adapter.extract_slug("https://boards.greenhouse.io/acme/jobs/123") == "acme"
    assert adapter.extract_slug("https://jobs.lever.co/acme") is None


# --- Lever ---

def test_lever_match():
    adapter = LeverAdapter()
    assert adapter.match("https://jobs.lever.co/acme") is True
    assert adapter.match("https://jobs.eu.lever.co/acme") is True
    assert adapter.match("https://boards.greenhouse.io/acme") is False

def test_lever_extract_slug():
    adapter = LeverAdapter()
    assert adapter.extract_slug("https://jobs.lever.co/acme") == "acme"
    assert adapter.extract_slug("https://jobs.eu.lever.co/acme") == "acme"
    assert adapter.extract_slug("https://boards.greenhouse.io/acme") is None


# --- Ashby ---

def test_ashby_match():
    adapter = AshbyAdapter()
    assert adapter.match("https://jobs.ashbyhq.com/acme") is True
    assert adapter.match("https://jobs.lever.co/acme") is False

def test_ashby_extract_slug():
    adapter = AshbyAdapter()
    assert adapter.extract_slug("https://jobs.ashbyhq.com/acme") == "acme"
    assert adapter.extract_slug("https://jobs.ashbyhq.com/Deel") == "Deel"
    assert adapter.extract_slug("https://jobs.lever.co/acme") is None
