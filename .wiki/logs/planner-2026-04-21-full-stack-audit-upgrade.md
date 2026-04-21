## Plan: OPENCODE MASTER AUDIT — FULL STACK INTELLIGENCE UPGRADE
Date: 2026-04-21
Type: RESEARCH + FEATURE (comprehensive audit + upgrade across all 4 surfaces)

Context gathered:
- Memory shows prior audit (2026-04-14) found: 88% budget bypass rate (partially fixed), 804 wiki orphans (unfixed), CLAUDE.md counts stale (107 agents vs 84 claimed), model naming drift
- Explorer found: Anti-Loop Protocol MISSING from Claude Code legiona agents but present in OpenCode; global_memory.md is TODO-empty; CLAUDE.md references 5 non-existent modules; OpenCode has ~100 agents with no parity mapping to Claude Code
- Both surfaces share MCPs: gitnexus, obsidian (wiki vault), filesystem; OpenCode has firecrawl+exa; Claude Code has contree

Key gaps identified during audit:
1. 🔴 CRITICAL: Anti-Loop Protocol MISSING from Claude Code .claude/skills/legiona/ agents (present in OpenCode but not Claude Code)
2. 🔴 CRITICAL: global_memory.md is TODO-empty — needs population from evolve()
3. 🟡 MEDIUM: CLAUDE.md references non-existent modules (core.agent_teams, core.context_health)
4. 🟡 MEDIUM: Wiki has 804 orphans (unfixed from prior audit)
5. 🟡 MEDIUM: Copilot instructions has Anti-Loop but lacks Interleaved Thinking Protocol
6. 🟡 MEDIUM: Obsidian MCP in Claude Code points to @modelcontextprotocol/server-obsidian (npm 404), OpenCode uses correct @iflow-mcp/kynlos-obsidian-mcp-server

Risk assessment:
- Adding Anti-Loop Protocol to Claude Code legiona agents is safe (backward-compatible addition)
- global_memory.md population is safe (read operation + structured write)
- CLAUDE.md module references are informational only (won't break runtime)
- Obsidian MCP fix is critical (current config returns 404 on install)

Approach:
- Phase 1: Verify all 4 surfaces have same intelligence standards (Copilot, Claude Code, OpenCode, LegionBot)
- Phase 2: Add missing protocols to Claude Code legiona agents (Anti-Loop + Interleaved Thinking)
- Phase 3: Create system wiki files (LEGIONA_SYSTEM.md, EVOLVED_RULES.md, COST_TRACKER.md)
- Phase 4: Audit design tokens in any UI code
- Phase 5: Test cross-surface bridge (opencode_bridge.py, claude_code_bridge.py)
- Phase 6: Verify tool modules (desktop_control, log_reader, fs_control, system_monitor)
- Phase 7: CLAUDE.md compression + UPGRADE_LOG.md
- Final: git add -A && commit && push