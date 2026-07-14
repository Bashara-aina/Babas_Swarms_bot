# FINAL VERIFICATION CHECKLIST — EVERY QUESTION, RECOMMENDATION, FINDING TRACKED

## Mission
Read every single file in the IndustReal consultation. For each question, recommendation, finding, and action item: determine its current status. Produce a master verification document.

---

### LOAD ALL FILES

**Context docs (20 files):**
`analyses/consult_claude_science/`
- 208 through 227 — all consultation documents

**V1 Agent Outputs (18 files):**
`analyses/consult_claude_science/agent_outputs/`
- agent01 through agent10 — V1 discovery
- agent11 through agent15 — V1 debate
- FINAL_CONSULTATION_REPORT.md — V1 executive summary
- IMPLEMENTATION_PLAN.md — V1 30-item ranked plan
- VERIFIED_CITATIONS.md — V1 ~100 verified papers

**V2 Agent Outputs (20 files):**
`analyses/consult_claude_science/consult_v2/agent_outputs/`
- agent01 through agent20 — V2 deep research agents

**Codebase (verify against):**
- `src/models/mvit_mtl_model.py`
- `src/config.py`
- `scripts/train_mtl_mvit.py`
- `src/losses/`
- `src/data/industreal_dataset.py`

---

### PROCESS

For each file, in order:

**Step 1 — Read the entire file**
**Step 2 — Extract every actionable item:**
- Questions asked (to Claude Science or to the team)
- Recommendations made (with expected impact)
- Findings/conclusions (with confidence level)
- Action items (with effort estimate)
- Implementation steps (with priority)

**Step 3 — For each item, determine status:**

| Status | Definition |
|--------|------------|
| ✅ ANSWERED | Question has been resolved by literature, experiment, or analysis |
| ✅ IMPLEMENTED | Code change has been made (verify by reading the actual code) |
| 🟡 POSTPONED | Intentional deferral with valid reason |
| ❌ NOT IMPLEMENTED | No action taken, no decision made |
| 🔴 NEEDS ATTENTION | Critical item with no resolution path |
| ⚪ OUTDATED | Superseded by newer findings or changed conditions |

**Step 4 — For "implemented" items:**
- Read the actual code file to verify the implementation exists
- Check: does the code match the recommendation?
- If not match: flag as 🔴 IMPLEMENTED INCORRECTLY

**Step 5 — Cross-reference:**
- Do V1 and V2 make conflicting recommendations? Flag as 🔴 CONFLICT
- Do V2 recommendations supersede V1? Update V1 status to ⚪ SUPERSEDED
- Are there items from context docs (208-227) that were never addressed by any agent? Flag as ❌ UNANSWERED

---

### OUTPUT FORMAT

**MASTER_VERIFICATION.md** — organized by source document:

```
## Doc/Source: [filename]

### Item 1: [brief description]
- Source: [doc name, section, line]
- Type: [question | recommendation | finding | action]
- Status: [ANSWERED | IMPLEMENTED | POSTPONED | NOT IMPLEMENTED | NEEDS ATTENTION]
- Evidence: [what proves this status — code link, paper citation, experiment result]
- Cross-ref: [related items in other documents]
- Priority: [CRITICAL | HIGH | MEDIUM | LOW]
- Notes: [any context needed]

### Item 2: ...
```

Final summary tables:

```
### Summary by Status
| Status | Count | Critical Items |
|--------|-------|----------------|
| ✅ ANSWERED | N | — |
| ✅ IMPLEMENTED | N | — |
| 🟡 POSTPONED | N | list |
| ❌ NOT IMPLEMENTED | N | list |
| 🔴 NEEDS ATTENTION | N | list |
| ⚪ OUTDATED / SUPERSEDED | N | — |
| 🔴 CONFLICT | N | list |

### Summary by Priority (unresolved only)
| Priority | Count | Items |
|----------|-------|-------|
| CRITICAL | N | list |
| HIGH | N | list |
| MEDIUM | N | list |
| LOW | N | list |

### Items Requiring Immediate Action
1. [item] — [reason]
2. [item] — [reason]
```

**UNANSWERED_QUESTIONS.md** — only items with status NEEDS ATTENTION or NOT IMPLEMENTED
- These are the gaps that must be addressed before submission
- Organized by: data/architecture/training/paper

---

### VERIFICATION RULES

1. **Every recommendation from V1 IMPLEMENTATION_PLAN.md** (30 ranked items): check if code was written, verify by reading the source
2. **Every question from V1 agent_outputs/*.md**: check if V2 agents addressed it, or if experiment resolved it
3. **Every finding from V2 agent_outputs/*.md**: verify against actual literature using paper-search MCP
4. **Every claim from V1 VERIFIED_CITATIONS.md**: re-verify (papers may have been updated, retracted, or superseded)
5. **Every experiment from 223_EXPERIMENTAL_PROTOCOL.md**: check if it was run, results exist
6. **Every ablation from 222_ABLATION_STUDY_PLANNING.md**: check if it was run
7. **Every risk from 225_RISK_ASSESSMENT.md**: check if it materialized, what was done

### TOOLS
- `Read`: all 58+ files
- `paper-search` MCP: re-verify any questionable citation
- `Bash` with `python3`: check if code changes exist in source files
- `grep`: search codebase for specific function names, parameters, implementations

### OUTPUT DIRECTORY
`analyses/consult_claude_science/verification/`
- `MASTER_VERIFICATION.md` — full checklist
- `UNANSWERED_QUESTIONS.md` — gaps requiring action
