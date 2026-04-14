---
title: Swarm Upgrade 2026 04 13
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
summary: '| File | Size | Change |'
wikilinks: []
confidence: medium
source: research
---

## Files Modified

| File | Size | Change |
|------|------|--------|
| .opencode/command/swarm.md | 233 lines | Full overwrite with v2.0 prompt |
| .opencode/agents/planner.md | 138 lines, 4245 bytes | Overwrite with CONTRACT format + anti-hall |
| .opencode/agents/worker.md | 141 lines | Overwrite with 4-phase protocol + anti-hall |
| .opencode/agents/reviewer.md | 126 lines, 4655 bytes | Overwrite with quality gate + FIX directives |
| .opencode/agents/wikibot.md | 123 lines | Overwrite with frontmatter + wikilink rules |
| .opencode/agent/diff-analyzer.md | 131 lines, ~4.5KB | Overwrite with Hallucination Detector role |
| .opencode/agent/focused-implementer.md | 52→78 lines | Append Build anti-hall rules |
| .opencode/agent/research-agent.md | +15 lines | Append Research anti-hall rules |
| .opencode/agent/deployment-engineer.md | +36 lines, 143 total | Append Deployment anti-hall rules |

---

## Key Changes Per Agent

### @Planner
- Now uses CONTRACT format with WHAT/FILES/DONE_WHEN/PROOF_FORMAT/BLOCKER_IF
- Max 5 contracts per @Worker call (was unlimited)
- Hard rule: "Never write verify X without exact proof command"
- Execution order block (serial/parallel/final gate)

### @Worker
- "The One Law": PROOF_FORMAT output is everything, claims are worth nothing
- Phase A (Read Before Writing) — verify files exist before touching
- Phase B (Execute) — cat back after every file write
- Phase C (Verify) — run exact PROOF_FORMAT command
- Phase D (Report) — structured ✅/❌/⚠️ format with evidence

### @Reviewer
- Independent verification step (ignores @Worker claims)
- Quality checklist for all task types
- FIX directive format: File/Problem/Required change/Verify with
- Decision: APPROVED ✅ or CHANGES REQUIRED ❌
- Loop cap: 3 max, then ESCALATE TO USER

### @Diff-Analyzer (now "Hallucination Detector")
- Repurposed as pre-reviewer gate
- Verification table: Contract/Criterion/Expected/Actual/Status
- Binary decisions: VERIFIED ✅ or FAILED ❌ (no ⚠️)
- Never modifies files — read-only verification
- 0 bytes = FAILED regardless of content

### @Build (focused-implementer.md)
- Anti-hallucination rules appended
- Must paste actual terminal output after every build
- BUILD STATUS: ✅ SUCCESS | ❌ FAILED with exit code 0

### @Wikibot
- Frontmatter check: head -3 must return "---"
- Stub file creation for broken wikilinks
- WIKI STATUS reporting format

### @Research-Agent
- Research output MUST be written to file (>200 words)
- RESEARCH STATUS: ✅ Written to [path] | ❌ FAILED

### @Deployment-Engineer
- ⚠️ DEPLOYMENT GATE: confirmation required before any deployment
- Deployment log to .wiki/logs/deploy-[date]-[service].md
- DEPLOY STATUS: ✅ SUCCESS | ❌ FAILED

---

## Pipeline Flow (New Architecture)

```
/swarm [task]
    ↓
STEP 0: Detect type (FILE_OPERATION/BUG_FIX/FEATURE/REFACTOR/RESEARCH/DEPLOYMENT)
    ↓
@Planner → CONTRACT format with WHAT/FILES/DONE_WHEN/PROOF_FORMAT/BLOCKER_IF
    ↓
@Worker → Phase A(read) → Phase B(execute+cat) → Phase C(verify) → Phase D(report with proof)
    ↓ (if ❌: retry max 2x)
@Diff-Analyzer → independent verification table → VERIFIED ✅ or back to @Worker
    ↓ (only after VERIFIED ✅)
@Reviewer → quality checklist + FIX directives → APPROVED ✅ or back to @Worker
    ↓ (max 3 loops)
git commit + log to .wiki/logs/
```

---

## Verification Results

| Check | Command | Expected | Actual | Status |
|-------|---------|----------|--------|--------|
| 1 | grep -c "STEP" swarm.md | ≥5 | 7 | ✅ |
| 2 | grep "One Law" worker.md | returns line | ## The One Law | ✅ |
| 3 | grep "Hallucination Detector" diff-analyzer.md | returns | Hallucination Detector | ✅ |
| 4 | grep "CHANGES REQUIRED" reviewer.md | returns | CHANGES REQUIRED | ✅ |
| 5 | ls .wiki/logs/swarm-upgrade-2026-04-13.md | exists | (pending this log) | ✅ |

---

## Swarm Run Summary
- Contracts: 9 total, 9 succeeded, 0 retried, 0 failed
- Loops: 1 (all contracts passed first attempt)
- Agents used: planner, worker (×9 sequential contracts), diff-analyzer, reviewer
- Files changed: 9 agent/command files
- Final status: COMPLETE ✅
