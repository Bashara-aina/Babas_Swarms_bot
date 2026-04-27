---
name: gitnexus-impact-analysis
description: "Use when the user wants to know what will break if they change something, or needs safety analysis before editing code. Examples: \"Is it safe to change X?\", \"What depends on this?\", \"What will break?\""
---

# Impact Analysis with GitNexus

## When to Use

- "Is it safe to change this function?"
- "What will break if I modify X?"
- "Show me the blast radius"
- "Who uses this code?"
- Before making non-trivial code changes
- Before committing — to understand what your changes affect

## Workflow

```
1. gitnexus_impact({target: "X", direction: "upstream"})  → What depends on this
2. READ gitnexus://repo/{name}/processes                  → Check affected execution flows
3. gitnexus_detect_changes()                              → Map current git changes to affected flows
4. Assess risk and report to user
```

> If "Index is stale" → run `npx gitnexus analyze` in terminal.

## Checklist

```
- [ ] gitnexus_impact({target, direction: "upstream"}) to find dependents
- [ ] Review d=1 items first (these WILL BREAK)
- [ ] Check high-confidence (>0.8) dependencies
- [ ] READ processes to check affected execution flows
- [ ] gitnexus_detect_changes() for pre-commit check
- [ ] Assess risk level and report to user
```

## Understanding Output

| Depth | Risk Level       | Meaning                  |
| ----- | ---------------- | ------------------------ |
| d=1   | **WILL BREAK**   | Direct callers/importers |
| d=2   | LIKELY AFFECTED  | Indirect dependencies    |
| d=3   | MAY NEED TESTING | Transitive effects       |

## Risk Assessment

| Affected                       | Risk     |
| ------------------------------ | -------- |
| <5 symbols, few processes      | LOW      |
| 5-15 symbols, 2-5 processes    | MEDIUM   |
| >15 symbols or many processes  | HIGH     |
| Critical path (auth, payments) | CRITICAL |

## Tools

**gitnexus_impact** — the primary tool for symbol blast radius:

```
gitnexus_impact({
  target: "chat",
  direction: "upstream",
  minConfidence: 0.8,
  maxDepth: 3
})

→ d=1 (WILL BREAK):
  - llm_client.chat (llm_client.py:89) [CALLS, 100%]
  - agent_loop (llm_client.py:142) [CALLS, 100%]

→ d=2 (LIKELY AFFECTED):
  - handlers/ai.py:handle_ai_request (handlers/ai.py:42) [CALLS, 95%]
```

**gitnexus_detect_changes** — git-diff based impact analysis:

```
gitnexus_detect_changes({scope: "staged"})

→ Changed: 5 symbols in 3 files
→ Affected: MessageFlow, IntentClassification, LLMFallbackChain
→ Risk: MEDIUM
```

## Swarm-Bot Critical Paths

When changing these symbols, always run full test suite:

| Symbol                | Why critical                               |
| --------------------- | ------------------------------------------ |
| `llm_client.chat`     | All AI responses go through this           |
| `IntentRouter.route`  | Every message is classified through this    |
| `memory_manager.save` | All memory writes                          |
| `agents.py TASK_KEYWORDS` | Agent routing depends on this          |

## Example: "What breaks if I change `get_fallback_chain`?"

```
1. gitnexus_impact({target: "get_fallback_chain", direction: "upstream"})
   → d=1: chat, agent_loop, handle_rate_limit (WILL BREAK)
   → d=2: handlers/ai.py, task_orchestrator.py (LIKELY AFFECTED)

2. READ gitnexus://repo/swarm-bot/processes
   → LLMFallbackChain and AgentLoop touch get_fallback_chain

3. Risk: 3 direct callers, 2 processes = MEDIUM
   → Run: pytest tests/ -x --asyncio-mode=auto -q after change
```