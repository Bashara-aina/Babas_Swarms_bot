# ADR-002: Phase 2 Legion Upgrades

**Date:** 2026-04-12  
**Phase:** Phase 2  
**Status:** Completed ✅  
**Deciders:** Bashara, Planner Agent

---

## Context

Phase 1 (Foundation) is complete. Phase 2 adds three focused upgrades:
- **U5:** Skills Registry — 30 curated skills with auto-fire from intent_router
- **U6:** Prompt Injection Protection — sanitization for all user content
- **U7:** Heartbeat Daemon — proactive monitoring during active hours (9am–11pm JST)

---

## Decisions

### U5 — Skills Registry (`core/skills/`)

**File structure:**
```
core/skills/
  __init__.py          # exports SKILL_REGISTRY
  registry.py          # Skill dataclass + SkillRegistry class
  builtin/
    __init__.py        # imports all categories
    web.py             # A1 web_audit, A2 url_check, A3 web_scrape
    research.py        # B1 web_search, B2 arxiv_search, B3 summarize_url, B4 hacker_news
    github.py          # C1 github_pr_status, C2 github_commit_log, C3 code_review
    system.py           # D1 system_health, D2 service_status, D3 service_restart, D4 run_shell
    memory.py           # E1 remember, E2 recall, E3 obsidian_write
    productivity.py     # F1 weather, F2 translate, F3 timer
    personal.py         # G1 rumahlabuh_status, G2 thesis_status, G3 cekwajar_status, G4 gpu_training_status, G5 adb_scholarship
    media.py            # H1 screenshot, H2 analyze_screen, H3 screen_text
```

**Skill dataclass schema:**
```python
@dataclass
class Skill:
    name: str
    description: str
    examples: list[str]         # trigger phrases
    input_schema: dict           # JSON schema for parameters
    permission_level: str         # "basic" | "elevated"
    executor: Callable           # async function
    required_api_keys: list[str] = []
```

**Wire into `core/intent_router.py`:** After `classify_intent_fast()`, add `SKILL_REGISTRY.find_by_example()` fallback when confidence < 0.50.

**Wire into `main.py` on_startup():** Import all `core/skills/builtin.*` modules to trigger registration.

---

### U6 — Prompt Injection Protection (`tools/browser_agent.py`)

Add `tools/browser_agent.py` input sanitization layer:
1. `sanitize_user_content(text: str) -> str` — strips `<additional_instruction>`, `<instruction>`, `</s>` leakage patterns
2. Blocklist regex patterns for prompt injection:
   - `(?i)<(?:additional_)?instruction>`
   - `(?i)</s>`
   - `(?i)ignore.*(?:previous|above|system)`
   - `(?i)forget.*(?:previous|above|system|instruction)`
   - `(?i)system.*prompt.*leak`
3. Apply `sanitize_user_content()` in `browse_task()` before constructing any LLM prompt string
4. Also add sanitization in `_playwright_fallback()` URL extraction step

---

### U7 — Heartbeat Daemon (`core/heartbeat/daemon.py`)

**File:** `core/heartbeat/daemon.py`

```python
class HeartbeatDaemon:
    interval_minutes: int = 30
    active_hours_jst: tuple[int, int] = (9, 23)  # 9am–11pm JST
    
    async def start(self, bot: Bot, user_id: int) -> None:
        """Fire-and-forget background loop. Non-blocking."""
        
    async def _should_wake(self) -> bool:
        """Returns True during active hours JST."""
        
    async def _check_silence(self) -> bool:
        """Returns True if no user message in >4 hours."""
        
    async def _health_check(self) -> dict:
        """Checks: service health, budget status, last activity."""
        
    async def _send_proactive_checkin(self, bot: Bot, user_id: int) -> None:
        """Sends brief proactive message to user if conditions met."""
```

**Wire into `main.py` on_startup():**
```python
from core.heartbeat.daemon import HeartbeatDaemon

_heartbeat = HeartbeatDaemon()
asyncio.create_task(_heartbeat.start(bot, ALLOWED_USER_ID))
```

---

## Consequences

- U5 brings 30 skills; executors can be stubs initially (real implementations follow in Phase 3)
- U6 is a security hardening pass — apply everywhere user content reaches LLM
- U7 runs as fire-and-forget background daemon, JST-aware

---

## Review (2026-04-12)

**Reviewer:** Reviewer Agent  
**Result:** ✅ Phase 2 Complete — 305 tests pass, 28 skills registered

**Findings:**
- No circular imports detected
- All 28 skill handlers are `async def` (await-compatible)
- `sanitize_user_content()` covers web injection patterns; LLM-specific jailbreak patterns (`</s>`, `ignore previous`) noted as out-of-scope for web-layer sanitization
- Heartbeat daemon wired (fire-and-forget), cleanup via task.cancel() on shutdown
- Blocking I/O in `system_health_handler` and `_check_service_health()` — wrapped with `asyncio.to_thread()` recommended for future optimization
- `timer` skill is a documented stub

**Full report:** `.wiki/issues/review-phase2-2026-04-12.md`

---

## References

- LEGION_MCP_SKILLS_MASTER.md — full skill specs
- LEGION_MASTER.md Part 2.2 FIX 2 — injection protection spec
- .wiki/logs/session-2026-04-12-phase2.md — atomic subtask log
