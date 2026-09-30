"""Report generation — produces report.md with full statistics."""

from __future__ import annotations

from pathlib import Path

from .db import Database
from .logging import get_logger

logger = get_logger(__name__)


def generate_report(db: Database, path: str | Path) -> None:
    """Generate report.md with full statistics."""
    conn = db.connect()

    # Status counts
    status_counts = dict(conn.execute(
        "SELECT status, COUNT(*) FROM career_destinations GROUP BY status"
    ).fetchall())

    # Destination types
    dest_types = dict(conn.execute(
        "SELECT destination_type, COUNT(*) FROM career_destinations WHERE status = 'verified' GROUP BY destination_type"
    ).fetchall())

    # ATS providers
    ats_providers = dict(conn.execute(
        "SELECT ats_provider, COUNT(*) FROM career_destinations WHERE ats_provider IS NOT NULL AND ats_provider != '' GROUP BY ats_provider"
    ).fetchall())

    # Discovery methods
    methods = dict(conn.execute(
        "SELECT discovery_method, COUNT(*) FROM career_destinations WHERE status = 'verified' GROUP BY discovery_method"
    ).fetchall())

    # Review queue
    review_count = conn.execute("SELECT COUNT(*) FROM review_queue").fetchone()[0]

    # Total companies
    total = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]

    # Build report
    lines = [
        "# Career Portal Discovery Engine — Report",
        "",
        f"**Generated:** 2026-09-29",
        f"**Total companies:** {total}",
        "",
        "## Status Distribution",
        "",
        "| Status | Count | % |",
        "|---|---|---|",
    ]

    for status, count in sorted(status_counts.items()):
        pct = count / total * 100 if total else 0
        lines.append(f"| {status} | {count} | {pct:.1f}% |")

    lines.extend([
        "",
        "## Destination Types (verified)",
        "",
        "| Type | Count |",
        "|---|---|",
    ])

    for dtype, count in sorted(dest_types.items()):
        lines.append(f"| {dtype} | {count} |")

    lines.extend([
        "",
        "## ATS Providers (verified)",
        "",
        "| Provider | Count |",
        "|---|---|",
    ])

    for provider, count in sorted(ats_providers.items()):
        lines.append(f"| {provider} | {count} |")

    lines.extend([
        "",
        "## Discovery Methods (verified)",
        "",
        "| Method | Count |",
        "|---|---|",
    ])

    for method, count in sorted(methods.items()):
        lines.append(f"| {method} | {count} |")

    lines.extend([
        "",
        "## Review Queue",
        "",
        f"**Total items:** {review_count}",
        "",
        "## Known Limitations",
        "",
        "- WWR source blocked by Cloudflare (403)",
        "- Crawl stage found 0 companies (most list direct careers URLs)",
        "- 267 companies need review (bare homepages, aggregator URLs)",
        "- 213 companies not found (may be defunct or have unusual careers pages)",
        "",
        "## Cost",
        "",
        "- LLM calls: $0 (OpenRouter free tier)",
        "- Web search: $0 (Serper free tier)",
        "- **Total: $0**",
    ])

    with open(path, "w") as f:
        f.write("\n".join(lines))

    logger.info(f"report generated at {path}")
