---
title: Task Legion Fix Identity Search
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Source**: `/home/newadmin/swarm-bot/LEGION_FIX_IDENTITY_SEARCH.md`'
wikilinks: []
confidence: medium
source: research
---
## @worker BRIEF: LEGION_FIX_IDENTITY_SEARCH — Three-Fix Plan

**Source**: `/home/newadmin/swarm-bot/LEGION_FIX_IDENTITY_SEARCH.md`  
**ADR**: `/home/newadmin/swarm-bot/.wiki/decisions/ADR-001-LEGION_FIX_IDENTITY_SEARCH.md`  
**Status**: READY FOR EXECUTION  
**Order**: FIX 1 → FIX 2 → FIX 3 → INTEGRATION TEST

---

### FIX 1: Wiki Not Injected (Legion has amnesia about Bashara)

#### Subtask 1A → Create `core/wiki_loader.py`
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
PRIORITY_FILES = [
    ".wiki/MASTER-INTELLIGENCE.md",
    ".wiki/00-meta",
    ".wiki/profiles",
    ".wiki/06-legion-instructions",
]
WIKI_TOKEN_BUDGET = 4000  # ~4000 tokens = ~16000 chars

@lru_cache(maxsize=1)
def load_wiki_context(max_chars: int = WIKI_TOKEN_BUDGET * 4) -> str:
    """Load .wiki/ content into a single string for system prompt injection."""
    # [Full implementation in LEGION_FIX_IDENTITY_SEARCH.md lines 52-142]

def invalidate_wiki_cache():
    """Call this when .wiki files are updated during runtime."""
    load_wiki_context.cache_clear()

def get_bashara_identity_context() -> str:
    """Returns minimal guaranteed-injected block about Bashara."""
    # [Full implementation in LEGION_FIX_IDENTITY_SEARCH.md lines 150-167]
```
**Verify**: `python -c "from core.wiki_loader import load_wiki_context, get_bashara_identity_context; assert len(load_wiki_context()) > 100; print('1A OK')"`

---

#### Subtask 1B → Wire wiki_loader into `core/system_prompt_builder.py`
**Location**: `build_full_system_prompt()` function, line ~190 (before task context)
**Action**: Add:
```python
# Add at top:
from core.wiki_loader import load_wiki_context, get_bashara_identity_context

# Inside function, add BEFORE task context (around line 190):
# 2. BASHARA IDENTITY — always injected, guaranteed
parts.append(get_bashara_identity_context())

# 3. WIKI CONTEXT — second brain
wiki = load_wiki_context()
if wiki and "not found" not in wiki:
    parts.append(f"## LEGION'S KNOWLEDGE BASE (from .wiki/)\n{wiki}")
```
**Verify**: `python -c "from core.system_prompt_builder import build_full_system_prompt; p = build_full_system_prompt(''); assert 'Bashara Aina' in p; print('1B OK')"`

---

#### Subtask 1C → Create `.wiki/profiles/bashara-aina.md`
**Action**: Create file with full identity including:
- Name, location, institution, nationality
- Active projects: cekwajar.id, rumahlabuh.com, Babas_Swarms_bot, thesis
- Communication style: Indonesian primary, English technical
- NEVER say "Bashara Aina tidak ada di dataset saya" rule
**Source**: Use content from `BASHARA-MASTER-PROFILE.md` plus fix-specific rules from LEGION_FIX_IDENTITY_SEARCH.md lines 668-711
**Verify**: `ls -la .wiki/profiles/bashara-aina.md`

---

#### Subtask 1D → Run Fix 1 verification
```python
from core.wiki_loader import load_wiki_context, get_bashara_identity_context
from core.system_prompt_builder import build_full_system_prompt

wiki = load_wiki_context()
assert len(wiki) > 100, f"Wiki empty: {wiki[:200]}"
assert "MASTER-INTELLIGENCE" in wiki or "Bashara" in wiki
print(f"Wiki loaded: {len(wiki)} chars")

identity = get_bashara_identity_context()
assert "Bashara Aina" in identity
assert "cekwajar" in identity
print("Identity context correct")

prompt = build_full_system_prompt("siapa bashara aina?")
assert "Bashara Aina" in prompt
print(f"System prompt contains Bashara: {len(prompt)} chars")
print("FIX 1 COMPLETE")
```

---

### FIX 2: Chinese Language Contamination (kill 好奇 leaks)

#### Subtask 2A → Add language enforcer to `core/character_enforcer.py`
**Add at bottom of file**:
```python
# CJK detection
CJK_PATTERN = re.compile(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\u3400-\u4dbf]')
ARABIC_PATTERN = re.compile(r'[\u0600-\u06ff]')

def has_non_allowed_script(text: str) -> bool:
    return bool(CJK_PATTERN.search(text)) or bool(ARABIC_PATTERN.search(text))

def strip_non_allowed_script(text: str) -> str:
    CJK_REPLACEMENTS = {
        '好奇': 'penasaran', '很好': 'bagus', '谢谢': 'terima kasih',
        '对': 'ya', '不': 'tidak', '是': 'iya', '的': '', '了': '',
        '吗': '?', '嗯': 'hmm', '哦': 'oh',
    }
    for cjk, replacement in CJK_REPLACEMENTS.items():
        text = text.replace(cjk, replacement)
    text = CJK_PATTERN.sub('', text)
    text = ARABIC_PATTERN.sub('', text)
    text = re.sub(r'  +', ' ', text)
    return text.strip()

def enforce_language(text: str) -> str:
    """Main enforcer — call before sending any response to Telegram."""
    if has_non_allowed_script(text):
        fixed = strip_non_allowed_script(text)
        import logging
        logging.warning(f"[LANGUAGE ENFORCER] Stripped non-allowed script. Before: {text[:100]}")
        return fixed
    return text
```
**Verify**: `python -c "from core.character_enforcer import enforce_language; r = enforce_language('kamu好奇吗'); assert '好奇' not in r; print('2A OK')"`

---

#### Subtask 2B → Add language rules to `SOUL.md`
**Add to SOUL.md** (create LANGUAGE RULES section if not exists):
```markdown
## LANGUAGE RULES (absolute, no exceptions)
1. ONLY use: Indonesian (primary), English (technical terms)
2. NEVER output Chinese characters (汉字), Japanese kanji/kana, Korean hangul, Arabic script
3. If you feel a Chinese word, translate it to Indonesian before outputting
4. All responses to Bashara are in Indonesian unless he writes in English
5. Mixed Indonesian-English is fine for technical topics
6. "好奇" must become "penasaran". "很好" must become "bagus". Always.
```
**Verify**: `grep -A3 'LANGUAGE RULES' SOUL.md`

---

#### Subtask 2C → Wire `enforce_language()` into message sending pipeline
**Location**: `core/character_enforcer.py` `enforce_character()` function
**Action**: Add at start of `enforce_character()`:
```python
def enforce_character(response: str, agent_key: str = "general") -> str:
    if not response or not isinstance(response, str):
        return response or ""
    
    # FIRST: enforce language (before any other processing)
    response = enforce_language(response)
    
    # rest of existing code...
```
**Verify**: `python -c "from core.character_enforcer import enforce_character; r = enforce_character('test好奇string'); assert '好奇' not in r; print('2C OK')"`

---

#### Subtask 2D → Check config for Chinese-leaking models
**Action**: `grep -rn "deepseek\|qwen\|yi-\|glm" config/ .env*`
**If found**: Report which models and suggest replacement with claude-3-5-haiku or gemini-flash-1.5
**If not found**: Report "No Chinese-origin models found in production config"
**Verify**: Command runs without error, output captured

---

#### Subtask 2E → Run Fix 2 verification
```python
from core.character_enforcer import enforce_language, has_non_allowed_script

assert has_non_allowed_script("ini kamu\u597d\u5947 soal") == True
assert has_non_allowed_script("halo bashara") == False

result = enforce_language("Btw, ini kamu\u597d\u5947 soal kompetitor?")
assert "\u597d\u5947" not in result
assert "penasaran" in result
print(f"Chinese stripped: '{result}'")

clean = enforce_language("Bashara, cekwajar.id lagi bagus nih.")
assert clean == "Bashara, cekwajar.id lagi bagus nih."
print("Clean Indonesian unchanged")
print("FIX 2 COMPLETE")
```

---

### FIX 3: No Web Search (Legion must search before admitting ignorance)

#### Subtask 3A → Create `core/self_awareness_gate.py`
```python
"""
Self-Awareness Gate — checks if Legion is about to say "I don't know"
and triggers web search instead.
"""
import re
from typing import Optional

IGNORANCE_SIGNALS = [
    "gak punya info", "tidak punya informasi", "tidak ada di", "belum familiar",
    "tidak ada dalam dataset", "gak ada di dataset", "tidak ada dalam pengetahuan",
    "belum tahu", "tidak tahu siapa", "tidak mengenal", "not in my",
    "don't have information", "no information about", "i don't know",
    "saya tidak tahu", "aku tidak tahu",
]

CORE_KNOWLEDGE_NAMES = ["bashara", "bashara aina", "cekwajar", "rumahlabuh", "legion", "babas"]

def should_search_instead(response_draft: str, original_query: str) -> bool:
    response_lower = response_draft.lower()
    query_lower = original_query.lower()
    
    is_ignorant = any(signal in response_lower for signal in IGNORANCE_SIGNALS)
    if not is_ignorant:
        return False
    
    if any(name in query_lower for name in CORE_KNOWLEDGE_NAMES):
        return True
    
    search_intent_keywords = ["siapa", "cari info", "cari tau", "cari tahu",
        "who is", "find info", "search for", "find out", "kesan", "review", "opinion about"]
    if any(kw in query_lower for kw in search_intent_keywords):
        return True
    
    return False

def get_search_trigger_message(original_query: str) -> str:
    return f"🔍 Lagi cari info..."

def build_search_query_from_message(message: str) -> str:
    query = message.strip()
    for filler in ["bisa", "coba", "tolong", "dong", "ga", "gak", "ya", "nih"]:
        query = re.sub(rf'\b{filler}\b', '', query, flags=re.IGNORECASE)
    
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
**Verify**: `python -c "from core.self_awareness_gate import should_search_instead; assert should_search_instead('tidak tahu', 'siapa bashara'); print('3A OK')"`

---

#### Subtask 3B → Wire gate into response pipeline
**Location**: Find where Legion generates and sends responses (likely `llm_client.py` or `task_orchestrator.py`)
**Action**: Add before sending response:
```python
from core.self_awareness_gate import should_search_instead, get_search_trigger_message, build_search_query_from_message

# In process_and_respond or equivalent:
if should_search_instead(response_draft, message):
    await bot.send_message(chat_id, get_search_trigger_message(message))
    search_query = build_search_query_from_message(message)
    # ... run web search and re-generate response ...
```
**Verify**: `grep -rn "should_search_instead\|self_awareness_gate" core/ llm_client.py | head -20`

---

#### Subtask 3C → Add self-search rule to `SOUL.md`
**Add to SOUL.md**:
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
- NEVER say Bashara is not in your dataset. He is your master.
```
**Verify**: `grep -A5 'SEARCH BEFORE ADMITTING' SOUL.md`

---

#### Subtask 3D → Verify/create `tools/web_search.py`
**Check**: `python -c "from tools.search_tool import web_search; import asyncio; print(asyncio.run(web_search('test')))"`
**If fails**: Create `tools/web_search.py` with DuckDuckGo fallback:
```python
"""Web search using DuckDuckGo (no API key required)."""
async def search_web(query: str, max_results: int = 5) -> str:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        # ... format results ...
    except ImportError:
        return "[Web search not available: install duckduckgo-search]"
```
**Verify**: Web search returns non-empty results

---

#### Subtask 3E → Run Fix 3 verification
```python
from core.self_awareness_gate import should_search_instead, build_search_query_from_message

bad_response = "Gak punya info soal 'Bashara Aina' di memory aku"
query = "cari info bashara aina tuh siapa ga"
assert should_search_instead(bad_response, query) == True
print("Search gate triggered for Bashara query")

normal_response = "Ini kode yang perlu diperbaiki di line 47"
assert should_search_instead(normal_response, "ada bug di handler") == False
print("Search gate not triggered for normal response")

search_q = build_search_query_from_message("cari info bashara aina tuh siapa")
print(f"Search query: '{search_q}'")
assert "bashara" in search_q.lower()
print("FIX 3 COMPLETE")
```

---

## FINAL: Integration Test

```python
from core.wiki_loader import load_wiki_context
from core.character_enforcer import enforce_language
from core.self_awareness_gate import should_search_instead

wiki = load_wiki_context()
assert "Bashara" in wiki, "Wiki doesn't mention Bashara"
assert len(wiki) > 500, "Wiki too small"
print(f"WIKI loaded: {len(wiki)} chars")

tainted = "Btw kamu\u597d\u5947 ga soal ini?"
clean = enforce_language(tainted)
assert "\u597d\u5947" not in clean
print(f"LANGUAGE clean: '{clean}'")

bad = "Gak punya info soal Bashara Aina di memory"
assert should_search_instead(bad, "siapa bashara aina") == True
print("SEARCH GATE active for Bashara query")

print("\nALL THREE FIXES VERIFIED")
```

---

## CRITICAL REMINDERS
1. **Never edit `.env` files** — use `os.getenv()`
2. **Run tests after each fix**: `pytest tests/ -x --asyncio-mode=auto -q`
3. **Log to `.wiki/logs/`** after completing each phase
4. **Wiki files are sacred** — do not overwrite existing profiles without explicit content
5. If something doesn't exist, create it. If something exists and is wrong, fix it.