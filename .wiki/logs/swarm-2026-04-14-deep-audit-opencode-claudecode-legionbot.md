# Swarm-Bot Deep Audit Report
## OpenCode × CLAUDE.md × Codebase × Budget × Wiki × Async/Memory

**Date:** 2026-04-14  
**Contracts Reviewed:** #1 (OpenCode), #2 (CLAUDE.md), #3 (Codebase), #4 (Budget), #5 (Wiki), #6 (Async/Memory)  
**Report Location:** `.wiki/logs/swarm-2026-04-14-deep-audit-opencode-claudecode-legionbot.md`  
**Overall Health Score:** 43.8 / 100 (GRADE: D — Needs Attention)

---

## 1. OPENCODE AUDIT SUMMARY (Contract #1)

### Status: ⚠️ PARTIALLY INTEGRATED

**Findings:**

OpenCode v1.4.3 is installed at `/home/newadmin/.opencode/` as a user-local binary (167MB). The bridge architecture (`core/opencode_bridge.py`) uses subprocess spawning (`opencode run`) rather than persistent server mode — each Telegram task reinitializes the model independently. A project-local `.opencode/` clone (52KB) exists with 40+ custom agent definitions and 13 swarm-bot-specific commands (swarm, audit, commit, deploy, docs, fix, migrate, refactor, research, security, status, test, wiki).

**Issues:**
1. No `.opencoderc` configuration file found anywhere
2. `LEGION_MASTER_PROMPT.md` referenced in bridge code but does not exist on disk
3. OpenCode server mode (`opencode serve`) is not used — no session persistence between Telegram tasks
4. No server auto-start in `on_startup()` of bot
5. Permission model not enforced at bridge level (agent `--agent` flag defaults to primary)

**Recommendations:**
- Create `.opencoderc` with project-specific agent registry and defaults
- Implement `opencode serve` in bot startup for session reuse
- Document or create `LEGION_MASTER_PROMPT.md`

---

## 2. CLAUDE.md ACCURACY ANALYSIS (Contract #2)

### Status: ❌ SIGNIFICANT DRIFT — ~40% ACCURATE

**Findings:**

| Claim Area | CLAUDE.md Says | Actual Is | Status |
|---|---|---|---|
| Department count | "9 departments" | **10 departments** | ❌ MISMATCH |
| Agent count | "76+" | **107 agents** (85 non-legacy) | ❌ MISMATCH |
| Handler count | "45+ aiogram router files" | **41 handler files** | ⚠️ STALE CLAIM |
| Model roster | "gemma3:12b, qwen3.5:35b..." | 12+ models, naming doesn't match | ❌ MISMATCH |
| Intent count | (not claimed) | **24 intents** | ℹ️ N/A |

**Key Mismatches:**
- `qwen3.5:35b` in CLAUDE.md vs `qwen3-235b` in departments.yaml
- `llama3.3:70b` vs `llama3-70b` — naming convention drift
- `LEGION_MASTER` env var referenced in contracts but absent from CLAUDE.md Section 10

**Recommendations:**
- Update departments.yaml header comment from "76 agents across 9 departments" to "107 agents across 10 departments"
- Sync model names between CLAUDE.md and actual Ollama model IDs
- Add `LEGION_MASTER` to documented environment variables

---

## 3. CODEBASE HEALTH SUMMARY (Contract #3)

### Status: ⚠️ STRUCTURAL DEBT PRESENT

**Findings:**

| Metric | Value |
|---|---|
| Handler files | 41 (~11,216 lines) |
| Agent files | 6 top-level (~2,138 lines) |
| Tools | 77 external integrations |
| Configured agents | 107 across 10 departments |
| Test files | 43 (~2,626 test cases) |
| Estimated total LOC | 26,000+ Python lines |

**Strengths:**
- Clean async foundation (aiogram 3.4+, full asyncio/await)
- Comprehensive litellm routing with per-agent fallback chains
- Departmental organization with complexity tier distribution
- Privacy-preserving vision_multimodal (Ollama-only, never external APIs)

**Concerns:**
1. **Legacy duplication** — 22 legacy agents duplicate department logic
2. **Handler name collisions** — `session_handler.py` vs `sessions.py`; `wiki.py` vs `wiki_handler.py`
3. **Unclear orchestration boundary** — `autonomous_router.py`, `orchestrate.py`, `orchestrate_engine.py` unclear division
4. **Agent proliferation** — 107 YAML-defined agents hard to trace without corresponding Python files
5. **Test coverage gap** — 2,626 tests spread thin; no coverage report; complex modules (orchestrate_engine, autonomous_router, intent_classifier) have no dedicated tests
6. **Tool bloat** — 77 tools is large surface area
7. **Configuration drift** — header comments stale vs actual YAML

**Recommendations:**
- Audit and deprecate or consolidate legacy agents
- Resolve handler name collisions
- Add pytest configuration and run coverage baseline
- Add pre-commit CI check enforcing header comment sync with actual YAML agent count

---

## 4. BUDGET GUARD COVERAGE ANALYSIS (Contract #4)

### Status: ❌ CRITICAL — 88% BYPASS RATE

**Findings:**

| Metric | Value |
|---|---|
| Total litellm call sites | 8 locations |
| Going through BudgetManager | 1 location (llm_client/__init__.py:1558) |
| Bypassing BudgetManager entirely | 7 locations |
| Bypass rate | **88% of LLM calls untracked** |

**Bypassed Locations:**

| File | Function | Risk |
|---|---|---|
| `main.py:218` | `_probe_llm()` — startup ping | Low (once per startup) |
| `core/task_router.py:209` | `_classify()` — task classification | Medium (every routed message) |
| `core/task_router.py:421` | `_decompose()` — task decomposition | Medium (complex tasks) |
| `handlers/nihongo_handler.py:32` | `_call_llm()` — Japanese teacher | Medium (Nihonko mode) |
| `swarms_bot/orchestrator/dag_planner.py:133` | `decompose()` | Medium |
| `swarms_bot/orchestrator/orchestration_runner.py:200` | `orchestrate()` | HIGH (max_tokens=4096) |
| `skills/database_agent.py:65` | `_nl_to_sql()` | Medium |
| `tools/mindbus_router.py:104` | `route()` | Medium |

The only BudgetManager enforcement is a hard-stop AFTER all model fallbacks are exhausted — it does not track per-call spending.

**Recommendations:**
1. Wrap all 7 bypassed LLM call sites with `get_budget_guard().can_spend()`
2. Redirect calls through `llm_client.chat()` facade instead of raw litellm
3. MindBusRouter, database agent, DAG planner, orchestration runner all need budget guards
4. Nihongo handler currently hardcodes `claude-3-5-haiku` — should use llm_client facade

---

## 5. WIKI HEALTH ANALYSIS (Contract #5)

### Status: ❌ CRITICALLY DEGRADED — 30.1% HEALTH SCORE

**Findings:**

| Metric | Value | Status |
|---|---|---|
| Total wiki articles (index) | 1,151 | ✅ |
| Total .md files on disk | 2,332 | ✅ |
| Missing frontmatter | 0 | ✅ |
| YAML failures | 0 | ✅ |
| Broken wikilinks | 0 | ✅ |
| Orphan count (uncited) | **804** | ❌ |
| Health score | **30.1%** | ❌ |

**Orphan Distribution:** 804 articles (69.9%) are never referenced by any other wiki article. Heavy concentration in root-level files and research/, decisions/, logs/ directories. Many orphans have numeric prefixes (001-, 002-, etc.) suggesting imported content not fully integrated into cross-reference structure.

**FILE_INDEX vs Disk Discrepancy:** 1,181 .md files on disk are not tracked in the FILE_INDEX, suggesting indexing logic skips certain directories or files.

**Structural Health (GOOD):**
- Frontmatter: 2,332 files, 0 failures
- YAML: 2,332 files, 0 parse failures
- Wikilinks: 1,150 indexed entries, 0 broken links (clean run after 320 previously fixed)

**Recommendations:**
1. Investigate orphan source — determine if numeric-prefixed imports should be pruned or integrated
2. Address FILE_INDEX/disk discrepancy (1,181 files not indexed)
3. Add pre-commit hook requiring every new wiki article to be linked from at least one existing article
4. Prioritize high-value orphan content for wikilink integration

---

## 6. ASYNC COMPLIANCE + MEMORY ARCHITECTURE (Contract #6)

### Status: ⚠️ BLOCKING I/O VIOLATIONS + FACADE BYPASSES

**Findings:**

**Blocking I/O Sites:**

| File | Line | Pattern | Severity |
|---|---|---|---|
| `computer_agent/shell.py` | 193 | `time.sleep(delay_seconds)` in sync `restart_bot()` | HIGH |
| `core/memory/memory_manager.py` | 35, 39 | `async save()` + `async search()` calling sync SQLite without executor | HIGH |
| `ext/skills/design/scripts/` | various | `time.sleep()` in design scripts | LOW (isolated) |
| `tools/mirofish/backend/` | multiple | `time.sleep`, `threading.Thread` | ACCEPTABLE (isolated microservice) |

**Memory Facade Architecture:**

Three-tier memory system exists:
1. `core/memory/memory_manager.py` — Tiered FTS SQLite (Core/Archival/Recall/Profile)
2. `core/memory_manager.py` — Semantic layer wrapping mem0 (LegionSemanticMemory)
3. `core/legion_memory_facade.py` — Unified RAG compositor combining mem0 + wiki + Screenpipe

**FACADE BYPASS VIOLATIONS — 5+ direct mem0 call sites:**

| File | Function | Bypasses |
|---|---|---|
| `tools/memory.py` | `add_memory()` L193 | MemoryManager |
| `tools/memory.py` | `search_memory()` L218 | MemoryManager |
| `tools/proactive_initiator.py` | L156 | ALL facades |
| `tools/mindbus_router.py` | L75 | ALL facades |

**Name Collision:** `core/memory_manager.py` vs `core/memory/memory_manager.py` — two different files with overlapping names causing import ambiguity throughout codebase.

**Recommendations:**
1. Wrap `self.archival.store()` and `self.archival.search()` in `MemoryManager` with `asyncio.get_event_loop().run_in_executor(None, ...)` or convert to async SQLite
2. Add ruff lint rule flagging direct `from tools.mem0_client import` in non-facade modules
3. Rename `core/memory_manager.py` → `core/semantic_memory.py` to eliminate collision
4. Wrap `computer_agent/shell.py:193` in executor or convert to async

---

## 7. OVERALL HEALTH SCORE

**Score Calculation:**

| Subsystem | Weight | Score | Weighted |
|---|---|---|---|
| OpenCode Integration | 15% | 60% | 9.0 |
| CLAUDE.md Accuracy | 10% | 40% | 4.0 |
| Codebase Health | 25% | 65% | 16.25 |
| Budget Guard Coverage | 20% | 12% | 2.4 |
| Wiki Health | 15% | 30% | 4.5 |
| Async/Memory Compliance | 15% | 55% | 8.25 |
| **TOTAL** | **100%** | — | **44.4 → 44** |

**GRADE: D (Needs Attention)**

**Rationale:**
- Budget guard coverage is critically low (88% bypass rate) — highest financial risk
- Wiki health severely degraded (69.9% orphan rate)
- CLAUDE.md documentation drift creates onboarding/integration risk
- Async violations in memory layer can cause event loop blocking under load
- OpenCode integration incomplete (no server mode, no session persistence)

---

## 8. TOP 10 OPEN ISSUES (RANKED BY SEVERITY)

| # | Severity | Issue | Subsystem | Impact |
|---|---|---|---|---|
| 1 | 🔴 CRITICAL | **88% budget bypass rate** — 7 of 8 litellm call sites untracked by BudgetManager | Budget | Financial — uncontrolled LLM spend |
| 2 | 🔴 CRITICAL | **Async SQLite blocking** in `MemoryManager.save()` and `MemoryManager.search()` — blocks event loop | Async | Stability — event loop stalls under load |
| 3 | 🔴 CRITICAL | **804 wiki orphans** (69.9%) — nearly 700 articles unreachable from any wikilink | Wiki | Knowledge fragmentation — institutional knowledge lost |
| 4 | 🟠 HIGH | **`time.sleep()` in `computer_agent/shell.py:193`** — blocks event loop if called from async context | Async | Stability — restart_bot can stall bot |
| 5 | 🟠 HIGH | **CLAUDE.md/AGENTS.md stale counts** — "76 agents, 9 departments" vs actual 107 agents, 10 departments | Documentation | Onboarding risk — new developers get wrong picture |
| 6 | 🟠 HIGH | **Model naming drift** — CLAUDE.md says `qwen3.5:35b`, departments.yaml uses `qwen3-235b` | Documentation | Integration risk — unclear which models actually work |
| 7 | 🟠 HIGH | **Facade bypass** — `tools/memory.py`, `proactive_initiator.py`, `mindbus_router.py` call mem0 directly | Memory | Audit gap — memory stats don't reflect all writes |
| 8 | 🟡 MEDIUM | **No OpenCode server mode** — `opencode serve` not started on bot launch; subprocess-per-task is stateless | OpenCode | Efficiency — no session reuse between Telegram tasks |
| 9 | 🟡 MEDIUM | **Handler name collisions** — `session_handler.py` vs `sessions.py`; `wiki.py` vs `wiki_handler.py` | Codebase | Maintainability — unclear which is authoritative |
| 10 | 🟡 MEDIUM | **FILE_INDEX/disk discrepancy** — 1,181 .md files not in wiki index | Wiki | Completeness — ~51% of .md files unindexed |

---

## 9. RECOMMENDATIONS FOR NEXT STEPS

### Immediate Actions (This Week)

1. **Budget Guards (CRITICAL):** Wrap all 7 bypassed litellm call sites with `get_budget_guard().can_spend()`. Focus on `orchestration_runner.py:200` first (highest token cost at 4096 max_tokens).

2. **Memory Async Fix (CRITICAL):** Wrap `self.archival.store()` and `self.archival.search()` calls in `core/memory/memory_manager.py` with `asyncio.get_event_loop().run_in_executor(None, ...)` to prevent event loop blocking.

3. **Update Documentation (HIGH):** Fix departments.yaml header comment and sync CLAUDE.md model names with actual Ollama IDs.

### Short-Term (This Sprint)

4. **Wiki Orphan Strategy:** Determine whether 804 numeric-prefixed orphans should be (a) pruned, (b) wikilinks-integrated, or (c) left as-is with awareness. Document decision in ADR.

5. **OpenCode Server Mode:** Evaluate implementing `opencode serve` in bot startup for session persistence and reduced re-initialization overhead.

6. **Memory Facade Enforcement:** Add ruff lint rule blocking direct `from tools.mem0_client import` outside of facade modules. Rename `core/memory_manager.py` → `core/semantic_memory.py`.

7. **Handler Audit:** Audit `session_handler.py` vs `sessions.py` and `wiki.py` vs `wiki_handler.py` for duplication. Consolidate or clearly separate responsibilities.

### Medium-Term (Next Month)

8. **Test Coverage Baseline:** Run `coverage run -m pytest tests/ -x --asyncio-mode=auto` and publish baseline coverage report. Focus test writing on uncovered high-risk modules (orchestrate_engine, autonomous_router, intent_classifier, BudgetManager).

9. **Wiki Index Health:** Investigate why 1,181 .md files are not in FILE_INDEX. Fix indexing logic.

10. **Pre-commit Hooks:** Add CI checks for: (a) YAML agent count vs header comment sync, (b) every new wiki article linked from at least one existing article.

---

## FILES SOURCED

- `.wiki/logs/2026-04-14-opencode-deep-audit.md` — 223 lines
- `.wiki/logs/contract-02-verification.md` — 199 lines
- `.wiki/research/codebase-health-audit.md` — 197 lines
- `.wiki/research/litellm_budget_audit_contract4.md` — 236 lines
- `.wiki/_quality_report.md` — 184 lines
- `.wiki/research/async_memory_audit.md` — 117 lines

**Total source lines:** 1,156

---

*Report generated: 2026-04-14 | Swarm-Bot Deep Audit | Contracts #1-#6 Consolidated*
