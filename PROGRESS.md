# Progress Log

## 2026-09-28 — Session 1

### Completed
- Phase 0: Environment inspection, architecture proposal, 6 decisions presented and approved
- Phase 1: Harness files (AGENTS.md, CLAUDE.md, .env.example, .gitignore, pyproject.toml)
- Phase 1: Core modules (config.py, logging.py, models.py, http.py, db.py, cli.py)
- Phase 1: Seed data (ats_patterns.json)
- Phase 1: Test scaffolding (tests/)
- Phase 1: Decision records (docs/decisions/0001-0004)
- Phase 1: Task tracking (TASKS.md)

### Decisions made
1. Language: Python
2. Research backend: Backend B first (operator agent)
3. LLM provider: OpenRouter (free tier)
4. Web search: Brave Search API (free tier)
5. Database: SQLite
6. Cost cap: $0/month
7. Agent-agnostic design confirmed

### Next tasks
- Run tests and verify
- CHECKPOINT 1

### Open questions
- None

### Status
- Phase 1 complete, CHECKPOINT 1 approved

## 2026-09-28 — Session 2

### Completed
- Phase 1: All tests pass (13/13, zero warnings)
- Phase 1: CHECKPOINT 1 approved

### Next tasks
- Phase 2: Ingestion, normalization, and deduplication

### Open questions
- None

### Status
- Phase 2 complete, CHECKPOINT 2 approved with limitations

## 2026-09-29 — Session 5

### Completed
- Phase 3: Evaluation-set template created with 31 companies
- Phase 3: All expected destinations approved by user
- Phase 3: Stratified across ats_seed, custom_page, malformed_seed, aggregator_seed, social_seed, acquired, ambiguous

### Next tasks
- Phase 4: ATS registry, adapters, and verification service

### Open questions
- None

### Status
- Phase 5 complete, CHECKPOINT 3 approved

## 2026-09-29 — Session 9

### Completed
- Phase 5: Full evaluation run — 502/884 companies processed
- Phase 5: 234 verified, 144 needs_review, 123 not_found
- Phase 5: User verified results by querying database directly
- Phase 5: CHECKPOINT 3 approved

### Next tasks
- Phase 6: Headless rendering (stage 6)

### Open questions
- None

### Status
- Phase 6 implementation complete, pending live test

## 2026-09-29 — Session 10

### Completed
- Phase 6: Playwright installed with Chromium
- Phase 6: Render stage (src/stages/render.py)
- Phase 6: Bounded waits, resource blocking, ATS embed detection
- Phase 6: All 69 tests pass

### Next tasks
- Live test of render stage on a JS-heavy page
- CHECKPOINT 4

### Open questions
- None

### Status
- Phase 6 implementation complete, pending live test

## 2026-09-29 — Session 8

### Completed
- Phase 5: Orchestrator state machine (orchestrator.py)
- Phase 5: Discovery stages (seed, ats_verify, website, crawl, slug_probe)
- Phase 5: CLI run command
- Phase 5: Small batch test — 3 verified, 2 not_found
- Phase 5: All 66 tests pass

### Next tasks
- Run full evaluation
- CHECKPOINT 3

### Open questions
- None

### Status
- Phase 5 implementation complete, pending full evaluation

## 2026-09-29 — Session 7

### Completed
- Phase 4: Live API tests — all 3 ATS providers verified
  - Greenhouse: consensys (7 jobs)
  - Lever: anomali (19 jobs), kraken (0 jobs), findem (4 jobs)
  - Ashby: Deel (0 jobs)
- Phase 4: Marked greenhouse, lever, ashby as verified in ats_patterns.json
- Phase 4: All 62 tests pass

### Next tasks
- Phase 5: Deterministic ladder and orchestrator

### Open questions
- None

### Status
- Phase 4 complete, all ATS providers verified

## 2026-09-29 — Session 6

### Completed
- Phase 4: ATS adapters (greenhouse, lever, ashby)
- Phase 4: Verification service (§7 acceptance rules)
- Phase 4: ATS registry loader
- Phase 4: All 62 tests pass

### Next tasks
- Live test of ATS API endpoints
- Mark providers as verified after live tests

### Open questions
- None

### Status
- Phase 4 implementation complete, pending live API tests

## 2026-09-28 — Session 4

### Completed
- Phase 2: Remote In Tech ingest — 884 companies, 43 mismatches, 0 duplicates
- Phase 2: WWR ingest — blocked by Cloudflare (403)
- Phase 2: All 49 tests pass

### Key findings
- Remote In Tech: GitHub repo (remoteintech/remote-jobs) has structured markdown files
  with YAML frontmatter (title, slug, website, careers_url, region, etc.)
- WWR: Blocked by Cloudflare WAF (403). The page is also JavaScript-rendered.
  Per master prompt: "Never bypass CAPTCHAs, login walls, paywalls, or other
  access controls. If blocked, record `blocked` and move on."
- 43 name/domain mismatches detected in Remote In Tech (e.g., addstructure → bazaarvoice.com)
- 0 duplicates within Remote In Tech (all 884 companies have unique domains)

### Ingestion limitations
- WWR is blocked by Cloudflare. Cannot ingest without bypassing the WAF.
- The webfetch tool can access WWR (likely uses a headless browser), but
  direct HTTP requests are blocked.
- WWR also requires JavaScript rendering (the static HTML is a shell).

### Next tasks
- Phase 3: Evaluation-set template
- Phase 4: ATS registry, adapters, and verification

### Open questions
- None

### Status
- Phase 2 complete, CHECKPOINT 2 approved with limitations

## 2026-09-28 — Session 3

### Completed
- Phase 2: Source inspection (remoteintech → GitHub repo, weworkremotely → HTML)
- Phase 2: URL normalization (src/normalize.py) — handles all Appendix B cases
- Phase 2: Registrable domain computation (src/domains.py) — uses tldextract
- Phase 2: Name/domain mismatch detection (src/mismatch.py)
- Phase 2: Deduplication (src/dedup.py) — domain identity, fuzzy matches go to review
- Phase 2: Source adapters (adapters/remoteintech.py, adapters/weworkremotely.py)
- Phase 2: CLI ingest command
- Phase 2: All 49 tests pass

### Key findings
- Remote In Tech: GitHub repo (remoteintech/remote-jobs) has structured markdown files
  with YAML frontmatter (title, slug, website, careers_url, region, etc.)
- WWR: 100 companies in server-rendered HTML, each with a profile page at /company/{slug}

### Next tasks
- Run ingest and verify
- CHECKPOINT 2

### Open questions
- None

### Status
- Phase 2 implementation complete, pending ingest run
