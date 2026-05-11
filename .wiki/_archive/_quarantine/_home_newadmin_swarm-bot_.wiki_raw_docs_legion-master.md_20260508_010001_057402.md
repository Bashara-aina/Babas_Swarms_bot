---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/raw/docs/legion-master.md",
  "reason": "daily_fast_scan: verdict=REJECT, score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-05-08T01:00:01.057434"
}
---

---
title: Legion Master
type: reference
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- docs
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Paste this into OpenCode to start any session:'
wikilinks: []
confidence: medium
source: research
---
# LEGION MASTER PROMPT
# The single file to paste into OpenCode for every session.
# Supersedes: AUDIT_NOW.md, LEGION_CLAWCODE_UPGRADE.md, LEGION_MCP_SKILLS_MASTER.md
# Last updated: 2026-04-12 v2

---

## HOW TO USE THIS FILE

Paste this into OpenCode to start any session:
```
Read LEGION_MASTER.md fully from top to bottom before touching any code.
Then read CLAUDE.md and SOUL.md.
Then execute the CURRENT SESSION TASK at the bottom of this file.
Do not skip any section. Every part is load-bearing context.
```

---

# ──────────────────────────────────────────────────
# PART 1 — WHO LEGION IS
# ──────────────────────────────────────────────────

Legion is Bashara's permanent AI coworker. Not a chatbot. Not an assistant.
Bashara = Data Science Master's student, Shibaura Institute of Technology, Tokyo (Narita, Chiba).
Machine: Ubuntu Linux, RTX 3060, 64GB RAM, 5TB storage.
Interface: Telegram (iPhone) ONLY.
Framework: aiogram 3.4+ (fully async)
LLM routing: litellm 1.57+ via OpenRouter + direct provider fallbacks
Deployment: systemd service (swarm-bot.service)

Bashara's active projects (Legion knows all of these deeply):
- Babas_Swarms_bot — Legion itself (this repo)
- rumahlabuh.com — Indonesian property rental platform (Next.js + Supabase + Midtrans)
- cekwajar.id — Indonesian wage/salary fairness tool (Next.js + Supabase)
- POPW thesis — assembly action recognition (ResNet-50, FPN, FiLM conditioning, Kendall MTL)
- ADB scholarship via Keio University nomination

Legion's personality (enforced by core/character_enforcer.py):
- NEVER says: "Certainly!", "Great!", "Sure!", "Of course!", "Absolutely!",
  "I'd be happy to", "As an AI"
- Language: Indonesian or English — matches Bashara's message language
- Tone: direct, technically precise, dry humor when appropriate
- Debates when Bashara is wrong — never agrees just to agree
- Short message = short reply. Deep question = depth.
- SOUL.md is Legion's living identity — read it at every boot and every session

---

# ──────────────────────────────────────────────────
# PART 2 — WHAT LEGION CAN DO TODAY (verified capabilities)
# ──────────────────────────────────────────────────

## 2.1 MEDIA FILES (sent directly via Telegram)

### ✅ SUPPORTED:
| Type | How | File |
|------|-----|------|
| Photos/Images | Vision: MiniMax or Ollama Gemma3/llava (local GPU) | handlers/media_tools.py |
| Voice notes | Transcribe: faster-whisper (GPU) > Groq Whisper > openai-whisper | handlers/voice.py |
| Audio files | Same pipeline as voice | handlers/voice.py |
| PDF | pdfplumber/PyPDF2; Tesseract OCR for scanned | tools/documents.py |
| DOCX | python-docx extraction | multimodal_processor.py |
| Excel (.xlsx) | openpyxl read/write | tools/documents.py |
| Plain text / TXT | Direct UTF-8 decode | multimodal_processor.py |
| Image OCR | pytesseract | tools/documents.py |
| Image generation | MiniMax API via /imagine | handlers/media_tools.py |
| Text-to-Speech | Kokoro-ONNX (local) or edge-tts (cloud) | multimodal_processor.py |

### ❌ MISSING — implement this session:
| Type | Fix needed |
|------|------------|
| Video files (.mp4, .mov) | Add F.video handler + ffmpeg + faster-whisper pipeline |
| CSV | Add to tools/documents.py dispatcher |
| PPTX | Add python-pptx to tools/documents.py |
| EPUB | Add ebooklib to tools/documents.py |
| RTF / ODT | Add striprtf / odfpy |
| Wiki file upload | wiki_handler.py:41 explicitly says "not yet implemented" |

### VIDEO FILE IMPLEMENTATION (paste directly into handlers/media_tools.py):
```python
@router.message(F.video | F.video_note)
async def handle_video(message: Message):
    if message.from_user.id != ALLOWED_USER_ID:
        return
    await message.answer("🎬 Analyzing video...")
    file = message.video or message.video_note
    file_info = await message.bot.get_file(file.file_id)
    file_path = f"/tmp/legion/video_{file.file_id}.mp4"
    await message.bot.download_file(file_info.file_path, file_path)
    from core.shell.sandbox import run_sandboxed
    frames_dir = f"/tmp/legion/frames_{file.file_id}"
    audio_path = f"/tmp/legion/audio_{file.file_id}.mp3"
    await run_sandboxed(f"mkdir -p {frames_dir} && ffmpeg -i {file_path} -vf fps=1 {frames_dir}/frame_%04d.jpg -y")
    await run_sandboxed(f"ffmpeg -i {file_path} -vn -acodec mp3 {audio_path} -y")
    from handlers.voice import transcribe_audio
    transcript = await transcribe_audio(audio_path)
    import os, base64
    from llm_client import chat
    frame_descs = []
    for fname in sorted(os.listdir(frames_dir))[:5]:
        with open(f"{frames_dir}/{fname}", "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        desc = await chat("vision", [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": "Describe this video frame briefly."}
        ]}])
        frame_descs.append(desc)
    summary = await chat("analyst", [{"role": "user", "content":
        f"Transcript: {transcript}\nFrames: {' | '.join(frame_descs)}\nSummarize this video."
    }])
    await message.answer(summary, parse_mode="HTML")
    await run_sandboxed(f"rm -rf {frames_dir} {file_path} {audio_path}")
# Requires: sudo apt install ffmpeg
```

### CSV / PPTX / EPUB IMPLEMENTATION (add to tools/documents.py dispatcher):
```python
elif ext == ".csv":
    import csv, io
    content = data.decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    return f"CSV: {len(rows)} rows, cols: {', '.join(reader.fieldnames or [])}\n{rows[:5]}"
elif ext == ".pptx":
    from pptx import Presentation
    prs = Presentation(io.BytesIO(data))
    return "\n".join(s.text_frame.text for sl in prs.slides for s in sl.shapes if s.has_text_frame)
elif ext == ".epub":
    import ebooklib; from ebooklib import epub; from bs4 import BeautifulSoup
    book = epub.read_epub(io.BytesIO(data))
    return "\n".join(BeautifulSoup(i.get_content(),"html.parser").get_text()
                     for i in book.get_items_of_type(ebooklib.ITEM_DOCUMENT))[:5000]
# Add to requirements.txt: python-pptx>=0.6.21, ebooklib>=0.18
```

---

## 2.2 LINK UNDERSTANDING (URLs pasted into Telegram chat)

### ✅ WORKING:
| Link Type | How | Command |
|-----------|-----|----------|
| GitHub repos | README fetch + trending analysis + deep-dive | /github_intel or auto-route |
| arXiv papers | PDF download + extraction + Q&A | /paper or /ask_paper |
| Any general URL | Playwright headless Chromium — JS-rendered, full page + screenshot | /scrape <url> |
| Research topic | Multi-page deep research, synthesized | /research <topic> |
| URL in message body | _URL_RE regex extracts URL, LLM classifies routing | TaskRouter auto-detect |

### ⚠️ PARTIAL / LIMITED:
| Type | Issue |
|------|-------|
| TikTok / Reels / Short video links | Page text scraped (title, description, DOM), but NO video content understanding |
| Shopee / Tokopedia / Amazon | Works if server-side rendered; JS SPAs may fail or return partial content |
| LinkedIn | Actively blocked by anti-bot measures — will fail |
| Bare URL with no context | TaskRouter keyword_task_type() returns None for short URLs — falls to chat |

### ❌ NOT SUPPORTED:
- Actual video content inside links (TikTok, YouTube, Instagram Reels)
- LinkedIn (blocked platform-side)
- Heavy JS SPAs on marketplace sites (intermittent)

### FIX 1: VIDEO LINKS — yt-dlp integration (tools/video.py)
```python
# Install: pip install yt-dlp && sudo apt install ffmpeg
# Supports: YouTube, TikTok, Instagram, Twitter/X, Reddit, 1500+ platforms

import yt_dlp, os
from handlers.voice import transcribe_audio
from llm_client import chat

async def understand_video_url(url: str) -> str:
    """Download video from URL and return transcript + visual summary."""
    out_dir = "/tmp/legion"
    os.makedirs(out_dir, exist_ok=True)
    ydl_opts = {
        "outtmpl": f"{out_dir}/%(id)s.%(ext)s",
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(info)
            title = info.get("title", "")
            description = info.get("description", "")[:500]
            uploader = info.get("uploader", "")
            duration = info.get("duration", 0)
    except Exception as e:
        return f"[Video download failed: {e}]"

    # Transcribe audio using existing faster-whisper pipeline
    transcript = await transcribe_audio(audio_path)

    # Summarize
    summary = await chat("analyst", [{"role": "user", "content":
        f"Video: {title} by {uploader} ({duration}s)\n"
        f"Description: {description}\n"
        f"Transcript: {transcript[:3000]}\n"
        f"Summarize what this video is about in 3-4 sentences."
    }])

    # Cleanup
    try: os.remove(audio_path)
    except: pass

    return f"🎥 <b>{title}</b> ({uploader})\n\n{summary}"
```

### FIX 2: JS SPA SCRAPING — Replace browser_agent.py with Crawl4AI
```python
# Install: pip install crawl4ai && crawl4ai-setup
# Crawl4AI renders JS, returns LLM-ready markdown, has anti-bot evasion built in
# 61k+ GitHub stars, async-native Python, perfect for Legion

from crawl4ai import AsyncWebCrawler

async def smart_scrape(url: str, question: str = "") -> str:
    """Scrape any URL including JS-heavy SPAs. Returns clean markdown."""
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(
            url=url,
            word_count_threshold=10,
            bypass_cache=True,
        )
    content = result.markdown[:4000]
    if question:
        from llm_client import chat
        answer = await chat("researcher", [{"role": "user",
            "content": f"Page content:\n{content}\n\nQuestion: {question}"}])
        return answer
    return content
# Install: pip install crawl4ai && crawl4ai-setup
```

### FIX 3: URL AUTO-ROUTING — Add to core/intent_router.py
```python
# Add at TOP of classify() method, before any keyword matching:
import re
from urllib.parse import urlparse
_URL_RE = re.compile(r"https?://[^\s]+")

def _classify_url(text: str):
    match = _URL_RE.search(text)
    if not match:
        return None
    domain = urlparse(match.group()).netloc.lower().removeprefix("www.")
    VIDEO_DOMAINS = {"youtube.com", "youtu.be", "tiktok.com",
                     "instagram.com", "twitter.com", "x.com",
                     "reddit.com", "vimeo.com"}
    if any(d in domain for d in VIDEO_DOMAINS):
        return IntentResult(intent="video_url", confidence=0.95, url=match.group())
    if "arxiv.org" in domain:
        return IntentResult(intent="paper_analysis", confidence=0.95, url=match.group())
    if "github.com" in domain:
        return IntentResult(intent="github_intel", confidence=0.95, url=match.group())
    if any(d in domain for d in ["shopee", "tokopedia", "amazon", "lazada"]):
        return IntentResult(intent="product_research", confidence=0.85, url=match.group())
    # Generic URL — scrape it
    return IntentResult(intent="web_scrape", confidence=0.80, url=match.group())

# In classify():
url_result = _classify_url(text)
if url_result:
    return url_result
# ... rest of existing classification logic
```

### FIX 4: LinkedIn — Realistic approach
```
LinkedIn actively blocks all scrapers. Open-source solutions get banned within days.
Only reliable option: Proxycurl API (https://nubela.co/proxycurl)
  - Free tier: 10 credits/month (enough for occasional profile lookups)
  - Add PROXYCURL_API_KEY to .env
  - Add as optional skill with graceful fallback message if key not set
Do NOT waste time building a scraper — it will break.
```

---

## 2.3 COMMANDS (what Bashara can send in Telegram)

### Slash commands — confirmed working:
```
/start /help /status          — system.py
/run /think /agent            — ai.py
/screen /do /cmd              — computer.py (sandbox gated)
/remember /recall /forget     — memory_commands.py
/memories /briefing /learn    — brain.py
/debate /opinion              — debate_handlers.py (✅ Apr 2026)
/emails /calendar             — communications.py (Composio)
/budget /soul                 — admin_handlers.py (✅ Apr 2026)
/vcsearch                     — voice.py (✅ Apr 2026)
/legion_sessions              — sessions.py (✅ renamed Apr 2026)
/imagine                      — media_tools.py
/scrape <url>                 — browser_agent.py (Playwright)
/paper <arxiv_url>            — arxiv handler
/research <topic>             — multi-page deep research
/github_intel <repo>          — GitHub specialized handler
```

### Natural language (no slash needed — after Skills upgrade):
```
"cek seo rumahlabuh"          → web_audit skill
"restart legion"              → service_restart skill
"gpu lagi training ga"        → gpu_training_status skill
"pusing nih"                  → emotion_modulator → empathy (no bullet list)
"cari paper FPN"              → arxiv_search skill
https://tiktok.com/...        → video_url intent → yt-dlp + transcribe
https://shopee.com/...        → product_research → Crawl4AI scrape
```

---

# ──────────────────────────────────────────────────
# PART 3 — CURRENT IMPLEMENTATION STATUS
# ──────────────────────────────────────────────────

## 63% complete as of 2026-04-12 (12/19 CLAUDE.md tasks)

### ✅ CONFIRMED DONE — do not redo:
- P0-1: /debate registered in main.py
- P0-2: /cmd asyncio.wait_for(timeout=30) — already existed
- P0-3: core/ruflo_manager.py created — needs 2-line main.py wire
- P1-1: /vcsearch added to voice.py
- P1-2: /sessions renamed to /legion_sessions
- P1-3: MCP stub removed from legion_extras.py
- P1-4: browser-use==0.1.21 pinned in requirements.txt
- P1-5: langchain-community added to requirements.txt
- P2-3: handlers/admin_handlers.py with /budget
- P2-4: handlers/admin_handlers.py with /soul
- P3-1: .github/workflows/legion-ci.yml created
- P3-2: tests/test_main.py created

### ❌ STILL OPEN:

CRITICAL:
- P0-4: parse_mode="Markdown" → HTML (186 files)
  Start: grep -rn 'parse_mode="Markdown"' handlers/
  Fix all hits. Then full codebase sweep.

HIGH:
- P0-3: Wire ruflo_manager.py into main.py (2 lines — see IMPLEMENTATION_STATUS.md)
- Budget gates on ALL background tasks (daily_briefing.py, composio_hub.py)
- Delete dead dirs if still exist: core/memory_old/, core/orchestration_old/, core/reliability_old/
- tests/test_system_prompt_builder.py::test_soul_is_first_section — missing

MEDIUM:
- P2-1: Migrate swarm logic main.py → swarm.py
- P2-2: Move /run /think ai.py → agent.py
- P3-3: ARCHITECTURE.md
- P3-4: docs/MIGRATION.md
- P3-5/6: Inline comments in main.py and agent.py

---

# ──────────────────────────────────────────────────
# PART 4 — CLAWCODE UPGRADE PLAN
# ──────────────────────────────────────────────────

Legion has a soul. ClawCode has a body. This plan gives Legion ClawCode's body.
Full code in LEGION_CLAWCODE_UPGRADE.md.

### PHASE 1 — Foundation (do today)

| Upgrade | File | Problem | Fix | Time |
|---------|------|---------|-----|------|
| U1: Session Transcripts | core/session/transcript.py | Restart = full amnesia | SQLite-backed history via aiosqlite | 30min |
| U2: Sandboxed Shell | core/shell/sandbox.py | Raw subprocess. No safety. | Blacklist guard + allowed paths | 20min |
| U3: Budget Gates | daily_briefing.py, composio_hub.py | Background tasks bypass budget | 3-line BudgetManager.can_spend() check | 20min |
| U4: Proactive Dedup | core/proactive/curiosity_engine.py | Same message 5x in 2 hours | 9-message pool + 4h cooldown | 15min |

Proactive pool (implement exactly):
```python
CHECKIN_POOL = [
    "Lo baik-baik aja?",
    "Masih hidup? Kasih kabar dong.",
    "Eh, lagi ngapain?",
    "Sunyi banget dari lo tadi.",
    "Ada yang lagi lo pikirin?",
    "Halo. Lagi stuck atau emang sengaja ghosting?",
    None, None, None,  # 33% chance: send nothing at all
]
```

### PHASE 2 — Architecture (next session)
| Upgrade | File | Time |
|---------|------|------|
| U5: Skills Registry | core/skills/ | 2h |
| U6: Prompt Injection Protection | tools/browser_agent.py | 30min |
| U7: Heartbeat Daemon | core/heartbeat/daemon.py | 1.5h |

### PHASE 3 — Integration (next week)
| Upgrade | File | Time |
|---------|------|------|
| U8: Webhook Listener | core/webhooks/ | 2h |
| U9: MCP Backbone | core/mcp/ | 3h |

---

# ──────────────────────────────────────────────────
# PART 5 — THE 30 SKILLS (Phase 2)
# ──────────────────────────────────────────────────

Full implementation code in LEGION_MCP_SKILLS_MASTER.md.

| Cat | Skill | Trigger examples | Needs |
|-----|-------|-----------------|-------|
| A | web_audit | "cek seo", "pagespeed", "audit website" | Google PageSpeed API (free) |
| A | url_check | "website down", "cek hidup ga" | aiohttp (no key) |
| A | web_scrape | "buka link ini", "summarize artikel" | Crawl4AI |
| B | web_search | "cari", "search", "googling" | Brave Search API (free) |
| B | arxiv_search | "cari paper", "thesis reference" | Free arXiv API |
| B | summarize_url | "tldr", "ringkas ini" | Crawl4AI + LLM |
| B | hacker_news | "hn", "berita tech" | Free HN API |
| B | video_url | TikTok/YouTube/IG link pasted | yt-dlp + faster-whisper |
| C | github_pr_status | "open prs", "cek pr" | GITHUB_TOKEN (existing) |
| C | github_commit_log | "latest commits", "apa yang dipush" | GITHUB_TOKEN |
| C | code_review | "review kode ini", "cek bug" | reviewer agent |
| D | system_health | "cek server", "gpu status", "ram berapa" | nvidia-smi (local) |
| D | service_status | "legion running ga", "cek nginx" | systemctl |
| D | service_restart | "restart legion", "restart nginx" | systemctl (elevated) |
| D | run_shell | "jalanin", "execute" | sandbox.py |
| E | remember | "inget ini", "catat", "simpan" | memory_manager |
| E | recall | "inget ga", "lo pernah simpen" | memory_manager |
| E | obsidian_write | "tulis di obsidian", "buat catetan" | Obsidian MCP |
| F | weather | "cuaca", "hujan ga" | OpenWeatherMap (free) |
| F | translate | "translate", "artinya apa", "bahasa jepang" | LibreTranslate (free) |
| F | timer | "set timer", "ingetin gw" | asyncio (no key) |
| G | rumahlabuh_status | "cek rumahlabuh", "ada inquiry baru" | Supabase |
| G | thesis_status | "thesis gimana", "deadline kapan" | memory recall |
| G | cekwajar_status | "cek cekwajar" | Supabase |
| G | gpu_training_status | "training gimana", "loss berapa" | nvidia-smi + log |
| G | adb_scholarship | "adb gimana", "beasiswa deadline" | memory recall |
| H | screenshot | existing computer_agent handler | — |
| H | analyze_screen | screenshot + vision | vision agent |
| H | screen_text | screenshot + OCR | pytesseract |

---

# ──────────────────────────────────────────────────
# PART 6 — MCP SERVERS (Phase 3)
# ──────────────────────────────────────────────────

Full connection code in LEGION_MCP_SKILLS_MASTER.md. Start free, expand later.

| # | Server | Cost | .env flag | Skill it powers |
|---|--------|------|-----------|------------------|
| 1 | Brave Search | Free | MCP_BRAVE_ENABLED | web_search |
| 2 | GitHub MCP | Free | MCP_GITHUB_ENABLED | github_* skills |
| 3 | Filesystem MCP | Free | MCP_FILESYSTEM_ENABLED | run_shell |
| 4 | Obsidian MCP | Free | MCP_OBSIDIAN_ENABLED | obsidian_write |
| 5 | Supabase MCP | Free | MCP_SUPABASE_ENABLED | rumahlabuh/cekwajar |
| 6 | Playwright/Crawl4AI | Free | MCP_BROWSER_ENABLED | web_audit, web_scrape |
| 7 | mem0 MCP | Paid | MCP_MEMORY_ENABLED | remember, recall |
| 8 | Ahrefs | Paid | MCP_AHREFS_ENABLED | web_audit enhanced |
| 9 | Notion | Free | MCP_NOTION_ENABLED | notes |
| 10 | Google Workspace | OAuth | MCP_GOOGLE_ENABLED | briefing, calendar |

---

# ──────────────────────────────────────────────────
# PART 7 — IRON RULES (CLAUDE.md summary — never violate)
# ──────────────────────────────────────────────────

1. ALL LLM calls → llm_client.chat() only. Never call litellm directly.
2. ALL memory writes → core/memory/memory_manager.py only. Never write to stores directly.
3. ALL shell execution → core/shell/sandbox.py run_sandboxed() only.
4. NEVER parse_mode="Markdown" — HTML only. Escape user content with html.escape().
5. NEVER threading or time.sleep() — asyncio only.
6. NEVER hardcode TELEGRAM_BOT_TOKEN or ALLOWED_USER_ID — os.getenv() always.
7. ALWAYS check ALLOWED_USER_ID before processing any command or message.
8. SOUL context MUST be section 0 in system_prompt_builder.py — before everything.
9. ALL background LLM tasks must call BudgetManager.can_spend() before any API call.
10. NEVER touch _old suffix files or dirs — dead code, delete references only.
11. Long messages: chunk at 4000 chars using split_and_send() from handlers/shared.py.
12. New module = new test in tests/ — not optional.

---

# ──────────────────────────────────────────────────
# PART 8 — SMOKE TESTS (run before AND after every session)
# ──────────────────────────────────────────────────

```bash
# Always run before starting
python -c "from core.soul_engine import build_soul_context; print(build_soul_context()[:80])"
python -c "from core.intent_router import IntentRouter; r=IntentRouter(); print(r.classify('write me code'))"
python -c "from core.system_prompt_builder import build_full_system_prompt; print(build_full_system_prompt('test')[:100])"
python -c "from core.character_enforcer import enforce_character; print(enforce_character('Certainly! Great!'))"

# After sandbox implemented
python -c "import asyncio; from core.shell.sandbox import run_sandboxed; print(asyncio.run(run_sandboxed('echo ok')))"

# After transcript implemented
python -c "import asyncio; from core.session.transcript import TRANSCRIPT; asyncio.run(TRANSCRIPT.init()); print('Transcript OK')"

# After skills implemented
python -c "
from core.skills import builtin
from core.skills.registry import SKILL_REGISTRY
print(f'Skills: {len(SKILL_REGISTRY._skills)}')
"

# After yt-dlp added
python -c "import yt_dlp; print('yt-dlp OK:', yt_dlp.version.__version__)"

# After Crawl4AI added
python -c "from crawl4ai import AsyncWebCrawler; print('Crawl4AI OK')"

# Full suite
pytest tests/ -x --asyncio-mode=auto -q
```

---

# ──────────────────────────────────────────────────
# PART 9 — DEFINITION OF DONE (Legion 10/10)
# ──────────────────────────────────────────────────

Legion is done when all of these work without a slash command:

- "pusing nih" at midnight → one sentence reply, like a friend. No bullet list.
- "cek seo rumahlabuh" → web_audit fires, returns real PageSpeed score.
- Restart swarm-bot.service → Legion resumes with last 20 turns. Zero amnesia.
- Silence for 8 hours → one varied check-in, different phrasing, then 4h quiet.
- GitHub PR merged at 3am → webhook fires, briefing summary in morning.
- Send .mp4 video file → frames extracted, audio transcribed, summary returned.
- Paste TikTok link → yt-dlp downloads, faster-whisper transcribes, summary returned.
- Paste Shopee link → Crawl4AI renders JS page, product info extracted cleanly.
- Send .csv file → columns shown, 5-row preview, analysis offered.
- "training gimana" → nvidia-smi parsed, loss from log, ETA returned.

---

# ──────────────────────────────────────────────────
# ► CURRENT SESSION TASK — EDIT THIS SECTION EACH SESSION
# ──────────────────────────────────────────────────

## SESSION 2026-04-12 — PHASE 1 COMPLETE

Run baseline smoke tests first. Then do steps in order.

### STEP 1: parse_mode fix (P0-4) — 30min
```bash
grep -rn 'parse_mode="Markdown"' handlers/
```
Change every hit to parse_mode="HTML". Add html.escape() around user-sourced content.
Verify: grep -rn 'parse_mode="Markdown"' . → 0 results.

### STEP 2: Wire ruflo_manager (P0-3) — 5min
Add 2 lines to main.py. Exact location in IMPLEMENTATION_STATUS.md.

### STEP 3: Budget gates (P1-1) — 15min
Add BudgetManager.can_spend() to: core/proactive/daily_briefing.py, tools/composio_hub.py
Also add hard-stop in llm_client.chat() as final net:
```python
if BudgetManager.is_daily_cap_exceeded():
    return "[Budget cap reached. LLM paused until midnight JST.]"
```

### STEP 4: Session Transcripts (U1) — 30min
Create core/session/transcript.py (full code in LEGION_CLAWCODE_UPGRADE.md UPGRADE 2)
Wire: main.py on_startup() + handlers/ai.py (push/pull on every message)

### STEP 5: Sandboxed Shell (U2) — 20min
Create core/shell/sandbox.py (full code in LEGION_CLAWCODE_UPGRADE.md UPGRADE 5)
Replace raw subprocess in: handlers/shared.py, computer_agent.py

### STEP 6: Proactive dedup (U4) — 15min
Update core/proactive/curiosity_engine.py with CHECKIN_POOL + 4h cooldown
(full code in LEGION_CLAWCODE_UPGRADE.md UPGRADE 9)

### STEP 7: Install new dependencies — 5min
```bash
pip install yt-dlp crawl4ai python-pptx ebooklib
crawl4ai-setup
sudo apt install ffmpeg
```
Add to requirements.txt:
```
yt-dlp>=2026.1.0
crawl4ai>=0.4.0
python-pptx>=0.6.21
ebooklib>=0.18
```

### STEP 8: Video file handler (Part 2.1) — 20min
Add F.video handler to handlers/media_tools.py
Full code in Part 2.1 above (VIDEO FILE IMPLEMENTATION block)

### STEP 9: CSV / PPTX / EPUB in documents.py — 15min
Add to tools/documents.py dispatcher
Full code in Part 2.1 above (CSV/PPTX/EPUB IMPLEMENTATION block)

### STEP 10: Video URL + URL routing fix — 30min
Create tools/video.py with understand_video_url() — full code in Part 2.2 FIX 1
Replace browser_agent.py scrape with Crawl4AI — full code in Part 2.2 FIX 2
Add URL auto-routing to core/intent_router.py — full code in Part 2.2 FIX 3

### STEP 11: Update docs — 10min
Update IMPLEMENTATION_STATUS.md with all completed steps from this session.
Update CLAUDE.md Section 9 to mark completed P-items.
Update this file's CURRENT SESSION TASK with next session's tasks.

### STEP 12: Full test run
```bash
pytest tests/ -x --asyncio-mode=auto -q
```
All tests must pass. Fix anything that breaks.

---

*Single source of truth for all OpenCode sessions.*
*Edit ONLY the CURRENT SESSION TASK block between sessions.*
*OpenCode updates IMPLEMENTATION_STATUS.md and CLAUDE.md at session end.*
