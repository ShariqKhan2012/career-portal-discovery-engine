# 0003: Web search provider

**Date:** 2026-09-28
**Status:** Accepted

## Context

The master prompt requires a web-search provider for the AI research stage. The user asked whether Tavily's "built for AI" features offer considerable specific advantages over Brave Search API.

## Analysis

Tavily's "built for AI" means it returns extracted, cleaned content ready for LLM consumption (not just links + snippets). It offers `include_answer`, domain filtering, and structured output. However, it is a hybrid aggregator (can return stale/404 links), was acquired by Nebius in Feb 2026, and its cleaned output is a black box that conflicts with this project's evidence-based verification requirement.

Brave Search API provides raw search results (links + snippets), an independent index (35B+ pages), a larger free tier (2,000 vs 1,000/month), and no acquisition risk.

## Decision

**Brave Search API.** This project needs raw URLs that the deterministic pipeline fetches, parses, and verifies — not LLM-processed answers. Brave provides the raw material with better terms and no platform risk.

## Consequences

- The HTTP layer handles all extraction and cleaning.
- Brave's free tier (2,000 queries/month) is sufficient for the initial run.
- If volume grows, the provider is swappable behind a simple interface.
