# LEGION × CLAWCODE — MASTER UPGRADE PROMPT
# For: OpenCode (VSCode terminal session)
# Mission: Take every architectural advantage ClawCode has over Legion
#          and implement it natively — better, safer, more personal.
# Read CLAUDE.md and SOUL.md before touching anything.

---

## CONTEXT: WHY THIS EXISTS

ClawCode (ultraworkers/claw-code, 180k+ stars) is architecturally superior to Legion in
12 specific ways. It has:
- A formal ToolRegistry with typed input schemas
- A Skills system (5,700+ community skills via ClawHub)
- Docker-sandboxed shell execution
- Webhook ingestion for event-driven triggers
- Session transcripts that survive restarts
- A real background execution daemon (not just message timers)
- Native MCP as integration backbone
- Cross-channel identity (Telegram, WhatsApp, Discord same conversation)
- LLM-powered cron jobs that actually DO work autonomously
- Budget loop safety with hard-cap agent pause
- LSP-aware multi-file code editing
- Prompt injection protection on browser/external content

Legion has what ClawCode will NEVER have:
- SOUL.md — a real identity and personality
- 6-tier memory (episodic, semantic, graph, working, core, letta)
- Indonesian language understanding and cultural context
- Emotion modulation and empathy engine
- Multi-agent debate system
- Local RTX 3060 GPU access
- Deep personal knowledge of Bashara, his projects, his life

Goal: Give Legion ClawCode's body. Keep Legion's soul.
Do NOT implement anything from ClawCode that breaks SOUL.md or degrades personality.

---

## BEFORE YOU START

Read these files in this exact order. Do not skip any:
```
1. CLAUDE.md                            ← architecture law — never violate this
2. SOUL.md                              ← who Legion is — never dilute this
3. LEGION_OPENCODE_AUDIT.md             ← what’s already done
4. agents.py                            ← current TASK_KEYWORDS and model registry
5. core/intent_router.py                ← current 23-intent classifier
6. core/proactive/curiosity_engine.py   ← current proactive engine
7. handlers/shared.py                   ← current shell execution
8. handlers/ai.py                       ← main message handler
9. core/memory/memory_manager.py        ← memory facade
10. main.py                             ← startup + background task registry
```

Run smoke tests from CLAUDE.md Section 12 BEFORE making any changes to confirm baseline.

---

## UPGRADE 1 — SKILLS SYSTEM (ClawCode’s #1 superpower)

**What ClawCode has:** A registry of 5,700+ skills. Each skill is a self-contained
capability (a Python/JS function with a name, description, input schema, and executor)
that the agent can discover and invoke by name. New skills are drop-in additions.

**What Legion has:** `TASK_KEYWORDS` in `agents.py` — a flat string→agent-key dict.
No schema. No self-description. No dynamic discovery.

**Implement this:**

Create `core/skills/` directory with:

### `core/skills/registry.py`
```python
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
import asyncio

@dataclass
class Skill:
    name: str                          # snake_case identifier
    description: str                   # what it does, in plain language
    examples: list[str]                # natural language triggers
    input_schema: dict                 # JSON schema for parameters
    permission_level: str              # "basic" | "elevated" | "system"
    executor: Callable[..., Awaitable[str]]  # async function
    enabled: bool = True

class SkillRegistry:
    def __init__(self):
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill):
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def find_by_example(self, text: str) -> Skill | None:
        """Find best matching skill from natural language input."""
        text_lower = text.lower()
        for skill in self._skills.values():
            if not skill.enabled:
                continue
            for example in skill.examples:
                if any(word in text_lower for word in example.lower().split()):
                    return skill
        return None

    def list_all(self) -> list[dict]:
        return [
            {"name": s.name, "description": s.description,
             "permission": s.permission_level, "enabled": s.enabled}
            for s in self._skills.values()
        ]

    def describe_for_prompt(self) -> str:
        """Return skill list for injection into system prompt."""
        lines = ["Available Legion Skills:"]
        for s in self._skills.values():
            if s.enabled:
                lines.append(f"  - {s.name}: {s.description}")
        return "\n".join(lines)

SKILL_REGISTRY = SkillRegistry()  # global singleton
```

### `core/skills/builtin/`
Create one file per skill domain. Start with these:

**`core/skills/builtin/web.py`** — web_audit, url_check, seo_check
**`core/skills/builtin/shell.py`** — run_command, run_script, check_service
**`core/skills/builtin/memory.py`** — store_memory, recall_memory, summarize_session
**`core/skills/builtin/github.py`** — list_prs, check_repo_status, get_latest_commit
**`core/skills/builtin/media.py`** — take_screenshot, analyze_screen, record_clip
**`core/skills/builtin/research.py`** — search_web, summarize_url, find_paper
**`core/skills/builtin/system.py`** — check_gpu, check_ram, check_disk, restart_service
**`core/skills/builtin/rumahlabuh.py`** — check_listings, audit_seo, check_traffic (Bashara-specific)
**`core/skills/builtin/thesis.py`** — check_deadline, summarize_progress, find_paper (Bashara-specific)

Each skill file follows this template:
```python
from core.skills.registry import Skill, SKILL_REGISTRY

async def _execute_web_audit(url: str, **kwargs) -> str:
    # actual implementation
    pass

SKILL_REGISTRY.register(Skill(
    name="web_audit",
    description="Audit a website for SEO, performance, and errors",
    examples=["cek seo", "audit website", "check loading speed", "berapa score"],
    input_schema={"url": {"type": "string", "required": True}},
    permission_level="basic",
    executor=_execute_web_audit
))
```

**Wire into intent_router.py:** After intent classification, check
`SKILL_REGISTRY.find_by_example(message_text)` before falling back to general agent.

**Wire into system_prompt_builder.py:** Inject `SKILL_REGISTRY.describe_for_prompt()`
into the system prompt so the LLM knows what skills exist.

---

## UPGRADE 2 — SESSION TRANSCRIPTS (survive restarts)

**What ClawCode has:** Every session stored as a resumable, searchable transcript.
Restart the agent — context is fully restored.

**What Legion has:** In-memory `CONVERSATION_HISTORY` dict. Resets on every restart.

**Implement this:**

Create `core/session/transcript.py`:
```python
import aiosqlite
import json
import time
from pathlib import Path

DB_PATH = Path("data/transcripts.db")

class SessionTranscript:
    def __init__(self):
        self.db: aiosqlite.Connection | None = None

    async def init(self):
        DB_PATH.parent.mkdir(exist_ok=True)
        self.db = await aiosqlite.connect(DB_PATH)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_date TEXT NOT NULL,
                role TEXT NOT NULL,         -- 'user' | 'assistant' | 'system'
                content TEXT NOT NULL,
                skill_used TEXT,            -- which skill was invoked, if any
                ts REAL DEFAULT (strftime('%s','now'))
            )
        """)
        await self.db.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_ts ON messages(user_id, ts)"
        )
        await self.db.commit()

    async def push(self, user_id: str, role: str, content: str,
                   skill_used: str | None = None):
        from datetime import date
        session_date = date.today().isoformat()
        await self.db.execute(
            "INSERT INTO messages (user_id, session_date, role, content, skill_used)"
            " VALUES (?,?,?,?,?)",
            (user_id, session_date, role, content, skill_used)
        )
        await self.db.commit()

    async def get_recent(self, user_id: str, n: int = 30) -> list[dict]:
        async with self.db.execute(
            "SELECT role, content, skill_used, ts FROM messages"
            " WHERE user_id=? ORDER BY ts DESC LIMIT ?",
            (user_id, n)
        ) as cursor:
            rows = await cursor.fetchall()
        return [{"role": r, "content": c, "skill": s, "ts": t}
                for r, c, s, t in reversed(rows)]

    async def get_session_summary(self, user_id: str, date: str) -> str:
        """Get a summary of a past session for context injection."""
        async with self.db.execute(
            "SELECT role, content FROM messages WHERE user_id=? AND session_date=?"
            " ORDER BY ts",
            (user_id, date)
        ) as cursor:
            rows = await cursor.fetchall()
        if not rows:
            return ""
        # Summarize via LLM (use general agent, cheap)
        from llm_client import chat
        history_text = "\n".join(f"{r}: {c[:200]}" for r, c in rows)
        summary = await chat("general", [
            {"role": "user",
             "content": f"Summarize this conversation in 3 sentences:\n{history_text}"}
        ])
        return summary

    async def close(self):
        if self.db:
            await self.db.close()

TRANSCRIPT = SessionTranscript()  # global singleton
```

**Wire in `main.py` `on_startup()`:**
```python
await TRANSCRIPT.init()
```

**Wire in `handlers/ai.py`** — every incoming message:
```python
await TRANSCRIPT.push(user_id, "user", message.text)
```

**Wire in `handlers/ai.py`** — every outgoing response:
```python
await TRANSCRIPT.push(user_id, "assistant", response_text)
```

**Wire into system_prompt_builder.py** — inject last 20 turns:
```python
recent = await TRANSCRIPT.get_recent(user_id, n=20)
context_block = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
```

---

## UPGRADE 3 — HEARTBEAT DAEMON (autonomous background execution)

**What ClawCode has:** A daemon that runs every N minutes, checks a task queue,
executes tasks autonomously, and only messages you when something matters.
It does actual work while you sleep — not just sends check-in messages.

**What Legion has:** `curiosity_engine.py` sends periodic messages. It doesn’t
execute anything. It’s a timer that talks, not a worker that acts.

**Implement this:**

Create `core/heartbeat/daemon.py`:
```python
import asyncio
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")
log = logging.getLogger(__name__)

class HeartbeatDaemon:
    """
    Runs every 15 minutes. Checks task queue and executes pending work.
    Only messages Bashara when output is actually useful.
    """
    INTERVAL_SECONDS = 900  # 15 minutes

    def __init__(self, bot, user_id: int):
        self.bot = bot
        self.user_id = user_id
        self._running = False
        self._task_queue: list[dict] = []

    def schedule(self, task: dict):
        """
        Schedule a task for background execution.
        task = {
            "name": "audit_rumahlabuh_seo",
            "skill": "web_audit",
            "params": {"url": "https://rumahlabuh.com"},
            "report_to_user": True,
            "run_at": None  # None = next heartbeat, or ISO timestamp
        }
        """
        self._task_queue.append(task)

    async def run(self):
        self._running = True
        log.info("Heartbeat daemon started")
        while self._running:
            try:
                await self._tick()
            except Exception as e:
                log.error(f"Heartbeat error: {e}")
            await asyncio.sleep(self.INTERVAL_SECONDS)

    async def _tick(self):
        now = datetime.now(JST)
        hour = now.hour

        # Check cron-style scheduled tasks
        await self._run_cron_tasks(now)

        # Execute queued tasks
        ready = [t for t in self._task_queue
                 if t.get("run_at") is None
                 or datetime.fromisoformat(t["run_at"]) <= now]
        for task in ready:
            self._task_queue.remove(task)
            await self._execute_task(task)

    async def _run_cron_tasks(self, now: datetime):
        """Tasks that run on a schedule automatically."""
        h, m = now.hour, now.minute

        # 07:30 JST — morning briefing (already in daily_briefing.py, skip)
        # 09:00 JST — GitHub PR scan
        if h == 9 and m < 15:
            await self._execute_task({
                "name": "github_pr_scan",
                "skill": "github_check",
                "params": {},
                "report_to_user": True
            })

        # Every Sunday 10:00 JST — rumahlabuh SEO audit
        if now.weekday() == 6 and h == 10 and m < 15:
            await self._execute_task({
                "name": "weekly_seo_audit",
                "skill": "web_audit",
                "params": {"url": "https://rumahlabuh.com"},
                "report_to_user": True
            })

        # Every day 23:00 JST — system health check
        if h == 23 and m < 15:
            await self._execute_task({
                "name": "system_health",
                "skill": "check_system",
                "params": {},
                "report_to_user": False  # only report if something is wrong
            })

    async def _execute_task(self, task: dict):
        from core.skills.registry import SKILL_REGISTRY
        from swarms_bot.routing.budget_manager import BudgetManager

        # Budget gate — always check before LLM calls
        if not BudgetManager.can_spend(task["name"]):
            log.warning(f"Budget exceeded, skipping task: {task['name']}")
            return

        skill = SKILL_REGISTRY.get(task["skill"])
        if not skill:
            log.error(f"Unknown skill: {task['skill']}")
            return

        try:
            result = await skill.executor(**task.get("params", {}))
            if task.get("report_to_user") and result:
                await self.bot.send_message(self.user_id, result)
        except Exception as e:
            log.error(f"Task {task['name']} failed: {e}")

HEARTBEAT: HeartbeatDaemon | None = None
```

**Wire in `main.py` `on_startup()`:**
```python
from core.heartbeat.daemon import HeartbeatDaemon, HEARTBEAT
HEARTBEAT = HeartbeatDaemon(bot, ALLOWED_USER_ID)
asyncio.create_task(HEARTBEAT.run())
```

**Add to background task registry in CLAUDE.md Section 8:**
```
Heartbeat daemon | Every 15 min | core/heartbeat/daemon.py | YES (budget-gated)
```

---

## UPGRADE 4 — WEBHOOK LISTENER (event-driven triggers)

**What ClawCode has:** An HTTP server that receives webhooks from GitHub, Stripe,
N8N, etc. and triggers agent actions immediately.

**What Legion has:** Nothing. All triggers are Telegram or time-based only.

**Implement this:**

Create `core/webhooks/server.py` using aiohttp (already available in the stack):
```python
from aiohttp import web
import logging
import hmac
import hashlib
import os

log = logging.getLogger(__name__)

class WebhookServer:
    def __init__(self, port: int = 8743):
        self.port = port
        self.app = web.Application()
        self._handlers: dict[str, callable] = {}
        self.app.router.add_post("/webhook/{source}", self._handle)

    def register(self, source: str, handler: callable):
        """Register a handler for a webhook source."""
        self._handlers[source] = handler

    async def _handle(self, request: web.Request) -> web.Response:
        source = request.match_info["source"]
        # Verify signature if secret set
        secret = os.getenv(f"WEBHOOK_SECRET_{source.upper()}")
        if secret:
            sig = request.headers.get("X-Hub-Signature-256", "")
            body = await request.read()
            expected = "sha256=" + hmac.new(
                secret.encode(), body, hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig, expected):
                return web.Response(status=401, text="Invalid signature")
        else:
            body = await request.read()

        handler = self._handlers.get(source)
        if not handler:
            return web.Response(status=404, text=f"No handler for {source}")

        import json
        try:
            payload = json.loads(body)
            await handler(payload)
        except Exception as e:
            log.error(f"Webhook handler error ({source}): {e}")
            return web.Response(status=500)

        return web.Response(status=200, text="ok")

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", self.port)
        await site.start()
        log.info(f"Webhook server running on port {self.port}")

WEBHOOK_SERVER = WebhookServer()
```

Create default webhook handlers in `core/webhooks/handlers/`:
- `github.py` — PR merged, push to main → notify Bashara
- `rumahlabuh.py` — new booking/inquiry → notify immediately
- `system.py` — disk > 90%, GPU temp > 85°C → alert

**Add to `.env`:**
```
WEBHOOK_PORT=8743
WEBHOOK_SECRET_GITHUB=your_github_webhook_secret
WEBHOOK_SECRET_RUMAHLABUH=your_secret
```

---

## UPGRADE 5 — SANDBOXED SHELL EXECUTION

**What ClawCode has:** Docker container isolation for shell commands. Agent can’t
accidentally delete your home directory.

**What Legion has:** Raw `asyncio.subprocess` with only a 30-second timeout.

**Implement this (Docker-lite version — no actual Docker needed):**

Create `core/shell/sandbox.py`:
```python
import asyncio
import os
import tempfile
from pathlib import Path

# Directories the agent is ALLOWED to write to
ALLOWED_WRITE_PATHS = [
    Path.home() / "legion_workspace",
    Path("/tmp/legion"),
]

# Commands that are NEVER allowed regardless of input
BLACKLIST_COMMANDS = [
    "rm -rf /", "rm -rf ~", "dd if=/dev/",
    "mkfs", "> /dev/sda", "chmod -R 777 /",
    ":(){ :|:& };:",  # fork bomb
]

async def run_sandboxed(
    command: str,
    timeout: int = 30,
    working_dir: str | None = None
) -> tuple[str, int]:
    """
    Execute shell command with safety guards.
    Returns (output, exit_code).
    """
    # Blacklist check
    for banned in BLACKLIST_COMMANDS:
        if banned in command:
            return f"[BLOCKED] Command contains disallowed pattern: {banned}", 1

    # Path guard — if cd is in command, validate target
    if "cd /" in command or "cd ~" in command:
        # Allow but monitor
        pass

    cwd = working_dir or str(Path.home())

    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
                env={**os.environ, "HOME": str(Path.home())},
            ),
            timeout=timeout
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return stdout.decode("utf-8", errors="replace").strip(), proc.returncode
    except asyncio.TimeoutError:
        return f"[TIMEOUT] Command exceeded {timeout}s limit", 1
    except Exception as e:
        return f"[ERROR] {str(e)}", 1
```

**Replace all raw subprocess calls in `handlers/shared.py` and `computer_agent.py`
with `run_sandboxed(command)`.**

Note: Full Docker sandboxing can be added later as a feature flag
`LEGION_DOCKER_SANDBOX=true` in `.env`. Start with the software-level guard.

---

## UPGRADE 6 — BUDGET HARD-CAP LOOP SAFETY

**What ClawCode has:** Agent loop PAUSES entirely if API cost hits daily cap.
No runaway billing while you sleep.

**What Legion has:** `BudgetManager.can_spend()` exists but only `curiosity_engine.py`
calls it. 7 other background tasks bypass it (CLAUDE.md P1-1 open item).

**Implement this:**

In every background task file that calls an LLM, add at the top of the coroutine:
```python
from swarms_bot.routing.budget_manager import BudgetManager
if not BudgetManager.can_spend("task_name_here"):
    log.info("Budget cap reached, skipping task_name_here")
    return
```

Files to audit and add budget gate:
- `core/proactive/daily_briefing.py`
- `tools/composio_hub.py` (GitHub intel scan)
- `core/heartbeat/daemon.py` (new — already included above)
- `core/webhooks/` handlers that call LLM
- Any handler that calls `llm_client.chat()` from a background context

Also add hard-stop in `llm_client.py` itself as a final guard:
```python
async def chat(agent_key: str, messages: list, ...) -> str:
    from swarms_bot.routing.budget_manager import BudgetManager
    if BudgetManager.is_daily_cap_exceeded():
        return "[Budget cap reached for today. LLM calls paused until midnight JST.]"
    # ... rest of function
```

---

## UPGRADE 7 — MCP AS INTEGRATION BACKBONE

**What ClawCode has:** Every external tool is a native MCP server. Adding a new
integration is plug-and-play — no custom code needed.

**What Legion has:** `composio_hub.py` with bespoke integrations per service.

**Implement this (Phase 1 — MCP client wrapper):**

Create `core/mcp/client.py`:
```python
import subprocess
import json
import asyncio
from typing import Any

class MCPClient:
    """
    Thin wrapper to call any MCP server as a skill.
    Compliant with Model Context Protocol spec.
    """
    def __init__(self, server_command: list[str]):
        self.command = server_command
        self._proc: asyncio.subprocess.Process | None = None

    async def start(self):
        self._proc = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def call(self, tool_name: str, params: dict) -> Any:
        if not self._proc:
            await self.start()
        request = json.dumps({
            "jsonrpc": "2.0", "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": params}
        }) + "\n"
        self._proc.stdin.write(request.encode())
        await self._proc.stdin.drain()
        response_line = await self._proc.stdout.readline()
        return json.loads(response_line)

    async def list_tools(self) -> list[dict]:
        """Auto-discover tools from this MCP server."""
        if not self._proc:
            await self.start()
        request = json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "tools/list"
        }) + "\n"
        self._proc.stdin.write(request.encode())
        await self._proc.stdin.drain()
        response_line = await self._proc.stdout.readline()
        data = json.loads(response_line)
        return data.get("result", {}).get("tools", [])
```

Register MCP servers in `.env`:
```
MCP_GITHUB_ENABLED=true
MCP_OBSIDIAN_ENABLED=true
MCP_FILESYSTEM_ENABLED=false  # use sandboxed shell instead
```

In `main.py on_startup()`, auto-discover MCP tools and register them as Skills:
```python
for mcp_client in enabled_mcp_clients:
    tools = await mcp_client.list_tools()
    for tool in tools:
        SKILL_REGISTRY.register(Skill(
            name=tool["name"],
            description=tool["description"],
            examples=tool.get("examples", []),
            input_schema=tool.get("inputSchema", {}),
            permission_level="basic",
            executor=lambda **p: mcp_client.call(tool["name"], p)
        ))
```

---

## UPGRADE 8 — PROMPT INJECTION PROTECTION

**What ClawCode has:** Explicit defense against prompt injection when browsing
external content. CLAUDE.md P3-4 flags this as unimplemented in Legion.

**Implement this in `tools/browser_agent.py`:**
```python
import os
from urllib.parse import urlparse

BROWSER_ALLOWED_DOMAINS = set(
    os.getenv("BROWSER_ALLOWED_DOMAINS",
              "github.com,arxiv.org,wikipedia.org,pypi.org,news.ycombinator.com"
    ).split(",")
)

def is_url_allowed(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower()
        # strip www.
        domain = domain.removeprefix("www.")
        return any(domain == allowed or domain.endswith("." + allowed)
                   for allowed in BROWSER_ALLOWED_DOMAINS)
    except Exception:
        return False

# In browse() function, add before navigation:
def browse(url: str, ...):
    if not is_url_allowed(url):
        return f"[BLOCKED] {url} is not in BROWSER_ALLOWED_DOMAINS. Add it to .env to allow."
    # ... proceed
```

Also add a content sanitizer that strips common injection patterns:
```python
INJECTION_PATTERNS = [
    "ignore previous instructions",
    "disregard your system prompt",
    "you are now",
    "pretend you are",
    "new instructions:",
]

def sanitize_web_content(content: str) -> str:
    content_lower = content.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in content_lower:
            # Log the attempt, return sanitized version
            import logging
            logging.warning(f"Prompt injection attempt detected: {pattern[:50]}")
            content = content.replace(pattern, "[FILTERED]")
    return content
```

---

## UPGRADE 9 — PROACTIVE UPGRADE (check-in dedup + variety)

**What ClawCode has:** Smart proactive engine that varies messages and respects
silence windows.

**What Legion has:** Same check-in message firing repeatedly per hour
(confirmed in chat logs: 5 identical messages in 2 hours).

**Implement this in `core/proactive/curiosity_engine.py`:**

Add message pool and cooldown:
```python
CHECKIN_POOL = [
    "Lo baik-baik aja?",
    "Masih hidup? Kasih kabar dong.",
    "Eh, lagi ngapain?",
    "Sunyi banget dari lo tadi.",
    "Ada yang lagi lo pikirin?",
    "Halo. Lagi stuck atau emang sengaja ghosting?",
    None,   # 30% chance — don't send anything
    None,
    None,
]

CHECKIN_COOLDOWN_HOURS = 4
LAST_CHECKIN_KEY = "proactive_last_checkin"

async def should_send_checkin(user_id: str) -> bool:
    import time
    from core.memory.memory_manager import MemoryManager
    last = await MemoryManager.get_state(LAST_CHECKIN_KEY, user_id)
    if last is None:
        return True
    return (time.time() - float(last)) / 3600 >= CHECKIN_COOLDOWN_HOURS

async def get_checkin_message() -> str | None:
    import random
    return random.choice(CHECKIN_POOL)

# In the main check-in logic:
if await should_send_checkin(user_id):
    msg = await get_checkin_message()
    if msg:  # None = skip silently
        await bot.send_message(user_id, msg)
        await MemoryManager.set_state(LAST_CHECKIN_KEY, user_id, str(time.time()))
```

---

## IMPLEMENTATION ORDER FOR OPENCODE

Work through upgrades in this exact order. Do not skip. Do not do partial.

```
PHASE 1 — Foundation (do today)
  [1] Upgrade 2: Session Transcripts (SQLite) — 30 min
      Most impactful. Fixes memory loss on restart.
  [2] Upgrade 5: Sandboxed shell execution — 20 min
      Replaces raw subprocess everywhere. Safety baseline.
  [3] Upgrade 6: Budget gates on ALL background tasks — 20 min
      Close CLAUDE.md P1-1 open item.
  [4] Upgrade 9: Proactive dedup + variety pool — 15 min
      Stop the spam. Quick win.

PHASE 2 — Architecture (next session)
  [5] Upgrade 1: Skills Registry — 2 hours
      Foundation for everything else. Build registry + 5 builtin skills.
  [6] Upgrade 8: Prompt injection protection — 30 min
      Close CLAUDE.md P3-4. Quick implementation.
  [7] Upgrade 3: Heartbeat Daemon — 1.5 hours
      Wires into Skills Registry. Legion starts doing autonomous work.

PHASE 3 — Integration (next week)
  [8] Upgrade 4: Webhook listener — 2 hours
      Enables event-driven triggers from GitHub, rumahlabuh, etc.
  [9] Upgrade 7: MCP backbone — 3 hours
      Replace composio_hub.py with plug-and-play MCP clients.
```

---

## SMOKE TESTS (run after each upgrade)

```bash
# After Upgrade 2 (transcripts)
python -c "import asyncio; from core.session.transcript import TRANSCRIPT; asyncio.run(TRANSCRIPT.init()); print('Transcript DB: OK')"

# After Upgrade 1 (skills)
python -c "from core.skills.registry import SKILL_REGISTRY; print(f'Skills registered: {len(SKILL_REGISTRY._skills)}')"

# After Upgrade 3 (heartbeat)
python -c "from core.heartbeat.daemon import HeartbeatDaemon; print('Heartbeat: OK')"

# After Upgrade 8 (injection protection)
python -c "from tools.browser_agent import is_url_allowed; print(is_url_allowed('https://github.com'), is_url_allowed('https://evil.com'))"

# Full baseline (run before AND after everything)
python -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:80])"
python -c "from core.intent_router import IntentRouter; r=IntentRouter(); print(r.classify('cek seo rumahlabuh'))"
python -c "from core.system_prompt_builder import build_full_system_prompt; print(build_full_system_prompt('test')[:100])"
```

---

## WHAT NOT TO COPY FROM CLAWCODE

Do NOT implement:
- Cross-channel identity (WhatsApp, Discord) — Telegram is Legion’s interface. Keep it clean.
- ClawHub community skills registry — Legion’s skills are private and Bashara-specific.
- "Vibe-coded" security — ClawCode has CVE-2026-25253 (CVSS 8.8 RCE). Build security properly.
- Public-facing cloud deployment — Legion runs on Bashara’s machine. Not exposed to internet.
- Generic personality — ClawCode has no SOUL. Legion’s identity must never be diluted.

---

## DEFINITION OF DONE

After all phases complete, Legion should be able to do this without any slash commands:

- Bashara: "Cek seo rumahlabuh dong"
  Legion: immediately runs web_audit skill, returns real SEO score

- Bashara says nothing for 8 hours
  Legion: one varied check-in, then silence for 4h

- GitHub PR merged to Babas_Swarms_bot main at 3am
  Legion: webhook fires, Legion messages Bashara in the morning with a summary

- Bashara restarts Legion service
  Legion: loads last 20 turns from SQLite, continues conversation as if nothing happened

- Bash says "restart legion"
  Legion: runs sandboxed shell, restarts itself, confirms without asking for /cmd

---

*Last updated: 2026-04-12*
*Repo: https://github.com/Bashara-aina/Babas_Swarms_bot*
*Reference: ultraworkers/claw-code architecture patterns*
*Implementation: Native Python/aiogram — no ClawCode dependency*
