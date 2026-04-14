---
title: Adr 001 Coding References Pipeline
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: User requested adding coding reference repos documentation to `.wiki/06-legion-instructions/CODING-REFERENCES.md`.
  The content consists of 20 curated GitHub repos intended to make opencode/Legion
  i...
wikilinks: []
confidence: medium
source: research
---
User requested adding coding reference repos documentation to `.wiki/06-legion-instructions/CODING-REFERENCES.md`. The content consists of 20 curated GitHub repos intended to make opencode/Legion into a 10/10 full-stack engineer.

**Target file**: `.wiki/06-legion-instructions/CODING-REFERENCES.md`  
**Target directory**: Already exists at `.wiki/06-legion-instructions/`
---


## Pipeline Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   PLANNER   │───▶│   WORKER    │───▶│  REVIEWER   │
│  (decompose)│    │  (execute)  │    │  (verify)   │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## Atomic Subtasks

### Subtask 1: Content Acquisition & Verification
**Agent**: @worker  
**Action**: Obtain the 20 GitHub repos list from user-provided context  
**Input**: User's curated repo list  
**Output**: Structured list of 20 repos with names, URLs, and descriptions  
**Done when**: All 20 repos are captured with required metadata  

### Subtask 2: File Write  
**Agent**: @worker  
**Action**: Write `CODING-REFERENCES.md` with frontmatter and repo entries  
**Input**: Structured repo list from Subtask 1  
**Output**: `.wiki/06-legion-instructions/CODING-REFERENCES.md`  
**Done when**: File exists at target path with valid content  

### Subtask 3: Quality Review  
**Agent**: @reviewer  
**Action**: Verify file content, formatting, links, and completeness  
**Input**: `.wiki/06-legion-instructions/CODING-REFERENCES.md`  
**Output**: Review report with PASS/FAIL and any fix requests  
**Done when**: Reviewer issues PASS or requests specific fixes  

### Subtask 4: Fixes (if needed)  
**Agent**: @worker  
**Action**: Address any reviewer-fix requests  
**Input**: Reviewer feedback  
**Output**: Updated `CODING-REFERENCES.md`  
**Done when**: All reviewer comments addressed  

---

## File Format Specification

```markdown
---
title: Coding References
description: Curated GitHub repos for building a 10/10 full-stack engineer agent
date: 2026-04-11
---

# Coding References

<!-- Repo entries -->

## Categories

| # | Repo | Focus | URL |
|---|------|-------|-----|
| 1  | repo-name | description | link |
...

## Notes

- Any additional context
```

---

## Done Criteria

### Subtask 1 (Content Acquisition)
- [ ] All 20 repos captured with:
  - Repository name
  - GitHub URL
  - Brief description (what it teaches)
  - Category/focus area

### Subtask 2 (File Write)
- [ ] File created at correct path
- [ ] Valid frontmatter (YAML)
- [ ] All 20 repos listed with valid URLs
- [ ] Proper heading structure
- [ ] Categorized appropriately

### Subtask 3 (Review)
- [ ] All URLs are valid GitHub links
- [ ] No placeholder text or TODOs
- [ ] Consistent formatting
- [ ] No hallucinations (repo info is verifiable)

---

## Final Deliverable

`.wiki/06-legion-instructions/CODING-REFERENCES.md` containing:
- 20 curated GitHub repos
- Proper frontmatter
- Clear categorization
- Descriptions for each repo explaining its relevance to full-stack engineering

---

## Alternatives Considered

1. **Single-agent execution**: Rejected — three-agent pipeline ensures review quality
2. **Multiple files by category**: Rejected — single file is simpler for LLM context window
3. **YAML format**: Rejected — Markdown table is more readable

---

## Dependencies

- User must provide the 20-repo list (external input)
- Target directory `.wiki/06-legion-instructions/` already exists
