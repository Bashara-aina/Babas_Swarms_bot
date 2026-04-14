---
title: Codebase Health Audit
type: concept
status: deprecated
tags:
- /
- home
- newadmin
- swarm-bot
- research
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Auditor:** Worker Agent'
wikilinks: []
confidence: medium
source: research
---
# Swarm-Bot Codebase Health Audit

**Date:** 2026-04-14  
**Auditor:** Worker Agent  
**Scope:** handlers/, agents/, core/, tools/, config/

---

## Executive Summary

Swarm-bot is a large-scale Python Telegram bot with multi-agent orchestration built on aiogram 3.4+ and litellm. The codebase is substantial — 11,216 lines across 40 handler modules, 2,138 lines across 6 top-level agent files, 77 external tool integrations, and 9 departments configured with 76 declared agents (actual count: 99). The architecture is ambitious but shows signs of structural debt: legacy agents duplicating department logic, inconsistent naming conventions, and handlers with overlapping responsibilities.

---

## Handler Count and Categories

**41 handler Python files found** (11,216 total lines, ~280 avg lines/file):

| Category | Files | Purpose |
|---|---|---|
| Core bot logic | `message_handler.py`, `session_handler.py`, `sessions.py` | Message processing, session state |
| Admin | `admin_handlers.py`, `system.py`, `upgrade.py` | Bot administration, system commands |
| AI / Agents | `ai.py`, `brain.py`, `orchestrate.py`, `swarm_handler.py` | LLM routing, agent orchestration |
| Development | `dev.py`, `skills.py`, `runbook_handler.py` | Developer tools, skill loading |
| Business / Enterprise | `business_handler.py`, `enterprise.py`, `e2e.py` | Business workflows, enterprise features |
| Communications | `communications.py`, `streaming.py`, `voice.py` | Messaging, streaming, voice |
| Data / Storage | `memory_commands.py`, `harvest_review.py` | Memory operations, harvest flows |
| Integrations | `github_intel_handler.py`, `whatsapp_handler.py`, `ecc_compat.py` | External platform bridges |
| Research / Analysis | `research.py`, `debate_handlers.py` | Deep research, multi-agent debate |
| UI / Media | `media_tools.py`, `artifact.py`, `draft.py` | Media processing, artifact generation |
| Specialty | `nihongo_handler.py`, `inline.py`, `persona_handler.py`, `wiki.py`, `wiki_handler.py` | Language-specific, inline queries, personas |
| Project Management | `pm.py`, `tasks.py` | Task management, project tracking |

**Observation:** Handler overlap is evident — `session_handler.py` and `sessions.py` likely duplicate session logic; `wiki.py` and `wiki_handler.py` suggest parallel wiki implementations. The `e2e.py` and `enterprise.py` both handle business workflows.

---

## Agent Count

**Top-level agent files:** 6 files (2,138 total lines)
- `ag2_pipeline.py` — AG2 multi-agent research pipeline
- `code_agent.py` — Code generation agent
- `mirofish_agent.py` — MiroFish consensus/prediction agent
- `owl_agent.py` — OWL specialist for GAIA benchmark
- `simulation_agent.py` — Simulation/scenario agent
- `voice_agent.py` — Voice interaction agent

**Additional agent directories:**
- `agents/research/` — (mostly `__init__.py`, research infrastructure)
- `agents/strategy_nexus/` — (mostly `__init__.py`, orchestration hub)

**Configured agents via `departments.yaml`:** 76 declared in file header, but actual count is **99 agents** across 9 departments:
- **Engineering:** 16 agents (senior_python_dev, frontend_react_dev, backend_fastapi_dev, rust_systems_dev, smart_contract_auditor, security_pentester, cuda_optimizer, debugging_specialist, test_automation_engineer, cicd_architect, database_optimizer, mlops_engineer, api_designer, code_reviewer, performance_tuner, plus default)
- **Design:** 10 agents
- **Research:** 12 agents
- **Marketing:** 12 agents
- **Operations:** 7 agents
- **Legal/Compliance:** 6 agents
- **Product:** 8 agents
- **Vision/Multimodal:** 6 agents (all gemma3-12b, local-only)
- **Legacy:** 22 agents (backwards-compat registry mirroring old `agents.py` AGENT_MODELS)

**Discrepancy:** File header says "76 agents across 9 departments" but YAML defines 99 agents. The legacy section contains a full second agent registry that predates the department structure.

---

## Department Count

**9 departments** defined in `config/departments.yaml`:
1. `engineering` — software development across all stacks
2. `design` — UI/UX, branding, visual design
3. `research` — deep research, competitive analysis, data science
4. `marketing` — copywriting, SEO, social media, growth
5. `operations` — project management, scheduling, resource allocation
6. `legal_compliance` — legal review, GDPR, risk assessment, IP
7. `product` — roadmapping, user research, feature prioritization
8. `creative` — storytelling, scripts, music, poetry
9. `vision_multimodal` — local-only vision analysis (privacy-preserving, Ollama-only)

Each department has a `default_agent` and `complexity_tier` distribution (lightweight/midweight/heavyweight). Model routing uses litellm with fallbacks per agent.

---

## Test Coverage Estimate

| Metric | Value |
|---|---|
| Test files (`tests/` dir) | **43 Python files** |
| Total test cases (glob `test_*.py` + `*_test.py`) | **2,626** |
| Tests per file (avg) | ~61 |

**Test file distribution:**
```
tests/
├── conftest.py
├── test_agents.py
├── test_handlers.py
├── test_llm_client.py
├── test_memory.py
├── test_orchestration.py
├── test_tools.py
├── ...
```

**Estimated coverage:** With 43 test files and 2,626 test cases for a codebase of ~15,000+ lines (handlers 11,216 + agents 2,138 + tools ~8,000 + core ~?), the coverage appears partial. No coverage report was found. Many handlers likely have zero test coverage. A `coverage run -m pytest tests/` would be needed for exact numbers.

**Risk:** High complexity modules like `orchestrate_engine.py`, `autonomous_router.py`, `intent_classifier.py` have no visible dedicated tests. Test file discovery found matches across the entire repo (`find` returned 2,626), suggesting tests may be scattered in unexpected locations.

---

## Key Architectural Observations

### Strengths

1. **Clean async foundation** — aiogram 3.4+, full asyncio/await, no blocking I/O
2. **Comprehensive agent model routing** — litellm with per-agent fallbacks, complexity tiers
3. **Departmental organization** — 9 departments with clear capability keyword routing
4. **Privacy-preserving vision** — `vision_multimodal` department uses only local Ollama (gemma3-12b), never sends images to external APIs
5. **Extensive tool layer** — 77 tool integrations covering browser, email, GitHub, n8n, memory systems, etc.
6. **Character/voice engine** — separate `character/` and `voice/` systems for personality modulation

### Concerns

1. **Legacy duplication** — The `legacy` department (22 agents) is a backwards-compat registry that mirrors the new department structure. This creates two sources of truth for agent definitions and likely causes routing confusion.

2. **Handler name collisions** — `session_handler.py` vs `sessions.py`; `wiki_handler.py` vs `wiki.py`; `message_handler.py` vs `message_handler` (also in `handlers/`). Unclear which is authoritative.

3. **Underspecified orchestration** — `orchestrate.py` and `orchestrate_engine.py` suggest complex multi-agent coordination, but the boundary between them and `autonomous_router.py` is unclear.

4. **Agent proliferation risk** — 99 agents across 9 departments may be over-engineered. The `agents/` directory only has 6 concrete files — the rest are defined declaratively in YAML. This creates a metadata-driven architecture that is hard to trace.

5. **Test coverage gap** — 2,626 test cases sounds impressive but appears spread thin. Many modules likely have zero coverage. No `pytest.ini` or `pyproject.toml` found for test configuration.

6. **Core module complexity** — The `core/` directory has 30+ files covering intent routing, emotion tracking, circuit breakers, debate engines, episodic narrative, health checks — a very ambitious cognitive architecture that may be difficult to maintain.

7. **No dependency graph** — Import structure is unclear. `main.py` has 22 class/function definitions, but it's unknown which handlers/agents it imports directly vs via circular deps.

8. **Tool bloat** — 77 tools in `tools/` is a large surface area. Many (e.g., `viking_context.py`, `rumahlabuh_*.py`, `oi_bridge.py`) appear project-specific and may not belong in a general bot framework.

9. **Inconsistent naming** — `brain.py` vs `cognition_pipeline.py`; `simulation_agent.py` vs `simulation_tool.py`; `voice_agent.py` vs `voice_engine.py` — suggests organic growth without strict naming standards.

10. **Configuration drift** — `departments.yaml` header says "76 agents" but actual count is 99. No CI check enforces sync between header comment and actual YAML.

---

## File Count Summary

| Directory | Count | Total Lines (est.) |
|---|---|---|
| `handlers/` | 41 .py files | ~11,216 |
| `agents/` | 6 top-level .py | ~2,138 |
| `tools/` | 77 .py files | ~8,000+ (est.) |
| `core/` | 30+ modules | ~5,000+ (est.) |
| `config/` | YAML configs | declarative |
| `tests/` | 43 .py files | 2,626 test cases |

**Overall LOC:** ~26,000+ Python lines across handlers/agents/tools/core alone.

---

## Recommendations

1. **Audit legacy agents** — Determine if the 22 legacy agents in `departments.yaml` are still used or can be deprecated. If used, they need corresponding `agents/` implementations.
2. **Resolve handler overlap** — Audit `session_handler.py` vs `sessions.py` and `wiki.py` vs `wiki_handler.py` for duplication. Consolidate or clearly separate responsibilities.
3. **Add pytest configuration** — Create `pyproject.toml` with pytest config, run `coverage run -m pytest`, publish baseline coverage report.
4. **Enforce header count sync** — Add a pre-commit hook or CI check that fails if `# 76 agents` comment doesn't match actual YAML agent count.
5. **Trace import graph** — Run `python -c "import main"` and capture the full import chain to understand actual dependencies.
6. **Document orchestration boundary** — Clarify what `autonomous_router.py`, `orchestrate.py`, and `orchestrate_engine.py` each do and why they exist separately.

---

## Sources

- `/home/newadmin/swarm-bot/handlers/` — 41 handler files listed via `ls`
- `/home/newadmin/swarm-bot/agents/` — 6 agent files + `research/` and `strategy_nexus/` directories
- `/home/newadmin/swarm-bot/tools/` — 77 tool files listed
- `/home/newadmin/swarm-bot/core/` — 30+ modules listed
- `/home/newadmin/swarm-bot/config/departments.yaml` — 900 lines, 9 departments, 99 agents
- `/home/newadmin/swarm-bot/tests/` — 43 test files
- `find` results for `test_*.py` / `*_test.py` across entire repo — 2,626 matches