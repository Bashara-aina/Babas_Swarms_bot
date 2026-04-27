---
name: gitnexus-debugging
description: "Use when the user is debugging a bug, tracing an error, or asking why something fails. Examples: \"Why is X failing?\", \"Where does this error come from?\", \"Trace this bug\""
---

# Debugging with GitNexus

## When to Use

- "Why is this function failing?"
- "Trace where this error comes from"
- "Who calls this method?"
- "This endpoint returns 500"
- Investigating bugs, errors, or unexpected behavior

## Workflow

```
1. gitnexus_query({query: "<error or symptom>"})            → Find related execution flows
2. gitnexus_context({name: "<suspect>"})                    → See callers/callees/processes
3. READ gitnexus://repo/{name}/process/{name}               → Trace execution flow
4. gitnexus_cypher({query: "MATCH path..."})               → Custom traces if needed
```

> If "Index is stale" → run `npx gitnexus analyze` in terminal.

## Checklist

```
- [ ] Understand the symptom (error message, unexpected behavior)
- [ ] gitnexus_query for error text or related code
- [ ] Identify the suspect function from returned processes
- [ ] gitnexus_context to see callers and callees
- [ ] Trace execution flow via process resource if applicable
- [ ] gitnexus_cypher for custom call chain traces if needed
- [ ] Read source files to confirm root cause
```

## Debugging Patterns

| Symptom              | GitNexus Approach                                          |
| -------------------- | ---------------------------------------------------------- |
| Error message        | `gitnexus_query` for error text → `context` on throw sites |
| Wrong return value   | `context` on the function → trace callees for data flow    |
| Intermittent failure | `context` → look for external calls, async deps            |
| Performance issue    | `context` → find symbols with many callers (hot paths)     |
| Recent regression    | `detect_changes` to see what your changes affect           |

## Tools

**gitnexus_query** — find code related to error:

```
gitnexus_query({query: "llm_client rate limit error"})
→ Processes: LLMFallbackChain, ChatRequestHandler
→ Symbols: get_fallback_chain, handle_rate_limit, LiteLLMError
```

**gitnexus_context** — full context for a suspect:

```
gitnexus_context({name: "get_fallback_chain"})
→ Incoming calls: chat, agent_loop, retry_handler
→ Outgoing calls: groq_chat, cerebras_chat (external API!)
→ Processes: LLMFallbackChain (step 2/4), AgentLoop (step 1/5)
```

**gitnexus_cypher** — custom call chain traces:

```cypher
MATCH path = (a)-[:CodeRelation {type: 'CALLS'}*1..2]->(b:Function {name: "get_fallback_chain"})
RETURN [n IN nodes(path) | n.name] AS chain
```

## Example: "LLM calls failing intermittently in agent_loop"

```
1. gitnexus_query({query: "llm rate limit error"})
   → Processes: LLMFallbackChain, RetryHandler
   → Symbols: get_fallback_chain, handle_rate_limit, LiteLLMError

2. gitnexus_context({name: "get_fallback_chain"})
   → Outgoing calls: groq_chat, cerebras_chat (external API!)

3. READ gitnexus://repo/swarm-bot/process/LLMFallbackChain
   → Step 2: get_fallback_chain → calls groq_chat (external)

4. Root cause: groq_chat calls external API without proper timeout handling
   → Fix: add asyncio.wait_for with timeout in llm_client.py
```

## Swarm-Bot Specific Patterns

For Telegram bot issues:
- `gitnexus_query({query: "telegram message handler"})` → find message processing flows
- `gitnexus_query({query: "aiogram handler error"})` → find router/handler issues

For LLM integration issues:
- `gitnexus_query({query: "litellm completion"})` → find LLM call chains
- `gitnexus_context({name: "chat"})` in llm_client.py → trace full LLM fallback chain