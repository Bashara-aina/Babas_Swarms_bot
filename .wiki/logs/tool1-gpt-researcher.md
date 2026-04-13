# Tool 1: gpt-researcher Integration — WORKER LOG

**Date:** 2026-04-12  
**Agent:** Worker  
**Task:** Wire gpt-researcher into Legion as a deep research skill

## Files Created

| File | Description |
|------|-------------|
| `core/integrations/__init__.py` | Integration module entry point |
| `core/integrations/gptr_client.py` | GPTResearcherClient wrapper |
| `core/integrations/dify_client.py` | Placeholder DifyClient (stub) |
| `core/skills/deep_research.py` | Deep research skill with skill meta + registration |

## Files Modified

| File | Change |
|------|--------|
| `core/skills/__init__.py` | Added `deep_research` to imports and `__all__` |
| `.env.example` | Added GPTR_LLM_MODEL, GPTR_SMART_MODEL, GPTR_SEARCH_API |

## Verification

```bash
$ python -c "from core.skills.deep_research import execute, SKILL_META; print('OK')"
gpt-researcher not installed. Run: pip install gpt-researcher
OK
```

```bash
$ python scripts/verify_wiring.py
...
Skill registry loaded: 29 skills registered   ← (up from 28 — deep_research added)
...
All wiring checks passed!
```

## Implementation Notes

- `deep_research.py` follows same registration pattern as `code_review.py` and `timer.py`
  (calls `_register_deep_research_skill()` at module load time)
- `GPTResearcherClient` gracefully degrades when `gpt-researcher` not installed
- Uses OpenRouter via existing `OPENROUTER_API_KEY` env var
- Search API defaults to DuckDuckGo, upgrades to Tavily if `BRAVE_API_KEY` is set
- `DifyClient` stub created to avoid import errors in `core/integrations/__init__.py`

## To Activate

```bash
pip install gpt-researcher
```

Then set in `.env`:
```
GPTR_LLM_MODEL=openai/gpt-4o-mini
GPTR_SMART_MODEL=anthropic/claude-3-5-haiku
GPTR_SEARCH_API=duckduckgo  # or tavily if TAVILY_API_KEY set
```