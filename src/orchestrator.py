"""Orchestrator — state machine for the discovery pipeline.

Concept note — why a state machine: the orchestrator controls when each
stage runs, retries, and escalates. AI is never in control of flow.
Each company moves through states: pending → in_progress → verified /
needs_review / not_found / blocked / inactive.
"""

from __future__ import annotations

import time
from typing import Optional

from .config import Config
from .db import Database
from .http import HttpClient, HttpError
from .logging import get_logger
from .models import (
    CareerDestination,
    Company,
    DiscoveryAttempt,
    DiscoveryRun,
    ErrorClass,
    ReviewQueueItem,
    Status,
)
from .stages.base import Stage, StageResult

logger = get_logger(__name__)


class Orchestrator:
    """State machine that processes companies through the discovery ladder."""

    def __init__(self, config: Config, db: Database, stages: list[Stage]):
        self.config = config
        self.db = db
        self.stages = stages

    async def process_company(
        self, company: Company, http_client: HttpClient, run_id: str
    ) -> CareerDestination:
        """Process a single company through the discovery ladder.

        Stops at the first stage that returns a verified result.
        """
        start_time = time.monotonic()
        logger.info(f"processing company {company.id}", extra={"company_id": company.id, "run_id": run_id})

        # Mark as in_progress
        self._update_status(company.id, Status.IN_PROGRESS)

        # Run each stage in order
        for stage in self.stages:
            # Skip render stage for non-JS-shell pages (it's a fallback)
            try:
                result = await stage.run(company, http_client, self.config, self.db)
            except HttpError as e:
                result = StageResult(
                    outcome="failed",
                    error_class=e.error_class,
                    error_message=str(e),
                )
            except Exception as e:
                result = StageResult(
                    outcome="failed",
                    error_class=ErrorClass.INTERNAL,
                    error_message=str(e),
                )

            # Record the attempt
            self._record_attempt(run_id, company.id, stage.name, result)

            # Check the outcome
            if result.outcome == "verified":
                dest = CareerDestination(
                    company_id=company.id,
                    status=Status.VERIFIED,
                    destination_type=result.destination_type,
                    careers_url=result.candidate_url,
                    job_board_url=result.candidate_url if result.destination_type == "ats_board" else None,
                    ats_provider=result.ats_provider,
                    ats_slug=result.ats_slug,
                    open_jobs_count=result.job_count,
                    discovery_method=stage.name,
                    confidence=0.9 if result.ats_provider else 0.7,
                    evidence_summary=str(result.evidence),
                    last_verified_at=None,
                    pipeline_version="0.1.0",
                )
                self.db.upsert_destination(dest)
                logger.info(
                    f"company {company.id} verified via {stage.name}",
                    extra={"company_id": company.id, "run_id": run_id},
                )
                return dest

            elif result.outcome == "blocked":
                self._update_status(company.id, Status.BLOCKED)
                return CareerDestination(
                    company_id=company.id,
                    status=Status.BLOCKED,
                    discovery_method=stage.name,
                    evidence_summary=result.error_message,
                    pipeline_version="0.1.0",
                )

            elif result.outcome == "needs_review":
                self._add_to_review_queue(company, stage.name, result)
                self._update_status(company.id, Status.NEEDS_REVIEW)
                return CareerDestination(
                    company_id=company.id,
                    status=Status.NEEDS_REVIEW,
                    discovery_method=stage.name,
                    evidence_summary=result.error_message,
                    pipeline_version="0.1.0",
                )

        # No stage verified — mark as not_found
        self._update_status(company.id, Status.NOT_FOUND)
        return CareerDestination(
            company_id=company.id,
            status=Status.NOT_FOUND,
            discovery_method="ladder_exhausted",
            pipeline_version="0.1.0",
        )

    def _update_status(self, company_id: str, status: Status) -> None:
        """Update the company's status in the database."""
        dest = self.db.get_destination(company_id)
        if dest:
            dest.status = status
        else:
            dest = CareerDestination(company_id=company_id, status=status)
        self.db.upsert_destination(dest)

    def _record_attempt(
        self, run_id: str, company_id: str, stage_name: str, result: StageResult
    ) -> None:
        """Record a discovery attempt."""
        attempt = DiscoveryAttempt(
            run_id=run_id,
            company_id=company_id,
            stage=stage_name,
            candidate_url=result.candidate_url,
            method=stage_name,
            output={"outcome": result.outcome, "evidence": result.evidence},
            outcome=result.outcome,
            error_class=result.error_class,
            duration=0.0,
        )
        self.db.add_attempt(attempt)

    def _add_to_review_queue(
        self, company: Company, stage_name: str, result: StageResult
    ) -> None:
        """Add a company to the review queue."""
        item = ReviewQueueItem(
            company_id=company.id,
            reason=f"{stage_name}: {result.error_message}",
            candidates=[result.candidate_url] if result.candidate_url else [],
            attempt_summary=result.error_message,
            suggested_next_action="manual_review",
        )
        self.db.add_review_item(item)
