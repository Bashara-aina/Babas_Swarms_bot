# Legion v4 — Master Implementation Prompt
# Use this entire file as your prompt in Claude Code.

---

## CONTEXT: WHO YOU ARE WORKING WITH

This is **Bashara's Legion bot** — a Telegram bot running on Ubuntu Linux (RTX 3060,
`~/swarm-bot` or `~/Babas_Swarms_bot`). It controls the PC via xdotool/wmctrl, uses
free cloud LLMs (Groq, Cerebras, ZAI, Gemini, OpenRouter) through litellm, and is
built on aiogram 3.x. Python venv is at `.venv/`. The `.env` file holds all secrets.

Bashara also has a deep learning research project called **WorkerNet** — a multi-task
model on the IKEA ASM dataset (685K frames, 3 tasks: detection + pose + activity).

**DO NOT suggest cloud deployments. DO NOT add logging of message content.
DO NOT use threading. Everything is async (asyncio). All APIs are free tier.**

---

## CRITICAL BUG FIXES — DO THESE FIRST BEFORE ANY NEW FEATURES

### Bug 1: `'NoneType' object has no attribute 'keys'`

**Root cause:** In `llm_client.py`, the `agent_loop()` function calls tool executors
that can return `None`. When the result is fed back into the messages list as a tool
response, it crashes because litellm expects `str`, not `None`.

**Fix in `llm_client.py`:** Every tool executor result must be coerced to string.
Wrap every `tool_result` assignment like this:

```python
# Anywhere a tool returns a result and it gets added to messages:
tool_result = str(result) if result is not None else "tool returned no output"
```

Also find the specific location where `outputs.get(...)` or similar dict access happens
on a potentially-None response and add a None guard:

```python
response = completion(...)
if response is None or not hasattr(response, 'choices') or not response.choices:
    break
msg = response.choices[0].message
if msg is None:
    break
```

### Bug 2: Groq outputting XML function syntax instead of JSON

**Symptom in logs:** `"failed_generation": "<function=open_app{\"app_name\": \"mozilla\"}>"`

**Root cause:** The system prompt contains XML-like tags or angle bracket syntax that
confuses Groq's function calling parser into outputting old XML-style tool calls instead
of the OpenAI JSON format. Groq is strict: any `<tag>` patterns in the system prompt
can bleed into function call generation.

**Fix in `llm_client.py`:**
1. Audit all system prompts in `SYSTEM_PROMPTS` dict — remove ALL angle bracket `<>` syntax
2. Replace any `<example>`, `<task>`, `<result>` tags with plain text equivalents
3. Add an explicit instruction at the top of the computer agent system prompt:

```python
SYSTEM_PROMPTS["computer"] = """You are Legion, an AI that controls a Linux desktop.
TOOL CALLING RULES:
- Always call tools using the tools parameter in the API call, never in message text
- Never write function calls as text in your response
- When you need to use a tool, output ONLY the tool call, no surrounding text
- Tool arguments must be valid JSON objects

You have these capabilities: take screenshots, click, type, run shell commands,
open apps, browse websites, read/write files. Always take a screenshot first to
see the current state before acting. After each action, take another screenshot
to verify it worked. Keep trying until the task is complete.
""" + "[rest of tools description in plain text, no XML tags]"
```

4. Also add `tool_choice="auto"` explicitly in every litellm `completion()` call that
   passes tools, because Groq requires this to be explicit:

```python
response = completion(
    model=model,
    messages=messages,
    tools=tools,
    tool_choice="auto",  # REQUIRED for Groq
    ...
)
```

### Bug 3: Scheduler init fails — `No module named 'aiosqlite'`

The bot is running from the system Python or a venv that doesn't have aiosqlite.

**Fix:** Add to startup script / requirements.txt AND add a pip install guard in
`tools/persistence.py`:

```python
try:
    import aiosqlite
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "aiosqlite", "--break-system-packages", "-q"])
    import aiosqlite
```

Also update `requirements.txt` to include: `aiosqlite>=0.19.0`

---

## PHASE 1 — ACADEMIC RESEARCH LAYER (for WorkerNet / POPW protocol)

### New file: `tools/arxiv.py`

Build a complete arXiv research tool. It must:

1. **`search_arxiv(query, max_results=5)`** — searches arXiv API
   (`http://export.arxiv.org/api/query?search_query=...`) and returns list of dicts:
   `{title, authors, abstract, arxiv_id, pdf_url, published}`

2. **`download_paper(arxiv_id)`** — downloads PDF to
   `~/swarm-bot/papers/{arxiv_id}.pdf`, returns local path

3. **`extract_paper_text(pdf_path)`** — extracts text using `pdfplumber`
   (already in requirements). Returns first 8000 chars (enough for abstract + intro)

4. **`analyze_paper(text, question)`** — sends paper text to the debug agent
   (ZAI GLM-4) with a structured professor-style analysis prompt:
   ```
   Analyze this research paper section with academic rigor:
   1. Core problem statement
   2. Key methodology / algorithm (with equations if present)
   3. Datasets used and evaluation metrics
   4. Main results and claims
   5. Limitations acknowledged by authors
   6. Open questions / future work
   7. Answer this specific question: {question}
   ```

5. **`analyze_codebase_vs_paper(code_files, paper_text)`** — cross-reference:
   reads code files, extracts class/function names, matches them to paper equations
   and methods, returns a structured comparison

6. **`WORKERNET_PAPERS`** — hardcoded dict of the 6 papers WorkerNet implements:
   ```python
   WORKERNET_PAPERS = {
       "kendall2018": {
           "query": "Multi-Task Learning Using Uncertainty to Weigh Losses Kendall 2018",
           "arxiv_id": "1705.07115",
           "implements": ["MultiTaskLoss", "log_var_det", "log_var_pose", "log_var_act"],
           "key_equation": "L = sum_t [exp(-s_t) * L_t + s_t]"
       },
       "lin2017": {
           "query": "Focal Loss Dense Object Detection RetinaNet Lin 2017",
           "arxiv_id": "1708.02002",
           "implements": ["FocalLoss", "DetectionHead"],
           "key_equation": "FL(p_t) = -alpha_t * (1 - p_t)^gamma * log(p_t)"
       },
       "feng2018": {
           "query": "Wing Loss Robust Facial Landmark Localisation Feng 2018",
           "arxiv_id": "1711.06753",
           "implements": ["WingLoss"],
           "key_equation": "wing(x) = w*ln(1 + |x|/epsilon) if |x| < w else |x| - C"
       },
       "cui2019": {
           "query": "Class-Balanced Loss Effective Number of Samples Cui 2019",
           "arxiv_id": "1901.05555",
           "implements": ["ClassBalancedFocalLoss"],
           "key_equation": "E_n = (1 - beta^n) / (1 - beta)"
       },
       "perez2018": {
           "query": "FiLM Visual Reasoning General Conditioning Layer Perez 2018",
           "arxiv_id": "1709.07871",
           "implements": ["PoseFiLMModule"],
           "key_equation": "FiLM(F|gamma,beta) = gamma * F + beta"
       },
       "ikea_asm": {
           "query": "IKEA Assembly Dataset Multi-Task Learning action recognition",
           "arxiv_id": "2007.09812",
           "implements": ["IKEAMultiTaskDataset"],
           "key_equation": "N/A - dataset paper"
       }
   }
   ```

### New commands in `main.py`

**`/paper <query>`**
- Searches arXiv for the query
- Returns top 3 results with title, authors, abstract summary
- Inline buttons: [📥 Download] [🔬 Full Analysis]

**`/workernet-papers`**
- Automatically fetches all 6 WorkerNet papers from `WORKERNET_PAPERS`
- For each paper: downloads PDF, extracts text, runs professor analysis
- Cross-references each paper's key equations against the actual code in
  `~/swarm-bot/` or wherever WorkerNet lives
- Returns a structured research brief for each paper
- Sends as multiple messages (one per paper) to avoid Telegram 4096 char limit

**`/research-project <github_url_or_local_path>`**
- If URL: git clones to `/tmp/research_{timestamp}/`
- Maps every Python file: class names, function names, imports, docstrings
- Extracts all paper citations (arXiv IDs, DOIs, paper titles in comments/README)
- Downloads and analyzes each cited paper
- Cross-references implementations against paper methodology
- Generates a professor-level research report sent across multiple Telegram messages

**`/ask-paper <arxiv_id> <question>`**
- Downloads specific paper, extracts text, answers the question using debug agent
- Example: `/ask-paper 1705.07115 is clamping log_var to [-3,1] justified in this paper?`

---

## PHASE 2 — WEBSITE & APP DEVELOPMENT (scaffold from Telegram)

### New file: `tools/scaffolder.py`

Build a full-stack project scaffolder:

1. **`scaffold_nextjs(project_name, features)`**
   - Creates `~/projects/{project_name}/` directory
   - Runs: `npx create-next-app@latest {name} --typescript --tailwind --app --no-git`
   - Adds shadcn/ui: `npx shadcn-ui@latest init`
   - Creates standard structure: `app/`, `components/`, `lib/`, `api/`
   - Adds auth stub if "auth" in features (NextAuth.js)
   - Adds Supabase client if "supabase" in features
   - Returns list of created files

2. **`scaffold_fastapi(project_name, features)`**
   - Creates project with: `main.py`, `models/`, `routes/`, `services/`, `tests/`
   - Adds SQLAlchemy + Alembic if "database" in features
   - Adds JWT auth if "auth" in features
   - Adds pytest structure with example tests
   - Creates `requirements.txt` and `Dockerfile`

3. **`scaffold_laravel(project_name, features)`**
   - Runs: `composer create-project laravel/laravel {name}`
   - Adds Breeze (auth) if "auth" in features
   - Adds API routes scaffold

4. **`run_tests_and_fix(project_path, max_attempts=3)`**
   - Runs project tests
   - If failing: sends output to coding agent with instruction to fix
   - Applies the fix, runs again
   - Loops up to `max_attempts` times
   - Returns final test status

5. **`push_to_github(project_path, repo_name, private=True)`**
   - Creates GitHub repo via `gh repo create`
   - Initializes git, adds remote, pushes
   - Returns repo URL

### Parallel agent execution for full-stack

In `tools/orchestrator.py`, add a `parallel_fullstack(task)` function:
- Decomposes the task into: frontend subtask + backend subtask + tests subtask
- Runs all 3 using `asyncio.gather()` with separate LLM calls
- Each call uses the coding agent (Devstral or llama-3.3-70b)
- Frontend call gets: "Write only the frontend/UI components for this task..."
- Backend call gets: "Write only the backend API/database layer for this task..."
- Merges outputs into a coherent project structure
- Returns combined file list

### New commands in `main.py`

**`/scaffold <framework> <description>`**
- Examples: `/scaffold nextjs personal portfolio with blog and dark mode`
- Examples: `/scaffold fastapi REST API for todo app with JWT auth`
- Calls appropriate scaffolder function
- Takes screenshot when done, sends to Telegram
- Sends GitHub repo URL when pushed

**`/build <task>`**
- Uses parallel_fullstack() — runs frontend + backend agents simultaneously
- Shows live progress: "⚡ Frontend agent: writing components... | Backend agent: writing API..."
- Runs tests automatically when done
- Pushes to GitHub
- Entire loop runs unattended overnight

---

## PHASE 3 — MULTI-AGENT TEAM (divisions model)

### Major rewrite of `tools/orchestrator.py`

The current `smart_route()` function is too simple. Replace with a full team model:

**Agent Registry** — define named specialist agents:
```python
AGENT_TEAM = {
    "strategist": {
        "model": "cerebras/qwen3-235b-a22b",
        "role": "High-level planning, architecture decisions, business strategy",
        "system": "You are a senior technical strategist. Break complex goals into clear sub-tasks..."
    },
    "developer": {
        "model": "openrouter/mistralai/devstral-small:free",
        "role": "Code generation, debugging, refactoring",
        "system": "You are a senior software engineer. Write clean, tested, production-ready code..."
    },
    "researcher": {
        "model": "groq/moonshotai/kimi-k2-instruct",
        "role": "Academic research, paper analysis, competitive intelligence",
        "system": "You are an academic researcher. Analyze papers rigorously, find evidence..."
    },
    "marketer": {
        "model": "groq/llama-3.3-70b-versatile",
        "role": "Content, social media, copywriting, brand strategy",
        "system": "You are a senior marketing strategist. Create compelling content..."
    },
    "analyst": {
        "model": "groq/moonshotai/kimi-k2-instruct",
        "role": "Data analysis, metrics, benchmarks, performance review",
        "system": "You are a quantitative analyst. Analyze data with statistical rigor..."
    },
    "devops": {
        "model": "groq/llama-3.3-70b-versatile",
        "role": "Infrastructure, deployment, CI/CD, security, monitoring",
        "system": "You are a senior DevOps engineer. Think about reliability, security, scalability..."
    },
    "pm": {
        "model": "cerebras/qwen3-235b-a22b",
        "role": "Project management, task decomposition, deadline tracking",
        "system": "You are a senior PM. Break work into clear tasks with owners and deadlines..."
    },
}
```

**`decompose_task(task, strategist_model)`** — sends task to strategist, returns:
```json
{
  "subtasks": [
    {"id": "1", "agent": "developer", "task": "...", "depends_on": []},
    {"id": "2", "agent": "researcher", "task": "...", "depends_on": []},
    {"id": "3", "agent": "analyst", "task": "...", "depends_on": ["1", "2"]}
  ]
}
```

**`execute_parallel(subtasks)`** — runs all independent subtasks with `asyncio.gather()`,
then runs dependent tasks sequentially, returns dict of results keyed by subtask id

**`synthesize_results(task, subtask_results, strategist_model)`** — sends all results
to strategist for final synthesis into a coherent answer

### Fix `/swarm` command in `main.py`

The current `/swarm` is broken (shows usage but doesn't run anything meaningful).
Replace it with the full team model:

```python
@dp.message(Command("swarm"))
async def cmd_swarm(msg: Message) -> None:
    if not await auth(msg): return
    task = msg.text.removeprefix("/swarm").strip()
    if not task:
        # show usage with examples
        return

    status = await msg.answer("🧠 strategist decomposing task...")

    try:
        subtasks = await decompose_task(task)
        agent_list = "\n".join(f"  • [{s['agent']}] {s['task'][:60]}..." for s in subtasks)
        await status.edit_text(f"⚡ running {len(subtasks)} agents in parallel:\n{agent_list}")

        results = await execute_parallel(subtasks)
        final = await synthesize_results(task, results)

        # Send result chunked
        for chunk in chunk_output(final):
            await msg.answer(chunk, parse_mode="HTML")
    except Exception as e:
        await status.edit_text(f"swarm error: <code>{e}</code>", parse_mode="HTML")
```

---

## PHASE 4 — DAILY BRIEFING (morning killer app)

### New file: `tools/briefing.py`

**`generate_briefing()`** — assembles a morning briefing:

1. **GitHub PRs**: runs `gh pr list --author @me --json title,url,state` and
   `gh pr list --review-requested @me --json title,url` via shell
2. **Training status**: reads latest lines from WorkerNet training log at
   `~/projects/*/logs/train.log` or similar — extracts last epoch metrics
3. **News**: fetches 3 tech news headlines via RSS from:
   - `https://hnrss.org/frontpage` (Hacker News)
   - `https://feeds.feedburner.com/TechCrunch` (TechCrunch)
   - `https://arxiv.org/rss/cs.CV` (Computer Vision papers)
4. **GPU/System**: calls `computer_agent.get_system_stats()`
5. **Weather**: simple HTTP call to `wttr.in/{city}?format=3`
6. **Calendar**: if Google Calendar API key available, fetch today's events.
   Otherwise: check for any `.ics` files or a simple `~/calendar.txt`

Format everything as a clean HTML Telegram message with sections and emojis.

### Schedule the briefing

In `on_startup()`, add:
```python
# Schedule daily briefing at 7:30 AM local time
asyncio.create_task(schedule_daily_briefing(bot, ALLOWED_USER_ID, hour=7, minute=30))
```

Add `schedule_daily_briefing()` that uses `asyncio.sleep()` to wait until the next
occurrence of the target time, sends the briefing, then sleeps 24 hours and repeats.

### New command: `/briefing`

Manual trigger for the morning briefing at any time.

---

## PHASE 5 — SECOND BRAIN / VECTOR MEMORY

### New file: `tools/memory.py`

Build a searchable knowledge base using SQLite + simple TF-IDF (no heavy dependencies):

1. **`add_memory(text, tags=None, source=None)`** — stores note in SQLite with:
   - Full text
   - Tags (comma-separated)
   - Source (telegram/arxiv/web/manual)
   - Timestamp
   - Simple word-frequency vector stored as JSON

2. **`search_memory(query, top_k=5)`** — TF-IDF cosine similarity search across all notes.
   If `sentence-transformers` is installed, use semantic embeddings instead.
   Returns top_k most relevant notes.

3. **`link_memories(note_id)`** — finds notes semantically similar to given note,
   suggests connections (like Obsidian graph)

4. **`export_to_obsidian(vault_path)`** — writes all notes as `.md` files to an
   Obsidian vault directory, with `[[wikilink]]` syntax for linked notes

5. **`auto_save_research(paper_analysis)`** — after every `/paper` command,
   automatically saves the analysis to memory with tags: `["arxiv", "research", paper_id]`

### New commands in `main.py`

**`/remember <note>`** — saves to memory, confirms with note ID

**`/recall <query>`** — searches memory, returns top 5 relevant notes

**`/memories`** — shows last 10 saved memories

**`/brain-export`** — exports all memories to `~/brain/` as Obsidian-compatible .md files

**Auto-save integration**: After every `/paper` and `/research-project` command,
automatically call `add_memory()` with the result. After every `/do` task that
produces notable output, ask the LLM "is this worth remembering?" and save if yes.

---

## PHASE 6 — PROJECT MANAGEMENT

### New file: `tools/project_manager.py`

1. **`transcript_to_tasks(transcript_text)`** — sends transcript to PM agent.
   Returns structured tasks:
   ```json
   [{"task": "...", "owner": "...", "deadline": "...", "priority": "high/mid/low"}]
   ```

2. **`save_tasks_local(tasks, project_name)`** — saves to SQLite via persistence.py

3. **`check_deadlines()`** — queries tasks due in next 48 hours, returns list

4. **`add_to_todoist(task, api_key)`** — if TODOIST_API_KEY in .env, creates task
   via Todoist REST API

5. **`add_to_linear(task, api_key)`** — if LINEAR_API_KEY in .env, creates issue
   via Linear GraphQL API

### New commands in `main.py`

**`/task-from <text>`** — convert any text/transcript to structured task list.
Example: `/task-from discussed: add auth by friday, deploy monday, john handles DB`

**`/tasks-due`** — shows tasks due in next 48 hours

**`/task-done <id>`** — mark task complete

---

## PHASE 7 — COMPETITIVE BENCHMARK MONITORING (for WorkerNet)

### Add to `tools/arxiv.py`

**`monitor_benchmark(dataset_name, your_metrics)`** — weekly job that:
- Searches arXiv for papers citing the IKEA ASM dataset
- Extracts reported accuracy/F1/mAP numbers
- Compares to WorkerNet's numbers: `{act_accuracy: 0.6046, mAP50: X, PCK005: X}`
- Returns: "New SOTA found: [paper] reports 64.2% vs your 60.46%"
  OR "No new SOTA — your model still competitive"

Schedule this weekly via the scheduler: every Monday 9 AM.

---

## PHASE 8 — DEVOPS AUTOMATION

### New file: `tools/devops.py`

1. **`check_vulnerabilities(project_path)`** — runs `pip-audit` or `safety check`
   on requirements.txt, parses output, returns list of CVEs with severity

2. **`dependency_updates(project_path)`** — runs `pip list --outdated`, returns
   packages with available updates and changelog URLs

3. **`check_gpu_health()`** — runs `nvidia-smi` and parses:
   temperature, VRAM used/total, GPU utilization, running processes

4. **`watch_training_log(log_path, callback)`** — tails a training log file,
   calls callback when: loss spikes, NaN detected, training completes,
   new best model saved

5. **`deploy_to_vps(project_path, host, user)`** — rsync project to VPS,
   restart systemd service, check it came up, return status

### New commands in `main.py`

**`/vuln-scan`** — run vulnerability scan on WorkerNet dependencies

**`/gpu`** — enhanced GPU status (temp, VRAM, processes, power draw)

**`/watch-training`** — start watching WorkerNet training log, alert on events.
Sets up a background monitor via scheduler.

---

## PHASE 9 — CONTENT & SOCIAL MEDIA

### New file: `tools/content.py`

1. **`draft_linkedin_post(topic, tone="professional")`** — generates LinkedIn post
   using marketer agent, formatted for LinkedIn (no markdown, paragraph breaks)

2. **`draft_tweet(topic, thread=False)`** — generates X/Twitter post(s) under 280 chars.
   If `thread=True`, generates a 5-tweet thread.

3. **`monitor_brand(keywords, platforms=["reddit", "hackernews"])`** — scrapes:
   - Reddit: search API `https://www.reddit.com/search.json?q={keyword}`
   - HN: `https://hnrss.org/mentions?q={keyword}`
   Returns mentions with sentiment (positive/negative/neutral)

4. **`rss_to_post(rss_url, platform="linkedin")`** — fetches latest RSS item,
   summarizes with marketer agent, drafts a platform-appropriate post

### New commands in `main.py`

**`/post <platform> <topic>`** — draft social media post
Example: `/post linkedin my WorkerNet model achieves 60% accuracy on IKEA ASM`

**`/brand-check <keyword>`** — search for mentions of keyword online

---

## PHASE 10 — OPENCLAW BRIDGE (run both simultaneously)

### Architecture decision:
Run **OpenClaw alongside Legion** on the same machine. Legion is the "master" bot.
When a user task requires OpenClaw's 50+ integrations (smart home, Apple notes,
Obsidian sync, etc.), Legion delegates to OpenClaw via HTTP and returns the result.

### Setup instructions (add to README):
```bash
# Install OpenClaw on same machine
git clone https://github.com/openclaw/openclaw ~/openclaw
cd ~/openclaw && npm install
cp config.example.json config.json
# Configure config.json to use Groq (free) as the LLM provider
# Set webhook_port: 3456
npm start &
```

### New file: `tools/openclaw_bridge.py`

1. **`OPENCLAW_BASE_URL = "http://localhost:3456"`**

2. **`is_openclaw_running()`** — `GET /health` check, returns bool

3. **`delegate_to_openclaw(task, context=None)`** — sends task to OpenClaw's
   API endpoint, waits for response, returns result string

4. **`openclaw_integrations()`** — lists all installed OpenClaw skills/integrations

5. **Auto-delegation rules** — in `main.py` natural language handler, before routing
   to Legion's own agents, check if the task matches OpenClaw-specific integrations:
   ```python
   OPENCLAW_KEYWORDS = [
       "apple notes", "obsidian", "things3", "philips hue", "smart home",
       "spotify", "apple music", "trello", "linear", "notion"
   ]
   if any(kw in task.lower() for kw in OPENCLAW_KEYWORDS):
       if await is_openclaw_running():
           result = await delegate_to_openclaw(task)
           # return result to user
   ```

6. **OpenClaw + Legion combined flow:**
   - Legion handles: desktop control, screenshots, file operations, code execution,
     WorkerNet monitoring, Python/shell commands, WhatsApp Web via Playwright
   - OpenClaw handles: smart home, native app integrations (Things3, Obsidian),
     Apple Notes/Calendar, Spotify
   - Both share: research tasks, web browsing (Legion's Playwright vs OpenClaw's browser)

### New command: `/delegate <task>`
Force delegation to OpenClaw, show the result in Telegram.

---

## FILE STRUCTURE AFTER ALL PHASES

```
~/swarm-bot/  (or ~/Babas_Swarms_bot/)
├── main.py              ← +15 new commands
├── llm_client.py        ← bug fixes + parallel agent support
├── computer_agent.py    ← unchanged (already comprehensive)
├── router.py            ← add researcher, marketer, devops, pm agent keys
├── requirements.txt     ← add: pdfplumber, feedparser, pip-audit
├── tools/
│   ├── __init__.py
│   ├── arxiv.py         ← NEW: paper fetcher + WorkerNet papers
│   ├── scaffolder.py    ← NEW: Next.js / FastAPI / Laravel scaffold
│   ├── memory.py        ← NEW: second brain / vector memory
│   ├── briefing.py      ← NEW: morning briefing assembler
│   ├── content.py       ← NEW: social media content + brand monitoring
│   ├── project_manager.py ← NEW: task extraction + Todoist/Linear
│   ├── devops.py        ← NEW: vuln scan, GPU health, training watcher
│   ├── openclaw_bridge.py ← NEW: delegate to OpenClaw
│   ├── web_browser.py   ← exists
│   ├── documents.py     ← exists
│   ├── email_client.py  ← exists
│   ├── git_tools.py     ← exists
│   ├── dev_tools.py     ← exists
│   ├── system_maintenance.py ← exists
│   ├── orchestrator.py  ← REWRITE: full team model
│   ├── persistence.py   ← exists + add memory table
│   └── scheduler.py     ← exists + add daily briefing schedule
```

---

## NEW `.env` VARIABLES TO ADD (with instructions for user)

```env
# Existing (already set):
TELEGRAM_BOT_TOKEN=
ALLOWED_USER_ID=
GROQ_API_KEY=
ZAI_API_KEY=
CEREBRAS_API_KEY=
GEMINI_API_KEY=
OPENROUTER_API_KEY=

# NEW — optional, add as needed:
GITHUB_TOKEN=           # gh CLI token for GitHub operations
TODOIST_API_KEY=        # https://app.todoist.com/app/settings/integrations/developer
LINEAR_API_KEY=         # https://linear.app/settings/api
OPENCLAW_PORT=3456      # local OpenClaw instance port (default 3456)
CITY_FOR_WEATHER=Jakarta  # used in daily briefing
WORKERNET_LOG_PATH=     # full path to your WorkerNet training log
WORKERNET_CODE_PATH=/media/newadmin/master/POPW/  # your POPW root
```

---

## IMPLEMENTATION ORDER

Do these in order. Each phase must be tested before moving to next:

1. **Bug fixes** (Phase 0) — fix NoneType + Groq tool calling + aiosqlite
2. **arxiv.py + /paper + /workernet-papers** (Phase 1) — test with one paper first
3. **Fix /swarm** (Phase 3 partial) — the current /swarm is broken, fix it
4. **daily briefing** (Phase 4) — high value, low complexity
5. **memory.py** (Phase 5) — needed by everything else that saves notes
6. **scaffolder.py + /build** (Phase 2) — complex but high value
7. **orchestrator.py rewrite** (Phase 3 full) — after /swarm works
8. **devops.py + /watch-training** (Phase 8) — valuable for WorkerNet
9. **content.py** (Phase 9)
10. **openclaw_bridge.py** (Phase 10) — only if OpenClaw is installed

---

## TESTING PROTOCOL

After each phase, test with these Telegram commands:

```
# Bug fixes:
/do open calculator          → should work without NoneType error
/screen                      → take screenshot, no crash

# Phase 1:
/paper Kendall multi-task learning uncertainty
/workernet-papers
/ask-paper 1705.07115 does clamping log_var to -3,1 appear in this paper?

# Phase 3:
/swarm analyze the IKEA ASM dataset codebase and suggest 3 improvements to WorkerNet

# Phase 4:
/briefing

# Phase 5:
/remember FiLM modulation helps activity recognition when pose is noisy
/recall FiLM
```

---

## IMPORTANT CONSTRAINTS — DO NOT VIOLATE

- All LLMs must use free tier APIs only (Groq, Cerebras, ZAI, Gemini, OpenRouter)
- Ollama gemma3:12b for vision only (privacy — screenshots never leave machine)
- No message content logging (privacy requirement)
- No threading — everything asyncio
- Telegram 4096 char limit — all responses must go through `chunk_output()`
- ALLOWED_USER_ID check on EVERY command handler — no exceptions
- WorkerNet training code is at `/media/newadmin/master/POPW/` — read-only access
  when doing research/analysis, never modify training files
- OpenClaw must use Groq (free) as its LLM provider — configure it to NOT use
  Claude or OpenAI API (those cost money)

---

## KNOWN WORKING STATE (as of March 10, 2026)

The following already works and should NOT be broken:
- /screen (takes screenshot via scrot, sends to Telegram)
- /keys (shows API key status — all 6 keys active)
- /run (LLM chat without computer use)
- /cmd (shell commands with safety filter)
- /stats, /git (system info)
- /think (QwQ reasoning mode)
- router.py (agent selection by keywords)
- All tools/ imports (web_browser, documents, email_client, git_tools, dev_tools,
  system_maintenance, orchestrator, persistence, scheduler)
- DISPLAY detection (auto-detects :1 on Bashara's machine)

The following is broken and must be fixed:
- /do (NoneType error + Groq XML function calling bug)
- /swarm (shows usage but doesn't actually run multi-agent)
- /scheduler (aiosqlite not in active venv)
