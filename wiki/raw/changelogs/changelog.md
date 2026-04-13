# Changelog

All notable changes to Legion (Babas Swarms Bot) are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [6.0.0] — 2026-04-07 — THE HUMANIZATION UPDATE

### The Problem This Solves
Legion was technically capable but felt robotic:
- Forgot everything between sessions
- Only worked when explicitly commanded
- Spoke in flat transactional text
- Was a yes-man with no opinions
- Had no inner life or emotional state

### What's New

**Persistent 3-Tier Memory (letta + mem0 architecture)**
- CoreMemory: high-priority facts always in every prompt
- ArchivalMemory: unlimited SQLite FTS5 store
- RecallMemory: full permanent conversation history
- Auto-extracts important facts from conversations

**Temporal Knowledge Graph (graphiti architecture)**
- Tracks facts over time with validity windows
- Seeded with known facts about Bashara from day one

**User Profile (memobase architecture)**
- Permanent profile of who Bashara is, not just what was said
- Grows automatically from interactions and explicit `/teach`

**Emotion Engine (openfeelz-inspired)**
- OCEAN-backed personality framing and PAD emotional state
- Tracks curiosity, frustration, energy, connection
- Persists across sessions and decays toward baseline

**Reflection Engine (generative_agents + Reflexion-inspired)**
- Micro-reflection after each turn
- Deep reflection every 10 turns
- Stores observations, technical opinions, lessons, concerns

**Autonomous Skill Selection (ReAct-style routing)**
- Plain text now routes automatically to chat/research/code/system/computer/memory
- Legacy slash commands remain supported

**New Commands**
- `/memory` — memory stats + core facts
- `/remember <fact>` — explicit permanent memory
- `/recall <query>` — archival memory search
- `/emotion` — current emotional state snapshot
- `/opinions` — current reflection/opinion block
- `/forget <key>` — remove core-memory key
- `/profile` — persistent user profile block
- `/teach <correction>` — correct/profile-teach Legion

### Breaking Changes
None. Existing slash-command flows are preserved.

---

## [v4.1.0] — 2026-03-14

### Added
- `handlers/` package: `main.py` refactored from 2678 lines → 230 lines into 12 focused handler modules (`computer`, `system`, `ai`, `research`, `brain`, `sessions`, `tasks`, `dev`, `pm`, `enterprise`, `shared`, `__init__`)
- Enterprise orchestration layer (`swarms_bot/`): `ChiefOfStaff`, `BudgetManager`, `SecurityGuard`, `AuditLogger`, `CostAwareRouter`, `CostMetricsCollector`, `SessionManager`
- New commands: `/loop`, `/loop_stop`, `/loop_pause`, `/loop_resume`, `/metrics`, `/budget`, `/routing_stats`, `/security_stats`, `/audit_summary`, `/multi_execute`, `/save`, `/resume`, `/sessions`
- Autonomous goal-pursuit loop with 25-iteration cap, $0.50 cost ceiling, 30-minute timeout
- 40-test enterprise test suite covering `ChiefOfStaff`, `CostMetrics`, `BudgetManager`, `SessionManager`
- `pyproject.toml` with pytest, coverage, and ruff configuration
- GitHub Actions CI (`ci.yml`) — lint + test on every push/PR across Python 3.11 and 3.12
- GitHub Actions Release (`release.yml`) — auto GitHub Release on version tags
- `Makefile` with `install`, `test`, `lint`, `run`, `docker`, `clean` targets
- `CHANGELOG.md`, `LICENSE` (MIT), `.pre-commit-config.yaml`
- GPU passthrough in `docker-compose.yml` for RTX 3060

### Fixed
- `#3` Remove `_AGENT_CHAIN` hardcode; use `get_fallback_chain('computer')` as single source of truth
- `#6` Remove `take_screenshot()` wrapper that shadowed `computer_agent`
- `#14` Call `add_to_thread()` on `max_iterations` exit path
- `#15` Fix `chunk_output()` to hard-split lines longer than `max_length`
- `#17` Use `aiofiles` for async screenshot read in `analyze_screenshot()`
- `#20` Fix `_compact_messages()`: inject summary as `system` role, not `user`
- `#21` Add 300s wall-clock timeout on `agent_loop()` via `asyncio.wait_for()`
- `#22` Increase `_COOLDOWN` from 60s → 90s for Groq free tier
- `#32` Fix `_parse_groq_xml_tool_call()` regex to handle nested JSON with depth counter
- `#33` Fix `_strip_think_tags()` to capture ALL `<think>` blocks, not just first
- `#34` Fix `run_shell_command` to only include stderr on non-zero exit
- `#35` Add PNG validation before base64 encoding in `analyze_screenshot()`
- `#55` Remove orphan `_tool_label` entries for non-existent tools

---

## [v4.0.0] — 2026-03-08

### Added
- Full computer use: screenshot, click, type, drag, scroll, window management
- Multi-provider LLM fallback chain (Groq, Cerebras, Gemini, OpenRouter, ZAI, Ollama)
- Per-agent routing: `computer`, `coding`, `debug`, `vision`, `math`, `architect`, `analyst`, `general`
- Second brain: `/remember`, `/recall`, `/memories`, `/briefing`
- arXiv paper search + PDF analysis: `/paper`, `/ask_paper`
- Deep web research: `/scrape`, `/research`
- Background scheduler: `/monitor`, `/schedule`, `/cancel`
- Project scaffolding: `/scaffold`, `/build`
- Email client: `/email`
- Context compaction for long threads
- LLM response caching layer
- QwQ-32b reasoning mode via `/think`

### Fixed
- Display detection fallback for headless Linux environments
- Groq XML tool call recovery from `BadRequestError`
- Rate limit cooldown per provider

---

## [v3.0.0] — 2026-02-01

### Added
- Initial multi-agent swarm architecture
- `/swarm` command for parallel specialist agent execution
- Thread memory system
- Ollama local model integration