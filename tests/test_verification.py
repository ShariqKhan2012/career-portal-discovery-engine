"""Tests for the verification service (§7 acceptance rules)."""

from src.verification import verify_candidate, VerificationResult


def test_verified_ats_board():
    """An API-verified ATS board with all checks passing."""
    result = verify_candidate(
        url="https://jobs.lever.co/acme",
        company_name="Acme",
        company_domain="acme.com",
        observed_this_run=True,
        shows_careers_content=True,
        ats_provider="lever",
        ats_slug="acme",
        job_count=5,
    )
    assert result.verified is True
    assert result.confidence >= 0.9


def test_not_observed_this_run():
    """A URL not observed this run is never verified."""
    result = verify_candidate(
        url="https://jobs.lever.co/acme",
        company_name="Acme",
        company_domain="acme.com",
        observed_this_run=False,
        shows_careers_content=True,
        ats_provider="lever",
        ats_slug="acme",
    )
    assert result.verified is False
    assert result.failed_check == "not_observed_this_run"


def test_does_not_belong_to_company():
    """A URL that doesn't belong to the company is not verified."""
    result = verify_candidate(
        url="https://jobs.lever.co/other-company",
        company_name="Acme",
        company_domain="acme.com",
        observed_this_run=True,
        shows_careers_content=True,
        ats_provider="lever",
        ats_slug="other-company",
    )
    assert result.verified is False
    assert result.failed_check == "does_not_belong_to_company"


def test_no_careers_content():
    """A page that doesn't show careers content is not verified."""
    result = verify_candidate(
        url="https://acme.com/about",
        company_name="Acme",
        company_domain="acme.com",
        observed_this_run=True,
        shows_careers_content=False,
    )
    assert result.verified is False
    assert result.failed_check == "no_careers_content"


def test_is_aggregator():
    """An aggregator URL is not verified."""
    result = verify_candidate(
        url="https://www.linkedin.com/company/acme/jobs",
        company_name="Acme",
        company_domain="acme.com",
        observed_this_run=True,
        shows_careers_content=True,
    )
    assert result.verified is False
    assert result.failed_check == "is_aggregator"


def test_ats_details_missing():
    """An ATS destination without a slug is not verified."""
    result = verify_candidate(
        url="https://jobs.lever.co/acme",
        company_name="Acme",
        company_domain="acme.com",
        observed_this_run=True,
        shows_careers_content=True,
        ats_provider="lever",
        ats_slug=None,
    )
    assert result.verified is False
    assert result.failed_check == "ats_details_missing"


def test_custom_page_verified():
    """A custom careers page with all checks passing."""
    result = verify_candidate(
        url="https://acme.com/careers",
        company_name="Acme",
        company_domain="acme.com",
        observed_this_run=True,
        shows_careers_content=True,
    )
    assert result.verified is True
    assert result.confidence >= 0.7
