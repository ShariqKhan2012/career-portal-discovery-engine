"""Tests for the AI research agent module."""

from src.agent.contract import AgentInput, AgentOutput, EvidenceItem


def test_agent_input_schema():
    """AgentInput has all required fields."""
    inp = AgentInput(
        company_id="test",
        company_name="Test Co",
        question="no careers link found",
    )
    assert inp.company_id == "test"
    assert inp.company_name == "Test Co"
    assert inp.known_domains == []
    assert inp.source_records == []


def test_agent_output_schema():
    """AgentOutput has all required fields."""
    out = AgentOutput(
        status_proposal="verified",
        careers_url="https://test.com/careers",
        confidence=0.9,
    )
    assert out.status_proposal == "verified"
    assert out.careers_url == "https://test.com/careers"
    assert out.confidence == 0.9


def test_evidence_item():
    """EvidenceItem has all required fields."""
    ev = EvidenceItem(
        url="https://test.com/careers",
        observation="Careers page with 5 job listings",
        why_it_matters="Shows active hiring",
    )
    assert ev.url == "https://test.com/careers"
    assert "5 job listings" in ev.observation


def test_agent_output_with_evidence():
    """AgentOutput can include evidence."""
    out = AgentOutput(
        status_proposal="verified",
        careers_url="https://test.com/careers",
        evidence=[
            EvidenceItem(
                url="https://test.com/careers",
                observation="Careers page",
                why_it_matters="Shows jobs",
            )
        ],
        confidence=0.9,
    )
    assert len(out.evidence) == 1
    assert out.evidence[0].url == "https://test.com/careers"
