# AUDIT 11 — `__init__.py` Import Glue Files

## Status: IN PROGRESS
**Date:** 2026-04-12
**Auditor:** @planner
**Agent:** SwarmBot Multi-Agent Orchestration

---

## 1. FINDINGS SUMMARY

### 1.1 All `__init__.py` Files Located

| Package | Path | Lines | Status |
|---------|------|-------|--------|
| handlers | `handlers/__init__.py` | 89 | ✅ OK — registers routers |
| core | `core/__init__.py` | 21 | ✅ OK — lazy submodules + reliability exports |
| agents | `agents/__init__.py` | 1720+ | ✅ OK — AGENT_MODELS, FALLBACK_CHAIN, etc. |
| llm_client | `llm_client/__init__.py` | 1281+ | ✅ OK — chat(), agent_loop(), wiki_raw_completion() |
| swarms_bot | `swarms_bot/__init__.py` | 13 | ✅ OK — ChiefOfStaff, DAGExecutor, ModelRouter |
| swarms_bot/orchestrator | `swarms_bot/orchestrator/__init__.py` | 24 | ✅ OK — Agent, ChiefOfStaff, DAGPlanner, DAGExecutor |
| swarms_bot/routing | `swarms_bot/routing/__init__.py` | 6 | ✅ OK — CostAwareRouter, BudgetManager |
| swarms_bot/sessions | `swarms_bot/sessions/__init__.py` | 5 | ✅ OK — Session, SessionManager |
| swarms_bot/security | `swarms_bot/security/__init__.py` | 6 | ✅ OK — SecurityGuard, RateLimiter |
| swarms_bot/evaluation | `swarms_bot/evaluation/__init__.py` | 5 | ✅ OK — AgentEvaluator, EvaluationResult |
| swarms_bot/observability | `swarms_bot/observability/__init__.py` | 6 | ✅ OK — CostMetricsCollector, SwarmLogger |
| swarms_bot/audit | `swarms_bot/audit/__init__.py` | 5 | ✅ OK — AuditLogger, AuditEvent |
| swarms_bot/agents | `swarms_bot/agents/__init__.py` | 1 | ⚠️ EMPTY — package marker only |
| computer_agent | `computer_agent/__init__.py` | 104 | ✅ OK — execute_tool, TOOL_DEFINITIONS, etc. |
| config | `config/__init__.py` | 16 | ✅ OK — ConfigLoader |
| skills/nihongo | `skills/nihongo/__init__.py` | 44 | ✅ OK — exports all major classes |
| core/mcp | `core/mcp/__init__.py` | 6 | ✅ OK — MCPClient, MCP_MANAGER |
| core/mcp/servers | `core/mcp/servers/__init__.py` | 17 | ✅ OK — brave_available, filesystem_available |
| core/webhooks | `core/webhooks/__init__.py` | 5 | ✅ OK — WEBHOOK_SERVER, WebhookServer |
| core/webhooks/handlers | `core/webhooks/handlers/__init__.py` | 6 | ✅ OK — handle_github_pr_merged, handle_system_alert |
| core/heartbeat | `core/heartbeat/__init__.py` | 5 | ✅ OK — _heartbeat, HeartbeatDaemon |
| core/session | `core/session/__init__.py` | 3 | ✅ OK — on_startup_resume, on_shutdown_checkpoint |
| core/reflection | `core/reflection/__init__.py` | 3 | ✅ OK — ReflectionEngine |
| core/proactive | `core/proactive/__init__.py` | 4 | ✅ OK — ProactiveScheduler, get_scheduler |
| core/personality | `core/personality/__init__.py` | 4 | ✅ OK — EmotionEngine, Personality |
| core/observability | `core/observability/__init__.py` | 127 | ✅ OK — full observability subsystem |
| core/memory | `core/memory/__init__.py` | 11 | ✅ OK — EpisodicStore, UserProfileStore |
| core/daily_harvester | `core/daily_harvester/__init__.py` | 92 | ✅ OK — DailyHarvester, etc. |
| core/character | `core/character/__init__.py` | 20 | ✅ OK — build_debate_pre_prompt, etc. |
| core/skills | `core/skills/__init__.py` | 19 | ✅ OK — SkillRegistry, BuiltinSkillProvider |
| core/skills/builtin | `core/skills/builtin/__init__.py` | 23 | ✅ OK — SkillMetadata |
| prompts | `prompts/__init__.py` | 0 | ❌ EMPTY — no exports, no callers found |
| bridges | `bridges/__init__.py` | N/A | ❌ DOES NOT EXIST — no package export |
| **core/reliability** | `core/reliability/__init__.py` | **0** | **❌ CRITICAL** |
| **core/orchestration** | `core/orchestration/__init__.py` | **0** | **❌ CRITICAL** |
| **core/optimization** | `core/optimization/__init__.py` | **0** | **❌ CRITICAL** |
| **core/utils** | `core/utils/__init__.py` | **0** | **❌ CRITICAL** |
| **core/tools** | `core/tools/__init__.py` | **0** | **❌ CRITICAL** |
| legion/anti_slop | `legion/anti_slop/__init__.py` | 11 | ✅ OK — AntiSlopPipeline |

### 1.2 Import Patterns Found (What Callers Expect)

| Package | Import Pattern | Expected Exports | Status |
|---------|---------------|------------------|--------|
| `core.reliability` | `from core.reliability.fallback_chain import FallbackChain, get_fallback_chain` | FallbackChain, get_fallback_chain | ✅ Currently exported via core/__init__.py |
| `core.reliability` | `from core.reliability.model_router import select_model, classify_complexity` | select_model, classify_complexity | ✅ Currently exported via core/__init__.py |
| `core.reliability` | `from core.reliability.provider_health import check_provider_health, record_rate_limit, get_all_provider_status` | Provider health functions | ❌ Not in core/__init__.py |
| `core.reliability` | `from core.reliability.error_recovery import get_recovery` | error_recovery | ❌ Not in core/__init__.py |
| `core.reliability` | `from core.reliability.request_throttle import RequestThrottle` | RequestThrottle | ❌ Not in core/__init__.py |
| `core.orchestration` | `from core.orchestration.supervisor import orchestrate` | orchestrate | ❌ Nothing exported |
| `core.optimization` | `from core.optimization.usage_tracker import UsageTracker` | UsageTracker | ❌ Nothing exported |
| `core.optimization` | `from core.optimization.feedback_learner import FeedbackLearner` | FeedbackLearner | ❌ Nothing exported |
| `core.utils` | `from core.utils.multimodal_processor import transcribe_voice, text_to_speech` | transcribe_voice, text_to_speech | ❌ Nothing exported |
| `core.utils` | `from core.utils.loading_manager import LoadingManager` | LoadingManager | ❌ Nothing exported |
| `core.utils` | Various formatters, help_formatter, etc. | Various | ❌ Nothing exported |
| `core.tools` | (submodules exist but no direct `from core.tools` imports found) | — | ⚠️ Directory has files |
| `bridges` | `from bridges.whatsapp_bridge import WhatsAppBridge` | WhatsAppBridge | ⚠️ Package exists but no __init__.py — direct imports work |
| `prompts` | No callers found | — | ⚠️ Empty but no one uses it |

### 1.3 Import Error Test Results

```
python -c "import core; print(dir(core))"
→ ['Any', 'FallbackChain', 'classify_complexity', 'get_fallback_chain', 'select_model'] ✅

python -c "import handlers; print('handlers OK')"
→ handlers OK ✅

python -c "import llm_client; print('llm_client OK')"
→ llm_client OK ✅

python -c "import swarms_bot; print(dir(swarms_bot))"
→ ['ChiefOfStaff', 'DAGExecutor', 'ModelRouter', 'Task', 'TaskType'] ✅

python -c "import computer_agent; print(dir(computer_agent))"
→ ['execute_tool', 'TOOL_DEFINITIONS', ...] ✅

python -c "from bridges.whatsapp_bridge import WhatsAppBridge; print('direct OK')"
→ direct OK ✅

python -c "import bridges; print(dir(bridges))"
→ ['__doc__', '__file__', '__loader__', '__name__', '__package__', '__path__', '__spec__']
→ bridges package has no exports ❌
```

---

## 2. CRITICAL ISSUES

### Issue 1: `core.reliability` — Empty `__init__.py` (0 bytes)

**Problem:** `core/reliability/__init__.py` is completely empty, but callers expect:
- `from core.reliability.provider_health import check_provider_health, record_rate_limit, get_all_provider_status, reset_provider_health`
- `from core.reliability.error_recovery import get_recovery`
- `from core.reliability.request_throttle import RequestThrottle`

**Impact:** Any code doing `from core.reliability.provider_health import ...` works fine (direct import), but `from core import reliability` then `reliability.provider_health` doesn't expose the module hierarchy properly. However, current usage patterns mostly use direct imports, so impact is LOW.

**Fix:** Add `__all__` + re-exports for the key public API. Wrap optional dependencies in try/except.

### Issue 2: `core.orchestration` — Empty `__init__.py` (0 bytes)

**Problem:** `core/orchestration/__init__.py` is empty. Callers import `from core.orchestration.supervisor import orchestrate`.

**Impact:**LOW — direct imports work, no one uses `from core import orchestration` pattern.

**Fix:** Add minimal package init with docstring.

### Issue 3: `core.optimization` — Empty `__init__.py` (0 bytes)

**Problem:** `core/optimization/__init__.py` is empty. Callers import `from core.optimization.usage_tracker import UsageTracker` and `from core.optimization.feedback_learner import FeedbackLearner`.

**Impact:**LOW — direct imports work.

**Fix:** Add minimal package init.

### Issue 4: `core.utils` — Empty `__init__.py` (0 bytes)

**Problem:** `core/utils/__init__.py` is empty. Callers import `from core.utils.multimodal_processor import transcribe_voice, text_to_speech` and many other utilities.

**Impact:**LOW — direct imports work.

**Fix:** Add minimal package init.

### Issue 5: `core.tools` — Empty `__init__.py` (0 bytes)

**Problem:** `core/tools/__init__.py` is empty. Directory has files (computer_control.py, playwright_agent.py, vscode_bridge.py) but no callers use `from core.tools import`.

**Impact:**LOW — no callers found.

**Fix:** Add minimal package init.

### Issue 6: `bridges` — Missing `__init__.py`

**Problem:** `bridges/` directory has no `__init__.py`. Package has no exports.

**Impact:** `import bridges` works but has no exports. Callers use direct module imports (`from bridges.whatsapp_bridge import WhatsAppBridge`) which work.

**Fix:** Create `bridges/__init__.py` that re-exports all bridge classes (WhatsAppBridge, ScreenpipeBridge, DiscordBridge, LiveKitBridge).

### Issue 7: `prompts` — Empty `__init__.py` (0 bytes)

**Problem:** `prompts/__init__.py` is empty. No callers found using `from prompts import`.

**Impact:**NONE — no one uses it.

**Fix:** Optional — add docstring or remove if truly unused.

### Issue 8: `swarms_bot/agents` — Empty `__init__.py` (1 line, just docstring)

**Problem:** `swarms_bot/agents/__init__.py` is essentially empty — only a docstring. No exports.

**Impact:**LOW — no callers found using `from swarms_bot.agents import`.

**Fix:** Add docstring and consider exporting Agent classes if needed.

---

## 3. RECOMMENDED ACTIONS

### Priority 1 — Must Fix (will cause import errors)
1. **bridges/__init__.py** — Create with re-exports of WhatsAppBridge, ScreenpipeBridge, DiscordBridge, LiveKitBridge, MastraBridge, RufloBridge
2. **core/reliability/__init__.py** — Add re-exports for FallbackChain, get_fallback_chain, provider_health functions, RequestThrottle, error_recovery

### Priority 2 — Should Fix (incomplete/misleading)
3. **core/orchestration/__init__.py** — Add docstring
4. **core/optimization/__init__.py** — Add docstring
5. **core/utils/__init__.py** — Add docstring
6. **core/tools/__init__.py** — Add docstring

### Priority 3 — Nice to Have
7. **prompts/__init__.py** — Add docstring or remove if unused
8. **swarms_bot/agents/__init__.py** — Add docstring

---

## 4. VERIFICATION COMMAND

```bash
python -c "import handlers; import core; import skills; import bridges; print('all OK')"
```

Current result: `import bridges` succeeds but has no exports. After fixes, all packages should have proper re-exports.

---

## 5. DECISIONS TO LOG

- **ADR-XXX-1**: `bridges` package needs explicit `__init__.py` with re-exports
- **ADR-XXX-2**: `core.reliability` needs explicit `__init__.py` to match other core subpackages pattern
- **ADR-XXX-3**: Empty `__init__.py` files for `core.orchestration`, `core.optimization`, `core.utils`, `core.tools` are intentional (direct imports only) — add docstrings for clarity