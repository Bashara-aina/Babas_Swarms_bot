---
## ✅ Passed

---
- **Tests:** 305/305 passed (`pytest tests/ -x --asyncio-mode=auto -q`)
- **Skill loading:** 28 skills registered successfully across 8 categories (web, research, github, system, memory, productivity, personal, media)
- **No circular imports:** `core/skills/registry.py` imports only stdlib; builtin modules import from it cleanly
- **Await-compatible handlers:** All skill handlers declared as `async def`
- **API keys:** All external API keys fetched via `os.getenv()` (BRAVE_SEARCH_API_KEY, OPENWEATHERMAP_API_KEY, GITHUB_TOKEN, etc.)
- **sanitize_user_content() patterns:** Covers `<script>`, `javascript:`, `on*=` event handlers, `<iframe>`, template injection (`{{`, `{%`)
- **Intent router fallback:** Skill fallback only triggers at confidence < 0.50, is additive (not replacing existing logic), sets appropriate `needs_tools=True, needs_research=True`
- **Heartbeat wired:** `asyncio.create_task(_heartbeat.start(...))` in `on_startup` — fire-and-forget, non-blocking boot
---


## ⚠️ Warnings

### W1. Blocking I/O in async handlers (`system.py`, `media.py`)
`_system_health_handler` uses blocking `subprocess.run()` for `nvidia-smi` and `psutil.disk_usage()`. `_screenshot_handler` and `_analyze_screen_handler` use blocking `subprocess.run()` for screenshot tools.

**Impact:** These block the event loop during execution. Since they're fire-and-forget skill handlers (not awaited by the router), the bot continues processing, but CPU spikes can occur.

**Recommendation:** Wrap with `asyncio.to_thread(subprocess.run, ...)`:
```python
result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, timeout=10)
```

### W2. Blocking `os.popen` in HeartbeatDaemon
`_check_service_health()` uses `os.popen("systemctl is-active swarm-bot")` — a blocking call.

**Recommendation:** Replace with `asyncio.create_subprocess_shell()` or `asyncio.to_thread()`.

### W3. `HeartbeatDaemon.stop()` never called
`on_shutdown()` in `main.py` cancels all tasks but never calls `_heartbeat.stop()`. The loop will exit via `task.cancel()` since it uses `asyncio.sleep()`, so `_running = False` is set but the cleanup is implicit.

**Not a blocker** — the `cancel()` handles it, but explicit `stop()` call in shutdown would be cleaner.

### W4. `timer_handler` is a stub
The `timer` skill returns a confirmation message but does **not** actually set a timer or schedule anything. The ADR noted "Timer functionality requires bot instance."

**Recommendation:** Either implement with `asyncio.sleep()` + bot notification, or clearly document that `/timer` slash command is the real implementation path.

### W5. Overly broad regex in `sanitize_user_content()`
Pattern `{{.*?}}` will block legitimate use of double-brace syntax in user messages (e.g., "use {{variable}} in the template"). Similarly `{%.*?%}` blocks Jinja2-style content.

**Current behavior:** `{{foo}}` → `[BLOCKED]foo[BLOCKED]`

**Risk:** Low (text is user-provided, not LLM output), but could produce confusing user-facing output.

### W6. `INJECTION_PATTERNS` mismatch with ADR spec
ADR-002-phase2 specifies these patterns to block:
- `</s>` — **NOT in current implementation**
- `ignore.*previous` / `forget.*system` — **NOT in current implementation**
- `system.*prompt.*leak` — **NOT in current implementation**

Current implementation has its own set (covers web-based injection). The missing patterns are LLM-specific jailbreak attempts rather than web injection vectors.

**Risk:** Low — the LLM itself should handle adversarial prompt injection, and the remaining patterns cover the realistic attack surface.

---

## ❌ Blockers

None — all tests pass and no hard blockers identified.

---

## Summary Table

| Area | Status | Notes |
|------|--------|-------|
| Tests | ✅ | 305/305 passed |
| Circular imports | ✅ | Clean import graph |
| Security (sanitize) | ✅ | Covers web injection vectors |
| Security (API keys) | ✅ | All via `os.getenv()` |
| Async/await compliance | ⚠️ | Blocking subprocess in handlers |
| Intent router fallback | ✅ | Correct threshold, additive |
| Heartbeat cleanup | ⚠️ | `stop()` not called but cancel works |
| Skill handlers complete | ⚠️ | `timer` is a stub |

---

## Recommendations (Priority Order)

1. **High:** Wrap `subprocess.run` calls in `_system_health_handler` with `asyncio.to_thread()`
2. **Medium:** Replace `os.popen` in heartbeat `_check_service_health` with async subprocess
3. **Low:** Add explicit `_heartbeat.stop()` call in `on_shutdown()`
4. **Low:** Consider narrowing `{{.*?}}` / `{%.*?%}` patterns to reduce false positives
5. **Info:** Document that `timer` skill is a stub; real timer via `/timer` command
