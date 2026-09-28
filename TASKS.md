# Task Tracker

## Phase 0 — Inspection and architecture
- [x] Inspect environment
- [x] Propose architecture
- [x] Present decisions
- [x] **CHECKPOINT 0** — approved 2026-09-28

## Phase 1 — Harness and foundation
- [x] Create AGENTS.md (constitution)
- [x] Create CLAUDE.md (thin import)
- [x] Create .env.example
- [x] Create .gitignore
- [x] Create pyproject.toml
- [x] Create src/config.py (all limits from §5)
- [x] Create src/logging.py (structured logging)
- [x] Create src/models.py (data models)
- [x] Create src/http.py (HTTP layer)
- [x] Create src/db.py (database + migrations)
- [x] Create src/cli.py (CLI stub)
- [x] Create ats_patterns.json (seed data)
- [x] Create tests/ (scaffolding)
- [x] Create docs/decisions/ (decision records)
- [x] Run tests and verify
- [x] **CHECKPOINT 1** — approved 2026-09-28

## Phase 2 — Ingestion, normalization, and deduplication
- [x] Check for structured sources (remoteintech → GitHub repo, weworkremotely → HTML)
- [x] Build source adapters (remoteintech.py, weworkremotely.py)
- [x] URL normalization (strip punctuation, expand shorteners, strip tracking)
- [x] Registrable domain computation (tldextract)
- [x] Name/domain mismatch detection
- [x] Deduplication by domain identity
- [x] Run ingest and verify
- [x] **CHECKPOINT 2** — approved with limitations (WWR blocked by Cloudflare)

## Phase 3 — Evaluation-set template
- [ ] Create agent/evals/golden.csv template
- [ ] Pause for user labels

## Phase 4 — ATS registry, adapters, and verification
- [ ] Verify API endpoint hypotheses
- [ ] Build ATS adapters (match, extract_slug, verify_board)
- [ ] Build verification service (§7)
- [ ] Mark providers as verified after live tests

## Phase 5 — Deterministic ladder and orchestrator
- [ ] Build stages 1-5
- [ ] Build state machine
- [ ] Build checkpoints, retries, review queue
- [ ] Run evaluation
- [ ] **CHECKPOINT 3** — results by stage, evaluation metrics

## Phase 6 — Headless rendering (stage 6)
- [ ] Add Playwright for JS-shell pages
- [ ] Bounded waits, resource blocking
- [ ] Re-run detectors on rendered DOM
- [ ] **CHECKPOINT 4** — representative successes and failures

## Phase 7 — AI research
- [ ] Build submission contract
- [ ] Build Backend B (operator agent)
- [ ] Run interactive batch
- [ ] Run evaluation
- [ ] **CHECKPOINT 5** — improvement over Phase 5, tool usage, budgets

## Phase 8 — Batch operation and full run
- [ ] Resumable batches
- [ ] Kill-and-resume demonstration
- [ ] Work through review queue
- [ ] Reviewer audit
- [ ] **CHECKPOINT 6** — status distribution, yield, unresolved cases

## Phase 9 — Exports, documentation, and handoff
- [ ] CSV, JSON, XLSX exports
- [ ] report.md
- [ ] README.md, docs/architecture.md, data-model.md, operations.md
- [ ] Confirm AGENTS.md matches reality
- [ ] **CHECKPOINT 7**

## Phase 10 — Refresh mode
- [ ] Process new directory entries
- [ ] reverify --older-than N days
- [ ] Detect ATS migrations
