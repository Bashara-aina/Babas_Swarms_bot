---

---
# Planner Output — Repository Cleanup
**Date**: 2026-04-12
**Task**: Full repository cleanup + README update
**Status**: DECOMPOSED

## EXECUTIVE SUMMARY

The repository has accumulated numerous one-time use files, master prompts, and obsolete documentation from various AI-assisted sessions. This cleanup will:
1. Delete all master prompt / one-time files (3 files identified)
2. Clean up the `_graveyard/` directory (obsolete backups)
3. Update README.md to reflect current state (v10/LegionSwarm branding)
4. Remove orphaned/duplicate documentation

---

## ATOMIC SUBTASKS

### SUBTASK 1: Delete Master Prompt Files (3 files)
**Action**: DELETE (one-time use / session-specific files)

| File Path | Reason for Deletion |
|-----------|---------------------|
| `LEGION_MASTER_PROMPT.md` | One-time master prompt for Telegram→opencode pipeline — 714 lines of consumed instructions, not reference material |
| `MASTER_PROMPT.md` | One-time GitHub Copilot Agent prompt — 1091 lines, fully consumed by implementation |
| `masterprompt.md` | One-time master prompt (v7) — 214 lines, replaced by CLAUDE.md |

**Verification after delete**: None needed — these are consumables, not source code

---

### SUBTASK 2: Clean Up `_graveyard/` Directory
**Action**: DELETE entire `_graveyard/` directory + contents

**Contents to delete**:
```
_graveyard/20260411/.env.bak
_graveyard/20260411/.env.env.bak
_graveyard/20260411/=0.23.0
_graveyard/20260411/computer_agent.py.bak
_graveyard/20260411/memory.backup/
_graveyard/20260411/obsidian_1.8.10_amd64.deb
_graveyard/20260411/memory.backup/semantic_cache.py
_graveyard/20260411/memory.backup/memory_manager.py
_graveyard/20260411/memory.backup/__init__.py
```

**Reason**: Obsolete backups from April 11 session — .env backups already superseded, computer_agent.py.bak is from v9 era, obsidian .deb is irrelevant, memory.backup is dead code

---

### SUBTASK 3: Clean Up LEGION_*.md Files
**Action**: INSPECT then DELETE or KEEP each file

| File | Recommendation | Reason |
|------|---------------|--------|
| `LEGION_MASTER.md` | **KEEP** | Current active master reference |
| `LEGION_PRODUCTION_HARDENING.md` | **KEEP** | Valid production hardening doc |
| `LEGION_WIRING_AUDIT_PROMPT.md` | **DELETE** | One-time audit prompt, consumed |
| `LEGION_NIHONGO_MODE.md` | **DELETE** | One-time feature prompt, consumed |
| `LEGION_FIX_IDENTITY_SEARCH.md` | **DELETE** | One-time fix prompt, consumed |
| `LEGION_VOICE_UPGRADE.md` | **DELETE** | One-time voice upgrade prompt, consumed |
| `LEGION_OPENCODE_AUDIT.md` | **DELETE** | One-time audit prompt, consumed |
| `LEGION_WIKI_LOOP.md` | **DELETE** | One-time wiki loop prompt, consumed |
| `LEGION_CLAWCODE_UPGRADE.md` | **DELETE** | One-time upgrade prompt, consumed |
| `LEGION_MCP_SKILLS_MASTER.md` | **DELETE** | One-time MCP skills prompt, consumed |

**Keep**: `LEGION_MASTER.md`, `LEGION_PRODUCTION_HARDENING.md`
**Delete**: 9 files

---

### SUBTASK 4: Delete MASTER_FIX_PROMPT.md
**Action**: DELETE

**Reason**: One-time master fix prompt — fully consumed by implementation session

---

### SUBTASK 5: Update README.md
**Action**: UPDATE (refresh content to reflect current v10/LegionSwarm state)

**Current issues**:
- References "v3" in title, but project is at v10
- Agent roster references old model names (gemma4:e4b, GLM-4, etc.)
- Setup instructions reference 3.10+, but CLAUDE.md says 3.11+
- Missing v10 commands: `/debate`, `/opinion`, `/budget`, `/soul`
- Missing OWL agent, code_exec, predictor, ag2_* agents
- Example commands are outdated

**Update needed**:
1. Title: "LegionSwarm v10" (not v3)
2. Agent roster: update to match current agents.py
3. Commands: add new v10 commands, remove obsolete ones
4. Setup: update Python version to 3.11+
5. Add /debate, /opinion, /budget, /soul to command tables
6. Remove "100+ slash commands" claim (now ~90 after consolidation)
7. Refresh examples with current commands

---

### SUBTASK 6: Delete Obsolete One-Time Documentation Files

| File | Recommendation | Reason |
|------|---------------|--------|
| `AUDIT_NOW.md` | **DELETE** | One-time audit trigger |
| `AUDIT_REPORT.md` | **DELETE** | Historical audit report (not current) |
| `DEEP_AUDIT_2026-04-10.md` | **DELETE** | One-time audit, superseded by WIRING_VERIFIED |
| `IMPLEMENTATION_STATUS.md` | **KEEP** | Current implementation tracking |
| `INTEGRATION_REPORT.md` | **DELETE** | One-time integration report |
| `INTEGRATION_RUN.txt` | **DELETE** | One-time run log |
| `CLEANUP_LOG.md` | **KEEP** | May be useful for history |
| `CONTRIBUTING.md` | **KEEP** | Valid contributor guide |
| `PRODUCTION_HARDENING_REPORT.md` | **DELETE** | Obsolete (superseded by LEGION_PRODUCTION_HARDENING.md) |
| `SWARM_WIRING.md` | **KEEP** | Valid architecture doc |
| `TESTING.md` | **KEEP** | Valid testing documentation |
| `WIRING_VERIFIED_2026-04-12.md` | **KEEP** | Current wiring verification report |
| `SOUL.md` | **KEEP** | Legion's living identity file |
| `CHANGELOG.md` | **KEEP** | Project changelog |

---

### SUBTASK 7: Clean Up Duplicate AGENTS.md Files
**Action**: DELETE redundant copies, keep only root `AGENTS.md`

| File | Recommendation | Reason |
|------|---------------|--------|
| `AGENTS.md` | **KEEP** | Root project agent context |
| `tools/AGENTS.md` | **DELETE** | Duplicate |
| `tests/AGENTS.md` | **DELETE** | Duplicate |
| `handlers/AGENTS.md` | **DELETE** | Duplicate |
| `core/AGENTS.md` | **DELETE** | Duplicate |
| `agents/AGENTS.md` | **DELETE** | Duplicate |
| `swarms_bot/AGENTS.md` | **DELETE** | Duplicate |

---

### SUBTASK 8: Clean Up prompts/ Directory
**Action**: DELETE consumed prompt file, keep active prompts

| File | Recommendation | Reason |
|------|---------------|--------|
| `prompts/master_v4.md` | **DELETE** | One-time v4 master prompt — consumed |
| `prompts/` directory | **INSPECT** after deletion | Check if directory becomes empty, remove if so |

---

### SUBTASK 9: Clean Up .github/workflows/ Copilot File
**Action**: DELETE

| File | Recommendation | Reason |
|------|---------------|--------|
| `.github/workflows/copilot-masterprompt.md` | **DELETE** | One-time Copilot prompt — consumed |

---

### SUBTASK 10: Verify No Broken References
**Action**: VERIFY after deletions

**Check**:
- Git status to confirm no broken imports
- Quick `python -c "from core.soul_engine import build_soul_context"` smoke test
- Verify wiki/ INDEX.md still valid

---

## FINAL CLEAN DIRECTORY STRUCTURE

After cleanup, the repository should look like:

```
swarm-bot/
├── main.py                      # Telegram bot entry point
├── agents.py                    # Agent registry
├── router.py                    # LLM routing (re-exports from agents.py)
├── llm_client.py                # LiteLLM client wrapper
├── computer_agent.py            # Desktop control
├── task_orchestrator.py         # DAG task planner
├── SOUL.md                      # Legion's living identity
├── CLAUDE.md                    # Master engineering prompt (current v10)
├── AGENTS.md                    # SwarmBot agent context
├── pyproject.toml
├── requirements.txt
├── Makefile
├── docker-compose.yml
├── deploy.sh
├── restart.sh
│
├── core/                        # Core systems
│   ├── soul_engine.py
│   ├── intent_router.py
│   ├── system_prompt_builder.py
│   ├── debate_engine.py
│   ├── character_voice.py
│   ├── working_memory.py
│   ├── cognition_pipeline.py
│   └── [other 40+ core modules]
│
├── handlers/                    # 33 aiogram router files
│   ├── shared.py
│   ├── system.py
│   ├── ai.py
│   ├── computer.py
│   ├── brain.py
│   ├── debate_handlers.py
│   ├── admin_handlers.py
│   └── [other 25 handlers]
│
├── tools/                       # External integrations
│   ├── browser_agent.py
│   ├── email_client.py
│   ├── github_intel.py
│   ├── memory.py
│   ├── persistence.py
│   ├── scheduler.py
│   ├── skill_loader.py
│   └── voice_engine.py
│
├── agents/                      # Department packages
├── bridges/                     # API connectors
├── config/                      # YAML configs
├── core/                        # Core utilities
├── swarms_bot/                  # Enterprise orchestration
├── skills/                      # Skill injection
├── wiki/                        # Knowledge base (auto-ingested)
│   ├── INDEX.md
│   ├── SCHEMA.md
│   ├── conversations/
│   ├── legion/
│   └── [other wiki sections]
│
├── docs/                        # Architecture docs
│   ├── ARCHITECTURE_V5.md
│   ├── MIGRATION.md
│   └── [other valid docs]
│
├── .github/workflows/
│   └── ci.yml
│
├── tests/                       # pytest suite
└── scripts/                     # Utility scripts
```

---

## SUMMARY TABLE

| Action | Count | Files |
|--------|-------|-------|
| **DELETE** master prompts | 3 | `LEGION_MASTER_PROMPT.md`, `MASTER_PROMPT.md`, `masterprompt.md` |
| **DELETE** LEGION_*.md consumed files | 9 | LEGION_WIRING_AUDIT_PROMPT.md, LEGION_NIHONGO_MODE.md, LEGION_FIX_IDENTITY_SEARCH.md, LEGION_VOICE_UPGRADE.md, LEGION_OPENCODE_AUDIT.md, LEGION_WIKI_LOOP.md, LEGION_CLAWCODE_UPGRADE.md, LEGION_MCP_SKILLS_MASTER.md, MASTER_FIX_PROMPT.md |
| **DELETE** _graveyard/ | 1 dir | All contents of _graveyard/20260411/ |
| **DELETE** consumed one-time docs | 6 | AUDIT_NOW.md, AUDIT_REPORT.md, DEEP_AUDIT_2026-04-10.md, INTEGRATION_REPORT.md, INTEGRATION_RUN.txt, PRODUCTION_HARDENING_REPORT.md |
| **DELETE** duplicate AGENTS.md | 5 | tools/, tests/, handlers/, core/, agents/, swarms_bot/ |
| **DELETE** prompts/master_v4.md | 1 | One-time v4 prompt |
| **DELETE** .github/workflows/copilot-masterprompt.md | 1 | One-time Copilot prompt |
| **UPDATE** README.md | 1 | Refresh to v10/LegionSwarm state |
| **KEEP** (no change) | ~50 | Valid source files, configs, active docs |

---

## EXECUTION ORDER

1. ✅ Task decomposed (this document)
2. → SUBTASK 1-3: Delete master prompts + LEGION files (can run in parallel)
3. → SUBTASK 4-7: Delete other consumed files (can run in parallel)
4. → SUBTASK 8-9: Clean up prompts/ and .github/
5. → SUBTASK 10: Verify no broken references
6. → SUBTASK 5: Update README.md (requires current context)
7. → Report completion to user

---

*Generated by: Planner Agent | Date: 2026-04-12*