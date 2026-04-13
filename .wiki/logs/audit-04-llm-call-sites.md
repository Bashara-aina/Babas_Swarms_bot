---
date: "2026-04-12"
audit: "Context Injection — Soul/Wiki/Memory/Search"
---
# AUDIT 04: LLM Call Sites Inventory

## Primary LLM Call Site: `llm_client/__init__.py`

### Main `chat()` function — `_call_model()` at line 1192

**messages[] at call time (line 1153-1155):**
```python
messages: list[dict] = [{"role": "system", "content": system_prompt}]
messages.extend(_conversation_history)  # from conversation_interface
messages.append({"role": "user", "content": user_content})
```

**Context layers in system_prompt (concatenated, NOT separate messages):**
1. Soul (line 915): `build_soul_context()` → included via prompt_sections → system_prompt
2. Memory: semantic_memory_lines (line 1011) → embedded in prompt_sections
3. Wiki: from `unified_prompt_context.gather_parallel_prompt_layers()` (line 1019) → prompt_sections
4. GSA Voice, emotions, narrative, relationship memory → all in prompt_sections
5. Skills, mode instructions, research policy → prompt_sections

**ISSUE:** All context concatenated into ONE system message. Not separate.

---

## Secondary Call Sites (tool-calling loop)

### `_agent_loop_inner()` — line 551
```python
messages: list[dict] = [
    {"role": "system", "content": system},
    {"role": "user", "content": task},
]
```
System = SYSTEM_PROMPTS.get(agent_key) — basic persona, NO soul/memory/wiki injected.
**ISSUE:** No soul, no memory, no wiki at all in agent_loop.

---

## Self-Awareness Gate Search — lines 1300-1320

```python
search_results = await search_web(search_query)
if search_results:
    tool_result_msg = {
        "role": "user",  # ← ISSUE: should be "system"
        "content": f"[Hasil pencarian web untuk: {task}]\n{search_results}\n\n..."
    }
    messages.append(tool_result_msg)
    synth_resp = await _call_model(model=chain[0], messages=messages, ...)
```
**ISSUE:** Search results injected as "user" message instead of "system" message.

---

## Other LLM Call Sites (secondary, lower priority)

| File | Line | Function | Context Injected? |
|------|------|----------|------------------|
| `core/intent_router.py` | 424 | litellm.acompletion | YES — via system_prompt |
| `core/skills/builtin/productivity.py` | 125 | litellm.acompletion | Unknown |
| `core/skills/builtin/research.py` | 119 | litellm.acompletion | Unknown |
| `tools/briefing.py` | 190 | litellm.acompletion | Unknown |
| `tools/swarm_wire.py` | 89, 97 | litellm.acompletion | Unknown |
| `tools/supabase_client.py` | 381, 435 | litellm.acompletion | Unknown |
| `tools/github_intel.py` | 172, 306 | litellm.acompletion | Unknown |
| `tools/location_advisor.py` | 142 | litellm.acompletion | Unknown |
| `swarms_bot/orchestrator/orchestration_runner.py` | 200 | litellm.acompletion | Unknown |
| `swarms_bot/orchestrator/dag_planner.py` | 133 | litellm.acompletion | Unknown |
| `handlers/streaming.py` | 53 | litellm.acompletion | Unknown |
| `core/self_upgrade.py` | 258, 396 | litellm.acompletion | Unknown |
| `core/memory/consolidator.py` | 156, 258 | litellm.acompletion | Unknown |
| `core/autonomous_router.py` | 549 | litellm.acompletion | Unknown |
| `core/capability_audit.py` | 160 | litellm.acompletion | Unknown |
| `skills/database_agent.py` | 65 | litellm.acompletion | Unknown |
| `legion/anti_slop/integration.py` | 84, 95 | _call_llm | Unknown |
| `handlers/nihongo_handler.py` | 257, 286 | _call_llm | Unknown |

---

## Summary of Issues Found

### Critical (must fix)
1. **Primary chat() function:** All context concatenated into single system message — should be separate messages for soul/memory/wiki
2. **Search injection:** Uses "user" role instead of "system" role for search results
3. **_agent_loop_inner():** No soul/memory/wiki context at all

### Medium (should fix)
4. **Secondary call sites:** Many tools/core modules call litellm directly without proper context

---

## Proposed Fix Architecture

In `llm_client/__init__.py` `chat()` function:

```python
# Build separate system messages for each context layer
_messages: list[dict] = []

# 1. Soul — FIRST, always present
_soul = build_soul_context()
if _soul:
    _messages.append({"role": "system", "content": f"[Soul]\n{_soul}"})

# 2. Memory — SECOND, via semantic search
_semantic_memory_lines = await LegionSemanticMemory().search_memories(task, str(user_id), limit=5)
if _semantic_memory_lines:
    _messages.append({"role": "system", "content": f"[Memory]\n" + "\n".join(_semantic_memory_lines)})

# 3. Wiki — THIRD, via unified_prompt_context
_wiki_blocks = await gather_parallel_prompt_layers(task, str(user_id), mode=_chat_mode)
for _block in _wiki_blocks:
    _messages.append({"role": "system", "content": _block})

# 4. Conversation history
if user_id:
    _conversation_history = get_conversation_history(str(user_id), last_n=6)
    _messages.extend(_conversation_history)

# 5. User message — LAST
_messages.append({"role": "user", "content": user_content})

# Now _messages has distinct system messages for each layer
# When search fires:
_messages.insert(3, {"role": "system", "content": f"[Search Results]\n{search_results}"})
```

---

**Logged:** 2026-04-12
**Audit:** LEGION AUDIT 04