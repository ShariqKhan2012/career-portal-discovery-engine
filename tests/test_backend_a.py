"""Tests for Backend A (in-app LLM agent)."""

from src.agent.backend_a import TOOLS, _build_user_message, _load_prompt
from src.agent.contract import AgentInput


def test_tools_defined():
    """All required tools are defined."""
    tool_names = [t["function"]["name"] for t in TOOLS]
    assert "search" in tool_names
    assert "fetch" in tool_names
    assert "submit" in tool_names


def test_prompt_loaded():
    """System prompt loads from file."""
    prompt = _load_prompt()
    assert "research assistant" in prompt.lower()
    assert "never invent a url" in prompt.lower()


def test_user_message_contains_context():
    """User message includes all context."""
    inp = AgentInput(
        company_id="test",
        company_name="Test Co",
        known_domains=["test.com"],
        source_records=[{"listed_url_raw": "https://test.com"}],
        previous_attempts=[{"stage": "seed", "outcome": "failed"}],
        existing_candidates=["https://test.com/careers"],
        question="no careers link found",
    )
    msg = _build_user_message(inp)
    assert "Test Co" in msg
    assert "test.com" in msg
    assert "no careers link found" in msg
