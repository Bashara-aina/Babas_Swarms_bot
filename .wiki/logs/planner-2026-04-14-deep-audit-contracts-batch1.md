---
title: Planner 2026 04 14 Deep Audit Contracts Batch1
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
summary: Audit OpenCode at /home/newadmin/.opencode/ — architecture, agent definitions,
  tool integrations, bridge to Telegram, config files, system prompts. Audit how OpenCode
  sends tasks to Legion via swar...
wikilinks: []
confidence: medium
source: research
---
### CONTRACT #1: OpenCode Architecture Audit

WHAT:
  Audit OpenCode at /home/newadmin/.opencode/ — architecture, agent definitions, tool integrations, bridge to Telegram, config files, system prompts. Audit how OpenCode sends tasks to Legion via swarm-bot bridges/.

FILES:
  READ:
    - /home/newadmin/.opencode/package.json
    - /home/newadmin/.opencode/.gitignore
    - /home/newadmin/.opencode/bin/ (if exists)
    - /home/newadmin/swarm-bot/bridges/ (entire directory)
    - /home/newadmin/swarm-bot/.wiki/opencode/ (entire directory)
    - /home/newadmin/swarm-bot/.wiki/decisions/*opencode* (ADR files)
    - /home/newadmin/swarm-bot/core/opencode* (if exists)
    - /home/newadmin/swarm-bot/.wiki/entities/opencode.md
  RUN:
    - find /home/newadmin/.opencode -type f -name "*.json" | head -20
    - ls -la /home/newadmin/swarm-bot/bridges/
    - find /home/newadmin/swarm-bot/bridges -type f
    - grep -r "opencode" /home/newadmin/swarm-bot/core/ --include="*.py" -l 2>/dev/null
    - grep -r "opencode" /home/newadmin/swarm-bot/.wiki/opencode/ -l 2>/dev/null

DONE_WHEN:
  - /home/newadmin/swarm-bot/.wiki/logs/swarm-YYYY-MM-DD-deep-audit-opencode-claudecode-legionbot.md exists with OpenCode findings section
  - Findings include: OpenCode installation method (npm/global), agent definitions found, tool integrations listed, Telegram bridge mechanism described, integration gaps identified
  - >200 words of OpenCode analysis

PROOF_FORMAT:
  FILE_OP: `ls -la /home/newadmin/.opencode/ && ls -la /home/newadmin/swarm-bot/bridges/`
  CONTENT: `head -50 /home/newadmin/swarm-bot/.wiki/logs/swarm-YYYY-MM-DD-deep-audit-opencode-claudecode-legionbot.md` (output showing OpenCode section header and findings)

BLOCKER_IF:
  - /home/newadmin/.opencode/ directory does not exist
  - /home/newadmin/swarm-bot/bridges/ is empty and no OpenCode integration documentation exists

DEPENDS_ON: none

---

### CONTRACT #2: Claude Code Audit — CLAUDE.md Claim Verification

WHAT:
  Audit Claude Code at /home/newadmin/.claude/ — verify all CLAUDE.md claims against actual implementation. Claims to verify: agent count, intent count, model roster, environment variables, settings accuracy.

FILES:
  READ:
    - /home/newadmin/.claude/CLAUDE.md
    - /home/newadmin/.claude/settings.json
    - /home/newadmin/swarm-bot/CLAUDE.md
    - /home/newadmin/swarm-bot/.wiki/entities/opencode.md (OpenCode entity doc)
    - /home/newadmin/swarm-bot/.wiki/entities/minimax-m2-7.md
    - /home/newadmin/swarm-bot/.wiki/decisions/2026-04-12-opencode-over-cursor.md
  RUN:
    - cat /home/newadmin/.claude/CLAUDE.md
    - cat /home/newadmin/.claude/settings.json
    - grep -E "(agent|model|intent|env|setting)" /home/newadmin/.claude/CLAUDE.md
    - ls -la /home/newadmin/.claude/projects/
    - ls -la /home/newadmin/.claude/plugins/
    - wc -l /home/newadmin/swarm-bot/CLAUDE.md

DONE_WHEN:
  - /home/newadmin/swarm-bot/.wiki/logs/swarm-YYYY-MM-DD-deep-audit-opencode-claudecode-legionbot.md exists with Claude Code findings section
  - Claims verified: agent count matches or mismatches, model roster listed, intent count verified, env vars match actual environment
  - Settings accuracy: settings.json values match documented behavior
  - >200 words of Claude Code analysis

PROOF_FORMAT:
  FILE_OP: `ls -la /home/newadmin/.claude/CLAUDE.md && wc -l /home/newadmin/.claude/settings.json`
  CONTENT: `grep -A 20 "## Claude Code" /home/newadmin/swarm-bot/.wiki/logs/swarm-YYYY-MM-DD-deep-audit-opencode-claudecode-legionbot.md`

BLOCKER_IF:
  - /home/newadmin/.claude/CLAUDE.md does not exist
  - settings.json is missing or unreadable

DEPENDS_ON: none

---

### CONTRACT #3: swarm-bot Codebase Health — Counts & Structure

WHAT:
  Audit swarm-bot handlers/, core/, agents/, tools/, config/ directories for accurate counts vs AGENTS.md claims. Verify: 45+ handlers count, 76+ agents count, 9 departments count. Audit handler file names, agent registry structure, department organization.

FILES:
  READ:
    - /home/newadmin/swarm-bot/AGENTS.md
    - /home/newadmin/swarm-bot/agents.py
    - /home/newadmin/swarm-bot/agents/ (directory listing)
    - /home/newadmin/swarm-bot/handlers/ (directory listing)
    - /home/newadmin/swarm-bot/config/ (directory listing)
    - /home/newadmin/swarm-bot/tools/ (directory listing)
    - /home/newadmin/swarm-bot/core/ (directory listing)
    - /home/newadmin/swarm-bot/swarms_bot/ (directory listing)
  RUN:
    - ls /home/newadmin/swarm-bot/handlers/ | wc -l
    - ls /home/newadmin/swarm-bot/agents/ | wc -l
    - ls /home/newadmin/swarm-bot/config/ | wc -l
    - ls /home/newadmin/swarm-bot/tools/ | wc -l
    - find /home/newadmin/swarm-bot/handlers -name "*.py" -type f | wc -l
    - find /home/newadmin/swarm-bot/agents -name "*.py" -type f | wc -l
    - cat /home/newadmin/swarm-bot/agents.py

DONE_WHEN:
  - Handler count: exact count vs "45+" claim in AGENTS.md
  - Agent count: exact count vs "76+" claim in AGENTS.md
  - Department count: exact count vs "9 departments" claim
  - Config file count listed
  - Tools count listed
  - Core module count listed
  - Findings written to audit report with >200 words

PROOF_FORMAT:
  FILE_OP: `find /home/newadmin/swarm-bot/handlers -name "*.py" | wc -l && find /home/newadmin/swarm-bot/agents -name "*.py" | wc -l`
  CONTENT: `grep -A 30 "## swarm-bot Codebase" /home/newadmin/swarm-bot/.wiki/logs/swarm-YYYY-MM-DD-deep-audit-opencode-claudecode-legionbot.md`

BLOCKER_IF:
  - handlers/ directory does not exist
  - agents/ directory does not exist

DEPENDS_ON: none

---

### CONTRACT #4: Budget Guard Coverage — litellm Call Sites

WHAT:
  Audit all litellm call sites in swarm-bot to determine what fraction goes through BudgetManager. Identify call sites that bypass budget tracking. Document the budget guard architecture.

FILES:
  READ:
    - /home/newadmin/swarm-bot/llm_client.py
    - /home/newadmin/swarm-bot/llm_client/ (entire package)
    - /home/newadmin/swarm-bot/core/ (grep for litellm, budget, BudgetManager)
    - /home/newadmin/swarm-bot/handlers/ (grep for litellm, budget)
    - /home/newadmin/swarm-bot/agents/ (grep for litellm, budget)
    - /home/newadmin/swarm-bot/swarms_bot/ (grep for litellm, budget)
    - /home/newadmin/swarm-bot/.wiki/decisions/*budget* (if exists)
    - /home/newadmin/swarm-bot/.wiki/decisions/*llm* (if exists)
  RUN:
    - grep -rn "litellm" /home/newadmin/swarm-bot --include="*.py" | grep -v ".pyc" | grep -v ".venv" | grep -v "node_modules"
    - grep -rn "BudgetManager" /home/newadmin/swarm-bot --include="*.py" | grep -v ".pyc" | grep -v ".venv"
    - grep -rn "budget" /home/newadmin/swarm-bot --include="*.py" | grep -v ".pyc" | grep -v ".venv"
    - find /home/newadmin/swarm-bot/llm_client -name "*.py" -type f

DONE_WHEN:
  - Total litellm call sites counted
  - Call sites going through BudgetManager counted
  - Call sites bypassing BudgetManager listed with file:line references
  - BudgetManager architecture described
  - Findings written to audit report with >200 words

PROOF_FORMAT:
  FILE_OP: `grep -rn "litellm" /home/newadmin/swarm-bot --include="*.py" | grep -v ".pyc" | grep -v ".venv" | wc -l`
  CONTENT: `grep -A 30 "## Budget Guard" /home/newadmin/swarm-bot/.wiki/logs/swarm-YYYY-MM-DD-deep-audit-opencode-claudecode-legionbot.md`

BLOCKER_IF:
  - llm_client.py does not exist
  - No BudgetManager found in codebase

DEPENDS_ON: none

---

### CONTRACT #5: Wiki Health — Frontmatter, YAML, Orphaned Links

WHAT:
  Audit swarm-bot .wiki/ directory for frontmatter validity, YAML syntax errors, and orphaned wikilinks. Verify post-audit fixes were applied correctly.

FILES:
  READ:
    - /home/newadmin/swarm-bot/.wiki/INDEX.md
    - /home/newadmin/swarm-bot/.wiki/SCHEMA.md
    - /home/newadmin/swarm-bot/.wiki/_meta/ (if exists)
    - /home/newadmin/swarm-bot/.wiki/agents/ (sample .md files)
    - /home/newadmin/swarm-bot/.wiki/concepts/ (sample .md files)
    - /home/newadmin/swarm-bot/.wiki/decisions/ (sample .md files)
    - /home/newadmin/swarm-bot/.wiki/architecture/ (sample .md files)
  RUN:
    - find /home/newadmin/swarm-bot/.wiki -name "*.md" -type f | head -50
    - for f in $(find /home/newadmin/swarm-bot/.wiki -name "*.md" -type f | head -20); do head -5 "$f"; echo "---"; done
    - grep -rn "\[\[" /home/newadmin/swarm-bot/.wiki --include="*.md" | wc -l
    - grep -rn "wikilinks" /home/newadmin/swarm-bot/.wiki --include="*.md" | head -20
    - ls /home/newadmin/swarm-bot/.wiki/logs/ | head -20

DONE_WHEN:
  - Frontmatter: sampled files show valid YAML frontmatter (title, type, status, tags, created)
  - YAML validity: no syntax errors detected in samples
  - Wikilinks: pattern `[[page-name]]` found, count listed
  - Orphaned links: any broken internal links identified
  - Wiki quarantine system: documented if present
  - Findings written to audit report with >200 words

PROOF_FORMAT:
  FILE_OP: `find /home/newadmin/swarm-bot/.wiki -name "*.md" -type f | head -20 | xargs head -5`
  CONTENT: `grep -A 30 "## Wiki Health" /home/newadmin/swarm-bot/.wiki/logs/swarm-YYYY-MM-DD-deep-audit-opencode-claudecode-legionbot.md`

BLOCKER_IF:
  - .wiki/ directory does not exist
  - No .md files found in .wiki/

DEPENDS_ON: none
