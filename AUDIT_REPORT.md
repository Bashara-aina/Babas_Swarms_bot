# 🔍 Babas_Swarms_bot — Full Code Audit Report (v2)

> Audited by Perplexity AI on **2026-03-10**  
> Files audited line-by-line: `main.py`, `llm_client.py`, `router.py`, `agents.py`, `computer_agent.py`, `agents/` dirs, `requirements.txt`  
> **57 total issues** across 5 severity tiers

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
**File:** `llm_client.py` line ~258, `router.py`  
**Severity:** 🔴 Critical  

The comment says "Synced with router.py" — but they are NOT synced:

| Position | `llm_client._AGENT_CHAIN` | `router.FALLBACK_CHAIN["computer"]` |
|----------|--------------------------|--------------------------------------|
| 1st | `zai/glm-4` | `groq/llama-3.3-70b-versatile` |
| 2nd | `groq/llama-3.3-70b-versatile` | `cerebras/qwen-3-235b-a22b` |
| 3rd | `cerebras/qwen-3-235b-a22b` | `gemini/gemini-2.0-flash` |
| 4th | `gemini/gemini-2.0-flash` | *(missing)* |
| 5th | `openrouter/meta-llama/...` | *(missing)* |

**Fix:** Remove `_AGENT_CHAIN` from `llm_client.py`. Call `get_fallback_chain("computer")` from `router.py` directly — one source of truth.

---

### Issue #4 — Typing indicator leak in `cmd_scrape` error path
**File:** `main.py` — `cmd_scrape()` function  
**Severity:** 🔴 Critical  

In the `except` block, `typing_task.cancel()` is called before `status_msg.delete()`. If the curl fallback also raises, neither runs — **`_keep_typing` leaks forever**, spamming "typing..." to the user.

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
**File:** `main.py` — `cmd_screen()`  
**Severity:** 🔴 Critical  

```python
_last_screenshot[msg.from_user.id] = path  # msg.from_user can be None
```

In aiogram 3.x, `msg.from_user` is `Optional[User]`. Channel posts crash with `AttributeError`.

**Fix:**
```python
if msg.from_user:
    _last_screenshot[msg.from_user.id] = path
```

---

### Issue #6 — `take_screenshot()` in `llm_client.py` shadows `computer_agent.take_screenshot()`
**File:** `llm_client.py` — bottom of file  
**Severity:** 🔴 Critical (silent wrong behavior)

`llm_client.py` defines its own `take_screenshot()` wrapper:
```python
async def take_screenshot() -> Optional[str]:
    """Wrapper that delegates to computer_agent.take_screenshot()."""
    return await computer_agent.take_screenshot()
```

But `main.py` does `from llm_client import take_screenshot` AND `from computer_agent import take_screenshot` in different scopes. Whichever import resolves last wins, creating **non-deterministic function resolution**. If the wrong one is used in the agent loop, screenshots may either loop infinitely or return stale paths.

**Fix:** Remove the wrapper in `llm_client.py`. Import `take_screenshot` only from `computer_agent` everywhere.

---

### Issue #7 — Potential arbitrary code execution via user-supplied alert condition
**File:** `main.py` — `cmd_alert()`, `tools/scheduler.py`  
**Severity:** 🔴 Security Risk  

The `--if` condition string is user-supplied and stored verbatim. If `TaskScheduler` evaluates it with `eval()`, any Python expression runs with bot privileges.

**Fix:** Use a safe DSL — only allow patterns like `"X in result"`, `"result > N"` with a whitelist parser.

---

### Issue #8 — `_detected_display` global is never reset on display change
**File:** `computer_agent.py` — `detect_display()`  
**Severity:** 🔴 Critical (on multi-session deployments)  

```python
global _detected_display
if _detected_display:
    return _detected_display  # cached forever, never refreshed
```

If the bot is started headlessly and a display connects later (common on a workstation), the cached `:0` value stays stale. Screenshot, click, and keyboard calls all silently fail with `cannot open display`.

**Fix:** Add a TTL or an explicit `reset_display_cache()` function that clears `_detected_display = None`:
```python
async def reset_display_cache() -> str:
    global _detected_display
    _detected_display = None
    return await detect_display()
```

---

### Issue #9 — `set_clipboard()` has shell injection via single-quote escape
**File:** `computer_agent.py` — `set_clipboard()`  
**Severity:** 🔴 Security  

```python
safe = text.replace("'", "'\\''")
out = await run_shell(f"echo '{safe}' | DISPLAY={display} xclip ...")
```

This approach breaks for text containing `$`, backticks, or newlines in the shell context — a payload like `$(rm -rf ~)` would still execute in some shells. For clipboard, pipe via `stdin` instead:

**Fix:**
```python
proc = await asyncio.create_subprocess_exec(
    "xclip", "-selection", "clipboard",
    stdin=asyncio.subprocess.PIPE,
    env={**os.environ, "DISPLAY": display}
)
await proc.communicate(input=text.encode())
```

---

## 🟠 INCORRECT BEHAVIOR — Silent Wrong Results

### Issue #10 — `/swarm` imports `tools/orchestrator.py` which may not exist
**File:** `main.py` — `cmd_swarm()`  
**Severity:** 🟠 High  

Import inside `try/except Exception` means a missing file gives a vague error with no guidance.

**Fix:** Use an explicit `ImportError` handler with a clear user message.

---

### Issue #11 — Cerebras model name mismatch (`-a22b` suffix)
**File:** `router.py`, `agents.py`, `llm_client.py`  
**Severity:** 🟠 High — one will always 404  

- `router.py` / `llm_client.py`: `cerebras/qwen-3-235b-a22b`  
- `agents.py`: `cerebras/qwen-3-235b`

Only one is correct. The wrong one 404s silently on every call.

**Fix:** Verify in Cerebras docs and use one name everywhere.

---

### Issue #12 — `detect_agent()` routes "research" to computer-use mode
**File:** `router.py` — `TASK_KEYWORDS["computer"]`  
**Severity:** 🟠 High  

`"research"` is in `TASK_KEYWORDS["computer"]`, routing `"research backpropagation"` to `_run_agent_loop()` (full desktop control) instead of chat.

**Fix:** Remove knowledge keywords from `TASK_KEYWORDS["computer"]`. Only action-oriented words belong there.

---

### Issue #13 — NL routing: `has_soft` beats `is_question` check
**File:** `main.py` — `handle_nl()`  
**Severity:** 🟠 Medium  

`"can you research how attention works?"` contains `"research"` → triggers computer use even though it's a knowledge question.

**Fix:** Move `is_question` check before `has_soft` in the routing ladder.

---

### Issue #14 — Thread history never saved when `agent_loop()` hits max iterations
**File:** `llm_client.py` — `agent_loop()`  
**Severity:** 🟠 Medium  

`add_to_thread()` is only called inside the `if not msg.tool_calls` branch. If max iterations are exhausted, `add_to_thread()` is never called — the full agentic task is lost from memory.

**Fix:** Call `add_to_thread()` before every `return` in `agent_loop()`.

---

### Issue #15 — `chunk_output()` doesn't handle lines longer than `max_length`
**File:** `llm_client.py` — `chunk_output()`  
**Severity:** 🟠 Medium  

Single lines > 4000 chars (base64, minified JSON) create chunks exceeding Telegram's 4096 limit → `MessageTooLong` API error.

**Fix:**
```python
for line in text.split("\n"):
    while len(line) > max_length:
        chunks.append(line[:max_length])
        line = line[max_length:]
```

---

### Issue #16 — `screenshot_region()` returns path even if file doesn't exist
**File:** `computer_agent.py` — `screenshot_region()`  
**Severity:** 🟠 Medium  

```python
return path if Path(path).exists() else None
```

This is correct, BUT `take_screenshot()` returns `path` without checking `stat().st_size > 1000` — it only size-checks in the loop, not in the final return. If `scrot` exits 0 but writes an empty file, `take_screenshot()` returns a valid-looking path that actually contains 0 bytes. The agent then tries to base64-encode an empty file and crashes inside `analyze_screenshot()`.

**Fix:**
```python
if Path(path).exists() and Path(path).stat().st_size > 500:
    return path
return None
```

---

### Issue #17 — `analyze_screenshot()` opens file synchronously in an async function
**File:** `llm_client.py` — `analyze_screenshot()`  
**Severity:** 🟠 Medium  

```python
with open(image_path, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()
```

This is a **blocking file read** inside an `async` function. For large screenshots (1–5 MB) on a busy event loop, this blocks all Telegram message processing during the read.

**Fix:**
```python
async with aiofiles.open(image_path, "rb") as f:
    raw = await f.read()
b64 = base64.b64encode(raw).decode()
```

---

### Issue #18 — `keyboard_type()` shell escape is incomplete
**File:** `computer_agent.py` — `keyboard_type()`  
**Severity:** 🟠 Medium  

```python
safe_text = text.replace("\\", "\\\\").replace("'", "'\\''")
cmd = f"... xdotool type ... -- '{safe_text}'"
```

`$`, backticks, `!`, and newlines are not escaped. A user asking the bot to type a shell command with `$(...)` in it could cause unintended shell execution. Additionally, `xdotool type` has known issues with non-ASCII characters — the `--clearmodifiers` flag doesn't help with Unicode above BMP.

**Fix:** Use `xdotool type` via `subprocess.run()` with the text passed as a proper argument, not interpolated into the shell string:
```python
await asyncio.create_subprocess_exec(
    "xdotool", "type", "--clearmodifiers", f"--delay={delay_ms}", "--", text,
    env={**os.environ, "DISPLAY": display}
)
```

---

### Issue #19 — `open_app()` uses `&` in shell but `run_shell()` waits for completion
**File:** `computer_agent.py` — `open_app()`  
**Severity:** 🟠 Medium  

```python
cmd = f"DISPLAY={display} {APP_MAP[key]} &"
await run_shell(cmd, timeout=5)
```

`run_shell()` uses `proc.communicate()` which waits for the process to finish. The `&` backgrounds the app in a subshell, but the subshell itself waits for `communicate()`. For apps that don't detach properly (like `gnome-terminal`), this **blocks for up to 5 seconds** on every open.

**Fix:** Use `subprocess.Popen()` or `asyncio.create_subprocess_shell()` without `communicate()` for fire-and-forget launches.

---

## 🟡 CODE QUALITY / DEAD CODE

### Issue #20 — `_compact_messages` injects summary as `"role": "user"` (wrong)
**File:** `llm_client.py` — `_compact_messages()`  
**Severity:** 🟡 Medium  

A conversation summary as a `user` message breaks the alternating turn structure and confuses LLMs.

**Fix:** Use `"role": "system"` for the compact summary message.

---

### Issue #21 — No wall-clock timeout on `agent_loop()` — can run indefinitely
**File:** `llm_client.py` — `agent_loop()`  
**Severity:** 🟡 Medium  

`max_iterations=20` with vision calls can take 10+ minutes with no timeout.

**Fix:**
```python
result = await asyncio.wait_for(agent_loop(task, ...), timeout=300.0)
```

---

### Issue #22 — Rate limit cooldown `_COOLDOWN = 60s` is too short for Groq
**File:** `llm_client.py`  
**Severity:** 🟡 Low  

Groq's free tier windows can be multi-minute. 60s means premature retries.

**Fix:** Increase to 90–120s or parse `Retry-After` from `litellm.RateLimitError`.

---

### Issue #23 — `_rate_limited` is in-memory only — resets on bot restart
**File:** `llm_client.py`  
**Severity:** 🟡 Low  

Restart during cooldown → immediate cascade of rate-limit errors on all providers.

**Fix:** Persist timestamps to `aiosqlite` DB (already a dependency in `requirements.txt`).

---

### Issue #24 — `cmd_git` hardcodes `~/swarm-bot` path
**File:** `main.py` — `cmd_git()`  
**Severity:** 🟡 Medium  

```python
"cd ~/swarm-bot && git status --short && git log --oneline -5"
```

**Fix:**
```python
bot_dir = Path(__file__).parent
await run_shell_command(f"cd '{bot_dir}' && git status --short && git log --oneline -5")
```

---

### Issue #25 — `git_status`, `git_pull`, etc. in `TOOL_DEFINITIONS` also hardcode `~/swarm-bot`
**File:** `computer_agent.py` — git tool definitions  
**Severity:** 🟡 Medium  

The git tools default to `~/swarm-bot` in their descriptions and implementations in `tools/git_tools.py`. Same problem as #24 but in the LLM-callable tool layer, meaning the agent itself may call `git_commit` on the wrong repo.

**Fix:** Default `repo_path` to `str(Path(__file__).parent)` dynamically.

---

### Issue #26 — Redundant `import time as _time` inside functions
**File:** `main.py` — `cmd_recall()`, `cmd_memories()`  
**Severity:** 🟡 Minor  

`time` is already imported at module level. Local re-imports shadow it unnecessarily.

**Fix:** Remove the local imports.

---

### Issue #27 — `PERSONALITY_WRAPPER` / `build_system_prompt()` in `agents.py` are dead code
**File:** `agents.py`  
**Severity:** 🟡 Low  

Nothing ever calls `build_system_prompt()`. The personality wrapper is never injected.

**Fix:** Wire it into `llm_client.py`'s `SYSTEM_PROMPTS` construction, or delete it.

---

### Issue #28 — `DEBATE_PERSONAS` and `DEBATE_ICONS` in `agents.py` are dead code
**File:** `agents.py`  
**Severity:** 🟡 Low (but represents the biggest missing feature)  

Fully-written personas (`strategist`, `devil_advocate`, `researcher`, `pragmatist`, `visionary`, `critic`) exist but no orchestrator uses them.

**Fix:** See Architecture Gaps section — build the debate loop.

---

### Issue #29 — `FALLBACK_MODELS` dict in `agents.py` is superseded and unused
**File:** `agents.py`  
**Severity:** 🟡 Low  

Legacy single-model fallback dict. `FALLBACK_CHAIN` (list) supersedes it but both exist.

**Fix:** Delete `FALLBACK_MODELS`.

---

### Issue #30 — `BROWSER_APPS` dict in `computer_agent.py` is never used
**File:** `computer_agent.py`  
**Severity:** 🟡 Low  

```python
BROWSER_APPS = {
    "whatsapp": "https://web.whatsapp.com",
    "gmail":    "https://mail.google.com",
    ...
}
```

`open_app()` does NOT reference `BROWSER_APPS` — it uses `APP_MAP` directly. `BROWSER_APPS` is unused dead code.

**Fix:** Either use it in `open_app()` (e.g., open these as `--app=` in Chrome), or delete it.

---

### Issue #31 — `keyboard_shortcut()` is a pure alias for `key_press()` — unnecessary
**File:** `computer_agent.py`  
**Severity:** 🟡 Minor  

```python
async def keyboard_shortcut(keys: str) -> str:
    """Alias for key_press, more descriptive name."""
    return await key_press(keys)
```

`keyboard_shortcut` is registered nowhere in `TOOL_DEFINITIONS` and not in the `execute_tool` dispatch map, so it's effectively dead code that can't be called by the agent.

**Fix:** Either add it to `TOOL_DEFINITIONS` and `execute_tool`, or delete it.

---

### Issue #32 — `_parse_groq_xml_tool_call()` regex is fragile
**File:** `llm_client.py`  
**Severity:** 🟡 Medium  

```python
r'function=(\w+)(\{[^}]*\})'  # only matches single-level JSON (no nested {})
```

This regex breaks on any tool argument with a nested JSON object (e.g., `web_fill_form` with `fields: {name: value}` — the outer `{` closes at the first `}`).

**Fix:** Use a proper JSON depth-counter parser instead of `[^}]*`.

---

### Issue #33 — `_strip_think_tags()` uses non-greedy `.*?` but `re.DOTALL` makes it greedy across calls
**File:** `llm_client.py` — `_strip_think_tags()`  
**Severity:** 🟡 Low  

```python
think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
```

If a model outputs multiple `<think>` blocks (e.g., QwQ-32b often does), only the first is captured. All subsequent thinking blocks remain in the answer and are sent to the user as raw text.

**Fix:**
```python
think_blocks = re.findall(r"<think>(.*?)</think>", text, re.DOTALL)
thinking = "\n\n".join(b.strip() for b in think_blocks)
answer = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
```

---

### Issue #34 — `run_shell()` in `computer_agent.py` captures stderr by default, mixing it with stdout
**File:** `computer_agent.py` — `run_shell()`  
**Severity:** 🟡 Low  

```python
return f"exit {proc.returncode}\nstdout: {out}\nstderr: {err}".strip()
```

When a command succeeds but writes warnings to stderr (e.g., `git pull`), those warnings are included in the `"(done, no output)"` return — confusing the LLM into thinking the command failed.

**Fix:** Only include `stderr` in the output on non-zero exit code:
```python
if proc.returncode == 0:
    return out or "(done, no output)"
return f"EXIT {proc.returncode}\n{out}\nSTDERR: {err}".strip()
```

---

### Issue #35 — No validation that screenshot file is a valid PNG before base64 encoding
**File:** `llm_client.py` — `analyze_screenshot()`  
**Severity:** 🟡 Medium  

If `take_screenshot()` returns a path to a partial/corrupted image (network drive, FUSE error), `base64.b64encode(f.read())` succeeds but the API returns `400 invalid image`. The error message is unhelpful (`b64 decode error`).

**Fix:**
```python
from PIL import Image
try:
    Image.open(image_path).verify()
except Exception as e:
    raise RuntimeError(f"Screenshot file is not a valid image: {e}")
```

---

## 🔵 ARCHITECTURE GAPS — Missing vs Your Vision

### Issue #36 — No true multi-agent debate loop
**File:** Missing: `tools/debate_orchestrator.py`  
**Severity:** 🔵 Feature Gap  

Goal: agents debate, challenge each other, synthesize the best answer.  
Reality: `/swarm` runs agents in parallel with **zero inter-agent communication**.

**What needs building:**
```
DecomposeTask → [Agent1...AgentN run in parallel]
  → Round 1: each agent gives initial answer
  → Round 2: each agent critiques others' answers
  → Round 3: devil_advocate attacks consensus
  → Synthesizer: final answer + confidence score
```
`DEBATE_PERSONAS` in `agents.py` are perfectly spec'd — they just need an orchestrator.

---

### Issue #37 — No deep search (Perplexity-style)
**File:** `tools/web_browser.py` — `deep_research()`  
**Severity:** 🔵 Feature Gap  

Current `/research`: search → scrape N pages → summarize. Single-pass, no iteration.

Missing:
- Multi-query expansion (5–10 search angles)
- Cross-source contradiction detection
- Iterative search-evaluate-refine loop
- Citation tracking and source quality scoring
- Structured output: findings / sources / confidence

---

### Issue #38 — No extended deep thinking (Opus/o1-style)
**File:** `main.py` — `cmd_think()`  
**Severity:** 🔵 Feature Gap  

`/think` just shows `<think>` tags from QwQ-32b. It's not deep thinking — it's visible chain-of-thought.

Missing:
- Multi-step reflection loop (think → critique → re-think)
- Budget tokens / effort scaling
- Hypothesis generation + testing scaffold
- Self-confidence assessment before answering

---

### Issue #39 — No Cursor/Claude Code-style capability
**File:** Missing: multi-file edit flow  
**Severity:** 🔵 Feature Gap  

`write_file` is fire-and-forget with no diff preview, no checkpoint, no rollback.

Missing:
- Diff preview before writing
- User confirmation on destructive edits
- Workspace snapshot before edits
- Multi-file edit with dependency awareness
- Test-run-fix loop

---

### Issue #40 — `APP_MAP` in `computer_agent.py` is hardcoded and not user-configurable
**File:** `computer_agent.py`  
**Severity:** 🔵 Minor Feature Gap  

`APP_MAP` contains Bashara's personal app preferences hardcoded (Spotify, Discord, Obsidian, PyCha rm, etc.). On any other machine or for any other user, half these entries either don't apply or are wrong.

**Fix:** Load `APP_MAP` from a `~/.legion/apps.json` config file with the hardcoded dict as default fallback. Expose a `/add_app` command to extend it at runtime.

---

### Issue #41 — No persistent user preferences / config system
**File:** Entire codebase  
**Severity:** 🔵 Feature Gap  

Every preference (default agent, language, response style, cooldown values) is hardcoded in constants. There's no per-user or per-session configuration that persists across restarts.

**Fix:** Use the existing `aiosqlite` dependency to persist a `user_config` table.

---

## 🟢 UX / UI IMPROVEMENTS

### Issue #42 — `/start` lists commands missing from `set_my_commands()`
**File:** `main.py`  
**Severity:** 🟢 UX  

`/maintenance`, `/delegate`, `/brain_export`, `/task_done`, `/watch_training`, `/alert`, `/monitor`, `/schedule` don't appear in Telegram's command autocomplete.

**Fix:** Register all user-facing commands in `set_my_commands()`.

---

### Issue #43 — No progress percentage or ETA during long operations
**File:** `main.py` — `_run_agent_loop()`  
**Severity:** 🟢 UX  

Step labels show `[1], [2]...` with no total or elapsed time.

**Fix:** Show `[4/20] $ npm test... (12s elapsed)`.

---

### Issue #44 — `result_keyboard` provider label is unhelpful
**File:** `main.py` — `result_keyboard()`  
**Severity:** 🟢 UX  

`↑OPENROUTER`, `↑ZAI` means nothing. Show model name instead: `↑qwen-3-235b`.

---

### Issue #45 — No `/stop` to cancel running agent loops
**File:** `main.py`  
**Severity:** 🟢 UX  

Once `/do <task>` starts, it can't be stopped. The bot is frozen for other commands.

**Fix:** Store `asyncio.Task` per user in `_running_tasks: dict[int, asyncio.Task]`. Add `/stop` to cancel it.

---

### Issue #46 — `kbd_agent_hint` buttons (Debug/Code) give no examples
**File:** `main.py` — `kbd_agent_hint()` handler  
**Severity:** 🟢 UX  

Tapping `🐛 Debug` just replies "debug mode — just type your task". Should show examples.

---

### Issue #47 — `/recall` output format is ugly
**File:** `main.py` — `cmd_recall()`  
**Severity:** 🟢 UX  

`#42 (03/09[]) rel:0.8432567` — raw float, empty tags displayed, confusing `#` prefix.

**Fix:**
```python
rel_pct = int(r['relevance'] * 100)
tags_str = f" • {r['tags']}" if r.get('tags') else ""
lines.append(f"  🧠 {ts}{tags_str} ({rel_pct}% match)")
```

---

### Issue #48 — No coordinate validation in `/click`
**File:** `main.py` — `cmd_click()`  
**Severity:** 🟢 UX  

`/click 99999 99999` accepted and silently fails.

**Fix:** Validate against screen bounds from `get_screen_size()`.

---

### Issue #49 — `/agent` exposes internal keys (e.g. `computer`)
**File:** `main.py` — `cmd_agent()`  
**Severity:** 🟢 UX  

`computer` is an internal routing key that users shouldn't invoke directly. The list also has no descriptions.

**Fix:** Create a `USER_FACING_AGENTS` allowlist with descriptions.

---

### Issue #50 — `open_app()` hardcodes `gnome-terminal` and `nautilus`
**File:** `computer_agent.py` — `APP_MAP`  
**Severity:** 🟢 UX (portability)  

`APP_MAP["terminal"] = "gnome-terminal"` and `APP_MAP["files"] = "nautilus ."` assume GNOME desktop. On KDE (Plasma), XFCE, or i3, these silently fail with `command not found`.

**Fix:** Auto-detect terminal emulator:
```python
import shutil
TERMINAL = next((t for t in ["gnome-terminal","konsole","xterm","alacritty"] if shutil.which(t)), "xterm")
```

---

### Issue #51 — `web_research` tool description says "10 pages" but `deep_research()` default may be different
**File:** `computer_agent.py` — `TOOL_DEFINITIONS` for `web_research`  
**Severity:** 🟢 Minor  

Tool description says `max_pages default: 10` but the actual `deep_research()` call uses `max_pages=args.get("max_pages", 10)` — consistent but the description should match the actual default in `tools/web_browser.py`. If that function's default was changed, the tool description silently lies to the LLM.

**Fix:** Import the default from `tools/web_browser.py` rather than duplicating it.

---

### Issue #52 — No `/help` command — only `/start`
**File:** `main.py`  
**Severity:** 🟢 UX  

`/start` is a one-shot greeting. Users returning after weeks have no way to browse capabilities without re-triggering the whole start flow. A `/help [topic]` with sections (coding, search, swarm, computer, memory) would improve discoverability.

---

### Issue #53 — Long shell outputs sent as raw text without code block formatting
**File:** `main.py` — `cmd_shell()`, `cmd_git()`  
**Severity:** 🟢 UX  

Shell output is sent wrapped in `<pre>` tags, which Telegram renders correctly — but when the output contains Telegram-reserved characters (`<`, `>`, `&`), it breaks HTML parsing and sends garbled text.

**Fix:** Escape HTML entities in shell output before wrapping in `<pre>`:
```python
import html
safe_output = html.escape(output)
await msg.answer(f"<pre>{safe_output}</pre>", parse_mode="HTML")
```

---

### Issue #54 — No command to list all scheduled tasks clearly
**File:** `main.py`  
**Severity:** 🟢 UX  

`/schedule` exists but its output format is unclear. A `/tasks` command that shows a numbered list with cron expression, next run time, and last result would significantly help.

---

### Issue #55 — `_tool_label()` has `"format_code"` and `"parallel_agents"` entries for non-existent tools
**File:** `llm_client.py` — `_tool_label()`  
**Severity:** 🟡 Minor  

```python
"format_code":     lambda a: f"✨ formatting {a.get('path','')}",
"parallel_agents": lambda a: f"🔄 swarm: {a.get('task','')[:40]}",
```

Neither `format_code` nor `parallel_agents` exist in `TOOL_DEFINITIONS` in `computer_agent.py`. These label entries are orphans — they reference tools that were planned but never implemented.

**Fix:** Either implement the tools and add them to `TOOL_DEFINITIONS`, or remove these orphan label entries.

---

### Issue #56 — `upgrade_from_git()` hardcodes `~/swarm-bot`
**File:** `computer_agent.py` — `upgrade_from_git()`  
**Severity:** 🟡 Medium  

Same problem as Issue #24 — the default `repo_dir` is hardcoded, not derived from `__file__`.

**Fix:**
```python
async def upgrade_from_git(repo_dir: str = str(Path(__file__).parent)) -> str:
```

---

### Issue #57 — No `.env.example` file in the repository
**File:** Repository root  
**Severity:** 🟢 UX / Developer Experience  

The bot needs `CEREBRAS_API_KEY`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `ZAI_API_KEY`, `HF_TOKEN`, `BOT_TOKEN`, `ALLOWED_USER_ID`, and optionally `EMAIL_*` vars. None of these are documented in an `.env.example`. A new deployment has zero guidance on what to configure.

**Fix:** Create `.env.example`:
```
BOT_TOKEN=your_telegram_bot_token
ALLOWED_USER_ID=your_telegram_user_id
CEREBRAS_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=
ZAI_API_KEY=
HF_TOKEN=
EMAIL_ADDRESS=
EMAIL_PASSWORD=
EMAIL_IMAP_SERVER=
EMAIL_SMTP_SERVER=
```

---

## 📊 Full Issue Priority Table

| # | Issue | File | Severity |
|---|-------|------|----------|
| 1 | Dual router conflict (`agents.py` vs `router.py`) | Multiple | 🔴 Critical |
| 2 | `agents/` dirs all empty + bash artifact folder | `agents/` | 🔴 Critical |
| 3 | `_AGENT_CHAIN` out of sync with `FALLBACK_CHAIN` | `llm_client.py` | 🔴 Critical |
| 4 | Typing indicator leak on scrape error path | `main.py` | 🔴 Critical |
| 5 | `msg.from_user` null dereference in `cmd_screen` | `main.py` | 🔴 Critical |
| 6 | `take_screenshot()` shadowed across modules | `llm_client.py` | 🔴 Critical |
| 7 | User-supplied alert condition → potential code exec | `main.py` | 🔴 Security |
| 8 | `_detected_display` cached forever, never refreshed | `computer_agent.py` | 🔴 Critical |
| 9 | `set_clipboard()` shell injection via `$` / backticks | `computer_agent.py` | 🔴 Security |
| 10 | `/swarm` tools import may fail silently | `main.py` | 🟠 High |
| 11 | Cerebras model name mismatch (`-a22b` suffix) | Multiple | 🟠 High |
| 12 | `detect_agent()` routes knowledge queries to computer | `router.py` | 🟠 High |
| 13 | `is_question` loses to `has_soft` in NL router | `main.py` | 🟠 Medium |
| 14 | Thread history not saved at max_iterations exit | `llm_client.py` | 🟠 Medium |
| 15 | `chunk_output()` breaks on lines > max_length | `llm_client.py` | 🟠 Medium |
| 16 | `screenshot_region()` returns path on empty file | `computer_agent.py` | 🟠 Medium |
| 17 | Blocking file read inside `async analyze_screenshot()` | `llm_client.py` | 🟠 Medium |
| 18 | `keyboard_type()` incomplete shell escape | `computer_agent.py` | 🟠 Medium |
| 19 | `open_app()` `&` backgrounding blocks event loop | `computer_agent.py` | 🟠 Medium |
| 20 | `_compact_messages` injects summary as `"user"` role | `llm_client.py` | 🟡 Medium |
| 21 | No wall-clock timeout on `agent_loop()` | `llm_client.py` | 🟡 Medium |
| 22 | Rate limit cooldown 60s too short for Groq | `llm_client.py` | 🟡 Low |
| 23 | `_rate_limited` resets on restart (in-memory only) | `llm_client.py` | 🟡 Low |
| 24 | `cmd_git` hardcodes `~/swarm-bot` path | `main.py` | 🟡 Medium |
| 25 | Git tools default to `~/swarm-bot` in tool layer | `computer_agent.py` | 🟡 Medium |
| 26 | Redundant `import time as _time` inside functions | `main.py` | 🟡 Minor |
| 27 | `PERSONALITY_WRAPPER` / `build_system_prompt` dead code | `agents.py` | 🟡 Low |
| 28 | `DEBATE_PERSONAS` / `DEBATE_ICONS` dead code | `agents.py` | 🟡 Low |
| 29 | `FALLBACK_MODELS` dict dead code | `agents.py` | 🟡 Low |
| 30 | `BROWSER_APPS` dict never used in `open_app()` | `computer_agent.py` | 🟡 Low |
| 31 | `keyboard_shortcut()` not wired to `execute_tool` | `computer_agent.py` | 🟡 Minor |
| 32 | `_parse_groq_xml_tool_call()` regex breaks on nested JSON | `llm_client.py` | 🟡 Medium |
| 33 | `_strip_think_tags()` only captures first `<think>` block | `llm_client.py` | 🟡 Low |
| 34 | `run_shell()` mixes stderr into success output | `computer_agent.py` | 🟡 Low |
| 35 | No PNG validation before base64 encoding screenshot | `llm_client.py` | 🟡 Medium |
| 36 | No inter-agent debate loop (core vision unimplemented) | Missing | 🔵 Feature |
| 37 | No deep search (Perplexity-style) | `tools/web_browser.py` | 🔵 Feature |
| 38 | No deep thinking loop (Opus/o1-style) | `main.py` | 🔵 Feature |
| 39 | No Cursor-style diff/confirm before file writes | Missing | 🔵 Feature |
| 40 | `APP_MAP` hardcoded, not user-configurable | `computer_agent.py` | 🔵 Minor Feature |
| 41 | No persistent user preferences / config system | Codebase | 🔵 Feature |
| 42 | `/start` lists commands missing from `set_my_commands()` | `main.py` | 🟢 UX |
| 43 | No progress % or ETA during long agent loops | `main.py` | 🟢 UX |
| 44 | `result_keyboard` shows unhelpful provider label | `main.py` | 🟢 UX |
| 45 | No `/stop` to cancel running agent loop mid-execution | `main.py` | 🟢 UX |
| 46 | Debug/Code keyboard buttons give no examples | `main.py` | 🟢 UX |
| 47 | `/recall` output format is ugly and unrounded | `main.py` | 🟢 UX |
| 48 | No screen coordinate validation in `/click` | `main.py` | 🟢 UX |
| 49 | `/agent` exposes internal keys (e.g. `computer`) | `main.py` | 🟢 UX |
| 50 | `open_app()` assumes GNOME — breaks on KDE/XFCE | `computer_agent.py` | 🟢 UX |
| 51 | `web_research` tool description may lie to LLM | `computer_agent.py` | 🟢 Minor |
| 52 | No `/help [topic]` command — only `/start` | `main.py` | 🟢 UX |
| 53 | Shell output HTML-special chars break `<pre>` render | `main.py` | 🟢 UX |
| 54 | No clear `/tasks` view for scheduled tasks | `main.py` | 🟢 UX |
| 55 | `_tool_label` has orphan entries for non-existent tools | `llm_client.py` | 🟡 Minor |
| 56 | `upgrade_from_git()` hardcodes `~/swarm-bot` | `computer_agent.py` | 🟡 Medium |
| 57 | No `.env.example` file in repo | Root | 🟢 DX |

---

## 🗺 Recommended Fix Order

**Sprint 1 — Stop the crashes (Issues #1–9)**
- Merge `agents.py` + `router.py` into one file (#1, #3)
- Clean `agents/` empty dirs + bash artifact (#2)
- Fix `take_screenshot` shadow (#6)
- Fix `cmd_screen` null dereference (#5)
- Fix `cmd_scrape` typing leak (#4)
- Fix `set_clipboard` injection (#9)
- Add `reset_display_cache()` (#8)

**Sprint 2 — Fix silent wrong behavior (Issues #10–19)**
- NL routing logic: question > soft keywords (#12, #13)
- Thread history on max_iterations exit (#14)
- `chunk_output` long line fix (#15)
- `analyze_screenshot` async file read (#17)
- `keyboard_type` proper subprocess escaping (#18)
- `open_app` non-blocking launch (#19)
- Screenshot empty file check (#16)

**Sprint 3 — Code cleanup (Issues #20–35)**
- Compact message role fix (#20)
- Agent loop timeout (#21)
- Remove dead code: `BROWSER_APPS`, `FALLBACK_MODELS`, `keyboard_shortcut` (#29–31)
- Fix `_strip_think_tags` multi-block (#33)
- Fix `run_shell` stderr mixing (#34)
- Fix orphan `_tool_label` entries (#55)
- Dynamic `~/swarm-bot` path (#24, #25, #56)

**Sprint 4 — Build core vision (Issues #36–41)**
- Debate orchestrator with `DEBATE_PERSONAS` (#36)
- Deep search: multi-query + iterative refine (#37)
- Deep thinking: reflect loop (#38)
- Diff-confirm before write_file (#39)
- `.env.example` + user config system (#41, #57)

**Sprint 5 — UX polish (Issues #42–54)**
- `/stop` command (#45)
- Progress `[N/20]` + elapsed time (#43)
- Model name in result keyboard (#44)
- `/help [topic]` command (#52)
- HTML-escape shell output (#53)
- Coordinate validation (#48)
