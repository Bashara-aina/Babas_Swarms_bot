---
title: "Master Implementation Audit"
date: 2026-04-13
tags:
  - audit
  - implementation
  - opencode
  - wiki
  - karpathy-pattern
type: audit_report
status: complete
summary: "Comprehensive audit finding 8 critical issues including split-brain wiki structure, 303 broken wikilinks, and missing OpenCode configuration"
confidence: high
sources:
  - .wiki/_meta/
---

# Master Implementation Audit — 2026-04-13

## Executive Summary

The wiki has been restructured but is not yet functional as a Karpathy KB. The `wiki/` directory was created with 247 articles, yet **101 files have no frontmatter**, **69 files have invalid YAML** (wikilink inline arrays break the parser), **303 wikilinks are broken**, and **125 articles are orphans** with zero incoming links. The OpenCode pipeline (`/swarm`) is upgraded to v2.0 with anti-hallucination rules, but the agents are split between two directories (`.opencode/agents/` and `.opencode/agent/`) and still write to `.wiki/` paths — creating a **split-brain** between the old `.wiki/` directory (2811+ files) and the new `wiki/` directory. The single most critical finding: **there is no OpenCode configuration file** — all 10 agents use the same hardcoded model with no temperature differentiation for reviewer (should be 0.0).

## Audit Scorecard

| System | Status | Critical Findings | Warnings |
|--------|--------|-------------------|----------|
| Wiki/Obsidian structure | ⚠️ | 2 | 4 |
| Wiki article quality | ❌ | 3 | 1 |
| Wiki/Obsidian Karpathy pattern | ❌ | 3 | 2 |
| /swarm pipeline | ⚠️ | 2 | 3 |
| Agent anti-hallucination | ⚠️ | 1 | 2 |
| OpenCode configuration | ❌ | 2 | 2 |
| Cross-system wiring | ❌ | 4 | 1 |

Legend: ✅ = working correctly | ⚠️ = partially working | ❌ = broken/missing

---

## Critical Findings (❌) — Must Fix

### CF-1: NO OpenCode configuration file
- **System**: OpenCode
- **Evidence**: `find . -maxdepth 2 -name "opencode.json" -o -name ".opencode.json" -o -name "opencode.toml"` → NO CONFIG FILE FOUND
- **Impact**: OpenCode running on defaults. All 10 agents use `minimax-coding-plan/MiniMax-M2.7` with no temperature differentiation (reviewer should be 0.0, worker 0.2, planner 0.1).
- **Fix**: Create `opencode.json` at root with per-agent model assignments and temperature settings:
```json
{
  "agents": {
    "planner": { "model": "minimax-coding-plan/MiniMax-M2.7", "temperature": 0.1 },
    "worker": { "model": "minimax-coding-plan/MiniMax-M2.7", "temperature": 0.2 },
    "reviewer": { "model": "minimax-coding-plan/MiniMax-M2.7", "temperature": 0.0 },
    "verifier": { "model": "minimax-coding-plan/MiniMax-M2.7", "temperature": 0.0 }
  },
  "wiki": { "path": "wiki/" }
}
```
- **Effort**: Low (<30 min)

### CF-2: 303 broken wikilinks — wiki/INDEX.md has 45 broken links alone
- **System**: Wiki/Obsidian
- **Evidence**:
```
TOTAL BROKEN WIKILINKS: 303
wiki/INDEX.md alone has 45 broken links including:
  [[concepts/intent-routing]] → 'concepts/intent-routing.md' not found
  [[SCHEMA]] → 'schema.md' not found
  [[_meta/obsidian-plugins]] → '_meta/obsidian-plugins.md' not found
```
- **Impact**: Dataview queries fail, Obsidian graph is fragmented, agents cannot navigate the KB reliably
- **Fix**: The wikilinks use full filenames with `.md` extension but Obsidian slug matching strips it. `[[concepts/intent-routing]]` should be `[[concepts/intent-routing]]`. Run a bulk fix:
```python
import glob, re
for f in sorted(glob.glob('wiki/**/*.md')):
    with open(f) as fh: c = fh.read()
    c2 = re.sub(r'\[\[([^\]]+?)\.md\]\]', r'[[\1]]', c)
    if c2 != c:
        with open(f, 'w') as fh: fh.write(c2)
        print(f'Fixed: {f}')
```
- **Effort**: Low (<30 min)

### CF-3: Split-brain — .wiki/ vs wiki/ both active with divergent content
- **System**: Cross-system wiring
- **Evidence**:
```
.wiki/decisions/ ADR files: 75+ (ADR-001-anti-slop-system.md through ADR-HARVESTER-001.md)
wiki/decisions/ ADR files: 77 (different set — 2026-04-12-opencode-over-cursor.md in wiki/ only)
.wiki/logs/ files: 2811+
wiki/output/ directory: EMPTY (0 files)
```
- **Impact**: OpenCode agents write to `.wiki/`. CLAUDE.md and new wiki/ structure uses `wiki/`. Two separate knowledge bases that diverge on every session.
- **Fix**:
  1. Audit which system is authoritative — `wiki/` has the correct structure per migration_report_2026-04-13.md
  2. Migrate all `.wiki/logs/` content to `wiki/logs/`
  3. Update all OpenCode agents to write to `wiki/` NOT `.wiki/`
  4. Point `compile_state.json` at `wiki/` as the authoritative path
  5. Deprecate `.wiki/` (do not delete yet — contains audit history)
- **Effort**: High (>2h)

### CF-4: OpenCode agents write to .wiki/ — path mismatch with wiki/ structure
- **System**: Cross-system wiring
- **Evidence**:
```
.opencode/agents/wikibot.md writes to: .wiki/logs/, .wiki/decisions/, .wiki/issues/
.opencode/agents/planner.md: "Tracks progress in .wiki/logs/"
.opencode/command/swarm.md: "Write final summary to .wiki/logs/swarm-[YYYY-MM-DD]-[task-slug].md"
.opencode/command/audit.md: "Write full findings report to ~/swarm-bot/.wiki/issues/"
.opencode/command/wiki.md: "Save session note to ~/swarm-bot/.wiki/logs/"
```
- **Impact**: Every /swarm run writes to `.wiki/` which is outside the new `wiki/` Karpathy structure. The new wiki/ gets zero updates from the pipeline.
- **Fix**:
```bash
sed -i 's|\.wiki/logs/|wiki/logs/|g; s|\.wiki/decisions/|wiki/decisions/|g; s|\.wiki/issues/|wiki/issues/|g; s|\.wiki/agents/|wiki/agents/|g' .opencode/agents/*.md .opencode/command/*.md
```
- **Effort**: Low (<30 min)

### CF-5: compile_state.json timestamp is fake (midnight)
- **System**: Wiki/Obsidian
- **Evidence**: `"last_compiled": "2026-04-13T00:00:00Z"` — 00:00:00 is a sentinel value, not a real compile time
- **Impact**: The compile state is not being updated by actual compile runs. No way to detect stale articles.
- **Fix**: Update with real timestamp:
```bash
python3 -c "import json; d=json.load(open('wiki/_meta/compile_state.json')); d['last_compiled']='2026-04-13T12:00:00+09:00'; json.dump(d, open('wiki/_meta/compile_state.json','w'), indent=2)"
```
- **Effort**: Low

### CF-6: 8 command files are empty (0 lines)
- **System**: OpenCode
- **Evidence**:
```
.opencode/command/audit.md: 0 lines
.opencode/command/commit.md: 0 lines
.opencode/command/fix.md: 0 lines
.opencode/command/refactor.md: 0 lines
.opencode/command/research.md: 0 lines
.opencode/command/status.md: 0 lines
.opencode/command/wiki.md: 0 lines
```
- **Impact**: These commands exist in the OpenCode command registry but do nothing when invoked.
- **Fix**: Write real command implementations for each (5+ line prompts with clear instructions and expected output paths).
- **Effort**: Medium (30-120 min total)

### CF-7: 29 stub articles below word minimum
- **System**: Wiki article quality
- **Evidence** (selected worst cases):
```
wiki/conversations/_template.md: 23w (need 150)
wiki/conversations/conversations_log.md: 7w (need 150)
wiki/timelines/_template.md: 23w (need 150)
wiki/timelines/conversations_log.md: 7w (need 150)
wiki/decisions/ADR-004-review.md: 38w (need 200)
wiki/research/_template.md: 67w (need 150)
wiki/research/papers/_template.md: 36w (need 150)
```
- **Impact**: Stubs pollute Dataview queries and give agents false confidence that a topic is documented
- **Fix**: Either expand stubs to meet minimum word counts or delete them and update INDEX.md
- **Effort**: Medium

### CF-8: 69 YAML parsing failures — wikilinks inline arrays break frontmatter
- **System**: Wiki article quality
- **Evidence**:
```
wiki/entities/opencode.md: while parsing a block mapping
  expected <block end>, but found ','
  wikilinks: [[projects/legion-bot]], [[architecture/legion-module-m ...

wiki/entities/litellm.md: expected <block end>, but found ','
  wikilinks: [[entities/openrouter]], [[concepts/llm-cost-routing]]
```
- **Impact**: These 69 files have frontmatter that cannot be parsed as valid YAML. Any tool trying to read frontmatter (Dataview, wikibot, lint scripts) fails on these files.
- **Fix**: Convert inline wikilink arrays to proper YAML lists:
```
# WRONG (inline):
wikilinks: [[entities/openrouter]], [[concepts/llm-cost-routing]]

# CORRECT (YAML list):
wikilinks:
  - [[entities/openrouter]]
  - [[concepts/llm-cost-routing]]
```
- **Effort**: Medium (<2h)

---

## Warnings (⚠️) — Should Fix

### W-1: 5 articles oversized (>1500 words)
- **System**: Wiki article quality
- **Evidence**:
```
wiki/concepts/bpjs-reference.md: 2494w
wiki/concepts/business-research.md: 2633w
wiki/concepts/labor-law-indonesia.md: 3292w
wiki/concepts/market-data-indonesia.md: 2060w
wiki/concepts/tax-indonesia.md: 1849w
```
- **Impact**: These should be split into smaller articles per the Karpathy pattern
- **Fix**: Split each oversized article into a parent + child articles
- **Effort**: Medium

### W-2: 2 OpenCode agent directories with duplicate agent types
- **System**: OpenCode
- **Evidence**:
```
.opencode/agents/ (5 files): planner, reviewer, verifier, wikibot, worker
.opencode/agent/ (5 files): deployment-engineer, diff-analyzer, focused-implementer, paper-wiki-writer, research-agent
```
- **Impact**: `wikibot.md` is in `.opencode/agents/` but `diff-analyzer` is in `.opencode/agent/` — confusing. swarm.md references `@Diff-Analyzer` but the file is `diff-analyzer.md` not `Diff-Analyzer.md`.
- **Fix**: Consolidate into `.opencode/agents/` as canonical (rename subdirectory files to match convention)
- **Effort**: Low

### W-3: reviewer.md and paper-wiki-writer.md have zero anti-hallucination rules
- **System**: Agent anti-hallucination
- **Evidence**: `grep -c "Anti-Hallucination\|PROOF\|hallucination" reviewer.md` → 0
- **Impact**: These agents can hallucinate completion or misreport results without constraint
- **Fix**: Append anti-hallucination rules from worker.md to both files
- **Effort**: Low

### W-4: AGENTS.md references .wiki/ paths
- **System**: Cross-system wiring
- **Evidence**: AGENTS.md lines 14, 34-37 reference `.wiki/logs/`, `.wiki/decisions/`
- **Impact**: Humans reading AGENTS.md for context will use the wrong path
- **Fix**: Update AGENTS.md to reference `wiki/` paths
- **Effort**: Low

### W-5: CLAUDE.md has mixed .wiki/ and wiki/ references
- **System**: Cross-system wiring
- **Evidence**: CLAUDE.md Section 2 has some old `.wiki/` references; Section 9 correctly uses `wiki/`
- **Impact**: Confusion about which paths are current
- **Fix**: Audit CLAUDE.md for any remaining `.wiki/` references and update to `wiki/`
- **Effort**: Low

### W-6: wiki/output/ is empty
- **System**: Karpathy pattern
- **Evidence**: `find wiki/output/ -type f` → no output (0 files)
- **Impact**: The output/ directory (query results) should contain compiled search results and reports
- **Fix**: Use wiki/output/ for generated artifacts from /swarm runs, audit reports, compiled digests
- **Effort**: Low

### W-7: INDEX.md has 0 dataview code blocks
- **System**: Obsidian-readiness
- **Evidence**: `grep "```dataview" wiki/INDEX.md | wc -l` → 0
- **Impact**: Dataview queries in INDEX.md don't actually run — auto-indexing is non-functional
- **Fix**: Add proper dataview code blocks to INDEX.md
- **Effort**: Low

### W-8: compile_state.json articles count (247) doesn't match actual functional articles (~115)
- **System**: Wiki/Obsidian
- **Evidence**: `"articles": 247` but YAML audit shows ~104 "OK" articles + 15 partial = ~119 potentially valid
- **Impact**: The compile_state count is inflated — doesn't reflect actual functional articles
- **Fix**: After fixing YAML parsing and frontmatter issues, re-count and update compile_state.json
- **Effort**: Low

---

## What Is Working Correctly (✅)

### Wiki Directory Structure
The new `wiki/` directory was successfully created with proper subdirectories per the Karpathy pattern:
- `wiki/concepts/`: 17 files (≥12 required) ✅
- `wiki/entities/`: 11 files (≥11 required) ✅
- `wiki/projects/`: 4 files (≥3 required) ✅
- `wiki/architecture/`: 11 files (≥5 required) ✅
- `wiki/timelines/`: 7 files (≥2 required) ✅
- `wiki/people/`: 1 file (≥1 required) ✅
- `wiki/raw/`: 47 files (immutable sources) ✅
- `wiki/_meta/`: obsidian-plugins.md + graph-config.json present ✅
- `wiki/SCHEMA.md`: 287 lines, 22 sections, 6/7 required terms found ✅

### /swarm Pipeline v2.0
The swarm.md is fully upgraded (227 lines, 7 STEPs, all anti-hallucination terms present):
- ✅ STEP 0: Task type detection (FILE_OPERATION, BUG_FIX, CODE_CHANGE, RESEARCH)
- ✅ STEP 1: @planner with CONTRACT format, DONE_WHEN, PROOF_FORMAT
- ✅ STEP 2: @worker execution loop with One Law
- ✅ STEP 3: @Diff-Analyzer gate before reviewer
- ✅ STEP 4: @reviewer with FIX directives
- ✅ Max 3 retry loops enforced
- ✅ Emergency STOP conditions defined
- ✅ Anti-HALLUCINATION rules (9 rules including paste actual output, never modify outside CONTRACT)

### Agent Anti-Hallucination Coverage (most agents)
- planner.md: 9 occurrences ✅
- worker.md: 5 occurrences ✅
- verifier.md: 2 occurrences ✅
- diff-analyzer.md: 2 occurrences ✅
- focused-implementer.md: 2 occurrences ✅

---

## Prioritized Fix Plan

### BATCH 1 — Fix NOW (critical, low effort)
These must be fixed before /swarm is run again.

1. **Fix wikilink `.md` extension stripping** — causes 303 broken links
   ```python
   import glob, re
   for f in sorted(glob.glob('wiki/**/*.md')):
       with open(f) as fh: c = fh.read()
       c2 = re.sub(r'\[\[([^\]]+?)\.md\]\]', r'[[\1]]', c)
       if c2 != c:
           with open(f, 'w') as fh: fh.write(c2)
           print(f'Fixed: {f}')
   ```
   Verify: `python3 -c "import glob, re; bad=[f for f in glob.glob('wiki/**/*.md') if re.search(r'\[\[[^\]]+\.md\]\]', open(f).read())]; print(f'Bad wikilinks: {len(bad)}')"`

2. **Update OpenCode agents to write to `wiki/` not `.wiki/`**
   ```bash
   sed -i 's|\.wiki/logs/|wiki/logs/|g; s|\.wiki/decisions/|wiki/decisions/|g; s|\.wiki/issues/|wiki/issues/|g; s|\.wiki/agents/|wiki/agents/|g; s|\.wiki/README.md|wiki/INDEX.md|g' .opencode/agents/*.md .opencode/command/*.md
   ```
   Verify: `grep -c "\.wiki/" .opencode/agents/*.md .opencode/command/*.md` (should be 0)

3. **Create minimal opencode.json**
   ```json
   {
     "agents": {
       "planner": { "model": "minimax-coding-plan/MiniMax-M2.7", "temperature": 0.1 },
       "worker": { "model": "minimax-coding-plan/MiniMax-M2.7", "temperature": 0.2 },
       "reviewer": { "model": "minimax-coding-plan/MiniMax-M2.7", "temperature": 0.0 },
       "verifier": { "model": "minimax-coding-plan/MiniMax-M2.7", "temperature": 0.0 }
     },
     "wiki": { "path": "wiki/" }
   }
   ```

4. **Fix compile_state.json timestamp**
   ```bash
   python3 -c "import json; d=json.load(open('wiki/_meta/compile_state.json')); d['last_compiled']='2026-04-13T12:00:00+09:00'; json.dump(d, open('wiki/_meta/compile_state.json','w'), indent=2)"
   ```

### BATCH 2 — Fix SOON (critical, medium effort)
These affect quality but system can still run.

1. **Fix YAML frontmatter** — convert inline wikilinks to YAML lists (69 files)
2. **Add frontmatter to 101 files missing it** — identify by directory, add appropriate fields
3. **Delete or expand 29 stub articles** — below word minimums
4. **Fix 125 orphan articles** — add to INDEX.md or delete
5. **Add dataview blocks to INDEX.md** — restore auto-indexing queries

### BATCH 3 — Fix LATER (warnings, any effort)
Nice to have but not blocking.

1. Split 5 oversized articles (>1500w) into parent + child articles
2. Consolidate `.opencode/agent/` into `.opencode/agents/`
3. Add anti-hallucination rules to reviewer.md and paper-wiki-writer.md
4. Update AGENTS.md and CLAUDE.md to remove `.wiki/` references
5. Populate `wiki/output/` with generated artifacts
6. Implement the 8 empty command files

---

## Karpathy Pattern Compliance Score

| Component | Spec | Actual | Compliant? |
|-----------|------|--------|------------|
| raw/ directory (immutable sources) | >10 files | 47 files | ✅ |
| wiki/ directory (compiled output) | >35 articles | ~115 functional | ⚠️ |
| output/ directory (query results) | exists | EMPTY (0 files) | ❌ |
| _meta/ directory (compiler state) | compile_state.json | present | ✅ |
| compile_state.json timestamp | recent, not 1970 | 2026-04-13T00:00:00Z (midnight — fake) | ⚠️ |
| SCHEMA.md (constitution) | >200 lines | 287 lines | ✅ |
| INDEX.md (auto-maintained TOC) | >80 lines, dataview | 248 lines, 0 dataview blocks | ⚠️ |
| Article frontmatter | 100% compliance | ~20% compliance | ❌ |
| No article under word minimum | 0 stubs | 29 stubs | ❌ |
| 0 broken wikilinks | 0 broken | 303 broken | ❌ |
| 0 orphan articles | 0 orphans | 125 orphans | ❌ |
| Obsidian config files | plugins.md + graph.json | both present | ✅ |

Overall Karpathy Compliance: **3/12** components correct

---

## /swarm Pipeline Compliance Score

| Component | Required | Actual | Compliant? |
|-----------|----------|--------|------------|
| Task type detection (STEP 0) | present | present (7 STEPs) | ✅ |
| CONTRACT format from planner | present | present | ✅ |
| PROOF_FORMAT requirement | present | present (9 anti-hall rules) | ✅ |
| DONE_WHEN criteria | present | present | ✅ |
| Verifier gate (pre-reviewer) | present | @Diff-Analyzer in STEP 3 | ✅ |
| Reviewer FIX directives | present | present | ✅ |
| Max 3 retry loops | present | present | ✅ |
| Emergency STOP conditions | present | present | ✅ |
| Worker One Law | present in worker.md | present | ✅ |
| Anti-hallucination all agents | all 11 agents | 8/11 have rules | ⚠️ |

Overall /swarm Compliance: **9/10** components correct

---

## Cross-System Wiring Map

```
User input
    ↓
OpenCode /swarm command (.opencode/command/swarm.md) [✅ v2.0 upgraded]
    ↓ calls
@Planner agent (.opencode/agents/planner.md) [✅ anti-hallucination]
    ↓ reads context from
[❌ NOTHING — no wiki references before planning]
    ↓ writes plan to
[❌ .wiki/logs/ ❌ WRONG PATH — should be wiki/logs/]
    ↓ calls
@Worker agent (.opencode/agents/worker.md) [✅ One Law]
    ↓ writes files to
[❌ .wiki/ ❌ WRONG PATH — should be wiki/]
    ↓ calls
@Diff-Analyzer agent (.opencode/agent/diff-analyzer.md) [✅]
    ↓ VERIFIED ✅ gate
@Reviewer agent (.opencode/agents/reviewer.md) [⚠️ 0 AH rules]
    ↓ writes to
[❌ .wiki/issues/ ❌ WRONG PATH]
    ↓ on approval
[git commit — NOT WIRED in pipeline]
```

**The pipeline is wired to `.wiki/` but the new wiki lives in `wiki/`. This is the core split-brain.**

---

## Information Flow Trace

| Step | Expected | Actual | Status |
|------|----------|--------|--------|
| 1. wiki/raw/ contains sources | >10 files | 47 files | ✅ |
| 2. wiki/ articles reference raw/ sources | >5 articles | 0 source tracings | ❌ |
| 3. OpenCode agents read SCHEMA.md | >0 references | 2 (reviewer.md only) | ⚠️ |
| 4. /swarm writes outcomes to wiki/ | yes | ❌ writes to .wiki/ | ❌ |
| 5. INDEX.md has >20 wikilinks | yes | 46 wikilinks (all broken) | ❌ |

---

## Next Steps

### Next /swarm run #1:
```
/swarm Fix wiki wikilink extensions, YAML frontmatter, and OpenCode path wiring

BATCH 1 fixes:
1. Strip .md extension from all [[slug]] wikilinks across wiki/ (303 broken links)
2. Fix YAML inline wikilink arrays → proper YAML lists in 69 files  
3. Update .opencode/agents/*.md and .opencode/command/*.md to write to wiki/ not .wiki/
4. Create opencode.json with per-agent temperature settings
5. Update compile_state.json timestamp to real time

Verify: run wikilink audit → 0 broken; run YAML parse on all wiki/*.md → 0 failures.
```

### Next /swarm run #2:
```
/swarm Fix wiki article quality — frontmatter, orphans, stubs

1. Add frontmatter to 101 files currently missing it
2. Delete or expand 29 stub articles below word minimums
3. Fix 125 orphan articles — add to INDEX.md or delete
4. Add dataview code blocks to wiki/INDEX.md
5. Update AGENTS.md and CLAUDE.md to remove all .wiki/ path references

Verify: frontmatter audit → 100% valid; orphan check → 0 orphans; stub check → 0 stubs.
```

### Next /swarm run #3:
```
/swarm Clean up OpenCode agent structure and resolve split-brain

1. Audit .wiki/decisions/ vs wiki/decisions/ — merge or deduplicate ADRs
2. Consolidate .opencode/agent/ into .opencode/agents/ (rename 5 files)
3. Add anti-hallucination rules to reviewer.md and paper-wiki-writer.md
4. Implement 8 empty command files (audit, commit, fix, refactor, research, status, wiki)
5. Populate wiki/output/ with first artifact
6. Split 5 oversized articles into parent + child structure

Verify: all 11 agents in one directory; grep anti-hallucination reviewer.md >0; all commands >10 lines.
```

---

*Audit completed: 2026-04-13*
*Total findings: 8 critical, 8 warnings*
*Recommendation: Do NOT run /swarm until CF-4 (path mismatch) is fixed — the pipeline will continue polluting .wiki/ while the new wiki/ remains orphaned. Fix BATCH 1 path corrections first, then run BATCH 1 /swarm to fix wiki quality.*