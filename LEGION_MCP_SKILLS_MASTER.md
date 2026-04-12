# LEGION × MCP — SKILLS + MCP CONNECTION MASTER PROMPT
# For: OpenCode (VSCode terminal)
# Mission: Wire Legion into the best 30 skills + top MCP servers from the community
# Read CLAUDE.md, SOUL.md, and LEGION_CLAWCODE_UPGRADE.md before starting.

---

## BEFORE YOU START

This document assumes LEGION_CLAWCODE_UPGRADE.md has been implemented.
Specifically, these must already exist:
- `core/skills/registry.py` — SkillRegistry + Skill dataclass
- `core/mcp/client.py` — MCPClient wrapper
- `core/session/transcript.py` — SessionTranscript

If they don't exist yet, implement LEGION_CLAWCODE_UPGRADE.md first.

Run baseline smoke test:
```bash
python -c "from core.skills.registry import SKILL_REGISTRY; print('Skills OK')"
python -c "from core.mcp.client import MCPClient; print('MCP client OK')"
```

---

## PART 1 — THE 30 LEGION SKILLS

These are the only 30 skills Legion needs. Curated from 5,700+ ClawHub skills down to
exactly what Bashara actually uses daily. Quality over quantity.

Create each skill in the correct file under `core/skills/builtin/`.
Every skill MUST follow the Skill dataclass schema from registry.py.

### CATEGORY A: WEB + SEO (Bashara uses daily for rumahlabuh + cekwajar)

**File: `core/skills/builtin/web.py`**

```python
# Skill A1: web_audit
# Runs PageSpeed Insights API + checks meta tags, og tags, robots.txt
Skill(
    name="web_audit",
    description="Full SEO and performance audit of any website",
    examples=["cek seo", "audit website", "berapa score", "check loading",
              "pagespeed", "performa website", "seo rumahlabuh"],
    input_schema={"url": {"type": "string", "required": True}},
    permission_level="basic",
    executor=_web_audit
)

# Implementation:
async def _web_audit(url: str) -> str:
    import aiohttp
    api_key = os.getenv("GOOGLE_PAGESPEED_API_KEY", "")
    psi_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile"
    if api_key:
        psi_url += f"&key={api_key}"
    async with aiohttp.ClientSession() as session:
        async with session.get(psi_url) as resp:
            data = await resp.json()
    score = data.get("lighthouseResult", {}).get("categories", {}).get("performance", {}).get("score", 0)
    fcp = data.get("lighthouseResult", {}).get("audits", {}).get("first-contentful-paint", {}).get("displayValue", "?")
    return f"📊 SEO Audit: {url}\nPerformance score: {int(score*100)}/100\nFCP: {fcp}"
```

```python
# Skill A2: url_check
# Quick HTTP status + redirect chain + SSL validity check
Skill(
    name="url_check",
    description="Check if a URL is up, its HTTP status, and SSL cert validity",
    examples=["website down", "cek website hidup", "status server", "is it down"],
    input_schema={"url": {"type": "string", "required": True}},
    permission_level="basic",
    executor=_url_check
)
```

```python
# Skill A3: web_scrape
# Fetch and summarize content from any URL (with injection protection)
Skill(
    name="web_scrape",
    description="Fetch and summarize the content of any webpage",
    examples=["buka link ini", "summarize artikel", "bacain url ini", "fetch page"],
    input_schema={"url": {"type": "string", "required": True},
                  "question": {"type": "string", "required": False}},
    permission_level="basic",
    executor=_web_scrape
)
# Uses browser_agent.py + sanitize_web_content() for injection protection
```

---

### CATEGORY B: SEARCH + RESEARCH (thesis + daily intel)

**File: `core/skills/builtin/research.py`**

```python
# Skill B1: web_search
# Brave Search API (private, no tracking) — primary search engine for Legion
Skill(
    name="web_search",
    description="Search the web using Brave Search for current information",
    examples=["cari", "search", "googling", "cek berita", "lookup", "find"],
    input_schema={"query": {"type": "string", "required": True},
                  "count": {"type": "int", "default": 5}},
    permission_level="basic",
    executor=_brave_search
)
# Requires: BRAVE_SEARCH_API_KEY in .env
# API: https://api.search.brave.com/res/v1/web/search
```

```python
# Skill B2: arxiv_search
# Search arXiv for CS/ML papers — critical for POPW thesis work
Skill(
    name="arxiv_search",
    description="Search arXiv for academic papers in CS, ML, CV",
    examples=["cari paper", "arxiv", "research paper", "find paper about",
              "action recognition paper", "thesis reference"],
    input_schema={"query": {"type": "string", "required": True},
                  "max_results": {"type": "int", "default": 5}},
    permission_level="basic",
    executor=_arxiv_search
)
# Free API: http://export.arxiv.org/api/query
```

```python
# Skill B3: summarize_url
# Fetch a URL and summarize it using the researcher agent
Skill(
    name="summarize_url",
    description="Fetch and summarize any webpage or paper PDF",
    examples=["summarize this", "tldr", "ringkas artikel ini", "what does this say"],
    input_schema={"url": {"type": "string", "required": True}},
    permission_level="basic",
    executor=_summarize_url
)
```

```python
# Skill B4: hacker_news
# Get top HN stories filtered for relevance to Bashara's interests
Skill(
    name="hacker_news",
    description="Get top Hacker News stories relevant to AI, ML, and dev tools",
    examples=["hn", "hacker news", "berita tech", "tech news today"],
    input_schema={},
    permission_level="basic",
    executor=_hacker_news
)
# Free API: https://hacker-news.firebaseio.com/v0/topstories.json
```

---

### CATEGORY C: GITHUB + CODE (daily dev workflow)

**File: `core/skills/builtin/github.py`**

```python
# Skill C1: github_pr_status
# List open PRs across Bashara's repos (Babas_Swarms_bot, rumahlabuh, cekwajar)
Skill(
    name="github_pr_status",
    description="List open pull requests across all of Bashara's active repos",
    examples=["open prs", "github status", "cek pr", "ada pr apa"],
    input_schema={},
    permission_level="basic",
    executor=_github_pr_status
)
# Uses GITHUB_TOKEN from .env via composio_hub or direct GitHub API
```

```python
# Skill C2: github_commit_log
# Get recent commits from a repo with brief summaries
Skill(
    name="github_commit_log",
    description="Get recent commits from a GitHub repo",
    examples=["latest commits", "commit history", "apa yang udah di push"],
    input_schema={"repo": {"type": "string", "required": True},
                  "limit": {"type": "int", "default": 5}},
    permission_level="basic",
    executor=_github_commit_log
)
```

```python
# Skill C3: code_review
# Pass a diff or file to the reviewer agent for feedback
Skill(
    name="code_review",
    description="Review code diff or file for bugs, style, and improvements",
    examples=["review kode ini", "cek bug", "ada masalah ga", "code review"],
    input_schema={"code": {"type": "string", "required": True},
                  "language": {"type": "string", "default": "python"}},
    permission_level="basic",
    executor=_code_review
)
# Routes to reviewer agent in agents.py
```

---

### CATEGORY D: SYSTEM + SHELL (machine management)

**File: `core/skills/builtin/system.py`**

```python
# Skill D1: system_health
# GPU temp, VRAM used, RAM used, disk space — all in one message
Skill(
    name="system_health",
    description="Check GPU, RAM, disk, and CPU status of the Legion machine",
    examples=["cek server", "gpu status", "ram berapa", "sistem ok ga",
              "disk space", "health check"],
    input_schema={},
    permission_level="basic",
    executor=_system_health
)
# Implementation: nvidia-smi, free -h, df -h via run_sandboxed()
```

```python
# Skill D2: service_status
# Check systemd service status (legion, nginx, postgresql, etc.)
Skill(
    name="service_status",
    description="Check if a system service is running",
    examples=["legion running ga", "cek nginx", "service status", "apakah jalan"],
    input_schema={"service": {"type": "string", "required": True}},
    permission_level="basic",
    executor=_service_status
)
```

```python
# Skill D3: service_restart
# Restart a specific service (no sudo required if sudoers configured)
Skill(
    name="service_restart",
    description="Restart a systemd service",
    examples=["restart legion", "restart nginx", "reboot service"],
    input_schema={"service": {"type": "string", "required": True}},
    permission_level="elevated",   # requires SUDO_PASS or NOPASSWD sudoers
    executor=_service_restart
)
```

```python
# Skill D4: run_shell
# Execute a sandboxed shell command (wraps core/shell/sandbox.py)
Skill(
    name="run_shell",
    description="Execute a shell command safely",
    examples=["jalanin", "execute", "run command", "ketik di terminal", "bash"],
    input_schema={"command": {"type": "string", "required": True}},
    permission_level="elevated",
    executor=_run_shell
)
```

---

### CATEGORY E: MEMORY + NOTES (knowledge management)

**File: `core/skills/builtin/memory.py`**

```python
# Skill E1: remember
# Store a fact to mem0 via memory_manager facade
Skill(
    name="remember",
    description="Store an important fact to Legion's permanent memory",
    examples=["inget ini", "remember", "simpan", "catat", "store this"],
    input_schema={"fact": {"type": "string", "required": True},
                  "category": {"type": "string", "default": "general"}},
    permission_level="basic",
    executor=_remember
)
```

```python
# Skill E2: recall
# Search mem0 for relevant memories
Skill(
    name="recall",
    description="Search Legion's memory for stored facts",
    examples=["inget ga", "recall", "kamu tau ga soal", "lo pernah simpen"],
    input_schema={"query": {"type": "string", "required": True}},
    permission_level="basic",
    executor=_recall
)
```

```python
# Skill E3: obsidian_write
# Write a note to Obsidian vault via MCP (if enabled)
Skill(
    name="obsidian_write",
    description="Write or update a note in Obsidian vault",
    examples=["tulis di obsidian", "save note", "buat catetan", "wiki entry"],
    input_schema={"title": {"type": "string", "required": True},
                  "content": {"type": "string", "required": True},
                  "folder": {"type": "string", "default": "Legion"}},
    permission_level="basic",
    executor=_obsidian_write
)
# Wired through Obsidian MCP server (see Part 2)
```

---

### CATEGORY F: PRODUCTIVITY (calendar, tasks, weather)

**File: `core/skills/builtin/productivity.py`**

```python
# Skill F1: weather
# Current weather + 3-day forecast for current location
Skill(
    name="weather",
    description="Get current weather and forecast for Narita/Jakarta/current location",
    examples=["cuaca", "weather", "hujan ga", "panas banget ga", "forecast"],
    input_schema={"city": {"type": "string", "default": "Narita,JP"}},
    permission_level="basic",
    executor=_weather
)
# Uses OpenWeatherMap API: OPENWEATHER_API_KEY in .env
```

```python
# Skill F2: translate
# Translate text between Indonesian, English, Japanese
Skill(
    name="translate",
    description="Translate text between Indonesian, English, and Japanese",
    examples=["translate", "terjemahkan", "artinya apa", "in english",
              "bahasa jepang", "bahasa inggris"],
    input_schema={"text": {"type": "string", "required": True},
                  "target_lang": {"type": "string", "default": "en"}},
    permission_level="basic",
    executor=_translate
)
# Free: LibreTranslate self-hosted OR DeepL free tier
```

```python
# Skill F3: timer
# Set a countdown timer that fires a Telegram notification
Skill(
    name="timer",
    description="Set a timer that sends a Telegram message when done",
    examples=["set timer", "ingetin gw", "reminder", "alarm",
              "kasih tau gw", "after X minutes"],
    input_schema={"minutes": {"type": "int", "required": True},
                  "label": {"type": "string", "default": "Timer"}},
    permission_level="basic",
    executor=_timer
)
# Uses asyncio.sleep() in a background task
```

---

### CATEGORY G: BASHARA-SPECIFIC SKILLS (ClawHub will NEVER have these)

**File: `core/skills/builtin/personal.py`**

```python
# Skill G1: rumahlabuh_status
# Check rumahlabuh.com listings, new inquiries, server uptime, traffic
Skill(
    name="rumahlabuh_status",
    description="Check rumahlabuh.com status: uptime, listings, new inquiries",
    examples=["rumahlabuh gimana", "cek rumahlabuh", "ada inquiry baru",
              "website property gw", "listing baru"],
    input_schema={},
    permission_level="basic",
    executor=_rumahlabuh_status
)
# Calls Supabase API for new inquiries + url_check for uptime
```

```python
# Skill G2: thesis_status
# Show thesis deadline countdown, last milestone, next step
Skill(
    name="thesis_status",
    description="Check thesis deadline, current progress, and next action",
    examples=["thesis gimana", "deadline kapan", "progress tesis",
              "popw status", "master thesis", "sidang kapan"],
    input_schema={},
    permission_level="basic",
    executor=_thesis_status
)
# Reads from memory: thesis_deadline, last_milestone, current_chapter
```

```python
# Skill G3: cekwajar_status
# Check cekwajar.id health, user stats, and pending features
Skill(
    name="cekwajar_status",
    description="Check cekwajar.id health and usage stats",
    examples=["cekwajar gimana", "cek cekwajar", "salary tool status"],
    input_schema={},
    permission_level="basic",
    executor=_cekwajar_status
)
```

```python
# Skill G4: gpu_training_status
# Check if a training job is running on the RTX 3060
Skill(
    name="gpu_training_status",
    description="Check GPU training job status, loss curve, estimated completion",
    examples=["training gimana", "gpu training", "model training status",
              "popw training", "loss berapa"],
    input_schema={"log_path": {"type": "string", "default": ""}},
    permission_level="basic",
    executor=_gpu_training_status
)
# Reads from WORKERNET_LOG_PATH (already in env reference)
```

```python
# Skill G5: adb_scholarship
# Check ADB scholarship deadline and application status
Skill(
    name="adb_scholarship",
    description="Check ADB scholarship status, deadlines, and pending requirements",
    examples=["adb gimana", "scholarship status", "beasiswa deadline"],
    input_schema={},
    permission_level="basic",
    executor=_adb_scholarship
)
# Reads from memory: adb_deadline, adb_docs_status
```

---

### CATEGORY H: MEDIA + SCREEN

**File: `core/skills/builtin/media.py`** (already partially exists in computer_agent.py)

```python
# Skill H1: screenshot  — wraps existing computer_agent functionality
# Skill H2: analyze_screen  — screenshot + vision model analysis
# Skill H3: screen_text  — OCR on current screen
# All three route to existing handlers in computer_agent.py
# Just register them as Skills so intent_router finds them naturally
```

---

## PART 2 — MCP SERVER CONNECTION GUIDE

These are the best MCP servers for Legion, curated from 60+ available servers.
Each entry includes: install command, .env config, and how to register in Legion.

### MCP SERVER 1: Brave Search (PRIMARY SEARCH)
**Why:** Privacy-first search, no Google dependency, free tier available [web:703]
**Stars:** Official Anthropic reference server
```bash
# Install
npx @modelcontextprotocol/server-brave-search
```
```env
# .env
BRAVE_SEARCH_API_KEY=your_key_here  # get free at https://brave.com/search/api/
MCP_BRAVE_ENABLED=true
```
```python
# core/mcp/servers/brave.py
BRAVE_MCP = MCPClient([
    "npx", "-y", "@modelcontextprotocol/server-brave-search"
])
# Register as skill web_search in core/skills/builtin/research.py
```

---

### MCP SERVER 2: GitHub (CODE + PR MANAGEMENT)
**Why:** Native GitHub operations — PRs, commits, issues, search code [web:701]
**Stars:** Official Anthropic reference server
```bash
npx @modelcontextprotocol/server-github
```
```env
GITHUB_PERSONAL_ACCESS_TOKEN=your_token
MCP_GITHUB_ENABLED=true
# Scope: repo, read:user
```
```python
# core/mcp/servers/github.py
GITHUB_MCP = MCPClient([
    "npx", "-y", "@modelcontextprotocol/server-github"
])
# Auto-discovers: create_issue, list_prs, search_code, get_file_contents, etc.
# Wire into Skill C1 (github_pr_status) and C2 (github_commit_log)
```

---

### MCP SERVER 3: Filesystem (LOCAL FILE ACCESS)
**Why:** Let Legion read/write files in allowed directories safely [web:703]
**Stars:** Official Anthropic reference server
```bash
npx @modelcontextprotocol/server-filesystem /home/bashara/legion_workspace
```
```env
MCP_FILESYSTEM_ENABLED=true
MCP_FILESYSTEM_ALLOWED_DIRS=/home/bashara/legion_workspace,/tmp/legion
```
```python
# core/mcp/servers/filesystem.py
FILESYSTEM_MCP = MCPClient([
    "npx", "-y", "@modelcontextprotocol/server-filesystem",
    "/home/bashara/legion_workspace"  # allowed root only
])
# Exposes: read_file, write_file, list_directory, move_file
# IMPORTANT: Never add / or ~ as allowed dirs
```

---

### MCP SERVER 4: Obsidian (WIKI + NOTES)
**Why:** Legion already writes to Obsidian wiki. MCP makes it native.
```bash
pip install mcp-obsidian  # Python implementation
# OR
npx obsidian-mcp-server
```
```env
OBSIDIAN_VAULT_PATH=/home/bashara/Documents/ObsidianVault
MCP_OBSIDIAN_ENABLED=true
```
```python
# core/mcp/servers/obsidian.py
OBSIDIAN_MCP = MCPClient([
    "python", "-m", "mcp_obsidian",
    "--vault", os.getenv("OBSIDIAN_VAULT_PATH")
])
# Exposes: read_note, write_note, search_notes, list_notes
# Wire into Skill E3 (obsidian_write)
```

---

### MCP SERVER 5: Supabase (DATABASE — rumahlabuh + cekwajar backend)
**Why:** Direct SQL queries to rumahlabuh and cekwajar databases [web:708]
```bash
npx @supabase/mcp-server-supabase
```
```env
SUPABASE_URL=your_project_url
SUPABASE_SERVICE_ROLE_KEY=your_key  # service role for direct queries
MCP_SUPABASE_ENABLED=true
```
```python
# core/mcp/servers/supabase.py
SUPABASE_MCP = MCPClient([
    "npx", "-y", "@supabase/mcp-server-supabase",
    "--supabase-url", os.getenv("SUPABASE_URL"),
    "--supabase-key", os.getenv("SUPABASE_SERVICE_ROLE_KEY")
])
# Exposes: query, insert, update, list_tables
# Wire into Skill G1 (rumahlabuh_status) and G3 (cekwajar_status)
```

---

### MCP SERVER 6: Playwright / Browser (WEB AUTOMATION)
**Why:** Full browser control for scraping, SEO checks, filling forms [web:703]
```bash
npx @modelcontextprotocol/server-playwright
# OR the more powerful:
pip install mcp-server-playwright
```
```env
MCP_BROWSER_ENABLED=true
BROWSER_ALLOWED_DOMAINS=github.com,arxiv.org,wikipedia.org,rumahlabuh.com,cekwajar.id
```
```python
# core/mcp/servers/browser.py
BROWSER_MCP = MCPClient([
    "python", "-m", "mcp_server_playwright"
])
# Exposes: navigate, screenshot, click, fill, extract_text
# Replace tools/browser_agent.py Playwright calls with this
# Wire into Skill A1 (web_audit) and A3 (web_scrape)
```

---

### MCP SERVER 7: Memory (SEMANTIC RECALL)
**Why:** mem0 already exists in Legion, but an MCP wrapper makes it composable [web:708]
```bash
pip install mem0-mcp
```
```env
MEM0_API_KEY=your_key  # already in .env
MCP_MEMORY_ENABLED=true
```
```python
# core/mcp/servers/memory.py
MEMORY_MCP = MCPClient([
    "python", "-m", "mem0_mcp"
])
# Exposes: add_memory, search_memory, list_memories, delete_memory
# Wire into Skill E1 (remember) and E2 (recall)
# Note: This wraps existing mem0 — do not create duplicate memory writes
# Always go through core/memory/memory_manager.py
```

---

### MCP SERVER 8: Ahrefs SEO (ADVANCED SEO — rumahlabuh)
**Why:** Professional-grade SEO data — backlinks, keywords, domain rating [web:701]
```bash
npx ahrefs-mcp-server
```
```env
AHREFS_API_KEY=your_key  # paid, but worth it for rumahlabuh
MCP_AHREFS_ENABLED=false  # set true only if Ahrefs subscription active
```
```python
# core/mcp/servers/ahrefs.py
# Wire into Skill A1 (web_audit) as enhanced SEO data source
```

---

### MCP SERVER 9: Notion (OPTIONAL — if you use Notion)
**Why:** Read/write Notion pages and databases as agent context [web:705]
```bash
npx @modelcontextprotocol/server-notion
```
```env
NOTION_API_TOKEN=your_integration_token
MCP_NOTION_ENABLED=false  # set true only if Notion is used
```

---

### MCP SERVER 10: Google Workspace (GMAIL + CALENDAR)
**Why:** Read Gmail and Calendar for briefings + scholarship deadline tracking [web:701]
```bash
pip install mcp-google-workspace
```
```env
GOOGLE_CREDENTIALS_PATH=/home/bashara/.config/legion/google_creds.json
MCP_GOOGLE_ENABLED=false  # requires OAuth setup
```
```python
# Wire into Skill F1 productivity and core/proactive/daily_briefing.py
```

---

## PART 3 — WIRING EVERYTHING TOGETHER

### Step 1: MCP Manager

Create `core/mcp/manager.py`:
```python
import os
import logging
from core.mcp.client import MCPClient
from core.skills.registry import SKILL_REGISTRY, Skill

log = logging.getLogger(__name__)

class MCPManager:
    """
    Starts all enabled MCP servers and auto-registers their tools as Skills.
    """
    def __init__(self):
        self._clients: dict[str, MCPClient] = {}

    def _is_enabled(self, key: str) -> bool:
        return os.getenv(f"MCP_{key.upper()}_ENABLED", "false").lower() == "true"

    async def start_all(self):
        server_configs = {
            "brave": ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
            "github": ["npx", "-y", "@modelcontextprotocol/server-github"],
            "filesystem": ["npx", "-y", "@modelcontextprotocol/server-filesystem",
                           os.getenv("MCP_FILESYSTEM_ALLOWED_DIRS", "/tmp/legion")],
            "obsidian": ["python", "-m", "mcp_obsidian",
                         "--vault", os.getenv("OBSIDIAN_VAULT_PATH", "")],
            "supabase": ["npx", "-y", "@supabase/mcp-server-supabase"],
        }

        for name, command in server_configs.items():
            if not self._is_enabled(name):
                continue
            try:
                client = MCPClient(command)
                await client.start()
                self._clients[name] = client

                # Auto-discover and register tools as Skills
                tools = await client.list_tools()
                for tool in tools:
                    SKILL_REGISTRY.register(Skill(
                        name=f"{name}_{tool['name']}",
                        description=tool.get("description", ""),
                        examples=tool.get("examples", []),
                        input_schema=tool.get("inputSchema", {}),
                        permission_level="basic",
                        executor=lambda **p, c=client, t=tool["name"]: c.call(t, p)
                    ))
                log.info(f"MCP {name}: started, {len(tools)} tools registered")
            except Exception as e:
                log.error(f"MCP {name} failed to start: {e}")
                # Non-fatal — Legion works without any MCP server

    async def stop_all(self):
        for name, client in self._clients.items():
            try:
                if client._proc:
                    client._proc.terminate()
            except Exception:
                pass

MCP_MANAGER = MCPManager()
```

### Step 2: Wire into main.py on_startup()

```python
# In on_startup():
from core.mcp.manager import MCP_MANAGER
from core.skills.builtin import web, research, github, system, memory, productivity, personal, media
# ^ importing these modules triggers SKILL_REGISTRY.register() for all builtin skills

await MCP_MANAGER.start_all()
log.info(f"Legion ready: {len(SKILL_REGISTRY._skills)} skills available")
```

### Step 3: Wire Skills into intent_router.py

In `core/intent_router.py`, add AFTER existing intent classification:
```python
from core.skills.registry import SKILL_REGISTRY

# At end of classify() method, before returning result:
if result.confidence < 0.50:  # low confidence from keyword classifier
    skill = SKILL_REGISTRY.find_by_example(text)
    if skill:
        return IntentResult(
            intent=skill.name,
            confidence=0.75,
            skill=skill,
            source="skill_registry"
        )
```

### Step 4: Wire Skills into system_prompt_builder.py

In `core/system_prompt_builder.py`, after soul injection (section 0):
```python
# Section 1: Available Skills
from core.skills.registry import SKILL_REGISTRY
skills_block = SKILL_REGISTRY.describe_for_prompt()
# Inject skills_block into prompt so LLM knows what it can do
```

---

## PART 4 — .env ADDITIONS

Add all of these to `.env`:
```env
# MCP Feature Flags (set to "true" to enable each server)
MCP_BRAVE_ENABLED=true           # free tier available
MCP_GITHUB_ENABLED=true          # uses existing GITHUB_TOKEN
MCP_FILESYSTEM_ENABLED=true      # safe, allowed dirs only
MCP_OBSIDIAN_ENABLED=false        # set true when vault path configured
MCP_SUPABASE_ENABLED=false        # set true when SUPABASE_SERVICE_ROLE_KEY set
MCP_BROWSER_ENABLED=false         # set true when playwright installed
MCP_MEMORY_ENABLED=false          # set true when mem0 key configured
MCP_AHREFS_ENABLED=false          # paid, set true when subscribed
MCP_NOTION_ENABLED=false          # set true when Notion integration configured
MCP_GOOGLE_ENABLED=false          # requires OAuth setup

# MCP Configs
MCP_FILESYSTEM_ALLOWED_DIRS=/home/bashara/legion_workspace,/tmp/legion
OBSIDIAN_VAULT_PATH=/home/bashara/Documents/ObsidianVault

# New API keys for builtin skills
BRAVE_SEARCH_API_KEY=             # https://brave.com/search/api/
GOOGLE_PAGESPEED_API_KEY=         # free at Google Cloud Console
```

---

## IMPLEMENTATION ORDER FOR OPENCODE

```
PHASE 1 — Foundation (1 session)
  [1] Create core/skills/registry.py
  [2] Create core/skills/builtin/__init__.py
  [3] Implement all 7 Categories (A-H) builtin skills — skeleton executors ok
  [4] Wire skill imports into main.py on_startup()
  [5] Smoke test: skills registered count > 25

PHASE 2 — MCP (1 session)
  [6] Create core/mcp/manager.py
  [7] Enable MCP_BRAVE_ENABLED + MCP_GITHUB_ENABLED first (free, easy)
  [8] Wire MCP_MANAGER.start_all() into on_startup()
  [9] Smoke test: brave search returns results, github lists PRs

PHASE 3 — Intent wiring (30 min)
  [10] Add SKILL_REGISTRY.find_by_example() fallback in intent_router.py
  [11] Add SKILL_REGISTRY.describe_for_prompt() in system_prompt_builder.py
  [12] Live test: send "cek seo rumahlabuh" without slash command
        Expected: web_audit skill fires, returns real PageSpeed score

PHASE 4 — Personal skills (1 session)
  [13] Implement G1-G5 fully (rumahlabuh, thesis, cekwajar, gpu, adb)
  [14] These connect to Supabase and memory — require real API keys
```

---

## SMOKE TESTS

```bash
# Skills registered
python -c "
from core.skills import builtin  # triggers all registrations
from core.skills.registry import SKILL_REGISTRY
print(f'Skills registered: {len(SKILL_REGISTRY._skills)}')
for s in SKILL_REGISTRY.list_all(): print(f'  {s[\"name\"]}: {s[\"permission\"]}')
"

# Skill discovery from natural language
python -c "
from core.skills import builtin
from core.skills.registry import SKILL_REGISTRY
tests = [
    ('cek seo rumahlabuh', 'web_audit'),
    ('restart legion', 'service_restart'),
    ('cari paper action recognition', 'arxiv_search'),
    ('thesis gimana', 'thesis_status'),
    ('gpu lagi training ga', 'gpu_training_status'),
]
for text, expected in tests:
    found = SKILL_REGISTRY.find_by_example(text)
    status = '✅' if found and found.name == expected else '❌'
    print(f'{status} \"{text}\" -> {found.name if found else None} (expected {expected})')
"

# MCP servers (after enabling)
python -c "
import asyncio
from core.mcp.manager import MCP_MANAGER
async def test():
    await MCP_MANAGER.start_all()
    print(f'MCP clients started: {list(MCP_MANAGER._clients.keys())}')
asyncio.run(test())
"

# Full baseline
python -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:80])"
python -c "from core.system_prompt_builder import build_full_system_prompt; print(build_full_system_prompt('test')[:100])"
```

---

## PASTE THIS INTO OPENCODE TO START

```
Read LEGION_MCP_SKILLS_MASTER.md fully.
Also read CLAUDE.md, SOUL.md, and LEGION_CLAWCODE_UPGRADE.md for full context.

Start with Phase 1:
1. Create core/skills/registry.py with Skill dataclass and SkillRegistry
2. Create core/skills/builtin/ directory with all 7 category files
3. Implement each skill as a registered Skill with a real async executor
4. For now, executors can be stubs that return placeholder text —
   the important thing is the registry is populated and wired.
5. Run the smoke tests from the bottom of this file.
6. Then move to Phase 2 (MCP servers)

Rules:
- Follow CLAUDE.md Section 3 for all async/memory/security rules
- All shell execution through core/shell/sandbox.py run_sandboxed()
- All memory writes through core/memory/memory_manager.py
- Never break existing functionality while adding new skills
```

---

*Last updated: 2026-04-12*
*Repo: https://github.com/Bashara-aina/Babas_Swarms_bot*
*MCP registry reference: https://mcpmarket.com*
*Skill count: 30 curated from 5,700+ ClawHub skills*
