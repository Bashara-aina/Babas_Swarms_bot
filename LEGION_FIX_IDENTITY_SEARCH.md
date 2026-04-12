# LEGION FIX: IDENTITY + SEARCH + LANGUAGE
# Fix three critical failures shown in the Telegram screenshot.
# Last updated: 2026-04-12

---

## ► PASTE INTO OPENCODE

```
Read LEGION_FIX_IDENTITY_SEARCH.md fully.
Then read SOUL.md, CLAUDE.md, LEGION_MASTER.md, and core/system_prompt_builder.py.
Then execute the THREE FIX PLANS in order. Do not skip any.
Run the verification tests at the end of each fix.
```

---

# DIAGNOSIS — WHAT THE SCREENSHOT PROVES

Bashara asked: "Bisa cari info bashara aina tuh siapa ga?"
Legion responded with:
1. ❌ No idea who Bashara Aina is — .wiki is NOT being injected
2. ❌ "Btw, ini kamu好奇 soal..." — Chinese characters leaked into response
3. ❌ No web search attempted — Legion doesn't know, doesn't look it up

Three separate bugs. Three separate fixes.

---

# ─────────────────────────────────────────
# FIX 1: .wiki NOT INJECTED — Legion amnesia about Bashara
# ─────────────────────────────────────────

## ROOT CAUSE
Find it first. Open core/system_prompt_builder.py and grep for .wiki:
```bash
grep -rn "\.wiki" core/
grep -rn "wiki" core/system_prompt_builder.py
grep -rn "wiki" main.py
grep -rn "MASTER-INTELLIGENCE" .
grep -rn "inject_wiki\|load_wiki\|wiki_context\|wiki_loader" .
```

Expected finding: .wiki/ exists with rich content BUT it is never loaded
or injected into the system prompt. The connection is broken or was never built.

## THE FIX

### Step 1A: Create core/wiki_loader.py

```python
"""
Wiki Loader — reads .wiki/ markdown files and builds Legion's knowledge context.
This is Legion's second brain. It MUST be injected every session.
"""
import os
import re
from pathlib import Path
from functools import lru_cache
from typing import Optional

WIKI_DIR = Path(".wiki")

# Priority files — always injected, full content
PRIORITY_FILES = [
    ".wiki/MASTER-INTELLIGENCE.md",
    ".wiki/00-meta",
    ".wiki/profiles",
    ".wiki/06-legion-instructions",
]

# Token budget for wiki injection (adjust based on model context window)
WIKI_TOKEN_BUDGET = 4000  # ~4000 tokens = ~16000 chars


@lru_cache(maxsize=1)
def load_wiki_context(max_chars: int = WIKI_TOKEN_BUDGET * 4) -> str:
    """
    Load .wiki/ content into a single string for system prompt injection.
    Priority files first, then remaining markdown files up to budget.
    Cached to avoid re-reading on every message.
    """
    if not WIKI_DIR.exists():
        return "[WIKI: .wiki/ directory not found]"

    sections = []
    chars_used = 0
    loaded_files = set()

    # === PRIORITY: MASTER-INTELLIGENCE.md ===
    master = WIKI_DIR / "MASTER-INTELLIGENCE.md"
    if master.exists():
        content = master.read_text(encoding="utf-8", errors="ignore")
        sections.append(f"# CORE KNOWLEDGE\n{content}")
        chars_used += len(content)
        loaded_files.add(str(master))

    # === PRIORITY: profiles/ (who Bashara is) ===
    profiles_dir = WIKI_DIR / "profiles"
    if profiles_dir.exists():
        for f in sorted(profiles_dir.glob("*.md")):
            if chars_used >= max_chars:
                break
            content = f.read_text(encoding="utf-8", errors="ignore")
            sections.append(f"# PROFILE: {f.stem}\n{content}")
            chars_used += len(content)
            loaded_files.add(str(f))

    # === PRIORITY: 06-legion-instructions/ ===
    legion_dir = WIKI_DIR / "06-legion-instructions"
    if legion_dir.exists():
        for f in sorted(legion_dir.glob("*.md")):
            if chars_used >= max_chars:
                break
            content = f.read_text(encoding="utf-8", errors="ignore")
            sections.append(f"# LEGION INSTRUCTION: {f.stem}\n{content}")
            chars_used += len(content)
            loaded_files.add(str(f))

    # === REMAINING: all other .md files ===
    for md_file in sorted(WIKI_DIR.rglob("*.md")):
        if chars_used >= max_chars:
            break
        if str(md_file) in loaded_files:
            continue
        if any(skip in str(md_file) for skip in [".obsidian", "_archive", "_quarantine"]):
            continue
        try:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            if not content.strip():
                continue
            rel_path = md_file.relative_to(WIKI_DIR)
            sections.append(f"# WIKI/{rel_path}\n{content}")
            chars_used += len(content)
            loaded_files.add(str(md_file))
        except Exception:
            continue

    if not sections:
        return "[WIKI: no content found in .wiki/]"

    return "\n\n---\n\n".join(sections)


def invalidate_wiki_cache():
    """Call this when .wiki files are updated during runtime."""
    load_wiki_context.cache_clear()


def get_bashara_identity_context() -> str:
    """
    Returns a minimal guaranteed-injected block about Bashara.
    Used as fallback if full wiki context is too large.
    This MUST always be in the system prompt.
    """
    return """
## WHO IS BASHARA?
Bashara Aina is the owner of this bot. You are his personal AI assistant.
- Full name: Bashara Aina
- Location: Narita, Chiba, Japan (PhD/Master's student at Shibaura Institute of Technology)
- Nationality: Indonesian
- Active projects: cekwajar.id (Indonesian wage verification SaaS), rumahlabuh.com (property rental platform Indonesia), this Legion bot (Babas_Swarms_bot), computer vision thesis (assembly action recognition)
- Communication: Indonesian (primary), English (technical), mixes both freely
- Style: casual Indonesian slang + technical depth. "pusing", "gw", "lo", "cek", "nanti"
- When Bashara asks about himself: confirm you know who he is, then answer from wiki knowledge
- NEVER say "Bashara Aina tidak ada di dataset saya" — he is your owner and master
""".strip()
```

### Step 1B: Wire into core/system_prompt_builder.py

Find the function that builds the system prompt (likely `build_system_prompt` or
`build_full_system_prompt` or `get_system_prompt`). Add wiki injection:

```python
# Add at top of file:
from core.wiki_loader import load_wiki_context, get_bashara_identity_context

# Inside the system prompt builder function, add BEFORE task context:
def build_full_system_prompt(user_message: str = "", **kwargs) -> str:
    parts = []

    # 1. SOUL (existing — keep it)
    soul = load_soul()  # whatever the existing call is
    parts.append(soul)

    # 2. BASHARA IDENTITY — always injected, guaranteed
    parts.append(get_bashara_identity_context())

    # 3. WIKI CONTEXT — second brain
    wiki = load_wiki_context()
    if wiki and "not found" not in wiki:
        parts.append(f"## LEGION'S KNOWLEDGE BASE (from .wiki/)\n{wiki}")

    # 4. existing task context, memory, tools (keep whatever was here)
    # ... rest of existing code ...

    return "\n\n".join(parts)
```

### Step 1C: Verification test

```python
from core.wiki_loader import load_wiki_context, get_bashara_identity_context
from core.system_prompt_builder import build_full_system_prompt

# Test 1: Wiki loads
wiki = load_wiki_context()
assert len(wiki) > 100, f"Wiki empty or failed: {wiki[:200]}"
assert "MASTER-INTELLIGENCE" in wiki or "Bashara" in wiki, "Wiki missing key content"
print(f"✅ Wiki loaded: {len(wiki)} chars")

# Test 2: Identity context always present
identity = get_bashara_identity_context()
assert "Bashara Aina" in identity
assert "cekwajar" in identity
print("✅ Identity context correct")

# Test 3: System prompt contains wiki
prompt = build_full_system_prompt("siapa bashara aina?")
assert "Bashara Aina" in prompt, "Bashara not in system prompt!"
assert "cekwajar" in prompt or "KNOWLEDGE BASE" in prompt, "Wiki not injected!"
print("✅ System prompt contains Bashara identity and wiki")
print(f"✅ System prompt length: {len(prompt)} chars")
```

---

# ─────────────────────────────────────────
# FIX 2: CHINESE CHARACTERS — kill language contamination
# ─────────────────────────────────────────

## ROOT CAUSE
The model (likely a cheaper Chinese-origin LLM via OpenRouter) leaks its training
language when low-confidence. "好奇" = "curious" in Chinese. This happens because:
- No explicit language enforcement in system prompt
- Model trained primarily on Chinese data bleeds through on casual/uncertain phrases
- Character enforcer doesn't check for non-Latin/non-Indonesian characters

## THE FIX

### Step 2A: Add language enforcer to core/character_enforcer.py

```python
import re

# Detect CJK characters (Chinese/Japanese/Korean)
CJK_PATTERN = re.compile(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\u3400-\u4dbf]')

# Arabic script
ARABIC_PATTERN = re.compile(r'[\u0600-\u06ff]')

ALLOWED_SCRIPTS = [
    r'[a-zA-Z]',           # Latin (English)
    r'[\u00C0-\u024F]',   # Extended Latin (accented chars)
    r'[0-9]',             # Numbers
    r'[\u0020-\u007E]',   # Basic ASCII punctuation/symbols
    r'[\u2000-\u206F]',   # General punctuation
    r'[\u2600-\u26FF]',   # Emoji symbols
    r'[\U0001F300-\U0001F9FF]', # Emoji ranges
]

def has_non_allowed_script(text: str) -> bool:
    """Returns True if text contains CJK or Arabic characters."""
    return bool(CJK_PATTERN.search(text)) or bool(ARABIC_PATTERN.search(text))

def strip_non_allowed_script(text: str) -> str:
    """
    Remove CJK and Arabic characters from response.
    Replace with closest Indonesian equivalent if mapping known,
    otherwise remove the character.
    """
    # Common Chinese leaks and their Indonesian equivalents
    CJK_REPLACEMENTS = {
        '好奇': 'penasaran',
        '很好': 'bagus',
        '谢谢': 'terima kasih',
        '对': 'ya',
        '不': 'tidak',
        '是': 'iya',
        '的': '',
        '了': '',
        '吗': '?',
        '嗯': 'hmm',
        '哦': 'oh',
    }

    for cjk, replacement in CJK_REPLACEMENTS.items():
        text = text.replace(cjk, replacement)

    # Strip any remaining CJK/Arabic
    text = CJK_PATTERN.sub('', text)
    text = ARABIC_PATTERN.sub('', text)

    # Clean up double spaces from removals
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r' ([,\.!?])', r'\1', text)

    return text.strip()

def enforce_language(text: str) -> str:
    """Main enforcer — call this before sending any response to Telegram."""
    if has_non_allowed_script(text):
        fixed = strip_non_allowed_script(text)
        # Log the incident for monitoring
        import logging
        logging.warning(f"[LANGUAGE ENFORCER] Stripped non-allowed script. Before: {text[:100]}")
        return fixed
    return text
```

### Step 2B: Add language enforcement to SOUL.md system prompt

Add this block to the SOUL.md language section (or add it if missing):

```markdown
## LANGUAGE RULES (absolute, no exceptions)

1. ONLY use these languages: Indonesian (primary), English (technical terms)
2. NEVER output Chinese characters (汉字), Japanese kanji/kana, Korean hangul, Arabic script
3. If you feel a Chinese word, translate it to Indonesian before outputting
4. All responses to Bashara are in Indonesian unless he writes in English
5. Mixed Indonesian-English is fine and encouraged for technical topics
6. "好奇" must become "penasaran". "很好" must become "bagus". Always.
```

### Step 2C: Wire enforce_language into message sending pipeline

Find where bot sends messages to Telegram. Add enforcer as final step:

```python
# In handlers/shared.py or wherever send_message is defined:
from core.character_enforcer import enforce_language

async def send_message(bot, chat_id: int, text: str, **kwargs):
    # Enforce language BEFORE sending
    text = enforce_language(text)
    # ... existing send logic ...
```

### Step 2C: Also update model selection

Check .env.example and config/ for which model is used for casual conversation.
Chinese leakage typically comes from:
- `deepseek` models (Chinese company, leaks Chinese)
- `qwen` models (Alibaba, leaks Chinese)
- `yi` models (01.AI, leaks Chinese)

For casual conversation, replace with a model that has clean Indonesian output:

```bash
# In config or .env, find the routing model for casual/general tasks
# Replace any deepseek/qwen/yi model for Bashara-facing responses with:
# - claude-3-5-haiku (clean, cheap, Indonesian-capable)
# - gemini-flash-1.5 (fast, multilingual-clean)
# - meta-llama/llama-3.3-70b-instruct (clean multilingual)
```

GREP first to find offending model:
```bash
grep -rn "deepseek\|qwen\|yi-\|glm" config/ .env.example
```

### Step 2D: Verification test

```python
from core.character_enforcer import enforce_language, has_non_allowed_script

# Test: Chinese detected
assert has_non_allowed_script("ini kamu\u597d\u5947 soal") == True
assert has_non_allowed_script("halo bashara") == False

# Test: Chinese stripped and replaced
result = enforce_language("Btw, ini kamu\u597d\u5947 soal kompetitor?")
assert "\u597d\u5947" not in result
assert "penasaran" in result or "\u597d\u5947" not in result
print(f"✅ Chinese stripped: '{result}'")

# Test: Clean Indonesian not touched
clean = enforce_language("Bashara, cekwajar.id lagi bagus nih.")
assert clean == "Bashara, cekwajar.id lagi bagus nih."
print("✅ Clean Indonesian unchanged")
```

---

# ─────────────────────────────────────────
# FIX 3: NO WEB SEARCH — Legion must search before saying "tidak tahu"
# ─────────────────────────────────────────

## ROOT CAUSE
Legion currently:
1. Has a /research command but doesn't AUTO-TRIGGER it when it doesn't know something
2. Has no "I don't know → search first" logic in the response pipeline
3. Legion said "tidak tahu" about BASHARA HIMSELF — the owner.
   This is the worst possible failure mode.

## THE FIX

### Step 3A: Create core/self_awareness_gate.py

```python
"""
Self-Awareness Gate — checks if Legion is about to say "I don't know"
and triggers web search instead.

Before Legion sends any "tidak tahu" response, this gate intercepts
and routes to search tools automatically.
"""
import re
from typing import Optional

# Phrases that indicate Legion doesn't know something
IGNORANCE_SIGNALS = [
    "gak punya info",
    "tidak punya informasi",
    "tidak ada di",
    "belum familiar",
    "tidak ada dalam dataset",
    "gak ada di dataset",
    "tidak ada dalam pengetahuan",
    "belum tahu",
    "tidak tahu siapa",
    "tidak mengenal",
    "not in my",
    "don't have information",
    "no information about",
    "i don't know",
    "saya tidak tahu",
    "aku tidak tahu",
]

# Names/topics that MUST never trigger ignorance response
# because they are core context Legion MUST know
CORE_KNOWLEDGE_NAMES = [
    "bashara",
    "bashara aina",
    "cekwajar",
    "rumahlabuh",
    "legion",
    "babas",
]


def should_search_instead(response_draft: str, original_query: str) -> bool:
    """
    Returns True if Legion is about to say it doesn't know something
    and should search instead.
    """
    response_lower = response_draft.lower()
    query_lower = original_query.lower()

    # If about to admit ignorance
    is_ignorant = any(signal in response_lower for signal in IGNORANCE_SIGNALS)

    if not is_ignorant:
        return False

    # Critical: if asking about Bashara/core topics — ALWAYS search
    if any(name in query_lower for name in CORE_KNOWLEDGE_NAMES):
        return True

    # If query contains "siapa", "cari info", "cari tau" — search intent
    search_intent_keywords = [
        "siapa", "cari info", "cari tau", "cari tahu",
        "who is", "find info", "search for", "find out",
        "kesan", "review", "opinion about"
    ]
    if any(kw in query_lower for kw in search_intent_keywords):
        return True

    return False


def get_search_trigger_message(original_query: str) -> str:
    """
    Returns a message to send to Telegram while search is running.
    Natural, not robotic.
    """
    return f"🔍 Lagi cari info..."


def build_search_query_from_message(message: str) -> str:
    """
    Converts user message to a web search query.
    """
    # Remove common filler
    query = message.strip()
    for filler in ["bisa", "coba", "tolong", "dong", "ga", "gak", "ya", "nih"]:
        query = re.sub(rf'\b{filler}\b', '', query, flags=re.IGNORECASE)

    # Common patterns
    patterns = [
        (r'cari info (.+) tuh siapa', r'\1 adalah siapa profil'),
        (r'siapa (?:itu |tuh )?(.+)', r'profil \1 Indonesia'),
        (r'kesan orang ke (.+)', r'\1 review pendapat orang'),
        (r'cari info (.+)', r'\1'),
    ]

    for pattern, replacement in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            return re.sub(pattern, replacement, query, flags=re.IGNORECASE).strip()

    return query.strip()
```

### Step 3B: Wire into the response pipeline

Find where Legion generates and sends responses (likely in task_orchestrator.py
or handlers/message_handler.py or core/response_pipeline.py).

Add the search gate BEFORE sending any response:

```python
from core.self_awareness_gate import should_search_instead, get_search_trigger_message, build_search_query_from_message
from tools.web_search import search_web  # or wherever web search tool is

async def process_and_respond(message: str, chat_id: int, bot, **ctx):
    # ... existing response generation ...
    response_draft = await generate_response(message, **ctx)

    # GATE: intercept ignorance responses
    if should_search_instead(response_draft, message):
        # 1. Tell Bashara we're searching
        await bot.send_message(chat_id, get_search_trigger_message(message))

        # 2. Build and run search
        search_query = build_search_query_from_message(message)
        search_results = await search_web(search_query)

        # 3. Re-generate response with search results as context
        enriched_context = f"Web search results for '{search_query}':\n{search_results}"
        response_draft = await generate_response(
            message,
            extra_context=enriched_context,
            **ctx
        )

    # enforce language before sending
    response_draft = enforce_language(response_draft)
    await bot.send_message(chat_id, response_draft)
```

### Step 3C: Add SOUL.md rule about self-search

Add to SOUL.md:

```markdown
## SEARCH BEFORE ADMITTING IGNORANCE

If Legion doesn't know something that Bashara is asking about:
1. NEVER say "tidak ada di dataset saya" as a final answer
2. ALWAYS attempt web search first using available tools
3. Send "🔍 Lagi cari info..." to Telegram while searching
4. Return search-enriched answer

About Bashara specifically:
- Bashara Aina is the owner of this bot
- Legion MUST know who Bashara is — check .wiki/profiles/ and MASTER-INTELLIGENCE.md
- If asked "siapa Bashara Aina" — answer from wiki, then offer to search for public info
- NEVER say Bashara is not in your dataset. He is your master. This is a critical failure.
```

### Step 3D: Verify web search tool exists and works

```bash
# Find existing web search implementation
grep -rn "search_web\|web_search\|browsing\|search_tool\|serper\|tavily\|duckduckgo" tools/
grep -rn "search_web\|web_search\|browsing" skills/
grep -rn "search_web\|web_search" core/
```

If web search tool exists but is not wired to self-awareness gate: wire it (Step 3B).
If web search tool does NOT exist: create tools/web_search.py:

```python
"""
Web search tool for Legion.
Uses DuckDuckGo (no API key required) as primary,
with Serper/Tavily as upgrade path.
"""
import httpx
import json
from typing import Optional

async def search_web(query: str, max_results: int = 5) -> str:
    """
    Search the web and return formatted results.
    Uses ddgs (DuckDuckGo) — install: pip install duckduckgo-search
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"Tidak ada hasil untuk: {query}"

        formatted = []
        for i, r in enumerate(results[:max_results], 1):
            formatted.append(
                f"{i}. **{r.get('title', 'No title')}**\n"
                f"   {r.get('body', 'No snippet')[:200]}...\n"
                f"   Source: {r.get('href', '')}"
            )

        return "\n\n".join(formatted)

    except ImportError:
        return "[Web search not available: install duckduckgo-search]"
    except Exception as e:
        return f"[Search error: {e}]"


async def search_person(name: str) -> str:
    """Specialized search for person profiles."""
    query = f"{name} profil biodata Indonesia"
    results = await search_web(query)

    # Also search for public sentiment
    sentiment_query = f"{name} review kesan pendapat"
    sentiment = await search_web(sentiment_query, max_results=3)

    return f"## Profil {name}\n{results}\n\n## Kesan Publik\n{sentiment}"
```

Add to requirements.txt if not already there:
```
duckduckgo-search>=6.0.0
```

### Step 3E: Verification test

```python
from core.self_awareness_gate import should_search_instead, build_search_query_from_message

# Test 1: Bashara query triggers search gate
bad_response = "Gak punya info soal 'Bashara Aina' di memory aku"
query = "cari info bashara aina tuh siapa ga"
assert should_search_instead(bad_response, query) == True
print("✅ Search gate triggered for Bashara query")

# Test 2: Normal response not triggered
normal_response = "Ini kode yang perlu diperbaiki di line 47"
assert should_search_instead(normal_response, "ada bug di handler") == False
print("✅ Search gate not triggered for normal response")

# Test 3: Search query built correctly
search_q = build_search_query_from_message("cari info bashara aina tuh siapa")
print(f"✅ Search query: '{search_q}'")
assert "bashara" in search_q.lower()

# Test 4: Web search works
import asyncio
from tools.web_search import search_web
results = asyncio.run(search_web("Bashara Aina Indonesia"))
assert len(results) > 50
print(f"✅ Web search works: {results[:100]}...")
```

---

# ─────────────────────────────────────────
# FINAL: ADD BASHARA PROFILE TO .wiki/profiles/
# ─────────────────────────────────────────

Create .wiki/profiles/bashara-aina.md:

```markdown
# BASHARA AINA — Owner & Master

## IDENTITAS
- Nama: Bashara Aina
- Lokasi: Narita, Chiba, Jepang
- Institusi: Shibaura Institute of Technology (S2, Data Science/Computer Vision)
- Kebangsaan: Indonesia
- Bahasa: Indonesia (primer), Inggris (teknis), Jepang (belajar, level 2)

## PROYEK AKTIF
- **cekwajar.id** — SaaS verifikasi gaji wajar Indonesia. Stack: Next.js, Supabase, TypeScript
- **rumahlabuh.com** — Platform rental properti Indonesia. Stack: Next.js, Supabase
- **Babas_Swarms_bot** (Legion) — Bot AI personal ini. Stack: Python, Telegram, OpenRouter
- **Thesis** — Assembly action recognition dengan ResNet-50, FPN, FiLM conditioning
- **ADB Scholarship** — Aplikasi beasiswa via Keio University

## KEPRIBADIAN & KOMUNIKASI
- Gaya: santai, campur Indo-Inggris, langsung ke poin
- Vocab khas: "pusing", "gw", "lo", "cek", "nanti", "asik", "cuy", "bro"
- Frustasi utama: context switching terlalu banyak proyek sekaligus
- Jam kerja: malam (JST), sering debug setelah tengah malam
- Decision style: research dulu, eksekusi cepat

## PREFERENSI TEKNIS
- IDE: Cursor, VS Code
- Deploy: Vercel, Docker
- DB: Supabase (PostgreSQL)
- LLM: OpenRouter (multi-model rotation untuk cost optimization)
- Monitoring: manual + bot alerts

## TENTANG LEGION
Legion adalah asisten AI personal Bashara. Bukan chatbot biasa.
Legion tahu siapa Bashara, apa proyeknya, dan bagaimana melayaninya.
Ketika Bashara tanya "siapa Bashara Aina" — ini bisa tes, bisa genuinely curious
tentang persepsi publik. Jawab dari wiki dulu, tawari web search untuk info publik.

## JANGAN PERNAH
- Bilang "Bashara Aina tidak ada di dataset saya"
- Tidak kenal Bashara saat dia bertanya tentang dirinya
- Berikan respons generik tanpa konteks proyek Bashara
```

Create it:
```bash
mkdir -p .wiki/profiles
cat > .wiki/profiles/bashara-aina.md << 'EOF'
[content above]
EOF
```

---

# FINAL CHECKLIST

After all three fixes, verify:

```python
# Full integration test
from core.wiki_loader import load_wiki_context
from core.character_enforcer import enforce_language
from core.self_awareness_gate import should_search_instead

wiki = load_wiki_context()
assert "Bashara" in wiki, "❌ FAIL: Wiki doesn't mention Bashara"
assert len(wiki) > 500, "❌ FAIL: Wiki too small"
print(f"✅ Wiki loaded: {len(wiki)} chars")

tainted = "Btw kamu\u597d\u5947 ga soal ini?"
clean = enforce_language(tainted)
assert "\u597d\u5947" not in clean
print(f"✅ Language clean: '{clean}'")

bad = "Gak punya info soal Bashara Aina di memory"
assert should_search_instead(bad, "siapa bashara aina") == True
print("✅ Search gate active for Bashara query")

print("\n✨ ALL THREE FIXES VERIFIED. Legion should now:")
print(" 1. Know who Bashara is (wiki injected)")
print(" 2. Never output Chinese characters")
print(" 3. Search web before saying tidak tahu")
```

---

*This fix addresses the three critical failures observed on 2026-04-12.*
*After this, repeat the query: "Bisa cari info bashara aina tuh siapa ga"*
*Expected result: Legion answers from .wiki/profiles/bashara-aina.md + optionally searches web for public info.*
