## Plan: LEGIONA OMEGA AUDIT v4.0
Date: 2026-04-21
Type: RESEARCH + IMPLEMENTATION (hybrid)
Context gathered:
- Bot running PID 449287, ~3h uptime
- CLAUDE.md: 27,548 bytes / 449 lines
- copilot-instructions.md: 9,479 bytes / 209 lines
- Wiki: 1,328 .md files, 410 orphans (compile_state shows real_orphans=0)
- 202 Python files in core/, 22 in lib/legiona/, 47 in handlers/, 88+ in tools/
- 44 OpenCode agent files across 36 directories
- 8 config YAML files
- 7,878 TODO/FIXME markers total
- Known CRITICAL issues: dangerous wildcard git permissions in settings.json, .env contains live secrets, monkey-patching in main.py:181-183, Legiona skills dir has NO Python implementations
- Known HIGH issues: Memory files stale (6 days old), missing referenced memory files

Risk assessment:
- Several CRITICAL security issues that must be addressed (but NOT .env contents)
- Large codebase with many interdependencies
- Multiple surfaces (Claude Code, OpenCode, Copilot, LegionBot) need alignment
- Self-evolution and reasoning_split correctness need verification

Approach:
- Group by 13 phases but consolidate into 10-15 contracts maximum
- Priority: Security fixes first (wildcard git permissions), then reasoning_split verification, then anti-hallucination expansion, then documentation
- All MiniMax M2.7 references must stay, reasoning_split must be verified as correct
- DO NOT alter .env secrets
