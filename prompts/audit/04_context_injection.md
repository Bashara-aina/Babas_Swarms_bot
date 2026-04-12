# AUDIT 04 — Context Injection (Search / Wiki / Memory / Soul)
> Paste this entire prompt into a new OpenCode session.
> Goal: search results, wiki, memory, and soul are ALL in LLM context before every call.

---

```
╔══════════════════════════════════════════════════════════════════╗
║  LEGION AUDIT 04 — Context Injection                            ║
║  Fix: results/memory/wiki/soul must reach the LLM messages[]   ║
╚══════════════════════════════════════════════════════════════════╝

STEP 1 — FIND THE LLM CALL SITE
Find every place litellm.acompletion() or call_llm() is called.
For each call site: what is in the messages[] list at that point?
Add a debug log if needed: logger.debug(f"messages={messages}")

STEP 2 — WEB SEARCH INJECTION
Find where DuckDuckGo / web search is executed (search in skills/, tools/, core/).
Trace the result from search execution → LLM call site.
If the result is NOT in messages[] before the LLM call:
  Find the gap and inject:
    messages.append({"role": "system", "content": f"[Search Results]\n{search_results}"})
  This injection must happen AFTER search completes and BEFORE litellm.acompletion().
Add timeout: asyncio.wait_for(search_coroutine, timeout=8.0)
Add empty-result fallback message.

STEP 3 — WIKI INJECTION
Find core/wiki_bridge.py or wiki_manager.py retrieve() function.
Trace: is the result injected into messages[] or system prompt?
If not:
  In core/system_prompt_builder.py, add:
    wiki_context = await wiki_bridge.retrieve(user_query)
    if wiki_context:
        system_prompt += f"\n\n[Wiki Context]\n{wiki_context}"
Verify wiki retrieval is called for EVERY message, not just wiki commands.

STEP 4 — MEMORY INJECTION
Find core/memory_engine.py read_memory(user_id) function.
Verify it is called BEFORE every LLM call (not just on /recall command).
If missing: add in system_prompt_builder.py or the main handler:
    memories = await memory_engine.read_memory(user_id)
    if memories:
        messages.insert(1, {"role": "system", "content": f"[Your memories about this user]\n{memories}"})
Verify write_memory() is called AFTER LLM responds with useful info.

STEP 5 — SOUL INJECTION
Find core/soul_engine.py get_system_prompt() or equivalent.
Verify the soul content is the FIRST item in every messages[] array (role: system).
Verify it is NEVER conditional (not behind an if-flag, not skipped for any reason).
If any code path assembles messages[] without soul first: fix it.
Add assertion at startup:
    soul = soul_engine.get_system_prompt()
    assert len(soul) > 100, "Soul not loaded!"
    assert "Legion" in soul[:500], "Soul identity missing!"

STEP 6 — VERIFY
Add a single log line at the LLM call site that prints len(messages) and message roles.
Confirm: soul(system) + memory(system) + wiki(system) + conversation + search(system) are all present.

DO NOT modify SOUL.md, CLAUDE.md, or LEGION_MASTER.md.
```
