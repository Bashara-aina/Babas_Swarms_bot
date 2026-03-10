# 🔍 Babas_Swarms_bot — Full Code Audit Report

> Audited by Perplexity AI on **2026-03-10**  
> Covers: `main.py`, `llm_client.py`, `router.py`, `agents.py`, `agents/` dirs, `requirements.txt`

---

## 🔴 CRITICAL — Likely Crashes / Data Loss (Fix First)

### Issue #1 — Dual Router Conflict: `agents.py` vs `router.py`
**File:** `main.py`, `llm_client.py`, `agents.py`, `router.py`  
**Severity:** 🔴 Critical  

`main.py` does `import router as agents`, so `agents.AGENT_MODELS` points to `router.py`.  
But `agents.py` also exists with a **completely different model registry**.  
`llm_client.py` imports from `router` directly.  

Mismatch examples:
- `agents.py` has `"research"` and `"humanizer"` — `router.py` does NOT
- `router.py` has `"computer"`, `"pm"`, `"devops"`, `"marketer"`, `"researcher"` — `agents.py` does NOT
- `/models` command shows agents from `router.py`, but swarm orchestrator may import from `agents.py`

**Fix:** Delete `agents.py` entirely. Consolidate everything into `router.py`. Or rename `router.py` → `agents.py` and update all imports consistently.

---

### Issue #2 — `agents/` subdirectories are ALL empty (Bash brace-expansion artifact in git)
**File:** `agents/` directory  
**Severity:** 🔴 Critical  

Every department folder (`engineering/`, `design/`, `research/`, `marketing/`, `operations/`, `legal_compliance/`, `product/`, `creative/`, `vision_multimodal/`, `nexus/`) contains **zero files**.  

Worse: there is a folder literally named `{engineering,design,research,marketing,operations,legal_compliance,product,creative,vision_multimodal,nexus}` — this is a **bash brace-expansion string** that was accidentally committed as a directory name instead of being expanded.

**Fix:**  
1. Delete `agents/{engineering,...}` garbage folder  
2. Add at minimum an `__init__.py` and one agent class per subdirectory  
3. Wire these into the swarm orchestrator

---

### Issue #3 — `_AGENT_CHAIN` in `llm_client.py` ≠ `FALLBACK_CHAIN["computer"]` in `router.py`
**File:** `llm_client.py` line ~155, `router.py` line ~40  
**Severity:** 🔴 Critical  

The comment even says "Synced with router.py" — but they are NOT synced:  

| Position | `llm_client._AGENT_CHAIN` | `router.FALLBACK_CHAIN["computer"]` |
|----------|--------------------------|--------------------------------------|
| 1st | `zai/glm-4` | `groq/llama-3.3-70b-versatile` |
| 2nd | `groq/llama-3.3-70b-versatile` | `cerebras/qwen-3-235b-a22b` |
| 3rd | `cerebras/qwen-3-235b-a22b` | `gemini/gemini-2.0-flash` |
| 4th | `gemini/gemini-2.0-flash` | *(missing)* |
| 5th | `openrouter/meta-llama/...` | *(missing)* |

**Fix:** Remove `_AGENT_CHAIN` from `llm_client.py`. Use `get_fallback_chain("computer")` from `router.py` directly so there is one source of truth.

---

### Issue #4 — Typing indicator leak in `cmd_scrape` error path
**File:** `main.py` — `cmd_scrape()` function  
**Severity:** 🔴 Critical  

In the `except` block of `cmd_scrape`, `typing_task.cancel()` is called before `status_msg.delete()`. If the curl fallback itself raises an exception, neither cancel nor delete is guaranteed to run — **the `_keep_typing` coroutine runs forever**, constantly sending "typing..." actions to the user's chat.

**Fix:**
```python
finally:
    typing_task.cancel()
    try:
        await status_msg.delete()
    except Exception:
        pass
```

---

### Issue #5 — `msg.from_user` null dereference in `cmd_screen`
**File:** `main.py` — `cmd_screen()` function  
**Severity:** 🔴 Critical  

```python
_last_screenshot[msg.from_user.id] = path  # msg.from_user can be None
```

In aiogram 3.x, `msg.from_user` is `Optional[User]`. If the message comes from a channel or anonymous admin, this raises `AttributeError: 'NoneType' object has no attribute 'id'`.

**Fix:**
```python
if msg.from_user:
    _last_screenshot[msg.from_user.id] = path
```

---

### Issue #6 — Redundant `import time as _time` inside function (shadows global)
**File:** `main.py` — `cmd_recall()` and `cmd_memories()` functions  
**Severity:** 🟡 Minor bug / confusion  

`time` is already imported at the top of `main.py`. Inside `cmd_recall` and `cmd_memories`, there are local re-imports as `import time as _time`. This shadows the global, creates confusion, and is unnecessary.

**Fix:** Remove the local imports. Use the already-imported `time` module.

---

### Issue #7 — Potential arbitrary code execution via user-supplied alert condition
**File:** `main.py` — `cmd_alert()`, `tools/scheduler.py`  
**Severity:** 🔴 Security Risk (low exposure since single-user, but bad practice)  

The `--if` condition string is user-supplied and stored verbatim. If `TaskScheduler` evaluates it with `eval()`, any Python expression can run with the bot's privileges.

**Fix:** Use a safe DSL (e.g., only allow `"X in result"`, `"result > N"` patterns) with a parser, not raw `eval()`.

---

## 🟠 INCORRECT BEHAVIOR — Silent Wrong Results

### Issue #8 — `/swarm` imports `tools/orchestrator.py` which may not exist
**File:** `main.py` — `cmd_swarm()` function  
**Severity:** 🟠 High  

```python
from tools.orchestrator import decompose_task, execute_parallel, synthesize_results
```

This import is inside a `try/except Exception` block, so if the file doesn't exist, the user gets a vague `swarm error: No module named 'tools.orchestrator'` message with no guidance.

**Fix:** Verify `tools/orchestrator.py` exists and is complete. Add a specific `ImportError` handler with a helpful message.

---

### Issue #9 — Cerebras model name mismatch between `router.py` and `agents.py`
**File:** `router.py` line ~20, `agents.py` line ~75  
**Severity:** 🟠 High — one will always 404  

- `router.py` uses: `cerebras/qwen-3-235b-a22b`  
- `agents.py` uses: `cerebras/qwen-3-235b`  

Only one is the correct Cerebras API model ID. The wrong one will return `404 model not found` on every call.

**Fix:** Verify against the Cerebras API docs and standardize to one name across all files.

---

### Issue #10 — `detect_agent()` routes "research" to computer-use mode
**File:** `router.py` — `TASK_KEYWORDS["computer"]`  
**Severity:** 🟠 High  

`"research"` is in `TASK_KEYWORDS["computer"]`, so `"research backpropagation"` triggers `_run_agent_loop()` (full computer control with screenshots, clicks) instead of a simple chat answer. This wastes API calls and confuses users.

**Fix:** Remove broad knowledge keywords from `TASK_KEYWORDS["computer"]`. Computer keywords should only be action-oriented (open, click, run, git, email). Knowledge research should route to `researcher` agent.

---

### Issue #11 — NL routing: `has_soft` triggers computer-use for pure knowledge questions
**File:** `main.py` — `handle_nl()` function  
**Severity:** 🟠 Medium  

Soft keywords include `"open"`, `"monitor"`, `"research"`. A message like:  
> *"can you research how attention mechanisms work?"*  

...triggers `_run_agent_loop()` (computer control mode) even though it's a knowledge question.

**Fix:** When `is_question` is True, it should ALWAYS win over `has_soft`. Move the `is_question` check before `has_soft`:
```python
if has_strong:
    await _run_agent_loop(msg, task)
elif is_question:        # Move this UP before has_soft
    await _execute_chat(msg, task)
elif has_soft:
    await _run_agent_loop(msg, task)
else:
    await _execute_chat(msg, task)
```

---

### Issue #12 — Thread history never saved for computer-use tasks
**File:** `llm_client.py` — `agent_loop()` function  
**Severity:** 🟠 Medium  

`add_to_thread()` is only called inside the `if not msg.tool_calls` branch (text-only final answer). But the loop exits via `return clean or answer, model` only in that branch. If the loop exits by exhausting `max_iterations`, `add_to_thread()` is **never called**, so the full agentic task is lost from thread memory.

**Fix:** Call `add_to_thread()` before every `return` statement in `agent_loop()`.

---

### Issue #13 — `chunk_output()` doesn't handle lines longer than `max_length`
**File:** `llm_client.py` — `chunk_output()` function  
**Severity:** 🟠 Medium  

If a single line is > 4000 characters (e.g., a minified JSON dump or base64 output), the current splitter appends it as one chunk exceeding Telegram's 4096 limit, causing `MessageTooLong` API error.

**Fix:**
```python
for line in text.split("\n"):
    while len(line) > max_length:  # Handle super-long lines
        chunks.append(line[:max_length])
        line = line[max_length:]
    # ... rest of logic
```

---

## 🟡 CODE QUALITY / DEAD CODE

### Issue #14 — `_compact_messages` injects summary as `"role": "user"` (semantically wrong)
**File:** `llm_client.py` — `_compact_messages()` function  
**Severity:** 🟡 Medium  

A conversation summary injected as a `user` message breaks the alternating user/assistant turn structure and can confuse LLMs into thinking the user said all of it.

**Fix:** Inject as a `system` message:
```python
compact_msg = {
    "role": "system",
    "content": f"[Compacted context from {len(middle)} prior steps]:\n{summary}"
}
```

---

### Issue #15 — No timeout on `agent_loop()` — can run indefinitely
**File:** `llm_client.py` — `agent_loop()` function  
**Severity:** 🟡 Medium  

`max_iterations=20` with vision model calls can take 10+ minutes. During this time the bot is unresponsive to the same user for all other commands. There is no wall-clock timeout.

**Fix:**
```python
try:
    result = await asyncio.wait_for(
        agent_loop(task, ...), timeout=300.0  # 5 min hard cap
    )
except asyncio.TimeoutError:
    await msg.answer("⏱ task timed out after 5 minutes — use /cancel next time")
```

---

### Issue #16 — Rate limit cooldown `_COOLDOWN = 60s` is too short for Groq
**File:** `llm_client.py` line ~105  
**Severity:** 🟡 Low  

Groq's free tier rate limits can have multi-minute windows. 60s cooldown means the bot retries a rate-limited provider too early.

**Fix:** Increase to 90–120s, or parse the `Retry-After` header from the rate limit error response if available in `litellm.RateLimitError`.

---

### Issue #17 — `_rate_limited` is in-memory only — resets on bot restart
**File:** `llm_client.py`  
**Severity:** 🟡 Low  

If the bot crashes and restarts during an active rate-limit cooldown, it immediately hammers all providers again, causing a cascade of rate-limit errors on startup.

**Fix:** Persist rate-limit timestamps to a small SQLite table or the existing `aiosqlite` DB (already a dependency).

---

### Issue #18 — `cmd_git` hardcodes `~/swarm-bot` path
**File:** `main.py` — `cmd_git()` function  
**Severity:** 🟡 Medium  

```python
"cd ~/swarm-bot && git status --short && echo '---' && git log --oneline -5"
```

If the bot is deployed to any other directory, this always fails silently (returns an error or the wrong repo's status).

**Fix:**
```python
bot_dir = Path(__file__).parent
output = await run_shell_command(f"cd '{bot_dir}' && git status --short && git log --oneline -5")
```

---

### Issue #19 — `PERSONALITY_WRAPPER` in `agents.py` is dead code
**File:** `agents.py`  
**Severity:** 🟡 Low  

`build_system_prompt(role_prompt)` is defined and uses `PERSONALITY_WRAPPER`, but nothing in `main.py` or `llm_client.py` ever calls `build_system_prompt()`. The personality wrapper is **never injected** into any agent's system prompt.

**Fix:** Either delete it, or wire `build_system_prompt()` into `llm_client.py`'s `SYSTEM_PROMPTS` construction so the personality actually applies.

---

### Issue #20 — `DEBATE_PERSONAS` and `DEBATE_ICONS` in `agents.py` are dead code
**File:** `agents.py`  
**Severity:** 🟡 Low — but represents the biggest missing feature  

Full debate personas (`strategist`, `devil_advocate`, `researcher`, `pragmatist`, `visionary`, `critic`) are defined with rich descriptions — but **no debate orchestrator exists**. The inter-agent debate/discussion/synthesis feature is **entirely unimplemented**.

**Fix:** See Architecture Gaps section (#22).

---

### Issue #21 — `FALLBACK_MODELS` dict in `agents.py` is superseded and unused
**File:** `agents.py`  
**Severity:** 🟡 Low  

`FALLBACK_MODELS` maps each agent to a single fallback model. The actual runtime uses `FALLBACK_CHAIN` (a list). `FALLBACK_MODELS` is legacy dead code that conflicts with `FALLBACK_CHAIN`.

**Fix:** Delete `FALLBACK_MODELS` entirely.

---

## 🔵 ARCHITECTURE GAPS — Missing vs Your Vision

### Issue #22 — No true multi-agent debate loop
**File:** Missing: `tools/debate_orchestrator.py`  
**Severity:** 🔵 Feature Gap  

Goal: agents debate, challenge each other, synthesize the best answer.  
Current reality: `/swarm` runs agents in parallel with zero inter-agent communication. Agents never see each other's output. There is no debate, challenge, or consensus round.

**What needs building:**
```
DecomposeTask → [Agent1, Agent2, ..., AgentN run in parallel]
     → Round 1: each agent gives initial answer
     → Round 2: each agent critiques others' answers  
     → Round 3: devil_advocate attacks the consensus
     → Synthesizer: produce final answer with confidence score
```
The `DEBATE_PERSONAS` in `agents.py` are perfectly spec'd for this — they just need an orchestrator.

---

### Issue #23 — No deep search (Perplexity-style)
**File:** `tools/web_browser.py` — `deep_research()`  
**Severity:** 🔵 Feature Gap  

Current `/research` is: search → scrape top N pages → summarize. That's a single-pass scrape, not deep research.

What's missing:
- Multi-query expansion (generate 5–10 search angles)
- Cross-source contradiction detection
- Iterative search-evaluate-refine loop
- Citation tracking and source quality scoring
- Structured output (findings vs. sources vs. confidence)

---

### Issue #24 — No extended deep thinking (Opus/o1-style)
**File:** `main.py` — `cmd_think()`  
**Severity:** 🔵 Feature Gap  

`/think` just routes to `debug` agent with `show_thinking=True`. This strips `<think>` tags from QwQ-32b — it's not deep thinking, it's just making the chain-of-thought visible.

What's missing:
- Multi-step reflection loop (think → critique own answer → re-think)
- Budget tokens / effort scaling
- Hypothesis generation + testing scaffold
- "Am I confident?" self-assessment before answering

---

### Issue #25 — No Cursor/Claude Code-style capability
**File:** Missing: multi-file edit flow  
**Severity:** 🔵 Feature Gap  

Current code editing is fire-and-forget `write_file` tool calls with no diff preview, no checkpoint, no rollback, no workspace context awareness.

What's missing:
- Show diff before writing (like `git diff`)
- User confirmation before destructive file writes
- Workspace snapshot / checkpoint before edits
- Multi-file edit with dependency awareness
- Test-run-check loop (edit → run tests → fix if broken)

---

## 🟢 UX / UI IMPROVEMENTS

### Issue #26 — `/start` lists commands missing from `set_my_commands()`
**File:** `main.py` — `cmd_start()` and `on_startup()`  
**Severity:** 🟢 UX  

`/start` text shows `/maintenance`, `/delegate`, `/brain_export`, `/task_done`, `/watch_training`, `/alert`, `/monitor`, `/schedule` — but these are not registered in `set_my_commands()`, so they won't appear in Telegram's command autocomplete `/` menu.

**Fix:** Add all user-facing commands to `set_my_commands()`, or split into visible (in autocomplete) vs. power-user (documented in `/start` only).

---

### Issue #27 — No progress percentage or ETA during long operations
**File:** `main.py` — `_run_agent_loop()`  
**Severity:** 🟢 UX  

The status message shows `[1] $ ls ...`, `[2] 📸 grabbing screen...` but gives no sense of how many steps remain or estimated time. After step 10+ it feels stuck.

**Fix:** Show `[step N/20]` and optionally elapsed time: `[4/20] $ npm test... (12s elapsed)`

---

### Issue #28 — `result_keyboard` provider label is unhelpful
**File:** `main.py` — `result_keyboard()` function  
**Severity:** 🟢 UX  

`↑OPENROUTER`, `↑ZAI`, `↑GROQ` tells the user nothing useful. Provider name is not as informative as the actual model.

**Fix:** Show the model name instead:
```python
model_label = parts[-1][:12] if len(parts) > 1 else parts[0][:12]
# Shows: ↑llama-3.3-70b or ↑qwen-3-235b
```

---

### Issue #29 — No `/cancel` for currently running agent loops
**File:** `main.py`  
**Severity:** 🟢 UX  

Once `/do <task>` starts, there is no way to stop it mid-execution. The existing `/cancel` command only cancels scheduled background tasks — not a running `agent_loop()`.

**Fix:** Store the running `asyncio.Task` per user in a `_running_tasks: dict[int, asyncio.Task]` dict. Add a `/stop` command that calls `task.cancel()` on the user's current running task.

---

### Issue #30 — `kbd_agent_hint` buttons (Debug/Code) do nothing useful
**File:** `main.py` — `kbd_agent_hint()` handler  
**Severity:** 🟢 UX  

Tapping `🐛 Debug` or `💻 Code` just replies "debug mode — just type your task" with no examples. The button could directly launch the agent with a prompt, or at minimum show concrete examples.

**Fix:**
```python
examples = {
    "debug": "e.g.:\n• `fix this error: ...`\n• `why is my loss NaN?`\n• paste traceback directly",
    "coding": "e.g.:\n• `write a FastAPI endpoint for...`\n• `refactor this function`\n• `add type hints to my class`"
}
await msg.answer(f"<b>{key} mode</b>\n\n{examples[key]}", parse_mode="HTML")
```

---

### Issue #31 — Memory `/recall` output is ugly and confusing
**File:** `main.py` — `cmd_recall()` function  
**Severity:** 🟢 UX  

```
#42 (03/09[]) rel:0.8432567
  Some memory text here...
```

- `rel:0.8432567` is a raw unrounded float
- `[]` shows empty tags with no graceful handling
- `#42` looks like a GitHub issue number

**Fix:**
```python
rel_pct = int(r['relevance'] * 100)
tags_str = f" • {r['tags']}" if r.get('tags') else ""
lines.append(f"  🧠 {ts}{tags_str} ({rel_pct}% match)")
lines.append(f"  {r['text'][:150]}\n")
```

---

### Issue #32 — No coordinate range validation in `/click`
**File:** `main.py` — `cmd_click()` function  
**Severity:** 🟢 UX + Correctness  

`/click 99999 99999` is accepted and silently fails or clicks off-screen. There is no check that coordinates are within reasonable screen bounds.

**Fix:**
```python
MAX_SCREEN_W, MAX_SCREEN_H = 7680, 4320  # max 8K resolution
if not (0 <= x <= MAX_SCREEN_W and 0 <= y <= MAX_SCREEN_H):
    await msg.answer(f"coordinates out of range (max {MAX_SCREEN_W}×{MAX_SCREEN_H})")
    return
```

---

### Issue #33 — `/agent` command exposes internal agent keys to user
**File:** `main.py` — `cmd_agent()` function  
**Severity:** 🟢 UX  

```python
valid = ", ".join(agents.AGENT_MODELS.keys())
# Shows: vision, coding, debug, math, architect, analyst, computer, general, researcher, marketer, devops, pm
```

`computer` is an internal routing key — users should not invoke it directly. Also, the list has no descriptions, so users don't know which to choose.

**Fix:** Create a `USER_FACING_AGENTS` allowlist with descriptions:
```python
USER_FACING_AGENTS = {
    "coding":    "💻 Write / refactor code",
    "debug":     "🐛 Trace errors, fix bugs",
    "math":      "📐 Equations, tensors, proofs",
    "architect": "🏗 System design, planning",
    "analyst":   "📊 Data analysis, metrics",
    "research":  "🔬 Academic / web research",
    "general":   "🧠 Everything else",
}
```

---

## Issue Priority Summary

| # | Issue | File | Priority |
|---|-------|------|----------|
| 1 | Dual router conflict (`agents.py` vs `router.py`) | Multiple | 🔴 Critical |
| 2 | `agents/` dirs all empty + bash artifact folder | `agents/` | 🔴 Critical |
| 3 | `_AGENT_CHAIN` out of sync with `FALLBACK_CHAIN` | `llm_client.py` | 🔴 Critical |
| 4 | Typing indicator leak on scrape error path | `main.py` | 🔴 Critical |
| 5 | `msg.from_user` null dereference in `cmd_screen` | `main.py` | 🔴 Critical |
| 6 | Redundant `import time as _time` inside functions | `main.py` | 🟡 Minor |
| 7 | User-supplied alert condition may allow code exec | `main.py` | 🔴 Security |
| 8 | `/swarm` tools import may fail silently | `main.py` | 🟠 High |
| 9 | Cerebras model name mismatch (`-a22b` suffix) | `router.py` / `agents.py` | 🟠 High |
| 10 | `detect_agent()` routes knowledge queries to computer | `router.py` | 🟠 High |
| 11 | `is_question` check loses to `has_soft` in NL router | `main.py` | 🟠 Medium |
| 12 | Thread history not saved for computer-use tasks | `llm_client.py` | 🟠 Medium |
| 13 | `chunk_output()` breaks on lines > max_length | `llm_client.py` | 🟠 Medium |
| 14 | Context summary injected as `"user"` role (wrong) | `llm_client.py` | 🟡 Medium |
| 15 | No wall-clock timeout on `agent_loop()` | `llm_client.py` | 🟡 Medium |
| 16 | Rate limit cooldown 60s too short for Groq | `llm_client.py` | 🟡 Low |
| 17 | `_rate_limited` resets on restart (in-memory only) | `llm_client.py` | 🟡 Low |
| 18 | `cmd_git` hardcodes `~/swarm-bot` path | `main.py` | 🟡 Medium |
| 19 | `PERSONALITY_WRAPPER` / `build_system_prompt` dead code | `agents.py` | 🟡 Low |
| 20 | `DEBATE_PERSONAS` / `DEBATE_ICONS` dead code | `agents.py` | 🟡 Low (feature gap) |
| 21 | `FALLBACK_MODELS` dict dead code | `agents.py` | 🟡 Low |
| 22 | No inter-agent debate loop (core vision unimplemented) | Missing file | 🔵 Feature |
| 23 | No deep search (Perplexity-style) | `tools/web_browser.py` | 🔵 Feature |
| 24 | No deep thinking loop (Opus/o1-style) | `main.py` | 🔵 Feature |
| 25 | No Cursor-style diff/confirm before file writes | Missing | 🔵 Feature |
| 26 | `/start` lists commands not in `set_my_commands()` | `main.py` | 🟢 UX |
| 27 | No progress % or ETA during long agent loops | `main.py` | 🟢 UX |
| 28 | `result_keyboard` shows unhelpful provider label | `main.py` | 🟢 UX |
| 29 | No `/stop` to cancel running agent loop mid-execution | `main.py` | 🟢 UX |
| 30 | Debug/Code keyboard buttons give no examples | `main.py` | 🟢 UX |
| 31 | `/recall` output format is ugly and unrounded | `main.py` | 🟢 UX |
| 32 | No screen coordinate validation in `/click` | `main.py` | 🟢 UX |
| 33 | `/agent` exposes internal keys (e.g. `computer`) | `main.py` | 🟢 UX |

---

## Recommended Fix Order

1. **Fix #1, #3** — Merge routers, single source of truth
2. **Fix #2** — Clean up `agents/` empty dirs + bash artifact
3. **Fix #4, #5** — Prevent crashes in `cmd_screen` and `cmd_scrape`  
4. **Fix #7** — Sanitize alert conditions (security)
5. **Fix #9** — Verify correct Cerebras model name
6. **Fix #10, #11** — Fix NL routing logic
7. **Fix #12, #13, #14** — Fix thread saving, chunk splitting, compact role
8. **Fix #15** — Add timeout to agent loop
9. **Fix #18** — Dynamic git path
10. **Fix #22–25** — Build the actual swarm debate + deep search features
11. **Fix #26–33** — UX polish pass
