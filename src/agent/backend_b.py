"""Backend B: Operator agent.

A human or coding-agent subagent pulls work with agent-next and submits
with agent-submit. It is cheaper to start and useful for learning and
early evaluation. It is never allowed to write to the database or edit
source code.

Concept note — why Backend B first: it gives direct visibility into the
research process and produces the evaluation data needed to design
Backend A's prompts and tools.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .contract import AgentInput, AgentOutput


def agent_next(company_id: str, db) -> AgentInput:
    """Pull the next company for research.

    Returns an AgentInput with all the context the researcher needs.
    """
    from ..models import Status

    company = db.get_company(company_id)
    if not company:
        raise ValueError(f"company {company_id} not found")

    # Get source records
    conn = db.connect()
    rows = conn.execute(
        "SELECT listed_url_raw, listed_url_clean, profile_url FROM company_sources WHERE company_id = ?",
        (company_id,),
    ).fetchall()
    source_records = [
        {"listed_url_raw": r[0], "listed_url_clean": r[1], "profile_url": r[2]}
        for r in rows
    ]

    # Get previous attempts
    rows = conn.execute(
        "SELECT stage, outcome, candidate_url, evidence FROM discovery_attempts WHERE company_id = ?",
        (company_id,),
    ).fetchall()
    previous_attempts = [
        {"stage": r[0], "outcome": r[1], "candidate_url": r[2], "evidence": r[3]}
        for r in rows
    ]

    # Get existing candidates
    dest = db.get_destination(company_id)
    existing_candidates = dest.careers_url if dest and dest.careers_url else []

    return AgentInput(
        company_id=company_id,
        company_name=company.name,
        known_domains=[company.official_domain] if company.official_domain else [],
        source_records=source_records,
        previous_attempts=previous_attempts,
        existing_candidates=[existing_candidates] if existing_candidates else [],
        question="no careers link found",
    )


def agent_submit(output: AgentOutput, db) -> dict:
    """Submit a research result.

    Validates the schema, then the orchestrator independently re-fetches
    and re-verifies every URL before accepting.

    Returns a dict with the verdict.
    """
    # Validate schema (already validated by Pydantic, but double-check)
    if not output.status_proposal:
        raise ValueError("status_proposal is required")

    # The orchestrator will re-verify everything
    # For now, just return the output
    return {
        "status": "submitted",
        "company_id": output.careers_url,
        "proposal": output.status_proposal,
        "confidence": output.confidence,
    }
