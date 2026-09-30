# Operations

## Setup

```bash
# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run tests
pytest
```

## Configuration

All configuration is via `.env`:

| Variable | Default | Description |
|---|---|---|
| `SERPER_API_KEY` | — | Serper.dev API key for web search |
| `OPENROUTER_API_KEY` | — | OpenRouter API key for LLM |
| `OPENROUTER_MODEL` | `anthropic/claude-3-haiku` | LLM model |
| `MONTHLY_COST_CAP` | `0.0` | Monthly cost cap in USD |
| `REQUESTS_PER_SECOND_PER_DOMAIN` | `1.0` | Rate limit per domain |
| `GLOBAL_CONCURRENCY` | `8` | Global concurrent request limit |
| `DEFAULT_TIMEOUT_SECONDS` | `30` | HTTP timeout |
| `MAX_RETRIES` | `3` | Max retries per request |
| `MAX_FETCHES_PER_COMPANY` | `50` | Max fetches per company |
| `CACHE_DIR` | `.cache` | HTTP cache directory |
| `DB_PATH` | `data/career_discovery.db` | Database path |

## Running

```bash
# Ingest companies from a source
python -m src.cli ingest --source remoteintech

# Run the discovery pipeline
python -m src.cli run --batch 25

# Check status
python -m src.cli status

# Export results
python -m src.cli export

# Generate report
python -m src.cli report
```

## Costs

- **Web search**: Serper.dev free tier (2,500 searches/month)
- **LLM**: OpenRouter free tier
- **Total**: $0/month

The system tracks usage and pauses cleanly if any limit is approached.

## Limitations

- WWR source is blocked by Cloudflare (403)
- Crawl stage is limited — most companies list direct careers URLs
- 267 companies need review (bare homepages, aggregator URLs)
- 213 companies not found (may be defunct or have unusual careers pages)

## Future work

- Backend A (in-app LLM agent) for automated research
- Improved crawl stage with better JS detection
- ATS migration detection
- Periodic re-verification
- More source adapters
