# LEGION BOT — MASTER AUDIT & FIX DOCUMENT FOR OPENCODE
# Generated: 2026-04-12 | Repo: Bashara-aina/Babas_Swarms_bot
# Purpose: Deep professional audit → full fix plan to make Legion feel human, native, zero robot

---

## MISSION STATEMENT

Legion must feel like talking to a real senior friend — not a chatbot. Every interaction should
be native, without slash commands, without robotic fallbacks, without error messages leaking to
the user. The goal: Bashara types, Legion thinks and responds like a human who has context,
memory, opinions, and initiative.

---

## AUDIT FINDINGS — 10 CRITICAL FAILURE AREAS

### AREA 1: `progress_cb` vs `progress_fn` — API Breakage [CRITICAL]
**File affected:** `core/interpreter_bridge.py` (and anywhere agent_loop() is called)
**Symptom:** Every `/do` and `/cmd` command fails with:
  `agent_loop() got an unexpected keyword argument 'progress_cb'. Did you mean 'progress_fn'?`
**Root cause:** The Open Interpreter library changed its API. `progress_cb` was renamed to
  `progress_fn` in a newer version. The codebase was NOT updated.
**Fix:**
  1. Run: `grep -rn "progress_cb" . --include="*.py"`
  2. In every hit, replace `progress_cb=` → `progress_fn=`
  3. Also check if `agent_loop()` signature itself needs updating for the installed interpreter version.
  4. Pin the Open Interpreter version in requirements.txt to avoid future drift:
     `open-interpreter==X.Y.Z  # pinned — check installed version`

---

### AREA 2: SLASH COMMAND DEPENDENCY — NOT NATIVE [CRITICAL]
**Files affected:** `telegram_bot.py` (or equivalent entrypoint), `core/intent_router.py`,
  `core/task_router.py`
**Symptom:** Users must type `/do`, `/cmd`, `/screen`, `/keys` to trigger capabilities.
  This is not natural. Bashara should just say "cek rumahlabuh.com SEO-nya" and Legion does it.
**Root cause:** Intent detection only triggers capabilities when prefixed with slash commands.
  The `intent_router.py` and `task_router.py` likely check for `/` prefix BEFORE doing NLU.
**Fix:**
  1. In `core/intent_router.py` — add a natural language pass BEFORE slash-command routing.
     Every message should run through NLU intent classifier first.
  2. In `core/intent_classifier.py` — expand intent map:
     - "cek [url]", "check [url]", "buka [url]" → trigger `web_check` skill
     - "jalanin", "execute", "run", "ketik di terminal" → trigger shell execution
     - "restart", "restart bot" → trigger service management
     - "screen", "lihat layar" → trigger screen capture
  3. Create `core/natural_command_parser.py` — a thin NLP layer that maps casual Indonesian/English
     phrases to internal command names WITHOUT requiring slash prefix.
  4. Slash commands should still work as aliases, but never be required.
  5. Example mapping table to implement:
     ```python
     NATURAL_TRIGGERS = {
         r"cek.*(seo|website|speed|loading)": "web_audit",
         r"(run|jalanin|execute|ketik)\s+(.+)": "shell_exec",
         r"(restart|reboot)\s*(legion|bot)?": "service_restart",
         r"(screenshot|screen|lihat layar|tangkap layar)": "screen_capture",
         r"(cek|check)\s+key": "api_key_check",
         r"(buka|open|launch)\s+(.+)": "app_launch",
     }
     ```

---

### AREA 3: PROACTIVE ENGINE — FEELS ROBOTIC [HIGH]
**File affected:** `core/proactive_engine.py`
**Symptom from chat:**
  - "You've been quiet for about 493309 hours. Everything good?" (hours not clamped — overflow bug)
  - Repeating the same check-in message every hour when user is clearly offline
  - Scheduled messages sent in rapid succession (5 in 2 hours on same topic)
**Root Causes:**
  a. Duration calculation overflow — `493309 hours` means the timestamp math is wrong.
     Likely using epoch seconds vs milliseconds, or wrong timezone offset.
  b. No deduplication / cooldown on proactive messages. Same message fires repeatedly.
  c. No awareness of user's sleep schedule or timezone.
**Fixes:**
  1. Fix duration calc: use `pendulum` or always normalize to `datetime.utcnow()` with proper
     timezone handling. Cap displayed duration at "a few days" if > 72 hours.
  2. Add proactive cooldown: after sending a check-in, don't send another for 4+ hours.
     Store last_proactive_sent timestamp in Redis or SQLite.
  3. Add sleep zone awareness: if JST time is 00:00–07:00, suppress non-urgent proactive.
  4. Add dedup: if the last proactive message body is identical, skip it.
  5. Vary the language — have a pool of 10+ phrased check-ins, pick randomly.
  6. Fix for duration overflow bug:
     ```python
     # BAD:
     hours_silent = (now_ts - last_seen_ts)  # if timestamps differ in units, breaks
     # GOOD:
     from datetime import datetime, timezone
     delta = datetime.now(timezone.utc) - last_seen_dt
     hours_silent = delta.total_seconds() / 3600
     if hours_silent > 72: display = "a few days"
     elif hours_silent > 24: display = f"{int(hours_silent/24)} days"
     else: display = f"{int(hours_silent)} hours"
     ```

---

### AREA 4: API KEY ERROR LEAKING TO USER [HIGH]
**Files affected:** `core/interpreter_bridge.py`, telegram message handler
**Symptom:** Raw error messages shown to user:
  `🔑 api key issue — run /keys to check`
  This is system-internal info that should never surface as a user-facing message.
**Fix:**
  1. Wrap all capability invocations in try/except at the Telegram handler level.
  2. On API key error: silently attempt key rotation (fallback chain in `agents.py` already exists),
     THEN retry the action. Only tell Bashara if ALL fallbacks exhausted.
  3. Create `core/error_humanizer.py`:
     ```python
     def humanize_error(exc: Exception, context: str) -> str:
         if "api key" in str(exc).lower() or "authentication" in str(exc).lower():
             return "Eh, ada masalah sama API key-nya. Lagi coba fallback..."
         if "timeout" in str(exc).lower():
             return "Koneksi timeout. Lagi retry..."
         if "progress_cb" in str(exc) or "progress_fn" in str(exc):
             return None  # internal error, retry silently after fix
         return f"Ada error nih: {str(exc)[:100]}"
     ```
  4. Never show raw Python tracebacks or exception strings to Bashara.

---

### AREA 5: SOUL ENGINE NOT INJECTED INTO EVERY RESPONSE [HIGH]
**Files affected:** `core/soul_engine.py`, `core/system_prompt_builder.py`
**Symptom:** Legion sometimes sounds robotic ("Certainly!", uses corporate tone, breaks SOUL.md rules).
  The SOUL.md file exists and is well-written, but it's not being reliably injected.
**Root cause:** `system_prompt_builder.py` likely has a conditional path where soul content is
  not always included (e.g., when using sub-agents or debate mode).
**Fix:**
  1. In `core/system_prompt_builder.py` — make SOUL.md injection MANDATORY. Zero exceptions.
     It should be the first block of every system prompt, before any agent-specific instructions.
  2. Add a character enforcement post-processor: after every LLM response, run
     `core/character_enforcer.py` checks:
     - Contains "Certainly!" → rewrite opener
     - Contains "As an AI" → strip and rephrase
     - Starts with generic filler → trim it
  3. Add voice consistency check: if response is >3 sentences but has no Indonesian slang when
     Bashara wrote in Indonesian → flag for rewrite.
  4. Ensure `build_system_prompt()` in `agents.py` always calls `soul_engine.load_soul()` first.

---

### AREA 6: CONVERSATION PERSISTENCE BROKEN [HIGH]
**Files affected:** `core/memory_engine.py`, `router.py` → `CONVERSATION_HISTORY`
**Symptom:** Legion doesn't remember things said earlier in the same conversation.
  Each message starts almost fresh. The chat log shows Legion asking the same
  clarifying questions repeatedly.
**Root cause:** `CONVERSATION_HISTORY` in `agents.py` is an in-memory dict — it resets on restart.
  The mem0 integration may not be properly called on every exchange.
**Fix:**
  1. Implement persistent conversation buffer in SQLite or Redis:
     - Key: `user_id:session_date`
     - Value: list of `{role, content, timestamp}` dicts
     - Load on bot startup, flush every N messages
  2. On every incoming message: load last 20 exchanges from persistent store into context window.
  3. On every outgoing message: immediately write to persistent store.
  4. Create `core/session/persistent_context.py` if not exists:
     ```python
     class PersistentContext:
         def push(self, user_id, role, content): ...
         def get_recent(self, user_id, n=20) -> list[dict]: ...
         def summarize_old(self, user_id) -> str: ...  # compress old msgs
     ```
  5. Wire it into `conversation_interface.py` so every response pipeline uses it.

---

### AREA 7: INTENT ROUTING MISSES CASUAL MESSAGES [HIGH]
**Files affected:** `core/intent_router.py`, `core/intent_classifier.py`
**Symptom:** When Bashara says "Pusing nih" Legion correctly responds empathetically.
  But when Bashara says "Coba dong cek langsung" — Legion falls back to explaining
  it can't do it, even though the capability exists.
**Root cause:** Intent classifier has keyword-based routing that misses conversational phrases.
  "coba cek langsung" doesn't match any action trigger because it lacks the `/` prefix.
**Fix:**
  1. Move intent classification to an LLM-based classifier as primary:
     - Send last 3 messages + current message to a fast model (Groq llama-3.3-70b)
     - Ask: "What does the user want? Options: [web_check, shell_exec, chitchat, question,
       task_request, emotional_support, memory_store]"
     - Use the keyword matcher only as fallback
  2. Add context-aware resolution: if previous message was about SEO and user says
     "coba cek langsung" — resolve "it" to the SEO check automatically.
  3. Expand `TASK_KEYWORDS` in `agents.py` with Indonesian casual phrases.

---

### AREA 8: SUDO / SHELL EXECUTION ARCHITECTURE [MEDIUM]
**Files affected:** `core/interpreter_bridge.py`, `core/opencode_bridge.py`
**Symptom:** `sudo systemctl restart legion` fails because shell is non-interactive.
  Password cannot be passed through the current execution path.
**Fix:**
  1. Configure passwordless sudo for specific commands in `/etc/sudoers.d/legion`:
     ```
     bashara ALL=(ALL) NOPASSWD: /bin/systemctl restart legion
     bashara ALL=(ALL) NOPASSWD: /bin/systemctl status legion
     ```
  2. In `interpreter_bridge.py` — when detecting `sudo` commands, warn Bashara proactively:
     "Perintah ini butuh sudo. Mau aku kasih instruksi buat setup NOPASSWD?"
  3. For `opencode_bridge.py` — implement proper PTY (pseudoterminal) execution using
     `pexpect` library to handle interactive prompts:
     ```python
     import pexpect
     child = pexpect.spawn(f"sudo {command}")
     child.expect("password")
     child.sendline(password)
     child.expect(pexpect.EOF)
     ```
  4. Store sudo password in `.env` as `SUDO_PASS` (already encrypted at rest via systemd).

---

### AREA 9: WIKI SCAN QUALITY — 485/502 PAGES QUARANTINED [MEDIUM]
**Files affected:** `core/wiki_quality_gate.py`, `core/wiki_auto_ingest.py`
**Symptom:** Daily scan quarantines 96% of wiki pages with score=0.000.
  Pages like `README.md` and `MASTER-INTELLIGENCE.md` score near zero.
  This means the quality scoring algorithm is broken, not the content.
**Root cause:** `wiki_quality_gate.py` scoring function likely has a bug where
  it returns 0 for pages that don't match its exact expected format.
**Fix:**
  1. Audit `score_page()` in `wiki_quality_gate.py` — add debug logging to see
     what criteria are failing on a known-good page like README.md.
  2. Likely fix: the scoring function divides by zero or returns 0.0 default
     when a section header regex doesn't match. Add graceful fallback scoring.
  3. Update quarantine threshold: score=0.0 should trigger investigation, not auto-quarantine.
  4. Pages with score=0.000 that are clearly valid (README, CHANGELOG) → whitelist them.

---

### AREA 10: PERSONA LOADING RACE CONDITION [MEDIUM]
**Files affected:** `core/soul_engine.py`, bot startup sequence
**Symptom:** On cold start, Legion sometimes responds before SOUL.md is loaded.
  Results in generic/robotic first response.
**Root cause:** Async initialization — the bot starts accepting Telegram messages
  before `soul_engine.load_soul()` completes.
**Fix:**
  1. In main bot startup: make soul loading synchronous and blocking.
     ```python
     # startup sequence
     soul = SoulEngine()
     await soul.load()  # MUST complete before accepting messages
     await bot.start_polling()  # only after soul is ready
     ```
  2. Add health check: `GET /health` endpoint returns 503 until soul is loaded.
  3. Add startup message to Bashara: "Legion online. Soul loaded. Ready." (once, on each restart)

---

## MASTER IMPLEMENTATION ORDER

Priority order for OpenCode to implement (highest impact first):

1. **[P0] Fix `progress_cb` -> `progress_fn`** everywhere — unblocks ALL tool use
2. **[P0] Fix proactive timestamp bug** — 493309 hours is embarrassing, fix immediately
3. **[P0] Humanize all errors** — never show raw exceptions to Bashara
4. **[P1] Natural language command parsing** — eliminate slash command dependency
5. **[P1] Persistent conversation context** — fix memory between turns
6. **[P1] SOUL.md mandatory injection** — every response must have Legion's voice
7. **[P2] LLM-based intent classifier** — replace keyword matcher as primary
8. **[P2] Fix wiki quality gate scoring** — 96% quarantine rate is a bug
9. **[P2] Sudo/PTY execution via pexpect** — enable native shell control
10. **[P3] Async startup sequencing** — fix cold start persona race condition

---

## BONUS: LEGION PERSONALITY UPGRADES

Beyond bug fixes — these make Legion feel truly human:

### Response Style Enforcements (add to system_prompt_builder.py)
```
LEGION VOICE RULES (non-negotiable):
- Max 3 questions per response. Pick the most important one.
- Never bullet-list casual chat. Only use lists for technical output.
- When Bashara says something vague like "pusing" — ask ONE question, don't list options.
- Use ellipsis (...) sparingly — only when trailing off genuinely.
- React to Bashara's emotion FIRST, then offer help. Not the other way around.
- If Bashara hasn't replied in 2+ hours during daytime, ONE check-in max. Then go silent.
- Never start a response with "Oke!", "Siap!", "Tentu!" — start with the actual content.
- Match energy: if Bashara is brief, be brief. If Bashara writes a paragraph, write a paragraph.
- Swear occasionally in Indonesian context if Bashara does — it's authentic, not unprofessional.
```

### Memory Proactivity (add to soul_engine.py)
```python
PROACTIVE_MEMORY_TRIGGERS = [
    # If Bashara mentioned this and never followed up, bring it up naturally
    ("thesis deadline", "Btw lo thesis deadline-nya kapan tuh? Udah progress?"),
    ("rumahlabuh deploy", "Rumahlabuh gimana? Ada update dari kemarin?"),
    ("tired/pusing/stress", None),  # None = don't bring it up, be sensitive
]
```

### Capability Auto-Detection (wire into intent_router.py)
```python
# If user's message contains a URL → auto-run web check without asking
# If user's message mentions a file path → auto-check if file exists
# If user mentions an error message → auto-search for fix
# If user says "tadi error" → auto-check recent logs
```

---

## FILES TO CREATE (NEW)

1. `core/natural_command_parser.py` — NLP to internal command mapping
2. `core/error_humanizer.py` — exception to friendly Indonesian/English message
3. `core/session/persistent_context.py` — SQLite-backed conversation buffer
4. `core/persona_guard.py` — post-response filter enforcing SOUL.md voice

## FILES TO HEAVILY MODIFY

1. `core/interpreter_bridge.py` — fix progress_cb, add PTY support
2. `core/proactive_engine.py` — fix timestamp, add cooldown, vary messages
3. `core/intent_router.py` — add NLU pass before slash routing
4. `core/system_prompt_builder.py` — mandatory SOUL injection
5. `core/wiki_quality_gate.py` — fix scoring bug
6. `core/soul_engine.py` — blocking startup, proactive memory

---

## HOW TO USE THIS DOCUMENT WITH OPENCODE

1. Open OpenCode in your VSCode terminal
2. Reference this file: `LEGION_OPENCODE_AUDIT.md`
3. Prompt to paste into OpenCode:

```
Read LEGION_OPENCODE_AUDIT.md and implement all P0 items first, then P1, then P2.
Start with the progress_cb fix, then the proactive timestamp bug, then error humanizer.
After each fix, run the test suite and confirm no regressions.
Work through the file top to bottom. Surgical fixes only — do NOT refactor what isn't broken.
```

---

## CLAUDE CODE INSTRUCTIONS (for VSCode Claude Code extension)

Paste this into Claude Code's context window to start the session:

```
You are a senior software engineer auditing and fixing the Legion Telegram bot.
Repo: ~/path/to/Babas_Swarms_bot

Your mission: Make Legion feel like a real human friend, not a bot.
Zero slash commands required. Zero raw errors shown. Full natural language understanding.
Perfect memory. Consistent personality from SOUL.md on every single response.

Work through LEGION_OPENCODE_AUDIT.md top to bottom.
For each fix:
1. Read the affected file(s)
2. Apply the minimal correct fix
3. Confirm the fix with a brief explanation
4. Move to next item

Priority: P0 -> P1 -> P2 -> P3 -> Bonus upgrades.

Start with: grep -rn "progress_cb" . --include="*.py" to find and fix Area 1.
```

---

*End of LEGION_OPENCODE_AUDIT.md*
*Repo: https://github.com/Bashara-aina/Babas_Swarms_bot*
*Generated: 2026-04-12*
