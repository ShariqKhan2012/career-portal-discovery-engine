"""Command-line interface for the Career Portal Discovery Engine.

Commands will be added phase by phase. This is the entry point.
"""

from __future__ import annotations

import argparse
import sys

from .config import Config
from .db import Database
from .logging import get_logger

logger = get_logger(__name__)


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
        logger.info(f"ingest from {args.source} not yet implemented")
        print(f"Ingest from '{args.source}' — not yet implemented (Phase 2)")

    elif args.command == "run":
        logger.info(f"run with batch={args.batch} not yet implemented")
        print(f"Run with batch={args.batch} — not yet implemented (Phase 5)")

    elif args.command == "export":
        logger.info("export not yet implemented")
        print("Export — not yet implemented (Phase 9)")

    db.close()


if __name__ == "__main__":
    main()
