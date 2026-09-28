"""Data models for the Career Portal Discovery Engine.

These mirror the schema in master prompt §8. All structured data in the
system uses these Pydantic models for validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums (§8: three independent axes) ---


class Status(str, Enum):
    """Where the company stands in the pipeline."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"
    NOT_FOUND = "not_found"
    BLOCKED = "blocked"
    INACTIVE = "inactive"


class DestinationType(str, Enum):
    """Set when status is verified."""

    ATS_BOARD = "ats_board"
    CUSTOM_PAGE = "custom_page"
    CUSTOM_PAGE_WITH_ATS = "custom_page_with_ats"
    CAREERS_PAGE_NO_OPENINGS = "careers_page_no_openings"
    THIRD_PARTY_OFFICIAL = "third_party_official"


class CompanyState(str, Enum):
    ACTIVE = "active"
    ACQUIRED = "acquired"
    REBRANDED = "rebranded"
    DEFUNCT = "defunct"
    UNKNOWN = "unknown"


class ErrorClass(str, Enum):
    """Error taxonomy from master prompt §4b."""

    NETWORK = "network"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    ROBOTS_DISALLOWED = "robots_disallowed"
    PARSE = "parse"
    SCHEMA = "schema"
    BUDGET_EXCEEDED = "budget_exceeded"
    INTERNAL = "internal"


# --- Core entities ---


class Company(BaseModel):
    """A company with stable identity."""

    id: str = Field(description="Stable company ID (slug or UUID)")
    name: str
    name_normalized: str = Field(description="Lowercase, punctuation-stripped name")
    official_domain: Optional[str] = Field(
        default=None, description="Registrable domain (e.g. 'example.com')"
    )
    homepage: Optional[str] = None
    region: Optional[str] = None
    company_state: CompanyState = CompanyState.UNKNOWN
    parent_company_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CompanySource(BaseModel):
    """Raw data from a directory source."""

    company_id: str
    source_name: str
    profile_url: Optional[str] = None
    listed_url_raw: Optional[str] = Field(
        default=None, description="URL exactly as listed in the directory"
    )
    listed_url_clean: Optional[str] = Field(
        default=None, description="URL after normalization"
    )
    raw_metadata: Optional[dict] = None
    seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DiscoveryRun(BaseModel):
    """A single pipeline run."""

    run_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    config_snapshot: Optional[dict] = None
    code_version: Optional[str] = None
    cost_used: float = 0.0


class DiscoveryAttempt(BaseModel):
    """One stage attempt for one company in one run."""

    run_id: str
    company_id: str
    stage: str
    candidate_url: Optional[str] = None
    method: str
    agent_involved: bool = False
    input: Optional[dict] = None
    output: Optional[dict] = None
    evidence: Optional[dict] = None
    outcome: str
    error_class: Optional[ErrorClass] = None
    duration: Optional[float] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CareerDestination(BaseModel):
    """The current accepted verdict per company."""

    company_id: str
    status: Status
    destination_type: Optional[DestinationType] = None
    careers_url: Optional[str] = None
    job_board_url: Optional[str] = None
    ats_provider: Optional[str] = None
    ats_slug: Optional[str] = None
    jobs_api_url: Optional[str] = None
    open_jobs_count: Optional[int] = None
    discovery_method: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    evidence_summary: Optional[str] = None
    fallback_urls: list[str] = Field(default_factory=list)
    last_verified_at: Optional[datetime] = None
    pipeline_version: Optional[str] = None


class ReviewQueueItem(BaseModel):
    """An unresolved case awaiting human review."""

    company_id: str
    reason: str
    candidates: list[str] = Field(default_factory=list)
    attempt_summary: Optional[str] = None
    suggested_next_action: Optional[str] = None
    resolution: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None


class MergeRecord(BaseModel):
    """A deduplication decision with evidence."""

    kept_company_id: str
    merged_company_id: str
    reason: str
    evidence: Optional[dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
