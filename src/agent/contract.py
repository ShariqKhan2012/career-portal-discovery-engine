"""Submission contract for AI research.

Defines the input (agent-next) and output (agent-submit) schema.
Both backends (A: in-app LLM, B: operator agent) satisfy this contract.

Concept note — why a contract: the orchestrator doesn't care who performs
the research. It only cares that the submission is schema-valid and
independently re-verified.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    """Input to the research agent (from agent-next)."""

    company_id: str
    company_name: str
    known_domains: list[str] = Field(default_factory=list)
    source_records: list[dict] = Field(default_factory=list)
    previous_attempts: list[dict] = Field(default_factory=list)
    existing_candidates: list[str] = Field(default_factory=list)
    question: str  # "no careers link found", "choose between candidates", "is this an ATS?"


class EvidenceItem(BaseModel):
    """A single piece of evidence."""

    url: str
    observation: str
    why_it_matters: str


class AgentOutput(BaseModel):
    """Output from the research agent (to agent-submit)."""

    status_proposal: str  # "verified", "needs_review", "not_found"
    careers_url: str = ""
    job_board_url: str = ""
    ats_provider: str = ""
    ats_slug: str = ""
    candidates_considered: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning_summary: str = ""
    open_questions: list[str] = Field(default_factory=list)
