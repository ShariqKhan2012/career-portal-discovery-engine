"""Backend A: In-app LLM agent.

An LLM called through OpenRouter's API, behind a small swappable
interface. It has only these tools: search, fetch, submit.

Concept note — why Backend A is the production target: it is schedulable,
testable, and needs no human present. Backend B (operator agent) is for
learning and early evaluation.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from ..config import Config
from ..http import HttpClient
from ..logging import get_logger
from .contract import AgentInput, AgentOutput
from .llm import call_llm_with_tools
from .search import search

logger = get_logger(__name__)

# Tool definitions for the LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch",
            "description": "Fetch a URL and extract its text and links",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to fetch"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit",
            "description": "Submit your research findings",
            "parameters": {
                "type": "object",
                "properties": {
                    "status_proposal": {
                        "type": "string",
                        "enum": ["verified", "needs_review", "not_found"],
                    },
                    "careers_url": {"type": "string"},
                    "job_board_url": {"type": "string"},
                    "ats_provider": {"type": "string"},
                    "ats_slug": {"type": "string"},
                    "candidates_considered": {"type": "array", "items": {"type": "string"}},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "observation": {"type": "string"},
                                "why_it_matters": {"type": "string"},
                            },
                        },
                    },
                    "confidence": {"type": "number"},
                    "reasoning_summary": {"type": "string"},
                    "open_questions": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["status_proposal", "confidence", "reasoning_summary"],
            },
        },
    },
]


async def run_agent(
    inp: AgentInput,
    config: Config,
    http_client: HttpClient,
) -> AgentOutput:
    """Run the in-app LLM agent on a company.

    The agent can search, fetch, and submit. The orchestrator will
    independently re-verify everything.
    """
    # Build the system prompt
    system_prompt = _load_prompt()

    # Build the user message
    user_message = _build_user_message(inp)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # Define tool handlers
    def handle_search(query: str) -> str:
        results = search(query, config)
        return json.dumps(results)

    def handle_fetch(url: str) -> str:
        try:
            result = http_client.fetch(url)
            # Extract text and links (truncated)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(result.text, "lxml")
            text = soup.get_text(separator="\n", strip=True)[:2000]
            links = [a["href"] for a in soup.find_all("a", href=True)][:20]
            return json.dumps({"url": url, "text": text, "links": links})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def handle_submit(**kwargs) -> str:
        return json.dumps({"status": "submitted"})

    tool_handlers = {
        "search": handle_search,
        "fetch": handle_fetch,
        "submit": handle_submit,
    }

    # Run the LLM with tools
    response = call_llm_with_tools(messages, TOOLS, tool_handlers, config)

    # Parse the response
    try:
        content = response.get("content", "")
        if content:
            return AgentOutput(**json.loads(content))
    except (json.JSONDecodeError, ValidationError) as e:
        logger.error(f"failed to parse agent response: {e}")

    # Fallback: return a needs_review result
    return AgentOutput(
        status_proposal="needs_review",
        confidence=0.0,
        reasoning_summary="Failed to parse agent response",
    )


def _load_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    from pathlib import Path
    prompt_path = Path(__file__).parent / "prompts" / "research.txt"
    return prompt_path.read_text()


def _build_user_message(inp: AgentInput) -> str:
    """Build the user message with all context."""
    parts = [
        f"Company: {inp.company_name}",
        f"Known domains: {', '.join(inp.known_domains)}",
        f"Question: {inp.question}",
    ]

    if inp.source_records:
        parts.append(f"Source records: {json.dumps(inp.source_records)}")

    if inp.previous_attempts:
        parts.append(f"Previous attempts: {json.dumps(inp.previous_attempts)}")

    if inp.existing_candidates:
        parts.append(f"Existing candidates: {', '.join(inp.existing_candidates)}")

    return "\n".join(parts)
