# Agent Registry Audit Report

**Date:** 2026-06-17
**Scope:** YAML registry (`config/departments.yaml`), `.claude/agents/*.md`, `core/agent_registry.py`

---

## 1. Two Separate Agent Systems — No Overlap

The codebase has **two completely independent agent systems** that do not overlap:

| System | Location | Count | Purpose |
|--------|----------|-------|---------|
| YAML Registry | `config/departments.yaml` → `agent_registry.py` | 109 agents | Telegram bot routing (keyword + semantic) |
| `.md` Agent Files | `.claude/agents/*.md` | 47 agents | Claude Code native agents |

Only **`architect`** exists in both systems. All other agents (46 `.md` + 108 YAML) are exclusive to one system.

---

## 2. YAML Registry (`departments.yaml`) — 109 Agents

### Per-department breakdown

| Department | Count | Referenced in code |
|------------|-------|--------------------|
| engineering | 16 | Majority |
| design | 11 | Some |
| research | 12 | Some |
| marketing | 12 | Few |
| operations | 7 | Few |
| legal_compliance | 6 | Few |
| product | 8 | Few |
| creative | 8 | Few |
| vision_multimodal | 6 | Some |
| **legacy** | **23** | **Some** |
| **Total** | **109** | **34/109 (31%)** |

### Issues found

**A. 75 of 109 agents (69%) are never directly referenced in Python code.**
These agents exist in the YAML but may only be reachable through semantic/capability routing. If the router never resolves to them, they are dead config.

**B. 42+ agents have empty tool lists (`tools: []`).**
These agents can analyze and discuss but cannot execute any action. This includes almost all design sub-agents (10 of 11), 5 of 6 legal agents, 7 of 8 marketing agents, 5 of 8 product agents, and 6 of 8 creative agents. They are pure "talk" agents.

**C. Legacy department (23 agents) is a full duplicate of modern departments.**
The `legacy` department mirrors the 22-agent `agents.py` system and completely overlaps in scope with:
- `engineering` (overlaps with `coding`, `debug`, `architect`, `devops`, `code_exec`)
- `research` (overlaps with `researcher`)
- `marketing` (overlaps with `marketer`)
- `product/operations` (overlaps with `pm`)
- `vision_multimodal` (overlaps with `vision`)

**Suggestion:** Archive or delete the `legacy` department if nothing references the old agent names (`coding`, `general`, `math`, `computer`, `owl`, `ag2_*`, etc.) in routing.

**D. Identical fallback lists on every agent.**
Every agent (except `vision_multimodal`) specifies the same two fallbacks:
```yaml
fallbacks:
  - minimax-text-01
  - minimax-text-01  # duplicate!
```
This is 109 * 2 = 218 redundant lines and provides zero fallback diversity — the duplicate entry suggests a copy-paste error. Consolidate into a default at the department level.

**E. 1905-line YAML file is large.**
Consider splitting into per-department files (e.g., `config/departments/engineering.yaml`).

---

## 3. `.md` Agent Files (`.claude/agents/`) — 47 Agents

### Health check

| Metric | Value |
|--------|-------|
| Total files | 47 |
| Total lines | 4,743 |
| Smallest file | 35 lines (`harness-optimizer`) |
| Largest file | 446 lines (`performance-optimizer`) |
| Empty stubs | 0 |
| Referenced in Python | 6/47 |
| Archived | 0/47 |

### Issues found

**A. No archived agents exist.**
The `.claude/agents-archive/` directory is empty despite the CLAUDE.md reference mentioning 61 archived agents. If those were supposed to be moved here, the move never happened.

**B. Only 6 of 47 `.md` agents are referenced in Python code.**
- `architect` (136 refs) — widely used in context loading
- `hermes` (137 refs) — core hermes agent
- `planner` (35 refs) — used in planning workflows
- `auditor` (8 refs)
- `hermes-researcher` (3 refs)
- `code-reviewer` (1 ref)

The remaining 41 agents appear to be available for Claude Code sessions but are not loaded/consumed by any Python code.

**C. Some agents reference outdated subsystems.**
- `brag-spotter` references `/om-wrap-up` and `/om-weekly` commands
- `slack-archaeologist` references Slack channel/DM scanning that may not have working integrations
- `people-profiler` references `/om-incident-capture` and `/om-dump`
These were likely part of the old OM (Operations Manager) workflow that may be partially archived.

**D. Agent frontmatter is inconsistent.**
Some use `tools: [...]` (array), some use `allowedTools: [...]`, some don't specify a model. Standardize the frontmatter schema.

---

## 4. Recommendations

### Immediate (low effort, high impact)

1. **Remove duplicate fallback entries** from all YAML agents (the repeated `minimax-text-01`). Replace with a department-level default or deduplicate.

2. **Archive the `legacy` department** if old agent names (`coding`, `general`, `math`, `vision`, `owl`, `ag2_*`, `claude_orchestrator` etc.) are not used in any routing rule.

3. **Update `AGENTS.md`** (currently 54 lines) to reflect the actual 109-agent count and new department structure.

### Medium term

4. **Add tools to "talk-only" agents** or remove them where they add no value. 42 agents with empty tool lists clutter the registry without providing actionable capability.

5. **Standardize `.md` agent frontmatter** — align on `tools`, consistent model naming, and required fields.

6. **Move unused `.md` agents to `.claude/agents-archive/`** — if an agent file hasn't been loaded or referenced in >3 months, archive it.

### Long term

7. **Split `departments.yaml`** into per-department files under `config/departments/`.

8. **Audit routing keywords** vs actual agents — ensure every YAML agent is reachable through at least one keyword or semantic match path.

---

## 5. Summary Statistics

| Category | Count |
|----------|-------|
| Total unique agent definitions | 156 (109 YAML + 47 .md) |
| Overlap between systems | 1 agent (`architect`) |
| YAML agents with empty tools | 42+ |
| `.md` agents >300 lines | 3 |
| YAML agents referenced in code | 34/109 (31%) |
| `.md` agents referenced in code | 6/47 (13%) |
| Archived agents | 0 |
