# Master Implementation Prompt — 20 GitHub Repos for Claude Code / OpenCode / Legion Bot

**For:** Bashara (Babas_Swarms_bot, aiogram 3.x Telegram bot, RTX 3060 + 64GB RAM)
**Written:** April 2026
**Purpose:** Guide Claude Code, OpenCode, or any AI coding agent to implement all 20 repos in priority order
**Scope:** 20 repositories across coding agents, browser automation, sandboxing, MCP, A2A, RAG, HITL, observability

---

## CONTEXT: WHAT EXISTS NOW

### Core architecture (DO NOT BREAK)
```
swarm-bot/
├── main.py                     ← aiogram 3.x bot entry, do NOT add logic here
├── agents.py                   ← 84-agent registry, TASK_KEYWORDS, MODEL_ROUTING
├── router.py                   ← thin re-export from agents.py
├── llm_client.py               ← chat(), agent_loop(), fallback chains (ALL LLM calls go here)
├── SOUL.md                     ← Legion's living identity
├── data/beliefs.json           ← debate engine structured beliefs
├── tools/
│   ├── browser_agent.py        ← Playwright + browser-use autonomous browsing
│   ├── computer_use_agent.py   ← Vision-action loop (screenshot → gemma4:e4b → execute)
│   ├── composio_hub.py         ← Composio integrations (email, calendar, GitHub)
│   ├── briefing.py              ← Daily morning briefing
│   ├── n8n_bridge.py           ← n8n workflow automation
│   └── ruflo/server.js          ← Node.js sidecar (port 7834)
├── core/
│   ├── intent_router.py         ← 23-intent classifier
│   ├── soul_engine.py            ← SOUL.md → soul_context
│   ├── system_prompt_builder.py  ← layered prompt assembly (soul first, always)
│   ├── debate_engine.py          ← debate/opinion injection from beliefs.json
│   ├── emotion_modulator.py      ← sentiment → emotion state
│   ├── memory/
│   │   ├── memory_manager.py     ← Unified facade (USE THIS, not direct store calls)
│   │   ├── episodic_store.py     ← SQLite episodic memory
│   │   └── temporal_graph.py     ← SQLite knowledge graph
│   ├── personality/
│   │   ├── personality.py        ← LEGION_PERSONALITY dataclass
│   │   └── emotion_engine.py     ← emotion state machine
│   ├── character/
│   │   ├── disagreement_protocol.py
│   │   └── svara_surya.py        ← Indonesian business voice
│   └── proactive/
│       └── curiosity_engine.py   ← Background async loop (every 30 min)
├── handlers/                    ← One file per domain, all aiogram routers
│   ├── ai.py                    ← /run, /think, /agent + NL catch-all
│   ├── computer.py              ← /screen, /do, /cmd
│   └── communications.py        ← /emails, /calendar
├── config/
│   ├── models.yaml              ← provider registry + free tiers
│   ├── departments.yaml          ← 76 agents across 9 departments
│   └── routing_keywords.yaml    ← 200+ keywords → agent mapping
├── .opencode/agents/            ← OpenCode agent directory (existing)
├── .claude/settings.json        ← MCP server configuration
└── tests/                        ← pytest-asyncio test suite
```

### Key constraints (NEVER VIOLATE)
1. **All LLM calls** → `llm_client.chat()` — never call litellm or provider APIs directly
2. **All memory writes** → `memory_manager.py` facade — never write to stores directly
3. **No threading or time.sleep()** — fully async (asyncio)
4. **Parse mode** → `parse_mode="HTML"` with `html.escape()` for user-sourced text
5. **Subprocess timeout** → `asyncio.wait_for(proc, timeout=30)` for all shell commands
6. **Security** → Never hardcode tokens, always `os.getenv()`
7. **Model strings** → `provider/model` format: `groq/llama-3.3-70b-versatile`
8. **Ollama** → only for vision (`ollama_chat/gemma4:e4b`), never for text/coding

### Critical path for this implementation
```
WEEK 1 (P1 — Zero risk, maximum value):
  P1-1: contree-mcp         (30 min, pure config)
  P1-2: crawl4ai            (2h, async Python, drop-in tool)
  P1-3: e2b sandbox          (3h, fixes /cmd security gap)

WEEK 2 (P2 — Architecture):
  P2-1: plandex             (autonomous coding from phone)
  P2-2: nanobrowser          (3-agent browser crew)
  P2-3: burr + humanlayer    (HITL state machines)

MONTH 2 (P3 — Depth):
  P2-4: SWE-agent, A2A, promptflow eval, LangGraph orchestration
```

---

## REPOSITORY IMPLEMENTATIONS

---

### REPO #1 — plandex-ai/plandex
**Score:** 23/25 | **Priority:** P1
**What it is:** Terminal AI coding agent with persistent multi-file editing sessions, plan+diff workflows, git-aware commits
**Why it matters:** Fills the entire gap of autonomous multi-file coding from phone — Bashara's #1 use-case

#### Implementation steps

**Step 1 — Create wrapper file**
File: `tools/plandex_agent.py`

```python
"""
Plandex agent wrapper for swarm-bot.
Wraps plandex CLI as an async subprocess tool.
Plandex handles multi-file AI editing with plan/diff/apply workflow.
"""

import asyncio
import json
import subprocess
import os
import shutil
from pathlib import Path
from typing import AsyncGenerator

PLANDEX_CLI = shutil.which("plandex") or os.getenv("PLANDEX_PATH", "plandex")
PLANDEX_PROJECT_DIR = os.getenv("PLANDEX_PROJECT_DIR", "/home/newadmin/projects")

class PlandexAgent:
    """Async wrapper for plandex CLI."""

    async def plan(self, prompt: str, project_path: str) -> AsyncGenerator[str, None]:
        """
        Create a plan for the given prompt in the project.
        Args:
            prompt: The coding task description
            project_path: Absolute path to the project directory
        Yields:
            Streaming output lines from plandex
        """
        cmd = [
            PLANDEX_CLI, "plan",
            "--no-stream",
            "--project-dir", project_path,
            "--description", prompt,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=project_path,
        )
        for line in proc.stdout:
            yield line.decode().strip()

    async def apply(self, plan_id: str, project_path: str) -> str:
        """Apply the changes from an approved plan."""
        cmd = [
            PLANDEX_CLI, "apply",
            plan_id,
            "--project-dir", project_path,
            "--yes",
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return stdout.decode()

    async def diff(self, plan_id: str, project_path: str) -> str:
        """Get the diff of proposed changes for Bashara review."""
        cmd = [PLANDEX_CLI, "diff", plan_id, "--project-dir", project_path]
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()

    async def abort(self, plan_id: str, project_path: str) -> None:
        """Abort a running plan."""
        cmd = [PLANDEX_CLI, "abort", plan_id, "--project-dir", project_path]
        await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.DEVNULL)

# TODO: Bashara — decide if plans should auto-expire after N hours
# TODO: Bashara — should we use /tmp/plandex-sessions or ~/plandex-projects?
```

**Step 2 — Add handler**
File: `handlers/plandex_commands.py`

```python
"""
Plandex command handlers for /code, /plan, /apply, /diff, /abort.
Bashara routes coding tasks to plandex for autonomous multi-file editing.
"""

import asyncio
import html
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from tools.plandex_agent import PlandexAgent, PLANDEX_PROJECT_DIR
from handlers.shared import require_owner, split_and_send

router = Router()
_plandex = PlandexAgent()

@router.message(Command("code"))
async def cmd_code(message: Message, state: FSMContext):
    """
    /code <task description>
    Send a coding task to plandex. Shows plan first, then waits for /approve.
    Example: /code Refactor the intent_router to use keyword tuples instead of dict
    """
    await require_owner(message)
    task = message.text.replace("/code", "").strip()
    if not task:
        await message.answer("Usage: /code <task description>")
        return

    await message.answer(f"Planning: {html.escape(task[:80])}...")

    collected = []
    async for line in _plandex.plan(task, PLANDEX_PROJECT_DIR):
        collected.append(line)
        if len(collected) % 10 == 0:
            await message.answer(" " + "\\n".join(collected[-5:]))

    plan_id = "unknown"
    for l in collected:
        if "plan-" in l:
            parts = l.split("plan-", 1)
            if len(parts) > 1:
                plan_id = parts[1].split()[0]
                break

    await state.update_data(plan_id=plan_id, task=task)
    await state.set_state("plandex_plan_ready")

    diff = await _plandex.diff(plan_id, PLANDEX_PROJECT_DIR)
    await split_and_send(
        message,
        f"Plan ready (ID: `{plan_id}`)\\n\\n`{diff[:4000]}`"
    )
    await message.answer("Reply `/apply` to confirm, `/abort` to cancel.")

@router.message(Command("apply"))
async def cmd_apply(message: Message, state: FSMContext):
    """Apply the pending plandex plan after Bashara reviews the diff."""
    await require_owner(message)
    data = await state.get_data()
    plan_id = data.get("plan_id")
    if not plan_id:
        await message.answer("No pending plan. Use /code first.")
        return

    await message.answer("Applying plan...")
    result = await _plandex.apply(plan_id, PLANDEX_PROJECT_DIR)
    await state.clear()
    await message.answer(f"Applied:\\n{result[:4000]}")

@router.message(Command("abort"))
async def cmd_abort(message: Message, state: FSMContext):
    """Abort the pending plandex plan."""
    await require_owner(message)
    data = await state.get_data()
    plan_id = data.get("plan_id")
    if plan_id:
        await _plandex.abort(plan_id, PLANDEX_PROJECT_DIR)
    await state.clear()
    await message.answer("Plan aborted.")
```

**Step 3 — Wire in main.py**
Add to `main.py` router registration:
```python
from handlers.plandex_commands import router as plandex_router
router.include_router(plandex_router)
```
Also add `BotCommand("code", "Plan a coding task with Plandex")` to `set_my_commands`.

**Step 4 — .env additions**
```env
PLANDEX_PATH=/usr/local/bin/plandex
PLANDEX_PROJECT_DIR=/home/newadmin/projects
```

**Step 5 — Install plandex**
```bash
curl -sSL https://plandex.ai/install.sh | sh
plandex auth
```

---

### REPO #2 — nebius/contree-mcp
**Score:** 22/25 | **Priority:** P1
**What it is:** MCP server that provides condensed codebase tree context to any MCP-aware agent
**Why it matters:** Claude Code sessions on swarm-bot stop asking "where is X" — they know the structure. 30-min setup, zero code.

#### Implementation steps

**Step 1 — Update .claude/settings.json**

```json
{
  "mcpServers": {
    "contree": {
      "command": "npx",
      "args": ["-y", "@nebius/contree-mcp", "--path", "/home/newadmin/swarm-bot"],
      "env": {}
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/newadmin"]
    }
  }
}
```

**Step 2 — Verify**
```bash
npx -y @nebius/contree-mcp --path /home/newadmin/swarm-bot --dry-run
```

This is pure configuration — no Python code changes needed.

---

### REPO #3 — e2b-dev/e2b
**Score:** 20/25 | **Priority:** P1
**What it is:** Cloud sandboxes for safe code execution — replaces the unsafe `/cmd` that runs directly on the host
**Why it matters:** Critical security gap. Currently `/cmd` executes arbitrary shell on the host with no isolation.

#### Implementation steps

**Step 1 — Create sandbox wrapper**
File: `tools/sandbox_executor.py`

```python
"""
E2B sandboxed code execution.
Replaces bare subprocess /cmd with isolated cloud sandboxes.
SECURITY: Never execute untrusted code on the host.
"""

import os
import asyncio
from typing import Literal

class SandboxExecutor:
    """Async E2B sandbox executor for untrusted code."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("E2B_API_KEY")
        self._sandbox = None

    async def ensure_sandbox(self):
        if self._sandbox is None:
            from e2b import Sandbox
            self._sandbox = await Sandbox.create(api_key=self.api_key)
        return self._sandbox

    async def execute(
        self,
        code: str,
        language: Literal["python", "javascript", "bash"] = "python",
        timeout: int = 30,
    ) -> str:
        sandbox = await self.ensure_sandbox()
        ext = {"python": "py", "javascript": "js", "bash": "sh"}[language]
        filename = f"tmp_code.{ext}"

        await sandbox.filesystem.write(f"/tmp/{filename}", code)

        cmd_map = {
            "python": f"python3 /tmp/{filename}",
            "javascript": f"node /tmp/{filename}",
            "bash": f"bash /tmp/{filename}",
        }
        proc = await sandbox.process.start(cmd_map[language])

        try:
            result = await asyncio.wait_for(proc.finish(), timeout=timeout)
        except asyncio.TimeoutError:
            await proc.kill()
            return f"Timed out after {timeout}s"

        stdout = await proc.stdout.read()
        stderr = await proc.stderr.read()
        combined = stdout + stderr if isinstance(stdout, bytes) else stdout + (stderr or b"")

        await self._sandbox.close()
        self._sandbox = None

        return combined.decode() if isinstance(combined, bytes) else combined

    async def close(self) -> None:
        if self._sandbox:
            await self._sandbox.close()
            self._sandbox = None

_sandbox_exec: SandboxExecutor | None = None

def get_sandbox_executor() -> SandboxExecutor:
    global _sandbox_exec
    if _sandbox_exec is None:
        _sandbox_exec = SandboxExecutor()
    return _sandbox_exec
```

**Step 2 — Update shell tool**
In `computer_agent/shell.py`, add `safe` parameter to `_run_command()`:

```python
async def _run_command(self, command: str, safe: bool = False) -> str:
    if safe:
        executor = get_sandbox_executor()
        return await executor.execute(command, language="bash")

    # Original unsafe execution path
    proc = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
    except asyncio.TimeoutError:
        await proc.kill()
        raise TimeoutError(f"Command timed out after 30s: {command[:50]}")
    return stdout.decode() + stderr.decode()
```

**Step 3 — Add commands**
New `/cmd` with `safe=False` (default), new `/cmd_safe` using `safe=True`.

**Step 4 — .env**
```env
E2B_API_KEY=
LEGION_SANDBOX_ENABLED=true
```

---

### REPO #4 — nanobrowser/nanobrowser
**Score:** 22/25 | **Priority:** P2
**What it is:** Multi-agent browser automation (3 roles: Planner → Navigator → Validator)
**Why it matters:** Replaces `tools/browser_agent.py` (single-agent, serial, unreliable for multi-step tasks)

#### Implementation steps

**Step 1 — Create nanobrowser wrapper**
File: `tools/nanobrowser_agent.py`

```python
"""
Nanobrowser multi-agent wrapper.
Replaces browser_agent.py's single Playwright agent with a 3-agent crew:
  - Planner: decides next action step from goal
  - Navigator: executes CDP actions (click, type, scroll, etc.)
  - Validator: confirms the action produced the expected result
"""

import asyncio
import json
from typing import TypedDict, TypedDict

class BrowserState(TypedDict):
    url: str
    title: str
    viewport: str
    elements: list[dict]

@dataclass
class Action:
    action_type: str
    selector: str | None = None
    value: str | None = None
    target_url: str | None = None
    expected_result: str | None = None

from dataclasses import dataclass

class NanobrowserAgent:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser = None
        self._page = None

    async def _ensure_browser(self):
        if self._browser is None:
            pw = await async_playwright().start()
            self._browser = await pw.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
            )
        if self._page is None:
            self._page = await self._browser.new_page()
        return self._browser, self._page

    async def _planner(self, goal: str, state: BrowserState) -> Action:
        from llm_client import chat
        prompt = f"""Goal: {goal}
Current URL: {state['url']}
Title: {state['title']}
Clickable elements: {json.dumps(state['elements'][:10])}

What is the next action? Respond with JSON: {{"action_type": "click|nav|type|scroll|screenshot", "selector": "...", "value": "...", "target_url": "..."}}
"""
        response = await chat(model="openai/gpt-4o-mini", prompt=prompt)
        return Action(**json.loads(response))

    async def _navigator(self, page, action: Action) -> None:
        if action.action_type == "click" and action.selector:
            await page.click(action.selector, timeout=5000)
        elif action.action_type == "type" and action.selector and action.value:
            await page.fill(action.selector, action.value)
        elif action.action_type == "navigate" and action.target_url:
            await page.goto(action.target_url, wait_until="domcontentloaded", timeout=15000)
        elif action.action_type == "scroll":
            await page.evaluate(f"window.scrollBy(0, {action.value or 300})")
        await asyncio.sleep(0.5)

    async def _validator(self, action: Action, page) -> bool:
        if action.action_type == "navigate" and action.target_url:
            return action.target_url in page.url
        return True

    async def run(self, goal: str, max_steps: int = 10) -> str:
        _, page = await self._ensure_browser()

        for step in range(max_steps):
            state = BrowserState(
                url=page.url,
                title=await page.title(),
                viewport=f"{page.viewport_size['width']}x{page.viewport_size['height']}",
                elements=[
                    {"tag": await el.evaluate("el => el.tagName"),
                     "text": await el.evaluate("el => el.textContent?.trim()[:50]"),
                     "selector": f"#{await el.evaluate('el => el.id')}" if await el.evaluate("el => el.id") else None}
                    async for el in page.query_selector_all("a, button, input")
                ],
            )

            action = await self._planner(goal, state)
            await self._navigator(page, action)

            if not await self._validator(action, page):
                break

        screenshot = await page.screenshot()
        return f"Completed {step+1} steps. Final URL: {page.url}"

    async def close(self) -> None:
        if self._page:
            await self._page.close()
        if self._browser:
            await self._browser.close()
```

**Step 2 — Requirements**
```bash
pip install playwright
playwright install chromium --with-deps
```

---

### REPO #5 — princeton-nlp/SWE-agent
**Score:** 21/25 | **Priority:** P2
**What it is:** Autonomous agent: GitHub issue URL → clone repo → write fix → open PR
**Why it matters:** Legion learns to fix bugs autonomously from GitHub issue descriptions

#### Implementation steps

**Step 1 — Create bridge**
File: `tools/swe_agent_bridge.py`

```python
"""
SWE-agent bridge for swarm-bot.
Takes a GitHub issue URL, runs SWE-agent, streams output to Telegram.
Usage: /fix https://github.com/owner/repo/issues/123
"""

import asyncio
import os
import re
from urllib.parse import urlparse

SWE_AGENT_PATH = os.getenv("SWE_AGENT_PATH", "/home/newadmin/swe-agent")
AGENTS_TELEMETRY_ENDPOINT = os.getenv("AGENTS_TELEMETRY_ENDPOINT", "")

def parse_github_issue(url: str) -> tuple[str, str, int]:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 4 and parts[2] == "issues":
        return parts[0], parts[1], int(parts[3])
    raise ValueError(f"Invalid GitHub issue URL: {url}")

class SWEBridge:
    async def fix_issue(self, issue_url: str, stream_to=None) -> str:
        owner, repo, issue_num = parse_github_issue(issue_url)

        cmd = [
            "python", "-m", "swe_agent",
            "--repo", f"{owner}/{repo}",
            "--issue", str(issue_num),
            "--model", "gpt-4o",
            "--open-pr",
        ]

        env = dict(os.environ)
        if AGENTS_TELEMETRY_ENDPOINT:
            env["AGENTS_TELEMETRY_ENDPOINT"] = AGENTS_TELEMETRY_ENDPOINT

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=SWE_AGENT_PATH,
            env=env,
        )

        output_lines = []
        async for line in proc.stdout:
            decoded = line.decode().strip()
            output_lines.append(decoded)
            if len(output_lines) % 5 == 0:
                yield f" {decoded[-100:]}"

        await proc.wait()
        if proc.returncode == 0:
            pr_match = re.search(r"PR opened: (https://github.com/.*)", "\\n".join(output_lines))
            return pr_match.group(1) if pr_match else "PR opened successfully"
        return f"SWE-agent failed with code {proc.returncode}"

# TODO: Bashara — decide workflow:
# Option A: Auto-open PR after fix
# Option B: Show diff first → /approve → open PR (recommended — use with burr from REPO #9)
```

**Step 2 — Add handler**
File: `handlers/swe_commands.py`

```python
"""
SWE-agent handlers: /fix, /review-pr
"""

import asyncio
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from tools.swe_agent_bridge import SWEBridge
from handlers.shared import require_owner

router = Router()
_swe = SWEBridge()

@router.message(Command("fix"))
async def cmd_fix(message: Message):
    await require_owner(message)
    url = message.text.replace("/fix", "").strip()
    if not url.startswith("https://github.com/"):
        await message.answer("Usage: /fix <github_issue_url>")
        return

    await message.answer(f"Running SWE-agent on issue...\\n(url: {url[:60]}...)")

    async def stream():
        async for line in _swe.fix_issue(url, None):
            await message.answer(line)

    try:
        result = await asyncio.wait_for(stream(), timeout=600)
    except asyncio.TimeoutError:
        result = "Timed out after 10 minutes. Check logs."
    await message.answer(f"Done: {result}")
```

**Step 3 — Install SWE-agent**
```bash
git clone https://github.com/princeton-nlp/SWE-agent.git /home/newadmin/swe-agent
cd /home/newadmin/swe-agent && pip install -e .
```

---

### REPO #6 — google-a2a / A2A protocol
**Score:** 21/25 | **Priority:** P2
**What it is:** Google's Agent-to-Agent (A2A) protocol — external agents can discover and call Legion's 84 specialists
**Why it matters:** Future-proofs Legion to collaborate with Claude Code, OpenCode, other A2A agents

#### Implementation steps

**Step 1 — Create A2A server**
File: `swarms_bot/a2a_server.py`

```python
"""
A2A protocol server for Legion Bot.
Exposes Legion's 84 agents as A2A-discoverable endpoints.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import uuid
import os

class A2AMessage(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict[str, Any]
    id: str | None = None

class A2AResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    id: str | None = None

AGENT_CARD = {
    "name": "Legion",
    "description": "Bashara's permanent AI coworker — 84 specialized agents across 9 departments",
    "version": "1.0.0",
    "capabilities": {"streaming": True, "pushNotifications": False},
    "skills": [
        {"id": "coding", "name": "Coding Agent", "description": "Python, TypeScript, SQL generation"},
        {"id": "research", "name": "Research Agent", "description": "Academic research, citations"},
        {"id": "browser", "name": "Browser Agent", "description": "Autonomous web browsing"},
        {"id": "debate", "name": "Debate Agent", "description": "Dialectical reasoning"},
    ],
    "authentication": {"type": "api_key", "api_key_field": "X-Legion-Key"},
    "endpoint": f"https://{os.getenv('DOMAIN', 'localhost')}:7835/a2a",
}

app = FastAPI(title="Legion A2A Server")

@app.get("/.well-known/agent.json")
async def agent_card():
    return AGENT_CARD

@app.post("/a2a")
async def a2a_endpoint(message: A2AMessage):
    try:
        skill_id = message.params.get("skill")
        input_data = message.params.get("input", {})

        from core.nexus_orchestrator import NexusOrchestrator
        orchestrator = NexusOrchestrator()

        result = await orchestrator.route(
            agent_key=skill_id,
            task=input_data.get("task", ""),
            context=input_data,
        )

        return A2AResponse(
            result={
                "status": "success",
                "agent": skill_id,
                "output": result,
                "session_id": str(uuid.uuid4()),
            },
            id=message.id,
        )
    except Exception as e:
        return A2AResponse(error={"code": -32603, "message": str(e)}, id=message.id)

@app.get("/health")
async def health():
    return {"status": "ok", "agents": len(AGENT_CARD["skills"])}
```

**Step 2 — .env additions**
```env
LEGION_A2A_ENABLED=true
LEGION_A2A_API_KEY=
DOMAIN=
```

---

### REPO #7 — unclecode/crawl4ai
**Score:** 17/25 | **Priority:** P1
**What it is:** Async web crawler that returns clean markdown — free, local, no API key
**Why it matters:** Replaces basic Playwright fetching with structured, async, zero-cost web scraping

#### Implementation steps

**Step 1 — Create tool**
File: `tools/crawl4ai_tool.py`

```python
"""
Crawl4AI tool — async web crawling, returns clean markdown.
Free, local, no API key required.
"""

import asyncio
from typing import Literal

class Crawl4AITool:
    def __init__(self):
        self._crawler = None

    async def _get_crawler(self):
        if self._crawler is None:
            from crawl4ai import AsyncWebCrawler
            self._crawler = AsyncWebCrawler()
            await self._crawler.start()
        return self._crawler

    async def crawl(
        self,
        url: str,
        mode: Literal["fast", "balanced", "deep"] = "balanced",
        max_length: int = 10000,
    ) -> dict:
        crawler = await self._get_crawler()
        result = await crawler.crawl(url, mode=mode)
        markdown = result.markdown[:max_length]
        return {
            "url": url,
            "title": result.metadata.get("title", ""),
            "markdown": markdown,
            "links": result.metadata.get("links", [])[:20],
            "images": result.metadata.get("images", [])[:10],
        }

    async def crawl_multiple(self, urls: list[str], concurrency: int = 3) -> list[dict]:
        semaphore = asyncio.Semaphore(concurrency)

        async def crawl_one(url: str) -> dict:
            async with semaphore:
                return await self.crawl(url)

        return await asyncio.gather(*[crawl_one(u) for u in urls])

    async def close(self) -> None:
        if self._crawler:
            await self._crawler.stop()
            self._crawler = None
```

**Step 2 — Add /crawl command**
In `handlers/computer.py`:

```python
from tools.crawl4ai_tool import Crawl4AITool

_crawl4ai = Crawl4AITool()

@router.message(Command("crawl"))
async def cmd_crawl(message: Message):
    """
    /crawl <url> [mode]
    Modes: fast | balanced | deep
    """
    await require_owner(message)
    parts = message.text.replace("/crawl", "").strip().split()
    url = parts[0] if parts else None

    if not url or not url.startswith("http"):
        await message.answer("Usage: /crawl <url> [mode]")
        return

    mode = parts[1] if len(parts) > 1 else "balanced"
    await message.answer(f"Crawling {url}...")

    try:
        result = await _crawl4ai.crawl(url, mode=mode)
        text = f"**{result['title']}**\\n\\n{result['markdown']}"
        await split_and_send(message, text)
    except Exception as e:
        await message.answer(f"Crawl failed: {e}")
```

**Step 3 — Requirements**
```bash
pip install crawl4ai
python -m crawl4ai --install
```

---

### REPO #8 — microsoft/promptflow (LLM Eval)
**Score:** 21/25 | **Priority:** P2
**What it is:** LLM pipeline evaluation + observability — systematic offline eval of intent router, fallback chains, RAG accuracy
**Why it matters:** Zero evaluation tooling exists in Legion currently

#### Implementation steps

**Step 1 — Create evaluation flows**
```
tests/eval/
├── flows/
│   ├── intent_router_eval/
│   │   ├── flow.yaml
│   │   └── test_cases.jsonl
│   ├── fallback_chain_eval/
│   │   └── test_cases.jsonl
│   └── rag_eval/
│       └── test_cases.jsonl
└── run_eval.py
```

**Step 2 — flow.yaml example (intent_router_eval)**
```yaml
name: intent_router_eval
inputs:
  test_cases_path: str
  model: str = "groq/llama-3.3-70b-versatile"
outputs:
  precision: float
  recall: float
  f1: float

nodes:
  - name: load_cases
    type: python
    source: load_cases.py
  - name: classify
    type: llm
    provider: litellm
    model: ${inputs.model}
    prompt: |
      Classify this message into ONE intent:
      coding, research, browser, debate, computer, memory, communications,
      scheduling, creative, data_analysis, general

      Message: {{text}}
      Intent:
  - name: score
    type: python
    source: score.py
```

**Step 3 — run_eval.py**
```python
"""
Promptflow evaluation runner.
Run: python tests/eval/run_eval.py --flow intent_router
"""

import subprocess
import json
import argparse

async def run_flow(flow_name: str, test_cases: str) -> dict:
    cmd = [
        "pf", "run", "create",
        "--flow", f"tests/eval/flows/{flow_name}",
        "--data", test_cases,
        "--column-mapping", "text=${data.text}",
        "--stream",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--flow", choices=["intent_router", "fallback_chain", "rag"])
    args = parser.parse_args()

    results = await run_flow(
        flow_name=f"{args.flow}_eval",
        test_cases=f"tests/eval/flows/{args.flow}_eval/test_cases.jsonl",
    )

    print(f"\\n{'='*60}")
    print(f"Evaluation: {args.flow}")
    print(f"F1: {results['f1']:.3f}")

    if results['f1'] < 0.75:
        print(f" F1 below threshold (0.75) — intent router needs tuning")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

### REPO #9 — dagworks-inc/burr (HITL State Machines)
**Score:** 20/25 | **Priority:** P2
**What it is:** State machine framework for multi-step agent tasks with HITL approval flows
**Why it matters:** Bashara reviews drafts before Legion sends emails, clicks destructive buttons, opens PRs

#### Implementation steps

**Step 1 — Create HITL state machine**
File: `core/hitl_state_machine.py`

```python
"""
HITL state machine using Burr.
Multi-step agent tasks with human approval gates.
Example: /email → Draft → Show Bashara → Wait for /approve → Send or revise
"""

from burr.core import Application, Action
from burr.core.state import State

class HITLWorkflow:
    """Burr-based state machine for human-in-the-loop workflows."""

    def build_email_workflow(self, task: str) -> Application:
        return (
            ApplicationBuilder()
            .with_actions(
                draft=Action(name="draft", description="Generate email draft", fn=self._generate_draft),
                show_user=Action(name="show_user", description="Send draft to Bashara", fn=self._show_draft),
                wait_approval=Action(name="wait_approval", description="Pause for /approve or /revise", fn=self._wait_for_approval),
                send=Action(name="send", description="Send approved email", fn=self._send_email),
                revise=Action(name="revise", description="Regenerate with feedback", fn=self._revise_draft),
            )
            .with_transitions(
                ("draft", "show_user"),
                ("show_user", "wait_approval"),
                ("wait_approval", "send", lambda state: state.get("approved")),
                ("wait_approval", "revise", lambda state: state.get("revise_requested")),
                ("revise", "show_user"),
            )
            .with_state(task=task, draft_content="", approved=False, revise_requested=False)
            .with_identifying_property("hitl_email_workflow")
            .build()
        )

    async def _generate_draft(self, state: State) -> State:
        from llm_client import chat
        task = state.get("task")
        draft = await chat(
            model="groq/llama-3.3-70b-versatile",
            prompt=f"Write a professional email for: {task}",
        )
        return state.update(draft_content=draft)

    async def _show_draft(self, state: State) -> State:
        return state  # Handled externally

    async def _wait_for_approval(self, state: State) -> State:
        return state  # Polled via /approve or /revise

    async def _send_email(self, state: State) -> State:
        from tools.composio_hub import ComposioHub
        hub = ComposioHub()
        await hub.send_email(body=state.get("draft_content"))
        return state.update(sent=True)

    async def _revise_draft(self, state: State) -> State:
        return state.update(revise_requested=False)

# TODO: Bashara — define which actions should trigger HITL:
# - send_email: always
# - browser "delete" button clicks: always
# - opening PRs via SWE-agent: always
# - reading files: never
```

**Step 2 — Wire into communications handler**
```python
from core.hitl_state_machine import HITLWorkflow

_hittl = HITLWorkflow()

@router.message(Command("email"))
async def cmd_email(message: Message, state: FSMContext):
    await require_owner(message)
    task = message.text.replace("/email", "").strip()
    if not task:
        await message.answer("Usage: /email <task description>")
        return

    app = _hitl.build_email_workflow(task)
    new_state = await app.run(action_name="draft")
    draft = new_state.get("draft_content")

    await message.answer(f"Draft:\\n\\n{draft[:4000]}")
    await message.answer("Reply `/approve` to send, `/revise <feedback>` to change.")
```

**Step 3 — Requirements**
```bash
pip install burr
```

---

### REPO #10 — openai/swarm (Agent Handoff)
**Score:** 18/25 | **Priority:** P3
**What it is:** Lightweight agent handoff framework — "if agent A encounters X, hand off to agent B with full context"
**Why it matters:** Fixes context-loss when re-routing between agents

#### Implementation steps

**Step 1 — Create handoff primitives**
File: `core/swarm_handoff.py`

```python
"""
Swarm-inspired agent handoff for Legion.
Preserves full context across agent boundaries.
Currently agents lose context when re-routed through nexus_orchestrator.
"""

from dataclasses import dataclass
from typing import Any
from enum import Enum

class HandoffTarget(Enum):
    CODING = "coding"
    RESEARCH = "research"
    DEBATE = "debate"
    BROWSER = "browser"
    REVIEW = "reviewer"

@dataclass
class HandoffResult:
    target: HandoffTarget
    context: dict[str, Any]
    reason: str
    urgency: str = "normal"

class SwarmHandoff:
    def __init__(self):
        self._handoff_log: list[HandoffResult] = []

    def request_handoff(
        self,
        from_agent: str,
        to_target: HandoffTarget,
        context: dict[str, Any],
        reason: str,
        urgency: str = "normal",
    ) -> HandoffResult:
        result = HandoffResult(
            target=to_target,
            context={
                "source_agent": from_agent,
                "original_task": context.get("original_task"),
                "accumulated_context": context,
                "handoff_reason": reason,
                "urgency": urgency,
            },
            reason=reason,
            urgency=urgency,
        )
        self._handoff_log.append(result)
        return result

    def get_last_handoff(self) -> HandoffResult | None:
        return self._handoff_log[-1] if self._handoff_log else None
```

**Step 2 — Integrate into nexus_orchestrator**
In `core/nexus_orchestrator.py`, check for pending handoffs before routing:

```python
from core.swarm_handoff import SwarmHandoff, HandoffTarget

_swarm = SwarmHandoff()

async def route(self, task: str, context: dict) -> str:
    pending = _swarm.get_last_handoff()
    if pending and pending.target in self._agent_registry:
        return await self._execute_agent(pending.target.value, pending.context)

    agent_key = self._detect_agent(task)
    return await self._execute_agent(agent_key, {"task": task, **context})
```

---

### REPOS #11–20: BRIEF NOTES

**#11 getzep/zep** (Knowledge Graph Memory)
Replace `core/memory/temporal_graph.py` with Zep client. No handler changes — goes through `memory_manager.py` facade.
```
pip install zep-js
```

**#13 run-llama/llama_index** (Agentic RAG)
Plug into `LegionMemoryFacade`. Replace naive vector search with LlamaIndex query decomposition + hybrid BM25+vector + citation tracking.

**#14 langchain-ai/langgraph** (Multi-Agent Graph)
Major refactor of `core/nexus_orchestrator.py`. **Do this AFTER Week 1-2 stability confirmed.** Higher risk, budget 2 full sessions.

**#15 humanlayer/humanlayer** (HITL Approval API)
Declarative `@require_approval` on `computer_use_agent.py` destructive actions.

**#16 AgentOps-AI/agentops** (Observability)
Add `@agentops.record_action` to `llm_client.chat()` and all `tools/` entry points.

```python
import agentops
agentops.init(os.getenv("AGENTOPS_API_KEY"), default_tags=["legion", "telegram"])

@agentops.record_action("llm_chat")
async def chat(model: str, prompt: str) -> str:
    # ... existing logic
```

**#17 Aider-AI/aider** (Git-native AI coding)
Alternative to plandex. Skip unless plandex doesn't fit after 2 weeks.

**#18 mendableai/firecrawl** (Web extraction)
Free version already covered by crawl4ai. Only add if crawl4ai insufficient for complex JS-heavy sites. Requires API key (paid).

**#19 opendatalab/MinerU** (PDF intelligence)
For Bashara's academic paper pipeline. `/paper <pdf>` → MinerU extracts → Legion summarizes → wiki.

**#20 roboflow/supervision** (CV annotation)
Niche. Only implement if annotated `/screen` screenshots become frequent.

---

## DEPENDENCIES TO ADD

```txt
# requirements.txt additions
plandex>=0.1.0                  # REPO #1
e2b>=0.5.0                      # REPO #3
crawl4ai>=0.3.0                 # REPO #7
burr>=1.0.0                     # REPO #9
agentops>=0.3.0                 # REPO #16
promptflow>=1.0.0               # REPO #8 (eval only)
# SWE-agent: git clone + pip install -e .
# LangGraph: langgraph>=0.2.0  # REPO #14 (when ready)
# LlamaIndex: llama-index>=0.11.0  # REPO #13 (when ready)
```

---

## ENV ADDITIONS

```bash
# P1 (Week 1)
PLANDEX_PATH=/usr/local/bin/plandex
PLANDEX_PROJECT_DIR=/home/newadmin/projects
E2B_API_KEY=
LEGION_SANDBOX_ENABLED=true

# P2 (Week 2)
SWE_AGENT_PATH=/home/newadmin/swe-agent
LEGION_A2A_ENABLED=true
LEGION_A2A_API_KEY=
DOMAIN=

# P3 (Month 2)
AGENTOPS_API_KEY=
FIRE_CRAWL_API_KEY=  # only if crawl4ai insufficient
```

---

## TESTING CHECKLIST

After each repo implementation:

```bash
# Smoke tests
python -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:100])"
python -c "from core.intent_router import IntentRouter; r = IntentRouter(); print(r.route_sync('write me code'))"
python -c "from core.system_prompt_builder import build_full_system_prompt; print(build_full_system_prompt('test')[:200])"
python -c "from core.debate_engine import build_debate_instruction; print('debate ok')"

# Repo-specific smoke
python -c "from tools.plandex_agent import PlandexAgent; print('plandex ok')"
python -c "from tools.crawl4ai_tool import Crawl4AITool; print('crawl4ai ok')"
python -c "from core.hitl_state_machine import HITLWorkflow; print('burr ok')"
python -c "from core.swarm_handoff import SwarmHandoff; print('swarm ok')"

# Pytest
pytest tests/ -x --asyncio-mode=auto -q

# Live bot tests
# Run each new command end-to-end from Telegram before marking done
```

---

## PRIORITY ORDER (final)

| # | Repo | Score | Priority | Est. Time |
|---|------|-------|----------|-----------|
| 1 | plandex | 23 | P1 | 3 hours |
| 2 | contree-mcp | 22 | P1 | 30 min |
| 3 | crawl4ai | 17 | P1 | 2 hours |
| 4 | e2b sandbox | 20 | P1 | 3 hours |
| 5 | nanobrowser | 22 | P2 | 4 hours |
| 6 | SWE-agent | 21 | P2 | 4 hours |
| 7 | A2A protocol | 21 | P2 | 3 hours |
| 8 | burr | 20 | P2 | 4 hours |
| 9 | promptflow | 21 | P2 | 4 hours |
| 10 | humanlayer | 18 | P2 | 2 hours |
| 11 | swarm handoff | 18 | P3 | 2 hours |
| 12 | agentops | 18 | P2 | 1 hour |
| 13 | zep graph | 20 | P2 | 3 hours |
| 14 | llamaindex RAG | 19 | P3 | 5 hours |
| 15 | langgraph | 19 | P3 | 8 hours |
| 16 | firecrawl | 19 | P3 | 1 hour |
| 17 | aider | 19 | P3 | 2 hours |
| 18 | MinerU | 17 | P3 | 3 hours |
| 19 | agno tools | 17 | P3 | 2 hours |
| 20 | supervision | 17 | P4 | 2 hours |

Total implementation: ~50 hours across 10-12 sessions.
