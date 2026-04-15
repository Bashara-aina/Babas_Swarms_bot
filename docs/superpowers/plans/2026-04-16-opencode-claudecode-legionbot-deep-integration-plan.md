# OpenCode ⇄ Claude Code ⇄ LegionBot Deep Integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a unified 3-system integration — OpenCode, Claude Code, and LegionBot — sharing memory, spawning each other as recursive sub-agents, and using a common 4-agent pipeline.

**Architecture:** 4-layer integration: (1) joint memory facade + wiki-backed brain layer; (2) bidirectional bridges with recursive depth tracking; (3) shared skills/agents via path-rewrite symlinks; (4) unified 4-agent pipeline as universal executor for all 3 systems.

**Tech Stack:** Python 3.11+, asyncio, aiosqlite, shared wiki vault (.wiki/), subprocess spawning, gstack host config.

---

## File Structure

```
core/
├── joint_memory.py              # NEW: unified facade (Task 1)
├── claude_code_bridge.py        # NEW: bidirectional CC↔OpenCode (Task 4)
├── legion_callback_bridge.py   # NEW: recursive CC↔LegionBot (Task 5)
├── wiki_bridge.py              # MOD: add claude_code_write_session (Task 3)
├── builtin_hooks.py             # MOD: add CC session hooks (Task 10)
├── unified_prompt_context.py   # MOD: add _claude_code_brain_layer (Task 2)
└── opencode_bridge.py          # MOD: add directive parsing (Task 6)

.claude/skills/legiona/         # NEW: shared agent defs (Task 7)
├── README.md
├── coding.md
├── reviewer.md
└── researcher.md

.opencode/command/              # NEW: callback commands (Task 9)
├── legion-callback.md
└── claude-callback.md

ext/skills/gstack/hosts/
└── opencode.ts                 # MOD: add legiona/ rewrite (Task 8)

handlers/dev.py                  # MOD: add /codex handler (Task 11)

tests/
├── test_joint_memory.py        # NEW (Task 1)
├── test_claude_code_bridge.py  # NEW (Task 4)
└── test_legion_callback_bridge.py  # NEW (Task 5)

.wiki/
├── opencode/sessions/
├── claude-code/sessions/
├── joint-brain/cross-refs/
└── joint-brain/memory-protocol.md
```

---

## Task 1: Joint Memory Facade

**Files:**
- Create: `core/joint_memory.py`
- Create: `tests/test_joint_memory.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_joint_memory.py
import pytest, asyncio
from core.joint_memory import joint_save, joint_search, joint_get_recent

@pytest.mark.asyncio
async def test_joint_save_and_search():
    id1 = await joint_save("opencode test content", "opencode", tags=["test"])
    assert id1 > 0
    results = await joint_search("opencode test", sources=None)
    assert any(r["source"] == "opencode" for r in results)

@pytest.mark.asyncio
async def test_joint_get_recent():
    await joint_save("session 1", "opencode", tags=["test"])
    await joint_save("session 2", "claude-code", tags=["test"])
    recent = await joint_get_recent(days=7, sources=None)
    assert len(recent) >= 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_joint_memory.py -v`
Expected: `ERROR` — module not found

- [ ] **Step 3: Write minimal implementation**

```python
# core/joint_memory.py
"""Joint memory facade — single write path for all 3 systems."""
from __future__ import annotations
import asyncio, json, hashlib, os, re
from pathlib import Path
from typing import Any

WIKI_ROOT = Path(__file__).parent.parent / ".wiki"
SESSION_DIRS = {
    "opencode": WIKI_ROOT / "opencode" / "sessions",
    "claude-code": WIKI_ROOT / "claude-code" / "sessions",
    "legionbot": WIKI_ROOT / "legionbot" / "sessions",
}
CROSS_REFS_DIR = WIKI_ROOT / "joint-brain" / "cross-refs"

def _ensure_dirs():
    for d in list(SESSION_DIRS.values()) + [CROSS_REFS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def _slug(content: str) -> str:
    return hashlib.md5(content[:80].encode()).hexdigest()[:12]

async def joint_save(content: str, source: str, tags: list[str] | None = None, summary: str = "") -> int:
    """Write to joint brain. source: 'opencode' | 'claude-code' | 'legionbot'."""
    _ensure_dirs()
    slug = _slug(content)
    ts = str(asyncio.get_event_loop().time())
    entry_id = int(hashlib.md5(f"{source}{slug}{ts}".encode()).hexdigest()[:8], 16)

    session_dir = SESSION_DIRS.get(source, SESSION_DIRS["opencode"])
    filename = session_dir / f"{slug}.json"
    entry = {
        "id": entry_id,
        "content": content,
        "summary": summary or content[:200],
        "tags": tags or [],
        "source": source,
        "slug": slug,
    }
    async with asyncio.Lock():
        with open(filename, "w") as f:
            json.dump(entry, f)

    # Write cross-ref
    cross_ref = {
        "id": entry_id,
        "sources": [source],
        "query_terms": list(set(re.findall(r"\w{4,}", content.lower()))),
        "original_slug": slug,
    }
    cross_ref_file = CROSS_REFS_DIR / f"{slug}.json"
    with open(cross_ref_file, "w") as f:
        json.dump(cross_ref, f)

    return entry_id

async def joint_search(query: str, sources: list[str] | None = None, limit: int = 8) -> list[dict[str, Any]]:
    """Search across all sources or filter to specific ones."""
    _ensure_dirs()
    query_terms = set(re.findall(r"\w{4,}", query.lower()))
    results: list[tuple[int, dict]] = []

    search_dirs = SESSION_DIRS
    if sources:
        search_dirs = {k: SESSION_DIRS[k] for k in sources if k in SESSION_DIRS}

    for src, directory in search_dirs.items():
        for file in directory.glob("*.json"):
            try:
                with open(file) as f:
                    entry = json.load(f)
                entry["_src_file"] = str(file)
                # Simple term overlap scoring
                content_terms = set(re.findall(r"\w{4,}", entry.get("content", "").lower()))
                score = len(query_terms & content_terms)
                if score > 0:
                    results.append((score, entry))
            except Exception:
                continue

    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for _, r in results[:limit]]

async def joint_get_recent(days: int = 7, sources: list[str] | None = None, limit: int = 20) -> list[dict[str, Any]]:
    """Get recent session summaries across all systems."""
    return await joint_search("", sources=sources, limit=limit)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_joint_memory.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/joint_memory.py tests/test_joint_memory.py
git commit -m "feat: add joint_memory facade for OpenCode/Claude Code/LegionBot"
```

---

## Task 2: Add `_claude_code_brain_layer()` to `unified_prompt_context.py`

**Files:**
- Modify: `core/unified_prompt_context.py:1-30` (read existing first)
- Test: smoke — `python -c "from core.unified_prompt_context import _claude_code_brain_layer; print('ok')"`

- [ ] **Step 1: Read existing file**

```bash
head -80 core/unified_prompt_context.py
```

- [ ] **Step 2: Add `_claude_code_brain_layer()` function**

After the existing `_opencode_brain_layer()` function, add:

```python
async def _claude_code_brain_layer(query: str, limit: int = 3) -> str:
    """Query Claude Code session logs from joint brain."""
    try:
        from core.joint_memory import joint_search
        results = await joint_search(query, sources=["claude-code"], limit=limit)
        if not results:
            return ""
        block = "[CLAUDE CODE SESSIONS]\n"
        for r in results:
            block += f"— {r.get('summary', r.get('content', '')[:200])}\n"
        return block
    except Exception:
        return ""
```

- [ ] **Step 3: Smoke test**

Run: `python -c "from core.unified_prompt_context import _claude_code_brain_layer; print('ok')"`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add core/unified_prompt_context.py
git commit -m "feat: add _claude_code_brain_layer() to unified prompt context"
```

---

## Task 3: Add `claude_code_write_session()` to `wiki_bridge.py`

**Files:**
- Modify: `core/wiki_bridge.py` (read existing first)
- Test: smoke — `python -c "from core.wiki_bridge import claude_code_write_session; print('ok')"`

- [ ] **Step 1: Read existing file**

```bash
head -60 core/wiki_bridge.py
```

- [ ] **Step 2: Add `claude_code_write_session()` function**

Add after the existing `opencode_write_session_summary()` function:

```python
async def claude_code_write_session(session_md: str, summary: str = "") -> str:
    """Write Claude Code session to joint brain."""
    try:
        from core.joint_memory import joint_save
        tags = ["claude-code", "session"]
        await joint_save(session_md, "claude-code", tags=tags, summary=summary)
        return "ok"
    except Exception as e:
        return f"error: {e}"
```

- [ ] **Step 3: Smoke test**

Run: `python -c "from core.wiki_bridge import claude_code_write_session; print('ok')"`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add core/wiki_bridge.py
git commit -m "feat: add claude_code_write_session to wiki bridge"
```

---

## Task 4: Build `core/claude_code_bridge.py`

**Files:**
- Create: `core/claude_code_bridge.py`
- Create: `tests/test_claude_code_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_claude_code_bridge.py
import pytest, asyncio
from core.claude_code_bridge import run_claude_task, CLAUDE_CODE_CLI

def test_cli_path():
    assert CLAUDE_CODE_CLI is not None

@pytest.mark.asyncio
async def test_run_claude_task_smoke():
    result = await run_claude_task("say hello in 5 chars", timeout=30)
    assert "output" in result or "error" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_claude_code_bridge.py -v`
Expected: `ERROR` — module not found

- [ ] **Step 3: Write minimal implementation**

```python
# core/claude_code_bridge.py
"""Bidirectional bridge between Claude Code and OpenCode/LegionBot."""
from __future__ import annotations
import asyncio, os, shutil, re
from pathlib import Path
from typing import Any

CLAUDE_CODE_CLI = shutil.which("claude") or str(Path.home() / ".claude/bin/claude")
OPENCODE_CLI = "/home/newadmin/.opencode/bin/opencode"

async def run_claude_task(
    prompt: str,
    timeout: int = 180,
    model: str | None = None,
) -> dict[str, Any]:
    """Run a task via Claude Code CLI and return result."""
    full_prompt = f"{prompt}\n\nRespond concisely. End with RESULT: <your answer>."
    started = asyncio.get_event_loop().time()

    try:
        proc = await asyncio.create_subprocess_exec(
            CLAUDE_CODE_CLI, "-p", full_prompt,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {"output": "", "error": f"timeout after {timeout}s", "latency_ms": 0, "success": False}

        latency_ms = (asyncio.get_event_loop().time() - started) * 1000
        return {
            "output": stdout.decode()[:2000] if stdout else "",
            "error": stderr.decode()[:500] if stderr else "",
            "latency_ms": latency_ms,
            "success": proc.returncode == 0,
        }
    except FileNotFoundError:
        return {"output": "", "error": f"claude CLI not found at {CLAUDE_CODE_CLI}", "latency_ms": 0, "success": False}
    except Exception as exc:
        return {"output": "", "error": str(exc), "latency_ms": 0, "success": False}

# --- Directive parsing ---

DIRECTIVE_RE = re.compile(r"@claude[:\s]+(.+?)(?:\n|$)", re.IGNORECASE)

def extract_claude_directive(text: str) -> str | None:
    """Extract @claude directive from text."""
    m = DIRECTIVE_RE.search(text)
    return m.group(1).strip() if m else None

async def spawn_claude_from_opencode(
    task_result: str,
    depth: int = 0,
    max_depth: int = 3,
) -> dict[str, Any]:
    """Check OpenCode result for @claude directive, spawn Claude Code if found."""
    directive = extract_claude_directive(task_result)
    if not directive:
        return {"spawned": False, "reason": "no @claude directive found"}

    if depth >= max_depth:
        return {"spawned": False, "reason": f"max depth {max_depth} reached"}

    result = await run_claude_task(f"Execute this sub-task: {directive}", timeout=120)
    return {
        "spawned": True,
        "directive": directive,
        "result": result,
        "depth": depth,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_claude_code_bridge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/claude_code_bridge.py tests/test_claude_code_bridge.py
git commit -m "feat: add claude_code_bridge bidirectional Claude Code↔OpenCode bridge"
```

---

## Task 5: Build `core/legion_callback_bridge.py`

**Files:**
- Create: `core/legion_callback_bridge.py`
- Create: `tests/test_legion_callback_bridge.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_legion_callback_bridge.py
import pytest, asyncio
from core.legion_callback_bridge import SpawnTracker, LegionCallbackBridge, LEGION_DIRECTIVE_RE

def test_spawn_tracker_depth_limit():
    tracker = SpawnTracker(max_depth=3)
    assert tracker.can_spawn() is True
    tracker.record_spawn("task1", depth=0)
    tracker.record_spawn("task2", depth=1)
    tracker.record_spawn("task3", depth=2)
    assert tracker.can_spawn() is False

def test_directive_regex():
    m = LEGION_DIRECTIVE_RE.search("done! @legion please notify user")
    assert m is not None
    assert "notify user" in m.group(1)

@pytest.mark.asyncio
async def test_bridge_no_telegram_roundtrip():
    bridge = LegionCallbackBridge()
    result = await bridge.spawn_opencode_from_legion("test task", depth=0)
    assert "spawned" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_legion_callback_bridge.py -v`
Expected: `ERROR` — module not found

- [ ] **Step 3: Write minimal implementation**

```python
# core/legion_callback_bridge.py
"""Recursive bridge: LegionBot → OpenCode with depth tracking."""
from __future__ import annotations
import asyncio, re, time
from dataclasses import dataclass, field
from typing import Any

LEGION_DIRECTIVE_RE = re.compile(r"@legion[:\s]+(.+?)(?:\n|$)", re.IGNORECASE)

@dataclass
class SpawnTracker:
    """Tracks recursive spawn depth to prevent infinite loops."""
    max_depth: int = 3
    spawns: list[dict] = field(default_factory=list)

    def can_spawn(self, depth: int = 0) -> bool:
        return depth < self.max_depth

    def record_spawn(self, task_id: str, depth: int) -> None:
        self.spawns.append({"task_id": task_id, "depth": depth, "ts": time.time()})

    def get_active_spawns(self, max_age: int = 300) -> list[dict]:
        now = time.time()
        return [s for s in self.spawns if now - s["ts"] < max_age]

class LegionCallbackBridge:
    """Bridge for LegionBot to spawn OpenCode sub-tasks without Telegram round-trip."""

    def __init__(self, tracker: SpawnTracker | None = None):
        self.tracker = tracker or SpawnTracker()

    def parse_callback_directive(self, text: str) -> str | None:
        """Extract @legion directive from text."""
        m = LEGION_DIRECTIVE_RE.search(text)
        return m.group(1).strip() if m else None

    async def spawn_opencode_from_legion(
        self,
        task_prompt: str,
        depth: int = 0,
        timeout: int = 120,
    ) -> dict[str, Any]:
        """Spawn OpenCode from LegionBot task without Telegram round-trip."""
        if not self.tracker.can_spawn(depth):
            return {"spawned": False, "reason": f"max depth {self.tracker.max_depth} reached"}

        self.tracker.record_spawn(task_prompt[:50], depth)

        try:
            from core.opencode_bridge import run_opencode_task
            result = await run_opencode_task(
                prompt=task_prompt,
                project_dir="/home/newadmin/swarm-bot",
                agent="general",
                timeout=timeout,
            )
            return {
                "spawned": True,
                "result": result,
                "depth": depth,
            }
        except Exception as exc:
            return {"spawned": False, "reason": str(exc)}

    async def handle_legion_callback(self, text: str, depth: int = 0) -> dict[str, Any]:
        """Parse @legion directive and handle callback."""
        directive = self.parse_callback_directive(text)
        if not directive:
            return {"handled": False, "reason": "no @legion directive"}
        return await self.spawn_opencode_from_legion(directive, depth=depth)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_legion_callback_bridge.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/legion_callback_bridge.py tests/test_legion_callback_bridge.py
git commit -m "feat: add legion_callback_bridge with recursive depth tracking"
```

---

## Task 6: Update `core/opencode_bridge.py` — Directive Parsing + Callbacks

**Files:**
- Modify: `core/opencode_bridge.py` (read existing first)

- [ ] **Step 1: Read existing file**

```bash
head -100 core/opencode_bridge.py
```

- [ ] **Step 2: Add `extract_directives()` function**

Add after imports:

```python
DIRECTIVES_RE = re.compile(r"@(legion|claude)[:\s]+(.+?)(?:\n|$)", re.IGNORECASE)

def extract_directives(text: str) -> list[tuple[str, str]]:
    """Extract @legion and @claude directives from text."""
    return [(m.group(1).lower(), m.group(2).strip()) for m in DIRECTIVES_RE.finditer(text)]
```

- [ ] **Step 3: Add `handle_cross_system_callbacks()` function**

```python
async def handle_cross_system_callbacks(
    text: str,
    depth: int = 0,
    max_depth: int = 3,
) -> dict[str, Any]:
    """Parse cross-system directives and spawn appropriate agents."""
    results = []
    directives = extract_directives(text)

    for directive_type, directive_value in directives:
        if directive_type == "claude":
            from core.claude_code_bridge import spawn_claude_from_opencode
            result = await spawn_claude_from_opencode(text, depth=depth, max_depth=max_depth)
            results.append({"type": "claude", **result})
        elif directive_type == "legion":
            from core.legion_callback_bridge import LegionCallbackBridge
            bridge = LegionCallbackBridge()
            result = await bridge.handle_legion_callback(text, depth=depth)
            results.append({"type": "legion", **result})

    return {"callbacks": results}
```

- [ ] **Step 4: Integrate into `extract_report()`**

In `extract_report()` function, add before return:
```python
# Check for cross-system directives
callback_result = await handle_cross_system_callbacks(report_text)
```

- [ ] **Step 5: Commit**

```bash
git add core/opencode_bridge.py
git commit -m "feat: add @legion/@claude directive parsing and cross-system callbacks"
```

---

## Task 7: Create Shared Agent Definitions `.claude/skills/legiona/`

**Files:**
- Create: `.claude/skills/legiona/README.md`
- Create: `.claude/skills/legiona/coding.md`
- Create: `.claude/skills/legiona/reviewer.md`
- Create: `.claude/skills/legiona/researcher.md`

- [ ] **Step 1: Create directory and files**

```bash
mkdir -p .claude/skills/legiona
```

Create `.claude/skills/legiona/README.md`:
```markdown
---
name: legiona-shared-agents
description: Shared agent definitions for OpenCode, Claude Code, and LegionBot
type: skill
tags: [swarm, shared-agents, legiona]
created: 2026-04-16
---

# LegionA Shared Agents

Shared agent definitions used by all three systems. These agents are referenced
via path-rewrite symlinks from OpenCode (`.opencode/agents/legiona/`) and
LegionBot (`agents.py` lookup).

## Agents

- [coding.md](coding.md) — Shared coding agent
- [reviewer.md](reviewer.md) — Shared reviewer agent
- [researcher.md](researcher.md) — Shared researcher agent
```

Create `.claude/skills/legiona/coding.md`:
```markdown
---
name: legiona/coding
description: Shared coding agent for OpenCode, Claude Code, and LegionBot
type: agent
tags: [coding, shared, legiona]
created: 2026-04-16
---

# @coding — Shared Coding Agent

You are a senior software engineer. You write production-grade code.

## Guidelines

- Follow the project's coding style (Python: type hints, async-first, f-strings)
- Read back every file you write — verify it before reporting complete
- Use PROOF_FORMAT: show the exact file path + line count + proof of correctness
- Never modify `.env` or credential files
- Never run `rm -rf`
- All LLM calls go through `llm_client.chat()` — never call providers directly

## Anti-Hallucination Rules

1. After every file write: READ it back immediately
2. After every bash command: show actual stdout/stderr
3. Never report complete without PROOF_FORMAT output visible
```

Create `.claude/skills/legiona/reviewer.md`:
```markdown
---
name: legiona/reviewer
description: Shared reviewer agent for OpenCode, Claude Code, and LegionBot
type: agent
tags: [review, shared, legiona]
created: 2026-04-16
---

# @reviewer — Shared Reviewer Agent

You are a senior code reviewer. You audit changes for correctness, security, and style.

## Guidelines

- Verify all changed files against the original
- Run tests before approving
- Check for security vulnerabilities (injection, auth bypass, credential exposure)
- Ensure no `.env` or credential files were modified
- Use PROOF_FORMAT: list files reviewed, issues found, verdict

## Verdict

- `APPROVE` — ready to merge
- `REQUEST_CHANGES` — blockers found, specify what
- `FIX` — minor issues found, can self-correct
```

Create `.claude/skills/legiona/researcher.md`:
```markdown
---
name: legiona/researcher
description: Shared researcher agent for OpenCode, Claude Code, and LegionBot
type: agent
tags: [research, shared, legiona]
created: 2026-04-16
---

# @researcher — Shared Research Agent

You are a research analyst. You investigate topics and synthesize findings.

## Guidelines

- Cite sources with URLs and quotes
- Distinguish facts from speculation
- Write for a future AI colleague (LAW 1 of Karpathy KB)
- Every article must have: TL;DR, sources, current status
- Write 200-500 words per article
```

- [ ] **Step 2: Verify files exist**

```bash
ls -la .claude/skills/legiona/
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/legiona/
git commit -m "feat: add legiona shared agent definitions"
```

---

## Task 8: Update `ext/skills/gstack/hosts/opencode.ts` — Add LegionA Path Rewrite

**Files:**
- Modify: `ext/skills/gstack/hosts/opencode.ts`

- [ ] **Step 1: Read existing file**

```bash
cat ext/skills/gstack/hosts/opencode.ts
```

- [ ] **Step 2: Add legiona/ to pathRewrites**

Find the `pathRewrites` array and add:
```typescript
{ from: '.claude/skills/legiona', to: '.opencode/agents/legiona' },
```

- [ ] **Step 3: Commit**

```bash
git add ext/skills/gstack/hosts/opencode.ts
git commit -m "feat: add legiona path rewrite to gstack opencode host config"
```

---

## Task 9: Create Callback Commands for OpenCode

**Files:**
- Create: `.opencode/command/legion-callback.md`
- Create: `.opencode/command/claude-callback.md`

- [ ] **Step 1: Create files**

Create `.opencode/command/legion-callback.md`:
```markdown
---
name: legion-callback
description: Call back to LegionBot after task completion
type: command
tags: [callback, legion, bridge]
created: 2026-04-16
---

# Legion Callback Command

After task completion, if `@legion` directive was found:

1. Read the task result from `.wiki/opencode/sessions/`
2. Call `LegionCallbackBridge().handle_legion_callback(result_text)`
3. Pass the callback result to the Telegram response builder

This avoids a Telegram round-trip for internal callbacks.
```

Create `.opencode/command/claude-callback.md`:
```markdown
---
name: claude-callback
description: Spawn Claude Code as sub-agent from OpenCode
type: command
tags: [callback, claude, bridge]
created: 2026-04-16
---

# Claude Callback Command

After task completion, if `@claude` directive was found:

1. Parse the directive via `extract_claude_directive(result_text)`
2. Call `spawn_claude_from_opencode(result_text, depth=N)`
3. Write Claude Code result to `.wiki/claude-code/sessions/`
4. Return combined result to the parent pipeline
```

- [ ] **Step 2: Commit**

```bash
git add .opencode/command/legion-callback.md .opencode/command/claude-callback.md
git commit -m "feat: add legion-callback and claude-callback commands"
```

---

## Task 10: Update `core/builtin_hooks.py` — Add Claude Code Session Hooks

**Files:**
- Modify: `core/builtin_hooks.py`

- [ ] **Step 1: Read existing file**

```bash
head -100 core/builtin_hooks.py
```

- [ ] **Step 2: Add `claude_code_session_start_hook()` and `claude_code_session_end_hook()`**

Add after the existing OpenCode hook functions:

```python
async def claude_code_session_start_hook(session_id: str, prompt: str) -> None:
    """Called when a Claude Code session starts."""
    try:
        from core.wiki_bridge import claude_code_write_session
        await claude_code_write_session(
            session_md=f"# Claude Code Session\n\n**Started**: {session_id}\n\n## Prompt\n\n{prompt[:500]}",
            summary=f"CC session start: {prompt[:100]}",
        )
    except Exception as e:
        logger.warning("claude_code_session_start_hook failed: %s", e)

async def claude_code_session_end_hook(session_id: str, report: str) -> None:
    """Called when a Claude Code session ends."""
    try:
        from core.wiki_bridge import claude_code_write_session
        await claude_code_write_session(
            session_md=f"# Claude Code Session\n\n**ID**: {session_id}\n\n## Result\n\n{report[:2000]}",
            summary=f"CC session end: {report[:100]}",
        )
    except Exception as e:
        logger.warning("claude_code_session_end_hook failed: %s", e)
```

- [ ] **Step 3: Commit**

```bash
git add core/builtin_hooks.py
git commit -m "feat: add claude_code session hooks to builtin_hooks"
```

---

## Task 11: Add `/codex` Handler to `handlers/dev.py`

**Files:**
- Modify: `handlers/dev.py` (read existing first)
- Modify: `main.py` (register command)

- [ ] **Step 1: Read existing handlers/dev.py**

```bash
cat handlers/dev.py
```

- [ ] **Step 2: Add `/codex` handler**

Add after the existing handlers:

```python
@router.message(F.text & ~F.text.startswith("/"))
async def handle_codex(message: Message, state: FSMContext):
    """Handle /codex — delegate to Claude Code via claude_code_bridge."""
    if not _shared.require_owner(message):
        return

    task = message.text.strip()
    if not task:
        await message.reply("Usage: /codex <task description>")
        return

    await message.reply("⏳ Spawning Claude Code...")

    try:
        from core.claude_code_bridge import run_claude_task
        result = await run_claude_task(task, timeout=180)
        if result.get("success") and result.get("output"):
            await message.reply(result["output"][:4000])
        else:
            await message.reply(f"Claude Code error: {result.get('error', 'unknown')}")
    except Exception as exc:
        await message.reply(f"Error: {exc}")
```

- [ ] **Step 3: Register command in main.py**

In `on_startup()` in `main.py`, add:
```python
BotCommand("codex", "Run a task via Claude Code"),
```

- [ ] **Step 4: Commit**

```bash
git add handlers/dev.py main.py
git commit -m "feat: add /codex handler for Claude Code bridge"
```

---

## Task 12: Update CLAUDE.md — Add Integration Architecture Section

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add Section 2b after Section 2**

Add to `CLAUDE.md` after the architecture map (after line ~100):

```markdown
## 2b. Three-System Integration Architecture

OpenCode, Claude Code, and LegionBot form a unified intelligence network.

### Joint Brain (`.wiki/`)

All three systems share the same wiki vault as the joint brain:
- `.wiki/opencode/sessions/` — OpenCode 4-agent pipeline sessions
- `.wiki/claude-code/sessions/` — Claude Code sessions
- `.wiki/legionbot/sessions/` — LegionBot sessions
- `.wiki/joint-brain/cross-refs/` — Cross-references between sessions

### Cross-System Bridges

| Bridge | File | Purpose |
|--------|------|---------|
| OpenCode → Claude Code | `core/claude_code_bridge.py` | Spawns CC as sub-agent from OpenCode |
| OpenCode → LegionBot | `core/legion_callback_bridge.py` | Recursive depth-limited callbacks |
| Claude Code → OpenCode | `core/claude_code_bridge.py` | Spawns OpenCode for implementation |
| LegionBot → OpenCode | `core/opencode_bridge.py` | Routes `/run` to OpenCode pipeline |

### Shared Memory Facade

`core/joint_memory.py` is the single write path for all three systems.
Never write to session directories directly — always use `joint_save()`.

### Directive Protocol

- `@claude <task>` — Spawn Claude Code as sub-agent
- `@legion <task>` — Call back to LegionBot (no Telegram round-trip)
- Depth tracking: max 3 recursive spawns to prevent infinite loops

### Shared Agents

`.claude/skills/legiona/` contains shared agent definitions used by all
three systems. OpenCode references them via path rewrite:
`.claude/skills/legiona` → `.opencode/agents/legiona`
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add three-system integration architecture to CLAUDE.md"
```

---

## Self-Review Checklist

- [ ] All 12 tasks have failing tests before implementation
- [ ] No "TBD", "TODO", or placeholder requirements
- [ ] Type signatures consistent across all tasks
- [ ] All new modules smoke-tested before commit
- [ ] No single commit >200 lines (split if needed)

---

## Plan Complete

**Plan complete.** Two execution options:

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints

Which approach?
