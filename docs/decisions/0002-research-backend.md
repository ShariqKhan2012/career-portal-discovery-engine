# 0002: Research backend

**Date:** 2026-09-28
**Status:** Accepted

## Context

The master prompt defines two interchangeable backends for AI research: Backend A (in-app LLM agent) and Backend B (operator agent). A decision is needed on which to build first.

## Options

| | Backend A (in-app LLM) | Backend B (operator agent) |
|---|---|---|
| Production target | Yes | No (learning/eval only) |
| Effort to build | Higher | Lower |
| Schedulable | Yes | No (needs human or subagent) |
| Learning value | Abstract | Direct |

## Decision

**Build Backend B first.** It is cheaper, gives direct visibility into the research process, and produces the evaluation data needed to design Backend A's prompts and tools.

## Consequences

- Backend B will be used for early evaluation and learning.
- Backend A becomes the Phase 7 production target.
- The submission contract (schema) is designed once and shared by both backends.
