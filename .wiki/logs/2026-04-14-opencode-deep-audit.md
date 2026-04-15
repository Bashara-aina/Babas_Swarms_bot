---
title: Opencode Deep Audit
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
summary: '- **Install path**: `/home/newadmin/.opencode/` (user-local, not npm global)'
wikilinks: []
confidence: medium
source: research
---

# OpenCode Deep Audit — 2026-04-14

## 1. OpenCode Install Method

### Location & Version
- **Install path**: `/home/newadmin/.opencode/` (user-local, not npm global)
- **Binary**: `/home/newadmin/.opencode/bin/opencode` — 167MB self-contained binary
- **Version**: `1.4.3` (confirmed via `opencode --version`)
- **Package**: `@opencode-ai/plugin@1.4.3` in `package.json`
- **Plugin package**: `@opencode-ai/plugin@1.4.3` with dependencies on `@opencode-ai/sdk@1.4.3` and `zod@4.1.8`
- **Node modules**: `/home/newadmin/.opencode/node_modules/` (no global install)

### Project-Local Clone
- **Second install**: `/home/newadmin/swarm-bot/.opencode/` — 52KB, a project-local copy
  - Same package.json (`@opencode-ai/plugin@1.4.3`)
  - Same node_modules structure
  - Purpose: agent definitions and commands (not the binary itself — binary is in user's home)

### Install Method
The binary at `/home/newadmin/.opencode/bin/opencode` is the primary installation. The swarm-bot/.opencode/ is a configuration clone containing only agents/commands, not the runtime. This is NOT an npm global install — it's a user-local installation (possibly via `npm install -g` or direct binary download, with the package.json stored in user home).

---

## 2. Agent Definitions & Count

### Custom Legion Agents (swarm-bot/.opencode/agents/)
**6 dedicated pipeline agents:**
| Agent | File | Role |
|-------|------|------|
| @planner | `planner.md` | Master orchestrator, CONTRACT decomposition |
| @worker | `worker.md` | Precise execution, anti-hallucination prover |
| @reviewer | `reviewer.md` | Quality gate, read-only verification |
| @wikibot | `wikibot.md` | Wiki knowledge management |
| @verifier | `verifier.md` | Silent mechanical pre-reviewer |
| @Diff-Analyzer | `diff-analyzer.md` | Hallucination detector pre-reviewer |
| @research-agent | `research-agent.md` | Read-only research |
| @deployment-engineer | `deployment-engineer.md` | Git/deploy/infrastructure specialist |

**32 department/specialty agents:**
- `azure/`, `backend/`, `blockchain/`, `cloud/`, `data/`, `db/`, `devops/`, `docs/`, `embedded/`, `frontend/`, `gaming/`, `langspecialists/`, `marketing/`, `mcp/`, `media/`, `meta/`, `ml/`, `mobile/`, `observability/`, `platform/`, `product/`, `python/`, `research/`, `security/`, `testing/`, `typescript/`, `web/`, `windows/`

**Total custom agents**: ~40 agent definitions in swarm-bot/.opencode/agents/

### OpenCode CLI Built-in Agents (from `opencode agent list`)
OpenCode ships with ~76+ pre-built agents covering:
- **Pipeline**: build, compaction, explore, general, plan, summary, title
- **Backend**: api-architect, api-designer, api-documenter, api-security-audit, backend-architect, backend-developer, fullstack-developer, mcp-server-architect, microservices-architect, symfony-specialist, websocket-engineer
- **Blockchain**: blockchain-developer, smart-contract-auditor, smart-contract-specialist, web3-integration-specialist
- **Cloud**: arm-migration, azure-iac-exporter, azure-iac-generator, azure-infra-engineer, azure-logic-apps-expert, azure-principal-architect, azure-saas-architect, azure-verified-modules-bicep
- Plus agents for: data, db, devops, docs, embedded, frontend, gaming, langspecialists, marketing, mcp, media, meta, ml, mobile, observability, platform, product, python, research, security, testing, typescript, web, windows

### Core Pipeline Model Configuration
All Legion custom agents specify:
```yaml
model: minimax-coding-plan/MiniMax-M2.7
temperature: 0.0-0.2
maxSteps: 10-50
```
The bridge (`opencode_bridge.py`) defaults to `LEGION_DEFAULT_MODEL` env var or `openrouter/anthropic/claude-sonnet-4-5`.

---

## 3. Telegram Bridge Mechanism

### Architecture Flow
```
[Telegram /opencode command]
  → handlers/dev.py:cmd_opencode() [line 182-219]
  → core/opencode_bridge.py:build_opencode_prompt()
  → core/opencode_bridge.py:run_opencode_task() [asyncio subprocess]
  → opencode CLI binary (subprocess)
  → core/opencode_bridge.py:extract_report()
  → send_chunked() back to Telegram
```

### Key Files
| File | Lines | Purpose |
|------|-------|---------|
| `handlers/dev.py` | 182-219 | `/opencode` Telegram command handler |
| `core/opencode_bridge.py` | 77 | Bridge module: prompt building, subprocess execution, report extraction |

### Bridge Functions

**`build_opencode_prompt(telegram_msg, project, user)`**
- Wraps the Telegram message in a Legion master prompt template
- Includes: user, project, timestamp, instruction text
- References LEGION MASTER PROMPT pipeline stages: STAGE 0-5

**`run_opencode_task(prompt, project_dir, agent, model, timeout)`**
- Uses `asyncio.create_subprocess_exec()` — async, not threading
- Command: `opencode run [prompt] --model [model] [--agent [agent]]`
- Default timeout: 1800s (30 minutes)
- Default model: `LEGION_DEFAULT_MODEL` env var or `openrouter/anthropic/claude-sonnet-4-5`
- Environment: `OPENCODE_DISABLE_AUTOUPDATE=true` set
- Zombie prevention: `await process.wait()` after `kill()` and on error paths

**`extract_report(opencode_output)`**
- Looks for `━━━━━━━━━━━━━━━━━━━━━━━━━━━` marker in output
- Returns last 4000 chars from marker position
- Fallback: last 2000 chars of output

### How OpenCode → Legion sends tasks
The bridge uses **subprocess spawning** (`opencode run`), NOT the OpenCode server mode (`opencode serve`). Each Telegram task spawns a fresh subprocess that:
1. Receives the prompt via CLI argument
2. Executes with the configured model
3. Streams output back to stdout
4. Exits when complete

---

## 4. Tool Integrations

### OpenCode CLI Commands Available
```
opencode completion    Shell completion script
opencode acp           ACP (Agent Client Protocol) server
opencode mcp           MCP (Model Context Protocol) servers
opencode [project]     Start opencode TUI [default]
opencode attach        Attach to running server
opencode run           Run with message
opencode debug         Debugging tools
opencode providers     Manage AI providers/credentials
opencode agent         Manage agents
opencode upgrade       Upgrade opencode
opencode serve         Headless server
opencode web           Web interface
opencode models        List available models
opencode stats         Token usage/cost
opencode export/import Session data
opencode github        GitHub agent
opencode pr            Fetch/checkout PR branch
opencode session       Manage sessions
opencode plugin        Install plugins
opencode db            Database tools
```

### Swarm-Bot Custom Commands (swarm-bot/.opencode/command/)
| Command | Purpose |
|---------|---------|
| `swarm.md` | Multi-agent pipeline orchestrator (planner→worker→DiffAnalyzer→reviewer) |
| `audit.md` | Conduct code/system audits |
| `commit.md` | Git commit operations |
| `deploy.md` | Deployment operations |
| `docs.md` | Documentation generation |
| `fix.md` | Bug fixes |
| `migrate.md` | Data/code migrations |
| `refactor.md` | Code refactoring |
| `research.md` | Research tasks |
| `security.md` | Security operations |
| `status.md` | Status checks |
| `test.md` | Test operations |
| `wiki.md` | Wiki/documentation tasks |

### MCP Support
- `opencode mcp` manages MCP servers (Model Context Protocol)
- `mcp/` directory exists in agents with MCP-related agents

---

## 5. Identified Gaps in the Bridge

### Gap 1: No .opencoderc Configuration File
- **Status**: NOT FOUND at `/home/newadmin/.opencoderc`, `~/.opencoderc`, or in project
- **Impact**: No persistent per-project OpenCode configuration (agents, permissions, defaults)
- **Evidence**: `find /home/newadmin/.opencode -name "*.yaml" -o -name "*.yml" -o -name "*.json" | grep -v node_modules` returned no config files

### Gap 2: LEGION_MASTER_PROMPT.md Referenced But Not Found
- **Status**: Referenced in `build_opencode_prompt()` but no file found at glob search
- **Impact**: The "LEGION MASTER PROMPT pipeline" mentioned in Telegram prompts may not exist as a standalone file
- **Evidence**: `glob(**/LEGION_MASTER_PROMPT.md)` returned no files

### Gap 3: Subprocess Mode vs Server Mode
- **Current**: Bridge uses `opencode run` subprocess per task (stateless)
- **Gap**: `opencode serve` (persistent headless server) is NOT used
- **Impact**: Each task reinitializes the model, no session persistence between Telegram tasks
- **Evidence**: `core/opencode_bridge.py` uses `asyncio.create_subprocess_exec()` with `opencode run`

### Gap 4: No Server Startup in Bot on_startup()
- **Status**: `opencode serve --port 4096 &` is listed as a TODO in architecture doc
- **Impact**: OpenCode server is never auto-started when bot launches
- **Evidence**: `.wiki/architecture/opencode-integration-2026-04-11.md` line 88-92: "Next Steps: Start opencode server..."

### Gap 5: swarm-bot/.opencode/ Has No Runtime Configuration
- **Status**: The project-local `.opencode/` directory contains only agents/commands, no config
- **Impact**: No project-specific agent registry or permission overrides
- **Evidence**: Only `agent/`, `agents/`, `command/` subdirs present; no `.opencoderc` or equivalent

### Gap 6: Permission Model Not Enforced at Bridge Level
- **Status**: `opencode agent list` shows detailed permission structures (read, edit, bash, external_directory patterns)
- **Gap**: Bridge passes all commands through `opencode run` without specifying agent context
- **Impact**: No agent-specific permission enforcement from Telegram-originated tasks
- **Evidence**: `run_opencode_task()` only passes `--agent` flag optionally; defaults to primary agent

---

## Sources
- `/home/newadmin/.opencode/package.json` — opencode@1.4.3
- `/home/newadmin/.opencode/bin/opencode` — 167MB binary
- `/home/newadmin/swarm-bot/core/opencode_bridge.py` — bridge implementation
- `/home/newadmin/swarm-bot/handlers/dev.py` lines 182-219 — /opencode handler
- `/home/newadmin/swarm-bot/.wiki/architecture/opencode-integration-2026-04-11.md` — integration doc
- `/home/newadmin/swarm-bot/.opencode/agents/*.md` — 40+ custom agent definitions
- `/home/newadmin/swarm-bot/.opencode/command/*.md` — 13 custom command definitions
- `opencode agent list` — built-in agent registry
- `opencode --help` — CLI commands
