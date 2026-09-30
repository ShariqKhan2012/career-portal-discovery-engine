# Architecture

## Overview

```
CLI → Orchestrator (state machine) → Discovery ladder (stages 1-6) → AI research (7) → Review queue
                                    ↓
                              HTTP layer (cache, rate limits, robots, retries)
                                    ↓
                              SQLite database
```

## Components

### CLI (`src/cli.py`)
Entry point. Commands: ingest, run, status, agent-next, agent-submit, export, report.

### Orchestrator (`src/orchestrator.py`)
State machine that processes companies through the discovery ladder. Controls when each stage runs, retries, and escalates. AI is never in control of flow.

### Discovery stages (`src/stages/`)
Each stage is a class that implements the `Stage` interface:
- `seed` — classify the listed URL
- `ats_verify` — verify ATS boards via provider API
- `website` — discover the official website
- `crawl` — crawl for careers pages
- `slug_probe` — probe ATS slugs with collision guard
- `render` — headless rendering for JS-shell pages

### HTTP layer (`src/http.py`)
All network calls go through this module. Provides disk caching, per-domain rate limiting, robots.txt enforcement, retries with exponential backoff, and error classification.

### ATS adapters (`src/ats/`)
Each ATS provider implements: `match`, `extract_slug`, `verify_board`. Adding a new provider means writing one adapter and nothing else.

### Verification service (`src/verification.py`)
Implements the §7 acceptance rules. A candidate is verified only if all checks pass.

### AI research (`src/agent/`)
Bounded, pluggable backend. Backend B (operator agent) is implemented. Backend A (in-app LLM) is the production target.

### Database (`src/db.py`)
SQLite with migrations. All database writes go through this module.

### Export (`src/export.py`)
CSV, JSON, and Excel exports.

## Data flow

1. **Ingest** — fetch companies from directory sources, normalize URLs, store in database
2. **Run** — process each company through the discovery ladder
3. **Verify** — check each candidate against the §7 acceptance rules
4. **Export** — produce CSV, JSON, XLSX, and report.md

## Key design decisions

- **Deterministic-first**: AI is one bounded stage, entered only when deterministic stages fail
- **Evidence-based**: every URL must be observed with evidence stored in the database
- **Resumable**: state is persisted after each company; any run can be killed and restarted
- **Agent-agnostic**: standard Python, works with any coding agent (Claude Code, OpenCode, etc.)
