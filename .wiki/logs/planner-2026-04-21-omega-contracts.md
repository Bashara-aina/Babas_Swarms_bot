# LEGIONA OMEGA AUDIT v4.0 — CONTRACT PLAN
**Date:** 2026-04-21 | **Phase:** 0 Discovery Complete → Contracts Released

---

## Contract Summary (12 contracts across 6 phases)

| # | Name | Type | Est Complexity |
|---|------|------|----------------|
| 1 | Security Audit & Critical Fixes | IMPLEMENTATION | HIGH |
| 2 | Reasoning_split + M2.7 Self-Evolution Verification | VERIFICATION | HIGH |
| 3 | Anti-Hallucination 5→8 Pillars Expansion | IMPLEMENTATION | MED |
| 4 | CLAUDE.md Maximization + OMEGA_BASELINE | IMPLEMENTATION | MED |
| 5 | OpenCode 44 Agents Alignment | VERIFICATION | HIGH |
| 6 | Copilot Maximum Usefulness | IMPLEMENTATION | MED |
| 7 | Cross-Surface Unification + Architecture Map | IMPLEMENTATION | MED |
| 8 | Memory/Wiki/Knowledge Hygiene | IMPLEMENTATION | MED |
| 9 | Deployment/Operations Readiness | IMPLEMENTATION | MED |
| 10 | Documentation Compilation | IMPLEMENTATION | MED |

---

## PHASE 1: Security & Critical Fixes

### CONTRACT #1: Security Audit & Critical Fixes (CRITICAL)

**WHAT:**
Fix dangerous security issues: (1) dangerous wildcard git permissions in settings.json, (2) monkey-patching bot methods in main.py:181-183, (3) verify .env protection without altering contents, (4) create FAILURE_MODES.md and RECOVERY_RUNBOOK.md

**FILES:**
READ:
- `.claude/settings.json`
- `main.py` (lines ~175-190)
- `.env` (verify protection only, NOT contents)
- `lib/legiona/skills/` directory structure

WRITE:
- `.claude/settings.json` (fix wildcard git permissions)
- `main.py` (remove monkey-patching if found)
- `docs/FAILURE_MODES.md` (new)
- `docs/RECOVERY_RUNBOOK.md` (new)

**DONE_WHEN:**
- settings.json has NO wildcard `"*"` git permissions (replaced with explicit paths)
- main.py has NO monkey-patching of bot methods (or documented with ADR if unavoidable)
- .env file exists but IS NOT tracked in git (verified via .gitignore)
- docs/FAILURE_MODES.md exists, >500 bytes, describes failure modes
- docs/RECOVERY_RUNBOOK.md exists, >500 bytes, describes recovery steps

**PROOF_FORMAT:**
```
# Security fixes verification
grep -r '"\*"' /home/newadmin/swarm-bot/.claude/settings.json && echo "FAIL: wildcards found" || echo "PASS: no wildcards"
# Verify monkey-patching gone
grep -n "monkey\|patch\|patching" /home/newadmin/swarm-bot/main.py || echo "PASS: no monkey-patching"
# Verify .gitignore protects .env
grep "\.env" /home/newadmin/swarm-bot/.gitignore || echo "WARN: .env not in gitignore"
# Verify docs created
ls -la /home/newadmin/swarm-bot/docs/FAILURE_MODES.md /home/newadmin/swarm-bot/docs/RECOVERY_RUNBOOK.md
```

**BLOCKER_IF:**
- settings.json cannot be parsed as valid JSON
- main.py edit removes required functionality
- Bot stops responding after changes

---

## PHASE 2: Reasoning Split & M2.7 Verification

### CONTRACT #2: Reasoning_split + M2.7 Self-Evolution Verification

**WHAT:**
Verify reasoning_split=True is correctly implemented across all surfaces (Claude Code settings.json, OpenCode config, minimax_client.py, llm_client.py), verify M2.7 self-evolution correctness, create docs/EVALS.md

**FILES:**
READ:
- `.claude/settings.json` (verify reasoning_split=true, temperature=1.0, model=MiniMax-M2.7)
- `.opencode/opencode.json` (verify reasoning_split or equivalent setting)
- `lib/legiona/minimax_client.py` (verify reasoning_split passed to API)
- `core/llm_client.py` (verify reasoning_split parameter)
- `lib/legiona/self_evolve.py` (verify self-evolution logic)

WRITE:
- `docs/EVALS.md` (new - benchmarks, regression gates, eval procedures)

**DONE_WHEN:**
- `.claude/settings.json` contains `"reasoning_split": true`
- `.claude/settings.json` contains `"model": "MiniMax-M2.7"` or `"minimax-m2.7"`
- `lib/legiona/minimax_client.py` passes reasoning_split to API calls
- `lib/legiona/self_evolve.py` contains evolve() and load_evolved_rules() functions
- docs/EVALS.md exists, >1000 bytes, contains benchmark procedures

**PROOF_FORMAT:**
```bash
# Verify reasoning_split in Claude Code settings
grep -o '"reasoning_split": *true' /home/newadmin/swarm-bot/.claude/settings.json
# Verify model name
grep -o '"model": *"MiniMax' /home/newadmin/swarm-bot/.claude/settings.json
# Verify temperature
grep -o '"temperature": *1.0' /home/newadmin/swarm-bot/.claude/settings.json
# Verify minimax_client passes reasoning_split
grep "reasoning_split" /home/newadmin/swarm-bot/lib/legiona/minimax_client.py | head -5
# Verify self_evolve functions exist
grep -E "def evolve|def load_evolved" /home/newadmin/swarm-bot/lib/legiona/self_evolve.py
# Verify EVALS.md created
ls -la /home/newadmin/swarm-bot/docs/EVALS.md && wc -c /home/newadmin/swarm-bot/docs/EVALS.md
```

**BLOCKER_IF:**
- reasoning_split not found in any config file
- MiniMax M2.7 not the model in Claude Code settings
- self_evolve.py functions missing or broken

---

## PHASE 3: Anti-Hallucination & Documentation

### CONTRACT #3: Anti-Hallucination 5→8 Pillars Expansion

**WHAT:**
Expand anti-hallucination system from 5 pillars to 8 pillars, update all ANTI_HALLUCINATION.md files, create docs/MEMORY_SYSTEM.md

**FILES:**
READ:
- `.wiki/ANTI_HALLUCINATION.md` (existing 5 pillars)
- `.github/copilot-instructions.md` (anti-hallucination sections)
- `lib/legiona/memory/` (memory architecture)

WRITE:
- `.wiki/ANTI_HALLUCINATION.md` (expanded to 8 pillars)
- `.github/copilot-instructions.md` (update if needed)
- `docs/MEMORY_SYSTEM.md` (new - memory subsystem documentation)

**DONE_WHEN:**
- ANTI_HALLUCINATION.md documents 8 distinct pillars (not 5)
- Pillar 6: "Source Provenance Tracking" added
- Pillar 7: "Consistency Verification" added
- Pillar 8: "Temporal Decay Awareness" added
- docs/MEMORY_SYSTEM.md exists, >1500 bytes, covers all 4 memory tiers
- All 4 memory tiers documented: Working, Episodic, Semantic, Graph

**PROOF_FORMAT:**
```bash
# Count pillars in ANTI_HALLUCINATION.md
grep -c "^## Pillar" /home/newadmin/swarm-bot/.wiki/ANTI_HALLUCINATION.md
# Verify new pillars exist
grep -E "Pillar [678]:" /home/newadmin/swarm-bot/.wiki/ANTI_HALLUCINATION.md
# Verify MEMORY_SYSTEM.md
ls -la /home/newadmin/swarm-bot/docs/MEMORY_SYSTEM.md && wc -c /home/newadmin/swarm-bot/docs/MEMORY_SYSTEM.md
# Verify memory tiers documented
grep -E "Working|Episodic|Semantic|Graph" /home/newadmin/swarm-bot/docs/MEMORY_SYSTEM.md | wc -l
```

**BLOCKER_IF:**
- Existing 5-pillar content cannot be found
- File write fails due to permissions

---

### CONTRACT #4: CLAUDE.md Maximization + OMEGA_BASELINE

**WHAT:**
Audit and enhance CLAUDE.md to maximum usefulness, create docs/OMEGA_BASELINE.md baseline metrics document

**FILES:**
READ:
- `CLAUDE.md` (current state - 449 lines)
- `AGENTS.md` (agent context)
- `.claude/settings.json`

WRITE:
- `CLAUDE.md` (enhanced with OMEGA sections if missing)
- `docs/OMEGA_BASELINE.md` (new - baseline metrics for regression tracking)

**DONE_WHEN:**
- CLAUDE.md contains reasoning_split configuration
- CLAUDE.md contains anti-hallucination 8-pillar reference
- CLAUDE.md contains MiniMax M2.7 as default model
- docs/OMEGA_BASELINE.md exists, >2000 bytes
- OMEGA_BASELINE.md includes: token counts, latency baselines, cost baselines, accuracy baselines

**PROOF_FORMAT:**
```bash
# Verify CLAUDE.md has key sections
grep -E "reasoning_split|MiniMax|ANTI_HALLUCINATION" /home/newadmin/swarm-bot/CLAUDE.md | head -10
# Verify OMEGA_BASELINE created
ls -la /home/newadmin/swarm-bot/docs/OMEGA_BASELINE.md
wc -c /home/newadmin/swarm-bot/docs/OMEGA_BASELINE.md
# Verify baseline metrics exist
grep -E "baseline|metric|token|cost|latency" /home/newadmin/swarm-bot/docs/OMEGA_BASELINE.md | wc -l
```

**BLOCKER_IF:**
- CLAUDE.md cannot be read
- File write fails

---

## PHASE 4: Agent Alignment

### CONTRACT #5: OpenCode 44 Agents Alignment

**WHAT:**
Verify all 44 OpenCode agent files exist and have implementations (not just stubs), verify skills directory structure, create docs/ROUTING.md

**FILES:**
READ:
- `.opencode/opencode.json` (agent definitions)
- `.opencode/agents/` (agent files - verify count)
- `.opencode/skills/` (skills definitions)

WRITE:
- `docs/ROUTING.md` (new - routing architecture across surfaces)

**DONE_WHEN:**
- At least 40 OpenCode agent .md files exist in .opencode/agents/
- Each agent file >500 bytes (not empty stubs)
- docs/ROUTING.md exists, >1000 bytes, covers keyword→semantic→LLM routing
- Skills directory structure documented

**PROOF_FORMAT:**
```bash
# Count OpenCode agent files
find /home/newadmin/swarm-bot/.opencode/agents/ -name "*.md" | wc -l
# Check file sizes
find /home/newadmin/swarm-bot/.opencode/agents/ -name "*.md" -exec wc -c {} \; | sort -n | head -10
# Verify ROUTING.md created
ls -la /home/newadmin/swarm-bot/docs/ROUTING.md
wc -c /home/newadmin/swarm-bot/docs/ROUTING.md
```

**BLOCKER_IF:**
- Fewer than 30 agent files found
- Most agent files are empty (<200 bytes)

---

### CONTRACT #6: Copilot Maximum Usefulness

**WHAT:**
Audit and enhance .github/copilot-instructions.md for maximum alignment with LEGIONA v3, verify it matches system prompt v3

**FILES:**
READ:
- `.github/copilot-instructions.md` (current state - 209 lines)
- `.wiki/LEGIONA_SYSTEM.md` (v3 system prompt)

WRITE:
- `.github/copilot-instructions.md` (enhanced if gaps found)

**DONE_WHEN:**
- copilot-instructions.md references LEGIONA v3
- copilot-instructions.md contains anti-hallucination 8 pillars
- copilot-instructions.md contains reasoning_split guidance
- copilot-instructions.md contains uncertainty phrases section
- File is >209 lines after update (if update needed)

**PROOF_FORMAT:**
```bash
# Check copilot-instructions.md content
wc -l /home/newadmin/swarm-bot/.github/copilot-instructions.md
# Verify key sections exist
grep -E "LEGIONA v3|reasoning_split|pillar|uncertainty" /home/newadmin/swarm-bot/.github/copilot-instructions.md
# Verify file updated (if needed)
wc -c /home/newadmin/swarm-bot/.github/copilot-instructions.md
```

**BLOCKER_IF:**
- File cannot be read
- Update removes required content

---

## PHASE 5: Cross-Surface & Knowledge Hygiene

### CONTRACT #7: Cross-Surface Unification + Architecture Dependency Map

**WHAT:**
Verify OpenCode ↔ Claude Code ↔ LegionBot bridges work correctly, create docs/architecture_dependency_map.md, verify cross-surface directive protocol

**FILES:**
READ:
- `core/opencode_bridge.py` (bridge implementation)
- `core/claude_code_bridge.py` (Claude Code bridge)
- `lib/legiona/bot/handlers.py` (LegionBot handlers)
- `config/departments.yaml` (agent routing)

WRITE:
- `docs/architecture_dependency_map.md` (new)

**DONE_WHEN:**
- opencode_bridge.py implements @claude and @legion directives
- claude_code_bridge.py exists and connects to GitNexus MCP
- docs/architecture_dependency_map.md exists, >1500 bytes
- Dependency map covers: core/, lib/legiona/, handlers/, agents/, tools/
- Bot handlers import from correct locations

**PROOF_FORMAT:**
```bash
# Verify bridge files exist and contain key functions
grep -E "def.*claude|def.*legion" /home/newadmin/swarm-bot/core/opencode_bridge.py
ls -la /home/newadmin/swarm-bot/core/claude_code_bridge.py
# Verify architecture_dependency_map.md created
ls -la /home/newadmin/swarm-bot/docs/architecture_dependency_map.md
wc -c /home/newadmin/swarm-bot/docs/architecture_dependency_map.md
# Verify key modules listed
grep -E "core/|lib/legiona/|handlers/|agents/" /home/newadmin/swarm-bot/docs/architecture_dependency_map.md | head -20
```

**BLOCKER_IF:**
- Bridge files missing required functions
- File write fails

---

### CONTRACT #8: Memory/Wiki/Knowledge Hygiene

**WHAT:**
Fix stale memory files (6+ days old), recreate missing referenced files (bashara-identity.md, opencode-tool-permissions.md), create .wiki/ORPHAN_TRIAGE.md

**FILES:**
READ:
- `lib/legiona/memory/global_memory.md` (last modified date)
- `lib/legiona/memory/rules.md` (last modified date)
- `.wiki/` (orphan analysis)

WRITE:
- `lib/legiona/memory/global_memory.md` (refresh if stale)
- `lib/legiona/memory/rules.md` (refresh if stale)
- `.wiki/ORPHAN_TRIAGE.md` (new - orphan file triage report)
- `.wiki/bashara-identity.md` (recreate if missing)
- `.wiki/opencode-tool-permissions.md` (recreate if missing)

**DONE_WHEN:**
- ORPHAN_TRIAGE.md exists, >1000 bytes, categorizes orphan files
- All memory files <7 days old OR explicitly flagged as historical
- bashara-identity.md exists (recreated from context if missing)
- opencode-tool-permissions.md exists (recreated from context if missing)
- compile_state.json exists in .wiki/

**PROOF_FORMAT:**
```bash
# Check memory file freshness
find /home/newadmin/swarm-bot/lib/legiona/memory/ -name "*.md" -mtime +6 -ls
# Verify ORPHAN_TRIAGE.md created
ls -la /home/newadmin/swarm-bot/.wiki/ORPHAN_TRIAGE.md
wc -c /home/newadmin/swarm-bot/.wiki/ORPHAN_TRIAGE.md
# Verify missing files recreated
ls -la /home/newadmin/swarm-bot/.wiki/bashara-identity.md
ls -la /home/newadmin/swarm-bot/.wiki/opencode-tool-permissions.md
# Verify compile_state exists
ls -la /home/newadmin/swarm-bot/.wiki/compile_state.json
```

**BLOCKER_IF:**
- File system permissions prevent writes
- Wiki is in read-only state

---

## PHASE 6: Deployment & Documentation Compilation

### CONTRACT #9: Deployment/Operations Readiness

**WHAT:**
Verify systemd service configuration, verify bot running status, create docs/BOOT_SEQUENCE.md and docs/runtime_entrypoints.md

**FILES:**
READ:
- `swarm-bot.service` or systemd unit file location
- `main.py` (runtime entry points)
- `lib/legiona/bot/` (bot startup)

WRITE:
- `docs/BOOT_SEQUENCE.md` (new - startup sequence documentation)
- `docs/runtime_entrypoints.md` (new - runtime entry point map)

**DONE_WHEN:**
- Systemd service file exists or user-level service documented
- docs/BOOT_SEQUENCE.md exists, >1000 bytes, covers boot steps
- docs/runtime_entrypoints.md exists, >1000 bytes, maps all entry points
- Entry points documented: main.py, handlers/, agents/, tools/, lib/legiona/

**PROOF_FORMAT:**
```bash
# Verify docs created
ls -la /home/newadmin/swarm-bot/docs/BOOT_SEQUENCE.md
ls -la /home/newadmin/swarm-bot/docs/runtime_entrypoints.md
wc -c /home/newadmin/swarm-bot/docs/BOOT_SEQUENCE.md
wc -c /home/newadmin/swarm-bot/docs/runtime_entrypoints.md
# Verify key entry points documented
grep -E "main.py|handlers|agents|tools" /home/newadmin/swarm-bot/docs/runtime_entrypoints.md | head -10
```

**BLOCKER_IF:**
- Systemd service file missing and no alternative startup method

---

### CONTRACT #10: Documentation Compilation + Final Report

**WHAT:**
Create docs/OMEGA_UPGRADE_REPORT.md final report, update .wiki/LEGIONA_SYSTEM.md with v4 additions, update .wiki/UPGRADE_LOG.md, perform final exhaustion pass

**FILES:**
READ:
- `docs/UPGRADE_REPORT_v2.md` (previous report)
- `docs/LEGIONA_OVERVIEW.md` (feature inventory)
- `AGENTS.md` (current agent context)

WRITE:
- `docs/OMEGA_UPGRADE_REPORT.md` (new - comprehensive final report)
- `.wiki/LEGIONA_SYSTEM.md` (updated with v4 changes)
- `.wiki/UPGRADE_LOG.md` (appended with v4 entries)

**DONE_WHEN:**
- docs/OMEGA_UPGRADE_REPORT.md exists, >5000 bytes, covers all 13 phases
- LEGIONA_SYSTEM.md updated with reasoning_split=True verification
- LEGIONA_SYSTEM.md updated with 8-pillar anti-hallucination
- UPGRADE_LOG.md contains entry for OMEGA AUDIT v4.0
- All 10 deliverables from task description created

**PROOF_FORMAT:**
```bash
# Verify all required docs exist
for f in OMEGA_BASELINE.md OMEGA_UPGRADE_REPORT.md architecture_dependency_map.md runtime_entrypoints.md BOOT_SEQUENCE.md FAILURE_MODES.md RECOVERY_RUNBOOK.md EVALS.md ROUTING.md MEMORY_SYSTEM.md; do
    ls -la /home/newadmin/swarm-bot/docs/$f 2>/dev/null && echo "EXISTS: $f" || echo "MISSING: $f"
done
# Verify wiki updates
grep "OMEGA AUDIT v4" /home/newadmin/swarm-bot/.wiki/UPGRADE_LOG.md
grep "8.pillar\|8-pillar" /home/newadmin/swarm-bot/.wiki/LEGIONA_SYSTEM.md
# Final exhaustion check
ls /home/newadmin/swarm-bot/.wiki/ORPHAN_TRIAGE.md
```

**BLOCKER_IF:**
- Any required deliverable still missing after all contracts
- File write failures prevent completion

---

## Execution Order

**Serial (must run in sequence):**
1. Contract #1 (Security) — must complete before any network/permission-granting work
2. Contract #2 (Reasoning_split) — must verify core correctness before building on it
3. Contract #3 (Anti-Hallucination) — depends on #2 for framework
4. Contracts #4-#8 (can run in parallel after #3)
5. Contracts #9-#10 (can run after #4-#8 complete)

**Parallel batches:**
- Batch A (after #2): #3, #4
- Batch B (after #3): #5, #6, #7, #8
- Batch C (after #B): #9, #10

**Final gate:**
- Contract #10 (Documentation Compilation) — must run last

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Bot breaks during monkey-patching removal | MED | HIGH | Test with bot still running, revert if issues |
| OpenCode agent files are mostly stubs | HIGH | MED | Focus on verifying actual implementation files |
| Memory files reference missing docs | MED | MED | Recreate missing docs from context |
| Large number of TODO/FIXME markers | HIGH | LOW | Document known tech debt, don't fix unless critical |
| Systemd service vs user process mismatch | MED | MED | Document both, ensure bot stays running |

---

## Blockers (Stop and Report)

If ANY of these occur, STOP immediately and report:
- Bot PID 449287 stops responding after changes
- reasoning_split=True not found in ANY config
- MiniMax M2.7 replaced with another model
- .env file contents revealed or altered
- Git permissions broken (cannot commit)
- Import failures after changes (test with `python -c "import ..."`)

---

*Plan generated: 2026-04-21 | LEGIONA OMEGA AUDIT v4.0*
