# 0001: Language choice

**Date:** 2026-09-28
**Status:** Accepted

## Context

The master prompt requires choosing between Python and TypeScript. The user is an experienced full-stack developer, strongest in TypeScript, but new to agentic engineering and on an AI/ML learning path.

## Options

| | Python | TypeScript |
|---|---|---|
| Scraping ecosystem | Excellent (httpx, beautifulsoup4, lxml) | Good (cheerio, node-fetch) |
| AI/ML alignment | Dominant in agentic AI | Growing but secondary |
| Data work | pandas, openpyxl first-class | Less mature |
| User familiarity | Learning path | Strongest daily language |
| Playwright | First-class | First-class |
| SQLite | Built-in sqlite3 | better-sqlite3 |
| Schema validation | pydantic | Zod |

## Decision

**Python.** The scraping + data + AI ecosystem is significantly stronger, and it aligns with the user's AI/ML learning path.

## Consequences

- The user will learn Python alongside the project.
- Access to the best-in-class scraping and AI libraries.
- The system is well-specified enough that the language choice won't obscure the architecture.
