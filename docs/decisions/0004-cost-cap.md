# 0004: Cost cap

**Date:** 2026-09-28
**Status:** Accepted

## Context

The user has a strict $0/month budget for this learning project. They plan to use OpenRouter's free tier and do not want to spend money. They mentioned Antigravity CLI as a fallback with a generous free tier.

## Decision

**$0/month cost cap.** The system will use only free tiers:
- OpenRouter free tier for LLM calls
- Brave Search API free tier (2,000 queries/month) for web search

The system will track usage and pause cleanly if any limit is approached.

## Consequences

- The cost tracking system must work correctly even at $0.
- If free tier limits are insufficient, the user will be notified before any paid tier is needed.
- Antigravity CLI is noted as a potential fallback LLM provider.
- The implementation must be agent-agnostic to allow switching between Claude Code, OpenCode, and Antigravity.
