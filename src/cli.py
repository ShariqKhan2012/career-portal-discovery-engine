"""Command-line interface for the Career Portal Discovery Engine."""

from __future__ import annotations

import argparse
import asyncio
import sys

from .config import Config
from .db import Database
from .http import HttpClient
from .logging import get_logger
from .models import Company, CompanySource, Status
from .normalize import normalize_url, is_shortener
from .mismatch import is_mismatch
from .dedup import find_duplicates
from .domains import registrable_domain

logger = get_logger(__name__)


async def _run(batch_size: int, config: Config, db: Database) -> None:
    """Run the discovery pipeline on a batch of companies."""
    from .stages.seed import SeedStage
    from .stages.ats_verify import ATSVerifyStage
    from .stages.website import WebsiteStage
    from .stages.crawl import CrawlStage
    from .stages.slug_probe import SlugProbeStage
    from .orchestrator import Orchestrator
    from .models import DiscoveryRun, Status

    # Create a run record
    import uuid
    run_id = str(uuid.uuid4())[:8]
    run = DiscoveryRun(run_id=run_id, code_version="0.1.0")
    db.create_run(run)

    # Build the stage ladder
    stages = [
        SeedStage(),
        ATSVerifyStage(),
        WebsiteStage(),
        CrawlStage(),
        SlugProbeStage(),
    ]

    orchestrator = Orchestrator(config, db, stages)

    # Get pending companies
    company_ids = db.get_all_company_ids()
    pending = []
    for cid in company_ids:
        dest = db.get_destination(cid)
        if not dest or dest.status == Status.PENDING:
            company = db.get_company(cid)
            if company:
                pending.append(company)

    # Limit to batch size
    pending = pending[:batch_size]

    logger.info(f"running batch of {len(pending)} companies")

    async with HttpClient(config) as http:
        for company in pending:
            await orchestrator.process_company(company, http, run_id)

    # Summary
    counts = db.get_status_counts()
    print(f"\nRun {run_id} complete:")
    for status, count in sorted(counts.items()):
        print(f"  {status}: {count}")


async def _ingest(source: str, config: Config, db: Database) -> None:
    """Ingest companies from a source."""
    # Import adapters here to avoid circular imports
    if source == "remoteintech":
        from adapters.remoteintech import RemoteInTechAdapter
        adapter = RemoteInTechAdapter()
    elif source == "weworkremotely":
        from adapters.weworkremotely import WeWorkRemotelyAdapter
        adapter = WeWorkRemotelyAdapter()
    else:
        print(f"Unknown source: {source}")
        return

    logger.info(f"ingesting from {source}")

    async with HttpClient(config) as http:
        raw_companies = await adapter.fetch_companies(http)

    logger.info(f"fetched {len(raw_companies)} companies from {source}")

    # Normalize and build company records
    companies = []
    for raw in raw_companies:
        listed_url_raw = raw.get("listed_url_raw", "")
        listed_url_clean = normalize_url(listed_url_raw) if listed_url_raw else ""

        # Determine the best URL for domain extraction
        best_url = listed_url_clean or raw.get("raw_metadata", {}).get("website", "")
        domain = registrable_domain(best_url) if best_url else None

        company = Company(
            id=raw["slug"],
            name=raw["name"],
            name_normalized=raw["name"].lower(),
            official_domain=domain,
            homepage=raw.get("raw_metadata", {}).get("website", ""),
        )
        companies.append((company, raw, listed_url_clean))

    # Detect mismatches
    mismatches = []
    for company, raw, listed_url_clean in companies:
        urls = [listed_url_clean] if listed_url_clean else []
        urls.append(raw.get("raw_metadata", {}).get("website", ""))
        if is_mismatch(company.name, urls):
            mismatches.append(company.id)
            logger.warning(f"name/domain mismatch: {company.name} → {urls}")

    # Deduplicate
    company_dicts = [
        {"id": c.id, "name": c.name, "urls": [l] if l else [], "sources": [source]}
        for c, _, l in companies
    ]
    duplicates = find_duplicates(company_dicts)

    # Store in database
    for company, raw, listed_url_clean in companies:
        db.upsert_company(company)
        source_record = CompanySource(
            company_id=company.id,
            source_name=source,
            profile_url=raw.get("profile_url", ""),
            listed_url_raw=raw.get("listed_url_raw", ""),
            listed_url_clean=listed_url_clean,
            raw_metadata=raw.get("raw_metadata", {}),
        )
        db.add_company_source(source_record)

    # Log merges
    for kept, merged in duplicates:
        from .models import MergeRecord
        db.add_merge(MergeRecord(
            kept_company_id=kept["id"],
            merged_company_id=merged["id"],
            reason="same registrable domain",
            evidence={"domain": registrable_domain(kept["urls"][0])},
        ))

    # Summary
    print(f"\nIngest from '{source}':")
    print(f"  Companies fetched: {len(companies)}")
    print(f"  Name/domain mismatches: {len(mismatches)}")
    print(f"  Duplicate pairs found: {len(duplicates)}")
    if mismatches:
        print(f"  Mismatched IDs: {', '.join(mismatches[:10])}")
    if duplicates:
        print(f"  Merged pairs: {', '.join(f'{k['id']} ← {m['id']}' for k, m in duplicates[:10])}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="career-discovery",
        description="Career Portal Discovery Engine",
    )
    subparsers = parser.add_subparsers(dest="command")

    # --- status ---
    subparsers.add_parser("status", help="Show pipeline status")

    # --- ingest ---
    ingest_parser = subparsers.add_parser("ingest", help="Ingest companies from a source")
    ingest_parser.add_argument("--source", required=True, help="Source name")

    # --- run ---
    run_parser = subparsers.add_parser("run", help="Run the discovery pipeline")
    run_parser.add_argument("--batch", type=int, default=25, help="Batch size")

    # --- export ---
    subparsers.add_parser("export", help="Export results")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = Config()
    db = Database(config)
    db.migrate()

    if args.command == "status":
        counts = db.get_status_counts()
        print("Pipeline status:")
        for status, count in sorted(counts.items()):
            print(f"  {status}: {count}")
        total = sum(counts.values())
        print(f"  total: {total}")

    elif args.command == "ingest":
        asyncio.run(_ingest(args.source, config, db))

    elif args.command == "run":
        asyncio.run(_run(args.batch, config, db))

    elif args.command == "export":
        logger.info("export not yet implemented")
        print("Export — not yet implemented (Phase 9)")

    db.close()


if __name__ == "__main__":
    main()
