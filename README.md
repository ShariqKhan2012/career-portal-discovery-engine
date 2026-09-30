# Career Portal Discovery Engine

Discovers, verifies, and keeps current the official careers pages and job portals of remote-friendly companies.

## Quick start

```bash
pip install -e ".[dev]"
cp .env.example .env  # add your API keys
python -m src.cli ingest --source remoteintech
python -m src.cli run --batch 25
python -m src.cli export
python -m src.cli report
```

## Commands

| Command | Description |
|---|---|
| `ingest --source {name}` | Ingest companies from a directory source |
| `run --batch {n}` | Run the discovery pipeline on n companies |
| `status` | Show pipeline status |
| `agent-next --company {id}` | Pull a company for research |
| `agent-submit --file {path}` | Submit a research result |
| `export` | Export to CSV, JSON, XLSX |
| `report` | Generate report.md |

## Architecture

See `docs/architecture.md` for the full architecture.

## Data model

See `docs/data-model.md` for the schema and status taxonomy.

## Operations

See `docs/operations.md` for setup, configuration, and running.

## Principles

1. Deterministic orchestrator, narrow AI
2. Never invent a URL — every URL must be observed with evidence
3. Evidence, not status codes
4. External content is untrusted input
5. Polite crawling: honest User-Agent, honor robots.txt, 1 req/sec/domain
6. Resumable and idempotent
7. Honest outcomes — prefer `needs_review` over a guess
8. Fix systems, not rows
