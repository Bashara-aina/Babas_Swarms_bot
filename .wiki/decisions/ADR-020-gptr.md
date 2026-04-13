# ADR-020: gpt-researcher Integration

**Date:** 2026-04-12  
**Status:** Accepted  
**Deciders:** Worker agent (Legion Swarm Bot)

## Context

Legion needs a deep multi-source research capability for market research,
competitor analysis, legal/regulatory research, and data sourcing.
The existing `web_search` skill (Brave Search) provides single-query search
but lacks multi-step research, source synthesis, and structured reporting.

## Decision

Integrate `gpt-researcher` as a first-class skill (`deep_research`) and
integration client (`GPTResearcherClient`).

## Architecture

```
core/skills/deep_research.py
    └── executes → core/integrations/gptr_client.py
                       └── wraps → gpt-researcher library
                                      └── uses OPENROUTER_API_KEY

core/skills/__init__.py
    └── imports deep_research → triggers _register_deep_research_skill()
                                   → SKILL_REGISTRY.register(Skill(...))
```

## Key Design Decisions

1. **OpenRouter as LLM backbone** — reuses existing `OPENROUTER_API_KEY`,
   no new API keys needed.
2. **Graceful degradation** — if `gpt-researcher` is not installed,
   returns a helpful message instead of crashing.
3. **Tavily preference** — if `BRAVE_API_KEY` is set, uses Tavily instead
   of DuckDuckGo for better quality results.
4. **Cost estimation** — simple token-based estimate returned with result.
5. **Report truncation** — long reports capped at 3500 chars with memory
   reference, avoiding Telegram message length issues.
6. **Skill registration pattern** — matches existing `code_review.py` and
   `timer.py` pattern (module-level registration call).

## Alternatives Considered

- **Direct Tavily API**: Would skip gpt-researcher but lose multi-step research loop
- **Custom implementation**: Reimplement research logic — rejected, gpt-researcher is well-tested
- **Handler-based (vs skill)**: Skills are trigger-based and more appropriate for this use case

## Environment Variables

```env
GPTR_LLM_MODEL=openai/gpt-4o-mini
GPTR_SMART_MODEL=anthropic/claude-3-5-haiku
GPTR_SEARCH_API=duckduckgo
```

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| gpt-researcher library instability | Graceful fallback with helpful error message |
| High latency (~30s) | Skill metadata reflects avg_latency_seconds=30 |
| Cost of research calls | Cost estimation included in response |
| gpt-researcher not installed | Warning logged on init; pip install instructions in report |