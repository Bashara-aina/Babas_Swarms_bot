# LEGION BOT — MASTER AUDIT & FIX DOCUMENT FOR OPENCODE
# Generated: 2026-04-12 | Repo: swarm-bot
# Purpose: Deep professional audit → full fix plan to make Legion feel human, native, zero robot

---

## MISSION STATEMENT

Legion must feel like talking to a real senior friend — not a chatbot. Every interaction should
be native, without slash commands, without robotic fallbacks, without error messages leaking to
the user. The goal: Bashara types, Legion thinks and responds like a human who has context,
memory, opinions, and initiative.

---

## ✅ COMPLETED FIXES

### [P0-1] progress_cb → progress_fn
Status: **NOT A BUG** — verified clean. `llm_client/__init__.py` already uses `progress_fn`
correctly. `handlers/shared.py` calls it with `progress_fn=on_progress`. Smoke tests pass.

### [P0-2] Proactive timestamp overflow — `core/proactive/curiosity_engine.py`
Status: **FIXED**
- `_today_str()`: Replaced broken manual JST calc with proper `pytz`/`ZoneInfo`
- `_jst_hour()`: Same fix — now timezone-aware
- `_check_sleep_pattern()`: Guards for invalid timestamps (0 or future), display clamped at 72h,
  silent hours capped at 504. No more "493309 hours" bug.

### [P0-3] Error humanizer — `core/error_humanizer.py` (new file)
Status: **IMPLEMENTED**
- `humanize_error()` and `humanize_error_for_display()` convert raw exceptions to friendly Indonesian/English
- Suppresses internal errors silently (progress_cb/fn mismatches → retry)
- Routes API key errors → provider-specific message + fallback chain retry
- Wired into `handlers/shared.py` `_run_agent_loop()` and `_execute_chat()`

### [P1-1] Natural command parser — `core/natural_command_parser.py` (new file)
Status: **IMPLEMENTED**
- Maps casual Indonesian/English phrases → internal intents without slash prefix
- Patterns: `cek [url] SEO`, `jalanin|execute|run [cmd]`, `restart`, `screenshot`, `buka [app]`
- `get_action()` and `is_actionable()` helpers
- Smoke test: `"cek rumahlabuh.com SEO-nya"` → `intent=web_audit, confidence=0.85` ✅

### [P1-2] Wiki quality gate scoring bug — `core/wiki_quality_gate.py` + `core/wiki_scheduler.py`
Status: **FIXED**
- Added essential file whitelist (readme, changelog, license, master-intelligence) → always PASS
- Structure bonuses: headers, bullets, wiki links, markdown links
- Quarantine threshold lowered from <0.3 to <0.15 with NEEDS_IMPROVEMENT routing
- Double-gate: score 0.0-0.1 pages get `deep_gate()` before quarantine (only quarantine if REJECT)
- Content bonuses for 50+ and 100+ word pages

### [P1-3] SOUL.md injection — Already working
Status: **VERIFIED CLEAN** — `system_prompt_builder.py` has soul as section 0 at line 79-86.
Smoke test confirms 3890 chars loaded correctly.

### [P1-4] Intent classifier for casual Indonesian — Already working
Status: **VERIFIED CLEAN** — `core/intent_router.py` and `handlers/ai.py` already handle
casual Indonesian phrases via fallback keyword dispatch.

### [P1-5] Character enforcer — Already working
Status: **VERIFIED CLEAN** — `core/character_enforcer.py` strips banned phrases correctly.
Smoke test: `"help you with that."` → filtered properly.

---

## ⏳ REMAINING OPEN ITEMS

> These were NOT completed by OpenCode. Need manual implementation or further session.

---

### [P1-OPEN] Persistent Conversation Context
**Status: NOT IMPLEMENTED**
**Files:** `core/memory_engine.py`, `router.py` CONVERSATION_HISTORY

The `CONVERSATION_HISTORY` dict in `agents.py` is still in-memory only — resets on every
Legion restart. This is the core reason Legion "forgets" things from earlier in a session.
Mem0 is integrated but not guaranteed to be called on every exchange.

**What to implement:**
```python
# core/session/persistent_context.py
import sqlite3, json
from pathlib import Path

class PersistentContext:
    def __init__(self, db_path="data/conversation.db"):
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self._init_table()

    def _init_table(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user_id TEXT,
                role TEXT,
                content TEXT,
                ts REAL DEFAULT (strftime('%s','now'))
            )
        """)
        self.db.commit()

    def push(self, user_id: str, role: str, content: str):
        self.db.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?,?,?)",
            (user_id, role, content)
        )
        self.db.commit()

    def get_recent(self, user_id: str, n: int = 20) -> list[dict]:
        rows = self.db.execute(
            "SELECT role, content FROM messages WHERE user_id=? ORDER BY ts DESC LIMIT ?",
            (user_id, n)
        ).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def summarize_old(self, user_id: str, keep_recent: int = 20) -> None:
        """Compress messages older than keep_recent into a summary entry."""
        # Use LLM to summarize old messages, store as role="summary"
        pass
```

**Wire it in** `conversation_interface.py`:
- On EVERY incoming message: `ctx.push(user_id, "user", content)`
- On EVERY outgoing message: `ctx.push(user_id, "assistant", response)`
- Load via `ctx.get_recent(user_id, 20)` and inject into system prompt context

---

### [P2-OPEN] sudo/PTY Execution via pexpect
**Status: NOT IMPLEMENTED** — requires system-level config
**Files:** `core/interpreter_bridge.py`, `core/opencode_bridge.py`

**Step 1: One-time system setup (run manually):**
```bash
# Create passwordless sudo for Legion-specific commands only
echo "bashara ALL=(ALL) NOPASSWD: /bin/systemctl restart legion" | sudo tee /etc/sudoers.d/legion_restart
echo "bashara ALL=(ALL) NOPASSWD: /bin/systemctl status legion" | sudo tee -a /etc/sudoers.d/legion_restart
chmod 440 /etc/sudoers.d/legion_restart
```

**Step 2: Add `SUDO_PASS` to `.env`:**
```
SUDO_PASS=your_password_here
```

**Step 3: pexpect-based execution in `core/interpreter_bridge.py`:**
```python
import pexpect
import os

def run_sudo_command(command: str) -> tuple[str, int]:
    sudo_pass = os.environ.get("SUDO_PASS", "")
    child = pexpect.spawn(f"sudo {command}", timeout=30)
    idx = child.expect(["password", pexpect.EOF, pexpect.TIMEOUT])
    if idx == 0:
        child.sendline(sudo_pass)
        child.expect(pexpect.EOF)
    output = child.before.decode("utf-8", errors="ignore")
    return output, child.exitstatus or 0
```

---

### [P2-OPEN] Persona Loading Race Condition
**Status: NOT VERIFIED**
**Files:** main bot startup sequence, `core/soul_engine.py`

On cold start, if Legion starts accepting Telegram messages before `soul_engine.load_soul()`
completes, the first response can be robotic/generic.

**Fix:**
```python
# In main.py / bot startup
async def startup():
    soul = SoulEngine()
    await soul.load()   # BLOCKING — must complete before polling starts
    logger.info(f"Soul loaded: {len(soul.content)} chars")
    await bot.send_message(BASHARA_CHAT_ID, "Legion online. Soul loaded. 👁️")
    await application.start_polling()  # only now
```

---

### [P3-OPEN] Proactive Check-in Deduplication
**Status: PARTIALLY FIXED** (timestamp overflow fixed, but dedup not implemented)
**File:** `core/proactive/curiosity_engine.py` or `core/proactive_engine.py`

Legion still sends the SAME check-in phrase repeatedly. The chat log shows:
- "You've been quiet for about 9 hours..." at 10:20
- "You've been quiet for about 10 hours..." at 11:20
- "Pagi! Ada agenda hari ini..." at 11:02
- All within the same hour window.

**Fix needed:**
```python
# Add to proactive engine state
PROACTIVE_COOLDOWN_HOURS = 4  # don't check in more than once per 4 hours
LAST_CHECKIN_KEY = "last_proactive_checkin"

def should_send_checkin(user_id: str) -> bool:
    last = load_state(LAST_CHECKIN_KEY, user_id)
    if last is None:
        return True
    hours_since = (time.time() - last) / 3600
    return hours_since >= PROACTIVE_COOLDOWN_HOURS

# Also add message variety pool:
CHECKIN_POOL = [
    "Lo baik-baik aja?",
    "Masih hidup?",
    "Halo, lo ghosting aku nih.",
    "Eh, ada yang lagi lo pikirin?",
    "Sunyi banget dari lo tadi.",
    None,  # sometimes don't send at all (50% chance)
]
```

---

### [BONUS-OPEN] Conversation Memory Proactivity
**Status: NOT IMPLEMENTED**
**File:** `core/soul_engine.py` or `core/proactive_engine.py`

Legion should naturally bring up unresolved topics from memory:
```python
PROACTIVE_MEMORY_TRIGGERS = [
    ("thesis deadline", "Btw lo thesis deadline-nya kapan? Udah ada progress?"),
    ("rumahlabuh deploy", "Rumahlabuh gimana? Ada update dari kemarin?"),
    ("pusing", None),   # sensitive topic — never bring it up proactively
    ("tired", None),
]

# Check: if Bashara mentioned X and it was > 24h ago without resolution → ask once
```

---

### [BONUS-OPEN] Response Style Enforcements
**Status: NOT IMPLEMENTED**
**File:** `core/system_prompt_builder.py` or `core/character_enforcer.py`

Add this block to the system prompt (after SOUL.md, before task context):
```
LEGION VOICE RULES (applied on every response, no exceptions):
- Max 1 clarifying question per casual message. Not a list of questions.
- Never bullet-list during casual chitchat. Lists only for code/data output.
- Emotion first, solution second. If Bashara vents, acknowledge before fixing.
- Match energy: Bashara sends 3 words? Respond in 1-2 lines.
- If Bashara hasn’t replied in 2+ daytime hours: ONE check-in, then silence for 4h.
- Never open with "Oke!", "Siap!", "Tentu!", "Sure!", "Of course!" — just start talking.
- When Bashara says something vague like "pusing" — ask what’s wrong. ONE question.
- Use sarcasm and dry humor where appropriate — it’s authentic.
```

---

## REMAINING TODO PRIORITY ORDER

| Priority | Item | Effort | Impact |
|---|---|---|---|
| P1 | Persistent conversation context (SQLite) | 2h | 🔥 High — fixes memory loss |
| P2 | Proactive check-in dedup + variety | 30min | High — stops spam |
| P2 | Response style enforcement in system prompt | 15min | High — instant personality upgrade |
| P2 | sudo/PTY via pexpect | 1h | Medium — enables native shell |
| P3 | Startup race condition (soul blocking) | 30min | Medium — cold start quality |
| BONUS | Proactive memory triggers | 1h | Medium — real friend feel |

---

## OPENCODE PROMPT FOR NEXT SESSION

Paste this to continue where OpenCode left off:

```
You are a senior software engineer auditing and fixing the Legion Telegram bot.
Repo: ~/path/to/swarm-bot

Your next tasks in order:
1. Implement core/session/persistent_context.py (SQLite conversation buffer)
   Wire it into conversation_interface.py — push on every message, load on every response.
2. Add proactive check-in cooldown (4h) and message variety pool to core/proactive_engine.py
3. Add LEGION VOICE RULES block to core/system_prompt_builder.py after SOUL injection
4. Verify soul loading is blocking before bot.start_polling() in main startup

Surgical fixes only. Run smoke tests after each change.
```

---

*End of LEGION_OPENCODE_AUDIT.md*
*Repo: swarm-bot
*Generated: 2026-04-12*
