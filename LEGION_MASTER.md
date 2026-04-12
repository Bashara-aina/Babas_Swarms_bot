# LEGION MASTER PROMPT
# The single file to paste into OpenCode for every session.
# Supersedes: AUDIT_NOW.md, LEGION_CLAWCODE_UPGRADE.md, LEGION_MCP_SKILLS_MASTER.md
# Last updated: 2026-04-12

---

## HOW TO USE THIS FILE

Paste into OpenCode:
```
Read LEGION_MASTER.md fully from top to bottom before touching any code.
Then read CLAUDE.md and SOUL.md.
Then execute the CURRENT SESSION TASK at the bottom of this file.
```

---

# ──────────────────────────────────────────────────
# PART 1 — WHO LEGION IS
# ──────────────────────────────────────────────────

Legion is Bashara's permanent AI coworker, not a chatbot.
Bashara is a Data Science Master's student at Shibaura Institute of Technology, Tokyo.
Machine: Ubuntu Linux, RTX 3060, 64GB RAM, 5TB storage.
Interface: Telegram (iPhone) only.
Framework: aiogram 3.4+ (async)
LLM routing: litellm 1.57+ via OpenRouter
Deployment: systemd (swarm-bot.service)

Active projects Bashara works on daily:
- Babas_Swarms_bot (this repo) — Legion itself
- rumahlabuh.com — Indonesian property rental platform (Next.js + Supabase)
- cekwajar.id — Indonesian salary fairness tool (Next.js + Supabase)
- POPW thesis — assembly action recognition (ResNet-50, FPN, FiLM, Kendall MTL)
- ADB scholarship application via Keio University nomination

Legion's personality (enforced by core/character_enforcer.py):
- Never says: "Certainly!", "Great!", "Sure!", "Of course!", "Absolutely!",
  "I'd be happy to", "As an AI"
- Language: Indonesian or English matching Bashara's message
- Tone: direct, technically precise, dry humor
- Debates when Bashara is wrong — never agrees just to agree
- Short messages get short replies, deep questions get depth
- SOUL.md is the living identity — read at every session

---

# ──────────────────────────────────────────────────
# PART 2 — WHAT LEGION CAN DO TODAY (verified capabilities)
# ──────────────────────────────────────────────────

## 2.1 MEDIA HANDLING (what Legion receives from Telegram)

### ✅ SUPPORTED — Legion handles these right now:

| Type          | How it works                                                      | File                          |
|---------------|-------------------------------------------------------------------|-------------------------------|
| Photos/Images | Vision via MiniMax or Ollama Gemma3/llava (local RTX 3060)       | handlers/media_tools.py       |
| Voice notes   | Transcribe: faster-whisper (GPU) > Groq Whisper > openai-whisper | handlers/voice.py             |
| Audio files   | Same transcription pipeline as voice                             | handlers/voice.py             |
| PDF           | pdfplumber/PyPDF2 text; Tesseract OCR for scanned               | tools/documents.py            |
| DOCX          | python-docx text extraction                                      | multimodal_processor.py       |
| Excel (.xlsx) | openpyxl read/write                                              | tools/documents.py            |
| Plain text    | Direct UTF-8 decode                                              | multimodal_processor.py       |
| Image OCR     | pytesseract extraction                                           | tools/documents.py            |
| Image gen     | MiniMax API (/imagine command)                                   | handlers/media_tools.py       |
| TTS output    | Kokoro-ONNX (local) or edge-tts (cloud)                          | multimodal_processor.py       |

### ❌ NOT SUPPORTED — gaps to fill:

| Type          | Status     | What's needed                                                      |
|---------------|------------|--------------------------------------------------------------------|
| Video files   | ❌ Missing  | No F.video handler. Files ignored silently.                        |
| CSV           | ❌ Missing  | Not in documents.py. Common file Bashara sends.                    |
| PPTX          | ❌ Missing  | Not handled.                                                       |
| RTF / ODT     | ❌ Missing  | Not handled.                                                       |
| EPUB          | ❌ Missing  | Not handled.                                                       |
| Wiki ingestion| ❌ Partial  | wiki_handler.py:41 says "not yet implemented" for file uploads.   |

### HOW TO ADD VIDEO SUPPORT (implement this session if tasked):

```python
# In handlers/media_tools.py, add after existing photo handler:

@router.message(F.video | F.video_note)
async def handle_video(message: Message):
    if message.from_user.id != ALLOWED_USER_ID:
        return
    await message.answer("🎬 Processing video...")
    file = message.video or message.video_note
    file_info = await message.bot.get_file(file.file_id)
    file_path = f"/tmp/legion/video_{file.file_id}.mp4"
    await message.bot.download_file(file_info.file_path, file_path)

    # Strategy 1: Extract keyframes + analyze via vision agent
    # Strategy 2: Extract audio track + transcribe via voice pipeline
    # Strategy 3: Both — keyframe analysis + audio transcription merged

    # Step 1: Extract frames at 1fps using ffmpeg
    from core.shell.sandbox import run_sandboxed
    frames_dir = f"/tmp/legion/frames_{file.file_id}"
    await run_sandboxed(f"mkdir -p {frames_dir} && "
                        f"ffmpeg -i {file_path} -vf fps=1 {frames_dir}/frame_%04d.jpg -y")

    # Step 2: Extract audio
    audio_path = f"/tmp/legion/audio_{file.file_id}.mp3"
    await run_sandboxed(f"ffmpeg -i {file_path} -vn -acodec mp3 {audio_path} -y")

    # Step 3: Transcribe audio via existing voice pipeline
    from handlers.voice import transcribe_audio
    transcript = await transcribe_audio(audio_path)

    # Step 4: Analyze keyframes via vision agent
    import os
    frame_files = sorted(os.listdir(frames_dir))[:5]  # max 5 keyframes
    frame_descriptions = []
    from llm_client import chat
    for fname in frame_files:
        with open(f"{frames_dir}/{fname}", "rb") as f:
            frame_b64 = __import__("base64").b64encode(f.read()).decode()
        desc = await chat("vision", [{"role": "user", "content": [
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"}},
            {"type": "text", "text": "Describe what you see in this video frame briefly."}
        ]}])
        frame_descriptions.append(desc)

    # Step 5: Summarize everything
    summary_prompt = f"""
Video analysis:
Audio transcript: {transcript}
Key frames ({len(frame_descriptions)} frames): {' | '.join(frame_descriptions)}

Summarize what this video is about and what's important in it.
"""
    summary = await chat("analyst", [{"role": "user", "content": summary_prompt}])
    await message.answer(summary)

    # Cleanup temp files
    await run_sandboxed(f"rm -rf {frames_dir} {file_path} {audio_path}")
```

Requires: `ffmpeg` installed on the machine (`sudo apt install ffmpeg`).

### HOW TO ADD CSV / PPTX / EPUB SUPPORT:

In `tools/documents.py`, add to the document type dispatcher:

```python
# CSV
elif ext == ".csv":
    import csv, io
    content = data.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    preview = f"CSV: {len(rows)} rows, columns: {', '.join(reader.fieldnames or [])}"
    return preview + "\n" + str(rows[:5])  # first 5 rows as preview

# PPTX
elif ext == ".pptx":
    from pptx import Presentation
    prs = Presentation(io.BytesIO(data))
    text = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                text.append(shape.text_frame.text)
    return "\n".join(text)

# EPUB
elif ext == ".epub":
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    book = epub.read_epub(io.BytesIO(data))
    texts = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        texts.append(soup.get_text())
    return "\n".join(texts)[:5000]  # cap at 5k chars
```

Add to requirements.txt:
```
python-pptx>=0.6.21
ebooklib>=0.18
beautifulsoup4>=4.12  # likely already present
```

---

## 2.2 COMMANDS (what Bashara can send in Telegram)

### Confirmed working:
```
/start /help /status          — system.py
/run /think /agent            — ai.py
/screen /do /cmd              — computer.py (sandbox gated)
/remember /recall /forget     — memory_commands.py
/memories /briefing /learn    — brain.py
/debate /opinion              — debate_handlers.py (✅ registered Apr 2026)
/emails /calendar             — communications.py (Composio)
/budget /soul                 — admin_handlers.py (✅ added Apr 2026)
/vcsearch                     — voice.py (✅ added Apr 2026)
/legion_sessions              — sessions.py (✅ renamed Apr 2026)
/imagine                      — media_tools.py (image gen)
```

### Natural language (no slash needed — intent_router handles):
```
"cek seo rumahlabuh"    → web_audit skill (after skills upgrade)
"restart legion"        → service_restart skill
"gpu lagi training ga"  → gpu_training_status skill
"pusing nih"            → emotion_modulator → empathy response (no bullet lists)
"cari paper FPN"        → arxiv_search skill
```

---

# ──────────────────────────────────────────────────
# PART 3 — CURRENT IMPLEMENTATION STATUS
# ──────────────────────────────────────────────────

## Completion as of 2026-04-12: 63% (12/19 CLAUDE.md tasks)

### ✅ CONFIRMED DONE (do not redo):
- P0-1: /debate registered in main.py
- P0-2: /cmd asyncio.wait_for(timeout=30) — already existed
- P0-3: core/ruflo_manager.py created — needs 2-line integration in main.py
- P1-1: /vcsearch added to voice.py
- P1-2: /sessions renamed to /legion_sessions
- P1-3: MCP stub removed from legion_extras.py
- P1-4: browser-use==0.1.21 pinned in requirements.txt
- P1-5: langchain-community added to requirements.txt
- P2-3: handlers/admin_handlers.py with /budget
- P2-4: handlers/admin_handlers.py with /soul
- P3-1: .github/workflows/legion-ci.yml created
- P3-2: tests/test_main.py created

### ❌ STILL OPEN (work on these):

**CRITICAL:**
- P0-4: parse_mode="Markdown" → parse_mode="HTML" audit
  186 files identified. Do a targeted fix on handlers/ first:
  `grep -rn 'parse_mode="Markdown"' handlers/` — fix all hits.
  Then run across entire codebase.

**HIGH:**
- P0-3 integration: Add 2 lines to main.py to wire ruflo_manager.py
  (see IMPLEMENTATION_STATUS.md for exact location)
- Budget enforcement: All background tasks must call BudgetManager.can_spend()
  Files: core/proactive/daily_briefing.py, tools/composio_hub.py
- Delete dead dirs IF they still exist:
  core/memory_old/, core/orchestration_old/, core/reliability_old/
- tests/test_system_prompt_builder.py::test_soul_is_first_section — missing

**MEDIUM (next sessions):**
- P2-1: Migrate swarm logic from main.py → swarm.py
- P2-2: Move /run /think from ai.py → agent.py
- P3-3: ARCHITECTURE.md
- P3-4: docs/MIGRATION.md
- P3-5/6: Inline comments in main.py and agent.py

---

# ──────────────────────────────────────────────────
# PART 4 — CLAWCODE UPGRADE PLAN (architecture gaps to close)
# ──────────────────────────────────────────────────

Legion has a soul. ClawCode has a body. This plan gives Legion ClawCode's body.
Full implementation details in LEGION_CLAWCODE_UPGRADE.md.

## 4.1 UPGRADE PRIORITY ORDER

### PHASE 1 — Foundation (highest ROI, do first)

**U1: Session Transcripts** — `core/session/transcript.py`
```
Problem: CONVERSATION_HISTORY is in-memory. Restart = amnesia.
Fix: SQLite-backed transcript using aiosqlite.
Impact: Legion remembers everything across restarts. Biggest daily pain point.
Time: 30 minutes.
```
See LEGION_CLAWCODE_UPGRADE.md UPGRADE 2 for full code.

**U2: Sandboxed Shell** — `core/shell/sandbox.py`
```
Problem: /cmd and computer_agent.py use raw asyncio.subprocess.
Fix: Blacklist guard + allowed paths. No Docker needed.
Impact: Prevents accidental destructive commands. Security baseline.
Time: 20 minutes.
```
See LEGION_CLAWCODE_UPGRADE.md UPGRADE 5 for full code.

**U3: Budget Gates on ALL Background Tasks**
```
Problem: Only curiosity_engine.py checks BudgetManager.can_spend().
         daily_briefing.py, composio_hub.py, and others bypass it.
Fix: Add 3-line budget check at top of every background LLM coroutine.
Also: Add hard-stop in llm_client.py as final safety net.
Time: 20 minutes.
```

**U4: Proactive Dedup + Variety Pool** — `core/proactive/curiosity_engine.py`
```
Problem: Same check-in message fires 5 times in 2 hours (verified from chat logs).
Fix: 9-message variety pool + 4-hour cooldown stored in memory.
Time: 15 minutes.
```

Pool to implement:
```python
CHECKIN_POOL = [
    "Lo baik-baik aja?",
    "Masih hidup? Kasih kabar dong.",
    "Eh, lagi ngapain?",
    "Sunyi banget dari lo tadi.",
    "Ada yang lagi lo pikirin?",
    "Halo. Lagi stuck atau emang sengaja ghosting?",
    None,   # 30% chance — send nothing
    None,
    None,
]
```

---

### PHASE 2 — Architecture (next session)

**U5: Skills Registry** — `core/skills/`
```
Problem: TASK_KEYWORDS is a flat dict. No schemas, no discovery, no introspection.
Fix: Typed SkillRegistry with 30 curated skills (see Part 5 below).
Impact: Natural language triggers work without slash commands.
Time: 2 hours.
```

**U6: Prompt Injection Protection** — `tools/browser_agent.py`
```
Problem: No URL allowlist. Browser visits any URL.
Fix: BROWSER_ALLOWED_DOMAINS env var + content sanitizer.
Time: 30 minutes.
```

**U7: Heartbeat Daemon** — `core/heartbeat/daemon.py`
```
Problem: Legion proactive engine only messages. Never executes work autonomously.
Fix: 15-min background executor that runs Skills and only messages when done.
Impact: Legion audits rumahlabuh SEO every Sunday at 10:00 JST without being asked.
Time: 1.5 hours.
```

---

### PHASE 3 — Integration (next week)

**U8: Webhook Listener** — `core/webhooks/`
```
Event-driven triggers: GitHub push, rumahlabuh inquiry, system alerts.
Time: 2 hours.
```

**U9: MCP Backbone** — `core/mcp/`
```
Replace composio_hub.py with plug-and-play MCP clients.
Enables 10 curated MCP servers (see Part 6 below).
Time: 3 hours.
```

---

# ──────────────────────────────────────────────────
# PART 5 — THE 30 SKILLS (implement in Phase 2)
# ──────────────────────────────────────────────────

Full implementation code in LEGION_MCP_SKILLS_MASTER.md.
Quick reference:

### Category A — Web + SEO
| Skill | Trigger examples | API needed |
|-------|-----------------|------------|
| web_audit | "cek seo", "audit website", "pagespeed" | Google PageSpeed (free) |
| url_check | "website down", "cek hidup ga" | None (aiohttp) |
| web_scrape | "buka link ini", "summarize artikel" | None (playwright) |

### Category B — Search + Research
| Skill | Trigger examples | API needed |
|-------|-----------------|------------|
| web_search | "cari", "search", "googling" | Brave Search (free tier) |
| arxiv_search | "cari paper", "thesis reference" | None (free API) |
| summarize_url | "tldr", "ringkas ini" | None |
| hacker_news | "hn", "berita tech" | None (free API) |

### Category C — GitHub + Code
| Skill | Trigger examples | API needed |
|-------|-----------------|------------|
| github_pr_status | "open prs", "cek pr" | GITHUB_TOKEN (existing) |
| github_commit_log | "latest commits", "apa yang dipush" | GITHUB_TOKEN |
| code_review | "review kode ini", "cek bug" | Routes to reviewer agent |

### Category D — System + Shell
| Skill | Trigger examples | Permission |
|-------|-----------------|------------|
| system_health | "cek server", "gpu status", "ram berapa" | basic |
| service_status | "legion running ga", "cek nginx" | basic |
| service_restart | "restart legion", "restart nginx" | elevated |
| run_shell | "jalanin", "execute", "bash" | elevated |

### Category E — Memory + Notes
| Skill | Trigger examples |
|-------|------------------|
| remember | "inget ini", "catat", "simpan" |
| recall | "inget ga", "lo pernah simpen" |
| obsidian_write | "tulis di obsidian", "buat catetan" |

### Category F — Productivity
| Skill | Trigger examples | API needed |
|-------|-----------------|------------|
| weather | "cuaca", "hujan ga", "forecast" | OpenWeatherMap (free) |
| translate | "translate", "artinya apa", "bahasa jepang" | LibreTranslate (free) |
| timer | "set timer", "ingetin gw", "alarm" | None (asyncio) |

### Category G — Bashara-Specific (ClawHub will NEVER have these)
| Skill | Trigger examples | What it does |
|-------|-----------------|---------------|
| rumahlabuh_status | "cek rumahlabuh", "ada inquiry baru" | Supabase query + uptime |
| thesis_status | "thesis gimana", "deadline kapan" | Memory recall + countdown |
| cekwajar_status | "cek cekwajar" | Supabase query + uptime |
| gpu_training_status | "training gimana", "loss berapa" | nvidia-smi + log parse |
| adb_scholarship | "adb gimana", "beasiswa deadline" | Memory recall |

### Category H — Media + Screen
| Skill | Wraps |
|-------|-------|
| screenshot | computer_agent.py existing handler |
| analyze_screen | screenshot + vision agent |
| screen_text | screenshot + OCR |

---

# ──────────────────────────────────────────────────
# PART 6 — MCP SERVERS (implement in Phase 3)
# ──────────────────────────────────────────────────

Full connection code in LEGION_MCP_SKILLS_MASTER.md.
Quick reference:

| Priority | Server | Cost | .env flag | Wires into |
|----------|--------|------|-----------|------------|
| 1 | Brave Search | Free | MCP_BRAVE_ENABLED | web_search skill |
| 2 | GitHub MCP | Free | MCP_GITHUB_ENABLED | github_* skills |
| 3 | Filesystem MCP | Free | MCP_FILESYSTEM_ENABLED | run_shell skill |
| 4 | Obsidian MCP | Free | MCP_OBSIDIAN_ENABLED | obsidian_write skill |
| 5 | Supabase MCP | Free | MCP_SUPABASE_ENABLED | rumahlabuh/cekwajar skills |
| 6 | Playwright MCP | Free | MCP_BROWSER_ENABLED | web_audit, web_scrape |
| 7 | mem0 MCP | Paid | MCP_MEMORY_ENABLED | remember, recall skills |
| 8 | Ahrefs MCP | Paid | MCP_AHREFS_ENABLED | web_audit enhanced |
| 9 | Notion MCP | Free | MCP_NOTION_ENABLED | notes (if Notion used) |
| 10 | Google Workspace | OAuth | MCP_GOOGLE_ENABLED | briefing + calendar |

Start with Priority 1-3. They're free and cover 80% of daily needs.
All enabled/disabled via .env flags — Legion works without any MCP server.

---

# ──────────────────────────────────────────────────
# PART 7 — CRITICAL RULES (CLAUDE.md summary — never violate)
# ──────────────────────────────────────────────────

1. ALL LLM calls go through llm_client.chat() — never call litellm directly
2. ALL memory writes go through core/memory/memory_manager.py — never write directly
3. ALL shell execution goes through core/shell/sandbox.py run_sandboxed()
4. NEVER use parse_mode="Markdown" — HTML only, escape user content
5. NEVER use threading or time.sleep() — fully async, asyncio only
6. NEVER hardcode TELEGRAM_BOT_TOKEN or ALLOWED_USER_ID — always os.getenv()
7. ALWAYS check ALLOWED_USER_ID before processing any command
8. SOUL context MUST be injected first in system_prompt_builder.py
9. ALL background tasks must check BudgetManager.can_spend() before LLM calls
10. NEVER touch files with _old suffix — dead code, delete references only

---

# ──────────────────────────────────────────────────
# PART 8 — SMOKE TESTS (run before AND after every session)
# ──────────────────────────────────────────────────

```bash
# Baseline (always run these first)
python -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:80])"
python -c "from core.intent_router import IntentRouter; r=IntentRouter(); print(r.classify('write me code'))"
python -c "from core.system_prompt_builder import build_full_system_prompt; print(build_full_system_prompt('test')[:100])"
python -c "from core.debate_engine import build_debate_instruction; print('debate ok')"
python -c "from core.character_enforcer import enforce_character; print(enforce_character('Certainly! I can help.'))"

# After Skills Registry is implemented
python -c "
from core.skills import builtin
from core.skills.registry import SKILL_REGISTRY
print(f'Skills: {len(SKILL_REGISTRY._skills)}')
for s in SKILL_REGISTRY.list_all(): print(f'  {s[\"name\"]}')
"

# After Session Transcripts is implemented
python -c "import asyncio; from core.session.transcript import TRANSCRIPT; asyncio.run(TRANSCRIPT.init()); print('Transcript OK')"

# After Sandbox is implemented
python -c "import asyncio; from core.shell.sandbox import run_sandboxed; print(asyncio.run(run_sandboxed('echo ok')))"

# Full test suite
pytest tests/ -x --asyncio-mode=auto -q
```

---

# ──────────────────────────────────────────────────
# PART 9 — DEFINITION OF DONE
# ──────────────────────────────────────────────────

Legion is fully done when ALL of these pass without a slash command:

- Bashara sends "pusing nih" at midnight
  → Legion replies like a friend. One sentence. No bullet list. No options.

- Bashara sends "cek seo rumahlabuh"
  → web_audit skill fires, returns real PageSpeed score.

- Bashara restarts swarm-bot.service
  → Legion resumes with last 20 turns from SQLite. Zero amnesia.

- No message for 8 hours
  → One varied check-in, different phrasing. Then silence for 4 hours.

- GitHub PR merged at 3am
  → Webhook fires. Legion summarizes in morning briefing.

- Bashara sends a .mp4 video
  → Legion extracts frames, transcribes audio, returns summary.

- Bashara sends a .csv file
  → Legion reads columns, shows 5-row preview, offers analysis.

---

# ──────────────────────────────────────────────────
# ► CURRENT SESSION TASK — EDIT THIS SECTION EACH SESSION
# ──────────────────────────────────────────────────

## SESSION: 2026-04-12 — PHASE 1

Do these in order. Run smoke tests between each step.

### STEP 1: Fix parse_mode (P0-4) — 30 min
```bash
grep -rn 'parse_mode="Markdown"' handlers/
```
For every hit: change to parse_mode="HTML"
Wrap any user-sourced content: html.escape(user_text)
Then run: grep -rn 'parse_mode="Markdown"' . — expect 0 results

### STEP 2: Wire ruflo_manager into main.py — 5 min
See IMPLEMENTATION_STATUS.md for exact 2-line change.

### STEP 3: Add budget gates to daily_briefing.py and composio_hub.py — 15 min
Add at top of every coroutine that calls LLM:
```python
from swarms_bot.routing.budget_manager import BudgetManager
if not BudgetManager.can_spend("task_name"):
    return
```

### STEP 4: Session Transcripts — 30 min
Create core/session/transcript.py
Full code in LEGION_CLAWCODE_UPGRADE.md UPGRADE 2.
Wire into main.py on_startup() and handlers/ai.py

### STEP 5: Sandboxed Shell — 20 min
Create core/shell/sandbox.py
Full code in LEGION_CLAWCODE_UPGRADE.md UPGRADE 5.
Replace all raw subprocess calls in handlers/shared.py and computer_agent.py

### STEP 6: Proactive dedup — 15 min
Update core/proactive/curiosity_engine.py with CHECKIN_POOL and 4-hour cooldown.
Full code in LEGION_CLAWCODE_UPGRADE.md UPGRADE 9.

### STEP 7: Video + CSV support — 30 min
Add F.video handler in handlers/media_tools.py (full code in Part 2 above)
Add CSV/PPTX/EPUB to tools/documents.py (full code in Part 2 above)
Add to requirements.txt: python-pptx>=0.6.21, ebooklib>=0.18

### STEP 8: Update docs — 10 min
Update IMPLEMENTATION_STATUS.md to reflect all completed steps.
Update CLAUDE.md Section 9 to mark completed P-items.

### STEP 9: Full test run
```bash
pytest tests/ -x --asyncio-mode=auto -q
```
All tests must pass before this session is done.

---

*This file is the single source of truth for all OpenCode sessions.*
*Edit only the CURRENT SESSION TASK section between sessions.*
*Everything else is updated by OpenCode at end of each session.*
