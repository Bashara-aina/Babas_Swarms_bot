---
title: Wiki Path Audit
type: concept
status: deprecated
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: '| Tool | Wiki Path | Config Location | Status |'
wikilinks: []
confidence: medium
source: research
---
# Wiki Path Audit — 2026-04-14

## Executive Summary

| Tool | Wiki Path | Config Location | Status |
|------|-----------|-----------------|--------|
| **Legion Bot** | `.wiki/` (canonical) | `core/wiki_*.py` | WORKING — but INCONSISTENT |
| **OpenCode** | `.wiki/` | `.opencode/agents/wikibot.md` | CONFIGURED |
| **Claude Code** | None configured | `~/.claude/settings.json` | NOT CONFIGURED |

## Critical Finding: Split-Brain Wiki Path ⚠️

**There are TWO wiki directories:**
- `.wiki/` — canonical (2800+ files, active content)
- `wiki/` — legacy (only `_quarantine/`, deprecated)

**Files using WRONG path (`wiki/` without dot):**
```
core/wiki_quality_gate.py:28  WIKI_DIR = Path("/home/newadmin/swarm-bot/wiki")
core/wiki_loader.py:12         WIKI_DIR = Path("/home/newadmin/swarm-bot/wiki")
core/wiki_scheduler.py:30      WIKI_DIR = Path("/home/newadmin/swarm-bot/wiki")
```

**Files using CORRECT path (`.wiki/`):**
```
core/wiki_bridge.py:25        WIKI_DIR = REPO_ROOT / ".wiki"
core/wiki_manager.py:21       WIKI_DIR = REPO_ROOT / ".wiki"
core/wiki_auto_ingest.py:26   WIKI_DIR = REPO_ROOT / ".wiki"
handlers/wiki.py:140          from core.wiki_scheduler import WIKI_DIR
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LEGION_WIKI_ENABLED` | `1` | Enable/disable wiki system |
| `LEGION_WIKI_AUTO_INGEST` | `1` | Auto-ingest conversation turns |
| `LEGION_WIKI_AUTO_LINT` | `1` | Auto-lint wiki content |
| `LEGION_WIKI_LLM_MODEL` | `minimax/MiniMax-M2.7` | Model for wiki LLM ops |
| `LEGION_WIKI_ROUTER_MODEL` | `groq/llama-3.1-8b-instant` | Model for wiki routing |

**Source:** `llm_client/__init__.py:554`, `core/wiki_bridge.py:350-354`, `core/proactive/scheduler.py:124,149`

---

## OpenCode Wiki Configuration

**Location:** `/home/newadmin/swarm-bot/.opencode/agents/wikibot.md`

**Wiki paths hardcoded in agent prompt:**
```
Line 15: "Summarize completed sessions into .wiki/logs/"
Line 16: "Write architecture decisions into .wiki/decisions/"
Line 17: "Update .wiki/INDEX.md index"
Line 18: "Keep .wiki/agents/ files up to date"
Line 120: "Session logs go to .wiki/logs/YYYY-MM-DD-[topic].md"
Line 121: "Decisions go to .wiki/decisions/ADR-[NNN]-[slug].md"
```

**OpenCode global config:** `~/.opencode/` (home directory)
- No wiki path environment variable found
- No wiki path configuration file found
- Uses hardcoded `.wiki/` relative path

---

## Claude Code Wiki Configuration

**Location:** `~/.claude/settings.json`

**Findings:**
- NO wiki path environment variable
- NO wiki path in settings.json
- NO `.wiki` references in any Claude Code config

Claude Code does NOT have wiki integration configured.

---

## Legion Bot Wiki Configuration

### Canonical Path
`REPO_ROOT / ".wiki"` where `REPO_ROOT = Path(__file__).resolve().parent.parent`

### Files Using Canonical Path (CORRECT)
| File | Line | Path |
|------|------|------|
| `core/wiki_bridge.py` | 25 | `WIKI_DIR = REPO_ROOT / ".wiki"` |
| `core/wiki_manager.py` | 21 | `WIKI_DIR = REPO_ROOT / ".wiki"` |
| `core/wiki_auto_ingest.py` | 26 | `WIKI_DIR = REPO_ROOT / ".wiki"` |

### Files Using Wrong Path (BUG - `wiki/` without dot)
| File | Line | Path |
|------|------|------|
| `core/wiki_quality_gate.py` | 28 | `WIKI_DIR = Path("/home/newadmin/swarm-bot/wiki")` |
| `core/wiki_loader.py` | 12 | `WIKI_DIR = Path("/home/newadmin/swarm-bot/wiki")` |
| `core/wiki_scheduler.py` | 30 | `WIKI_DIR = Path("/home/newadmin/swarm-bot/wiki")` |

### OpenCode Bridge Integration
`core/wiki_bridge.py` provides bidirectional sync:
- OpenCode sessions → `.wiki/opencode/sessions/`
- OpenCode decisions → `.wiki/decisions/`
- Query function: `opencode_query_wiki()` at line 172

---

## Shared Config Files

| File | Purpose |
|------|---------|
| `.env.example` | Contains `LEGION_WIKI_ENABLED=1`, `LEGION_WIKI_LLM_MODEL`, `LEGION_WIKI_ROUTER_MODEL` |
| `AGENTS.md` | Documents `LEGION_WIKI_AUTO_INGEST=1` (line 22-23) |
| `.git/opencode` | Git submodule reference (points to opencode repo) |

---

## Proof: grep/find Output

### Legion Bot Wiki Path References
```
$ grep -n "WIKI_DIR" core/wiki_*.py
core/wiki_auto_ingest.py:26: WIKI_DIR = REPO_ROOT / ".wiki"
core/wiki_bridge.py:25:    WIKI_DIR = REPO_ROOT / ".wiki"
core/wiki_manager.py:21:   WIKI_DIR = REPO_ROOT / ".wiki"
core/wiki_quality_gate.py:28: WIKI_DIR = Path("/home/newadmin/swarm-bot/wiki")
core/wiki_loader.py:12:    WIKI_DIR = Path("/home/newadmin/swarm-bot/wiki")
core/wiki_scheduler.py:30: WIKI_DIR = Path("/home/newadmin/swarm-bot/wiki")
```

### Environment Variables
```
$ grep -n "LEGION_WIKI" llm_client/__init__.py core/wiki_bridge.py core/proactive/scheduler.py
llm_client/__init__.py:554:  m = model or os.getenv("LEGION_WIKI_LLM_MODEL", "minimax/MiniMax-M2.7")
llm_client/__init__.py:1465: if user_id and os.getenv("LEGION_WIKI_ENABLED", "1")...
llm_client/__init__.py:1474: if user_id and os.getenv("LEGION_WIKI_AUTO_INGEST", "1")...
core/wiki_bridge.py:350:    return os.getenv("LEGION_WIKI_ENABLED", "1")...
core/wiki_bridge.py:354:    return os.getenv("LEGION_WIKI_AUTO_INGEST", "1")...
core/proactive/scheduler.py:124: if os.getenv("LEGION_WIKI_AUTO_LINT", "1")...
core/proactive/scheduler.py:149: if os.getenv("LEGION_WIKI_AUTO_LINT", "1")...
```

### OpenCode Wiki References
```
$ grep -n "\.wiki" .opencode/agents/wikibot.md
15: Summarize completed sessions into .wiki/logs/
16: Write architecture decisions into .wiki/decisions/
17: Update .wiki/INDEX.md index
18: Keep .wiki/agents/ files up to date
20: Save to .wiki/decisions/ADR-[number]-[title].md
120: Session logs go to .wiki/logs/YYYY-MM-DD-[topic].md
121: Decisions go to .wiki/decisions/ADR-[NNN]-[slug].md
```

### Claude Code Wiki References
```
$ grep -rn "\.wiki\|WIKI_PATH\|wiki.*path" ~/.claude/
# NO RESULTS - Claude Code has no wiki integration configured
```

---

## Actions Required

1. **FIX split-brain wiki paths** — Update these files to use `.wiki` instead of `wiki`:
   - [ ] `core/wiki_quality_gate.py:28`
   - [ ] `core/wiki_loader.py:12`
   - [ ] `core/wiki_scheduler.py:30`

2. **Add wiki path to Claude Code** — Configure `~/.claude/settings.json` with wiki path if needed

3. **Standardize environment variable** — Consider adding `LEGION_WIKI_PATH` to avoid hardcoded paths

---

*Audit completed: 2026-04-14*
