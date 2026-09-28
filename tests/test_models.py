"""Tests for data models and semantic rules."""

from src.models import (
    Company,
    CompanyState,
    DestinationType,
    Status,
)


def test_company_defaults():
    company = Company(id="test-co", name="Test Co", name_normalized="test co")
    assert company.company_state == CompanyState.UNKNOWN
    assert company.parent_company_id is None


def test_status_values():
    """Every status in the taxonomy exists."""
    expected = {"pending", "in_progress", "verified", "needs_review", "not_found", "blocked", "inactive"}
    actual = {s.value for s in Status}
    assert expected == actual


def test_destination_type_values():
    expected = {"ats_board", "custom_page", "custom_page_with_ats", "careers_page_no_openings", "third_party_official"}
    actual = {d.value for d in DestinationType}
    assert expected == actual


def test_company_state_values():
    expected = {"active", "acquired", "rebranded", "defunct", "unknown"}
    actual = {s.value for s in CompanyState}
    assert expected == actual


def test_semantic_rule_blocked_not_inactive():
    """blocked != inactive — they are different statuses."""
    assert Status.BLOCKED != Status.INACTIVE


def test_semantic_rule_not_found_not_inactive():
    """not_found != inactive."""
    assert Status.NOT_FOUND != Status.INACTIVE
