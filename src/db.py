"""Database layer: SQLite with migrations.

All database writes go through this module. No direct SQL in business logic.
Concept note — why migrations: the schema evolves over phases. Versioned
migrations make upgrades reproducible and reversible.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from .config import Config
from .logging import get_logger
from .models import (
    CareerDestination,
    Company,
    CompanySource,
    DiscoveryAttempt,
    DiscoveryRun,
    MergeRecord,
    ReviewQueueItem,
)

logger = get_logger(__name__)

# --- Migration registry: (version, SQL) pairs ---

MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            name_normalized TEXT NOT NULL,
            official_domain TEXT,
            homepage TEXT,
            region TEXT,
            company_state TEXT NOT NULL DEFAULT 'unknown',
            parent_company_id TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS company_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL REFERENCES companies(id),
            source_name TEXT NOT NULL,
            profile_url TEXT,
            listed_url_raw TEXT,
            listed_url_clean TEXT,
            raw_metadata TEXT,
            seen_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS discovery_runs (
            run_id TEXT PRIMARY KEY,
            started_at TEXT NOT NULL,
            config_snapshot TEXT,
            code_version TEXT,
            cost_used REAL DEFAULT 0.0
        );

        CREATE TABLE IF NOT EXISTS discovery_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            company_id TEXT NOT NULL,
            stage TEXT NOT NULL,
            candidate_url TEXT,
            method TEXT NOT NULL,
            agent_involved INTEGER DEFAULT 0,
            input TEXT,
            output TEXT,
            evidence TEXT,
            outcome TEXT NOT NULL,
            error_class TEXT,
            duration REAL,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS career_destinations (
            company_id TEXT PRIMARY KEY REFERENCES companies(id),
            status TEXT NOT NULL,
            destination_type TEXT,
            careers_url TEXT,
            job_board_url TEXT,
            ats_provider TEXT,
            ats_slug TEXT,
            jobs_api_url TEXT,
            open_jobs_count INTEGER,
            discovery_method TEXT,
            confidence REAL,
            evidence_summary TEXT,
            fallback_urls TEXT,
            last_verified_at TEXT,
            pipeline_version TEXT
        );

        CREATE TABLE IF NOT EXISTS review_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            candidates TEXT,
            attempt_summary TEXT,
            suggested_next_action TEXT,
            resolution TEXT,
            resolved_by TEXT,
            resolved_at TEXT
        );

        CREATE TABLE IF NOT EXISTS merges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kept_company_id TEXT NOT NULL,
            merged_company_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            evidence TEXT,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_sources_company ON company_sources(company_id);
        CREATE INDEX IF NOT EXISTS idx_attempts_company ON discovery_attempts(company_id);
        CREATE INDEX IF NOT EXISTS idx_attempts_run ON discovery_attempts(run_id);
        CREATE INDEX IF NOT EXISTS idx_destinations_status ON career_destinations(status);
        """,
    ),
]


class Database:
    """SQLite database with migration support."""

    def __init__(self, config: Config):
        self.config = config
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Get or create a database connection."""
        if self._conn is None:
            self.config.ensure_dirs()
            self._conn = sqlite3.connect(str(self.config.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def migrate(self) -> None:
        """Run all pending migrations."""
        conn = self.connect()
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)"
        )
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        current_version = row[0] if row and row[0] else 0

        for version, sql in MIGRATIONS:
            if version > current_version:
                logger.info(f"running migration {version}")
                conn.executescript(sql)
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)", (version,)
                )
                conn.commit()

    # --- Company operations ---

    def upsert_company(self, company: Company) -> None:
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO companies (id, name, name_normalized, official_domain, homepage,
                                   region, company_state, parent_company_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                name_normalized=excluded.name_normalized,
                official_domain=excluded.official_domain,
                homepage=excluded.homepage,
                region=excluded.region,
                company_state=excluded.company_state,
                parent_company_id=excluded.parent_company_id
            """,
            (
                company.id, company.name, company.name_normalized,
                company.official_domain, company.homepage, company.region,
                company.company_state.value, company.parent_company_id,
                company.created_at.isoformat(),
            ),
        )
        conn.commit()

    def get_company(self, company_id: str) -> Optional[Company]:
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        if row is None:
            return None
        return Company(
            id=row["id"], name=row["name"],
            name_normalized=row["name_normalized"],
            official_domain=row["official_domain"],
            homepage=row["homepage"], region=row["region"],
            company_state=row["company_state"],
            parent_company_id=row["parent_company_id"],
            created_at=row["created_at"],
        )

    def get_all_company_ids(self) -> list[str]:
        conn = self.connect()
        rows = conn.execute("SELECT id FROM companies").fetchall()
        return [row["id"] for row in rows]

    # --- Source operations ---

    def add_company_source(self, source: CompanySource) -> None:
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO company_sources (company_id, source_name, profile_url,
                                         listed_url_raw, listed_url_clean, raw_metadata, seen_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source.company_id, source.source_name, source.profile_url,
                source.listed_url_raw, source.listed_url_clean,
                str(source.raw_metadata) if source.raw_metadata else None,
                source.seen_at.isoformat(),
            ),
        )
        conn.commit()

    # --- Discovery run operations ---

    def create_run(self, run: DiscoveryRun) -> None:
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO discovery_runs (run_id, started_at, config_snapshot, code_version, cost_used)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run.run_id, run.started_at.isoformat(),
                str(run.config_snapshot) if run.config_snapshot else None,
                run.code_version, run.cost_used,
            ),
        )
        conn.commit()

    # --- Discovery attempt operations ---

    def add_attempt(self, attempt: DiscoveryAttempt) -> None:
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO discovery_attempts (run_id, company_id, stage, candidate_url,
                                            method, agent_involved, input, output, evidence,
                                            outcome, error_class, duration, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt.run_id, attempt.company_id, attempt.stage,
                attempt.candidate_url, attempt.method,
                1 if attempt.agent_involved else 0,
                str(attempt.input) if attempt.input else None,
                str(attempt.output) if attempt.output else None,
                str(attempt.evidence) if attempt.evidence else None,
                attempt.outcome,
                attempt.error_class.value if attempt.error_class else None,
                attempt.duration, attempt.timestamp.isoformat(),
            ),
        )
        conn.commit()

    # --- Career destination operations ---

    def upsert_destination(self, dest: CareerDestination) -> None:
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO career_destinations (company_id, status, destination_type,
                                             careers_url, job_board_url, ats_provider, ats_slug,
                                             jobs_api_url, open_jobs_count, discovery_method,
                                             confidence, evidence_summary, fallback_urls,
                                             last_verified_at, pipeline_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_id) DO UPDATE SET
                status=excluded.status,
                destination_type=excluded.destination_type,
                careers_url=excluded.careers_url,
                job_board_url=excluded.job_board_url,
                ats_provider=excluded.ats_provider,
                ats_slug=excluded.ats_slug,
                jobs_api_url=excluded.jobs_api_url,
                open_jobs_count=excluded.open_jobs_count,
                discovery_method=excluded.discovery_method,
                confidence=excluded.confidence,
                evidence_summary=excluded.evidence_summary,
                fallback_urls=excluded.fallback_urls,
                last_verified_at=excluded.last_verified_at,
                pipeline_version=excluded.pipeline_version
            """,
            (
                dest.company_id, dest.status.value, dest.destination_type.value if dest.destination_type else None,
                dest.careers_url, dest.job_board_url, dest.ats_provider, dest.ats_slug,
                dest.jobs_api_url, dest.open_jobs_count, dest.discovery_method,
                dest.confidence, dest.evidence_summary,
                str(dest.fallback_urls),
                dest.last_verified_at.isoformat() if dest.last_verified_at else None,
                dest.pipeline_version,
            ),
        )
        conn.commit()

    def get_destination(self, company_id: str) -> Optional[CareerDestination]:
        conn = self.connect()
        row = conn.execute(
            "SELECT * FROM career_destinations WHERE company_id = ?", (company_id,)
        ).fetchone()
        if row is None:
            return None
        return CareerDestination(
            company_id=row["company_id"], status=row["status"],
            destination_type=row["destination_type"],
            careers_url=row["careers_url"], job_board_url=row["job_board_url"],
            ats_provider=row["ats_provider"], ats_slug=row["ats_slug"],
            jobs_api_url=row["jobs_api_url"],
            open_jobs_count=row["open_jobs_count"],
            discovery_method=row["discovery_method"],
            confidence=row["confidence"],
            evidence_summary=row["evidence_summary"],
            fallback_urls=row["fallback_urls"].split(",") if row["fallback_urls"] else [],
            last_verified_at=row["last_verified_at"],
            pipeline_version=row["pipeline_version"],
        )

    # --- Review queue operations ---

    def add_review_item(self, item: ReviewQueueItem) -> None:
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO review_queue (company_id, reason, candidates, attempt_summary,
                                      suggested_next_action, resolution, resolved_by, resolved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.company_id, item.reason,
                str(item.candidates), item.attempt_summary,
                item.suggested_next_action, item.resolution,
                item.resolved_by,
                item.resolved_at.isoformat() if item.resolved_at else None,
            ),
        )
        conn.commit()

    def get_review_queue(self) -> list[dict]:
        conn = self.connect()
        rows = conn.execute("SELECT * FROM review_queue").fetchall()
        return [dict(row) for row in rows]

    # --- Merge operations ---

    def add_merge(self, merge: MergeRecord) -> None:
        conn = self.connect()
        conn.execute(
            """
            INSERT INTO merges (kept_company_id, merged_company_id, reason, evidence, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                merge.kept_company_id, merge.merged_company_id,
                merge.reason, str(merge.evidence) if merge.evidence else None,
                merge.created_at.isoformat(),
            ),
        )
        conn.commit()

    # --- Stats ---

    def get_status_counts(self) -> dict[str, int]:
        conn = self.connect()
        rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM career_destinations GROUP BY status"
        ).fetchall()
        return {row["status"]: row["count"] for row in rows}
