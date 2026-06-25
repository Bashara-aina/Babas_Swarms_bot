# OPENCODE — OBSIDIAN / WIKI MASTER RESTRUCTURE PROMPT
# Karpathy LLM Knowledge Base Pattern — Universal Implementation
# Applies to: ANY folder, ANY project, ANY future content dropped in this repo
# Written: 2026-04-13 | Based on: Andrej Karpathy April 2026 LLM KB workflow

---

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  MISSION                                                          ┃
┃  Audit, correct, and rebuild the entire knowledge base in        ┃
┃  this repo following the Karpathy LLM KB pattern.                ┃
┃                                                                   ┃
┃  Input  → everything currently in this repo                      ┃
┃  Output → a clean, queryable, Obsidian-ready wiki/ vault         ┃
┃           that covers ALL projects, ALL ideas, ALL decisions      ┃
┃                                                                   ┃
┃  Do NOT touch: main.py, core/, handlers/, SOUL.md, CLAUDE.md     ┃
┃  Touch everything else that is documentation / knowledge         ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## PHASE 0 — AUDIT BEFORE TOUCHING ANYTHING

Before creating or moving a single file, do a complete audit.
Read every directory listed below. Output a structured audit report
to `wiki/_meta/audit_report_YYYY-MM-DD.md` with these sections:

### Directories to Audit

```
Root level .md files:
  AGENTS.md, CHANGELOG.md, CLAUDE.md, CLAUDE_DEEP_AUDIT_PROMPT.md,
  CLEANUP_LOG.md, CONCERNS_FIXED_REPORT.md, CONTRIBUTING.md,
  DEEP_AUDIT_2026-04-12.md, DEPLOYMENT.md, IMPLEMENTATION_STATUS.md,
  LEGION_CONCERNS_MASTER_PROMPT.md, LEGION_MASTER.md,
  LEGION_PRODUCTION_HARDENING.md, OPENCODE_DEPTH_UPGRADE_PROMPT.md,
  OPENCODE_EXTERNAL_TOOLS_INTEGRATION.md, README.md, SOUL.md,
  SWARM_WIRING.md, TESTING.md, WIRING_VERIFIED_2026-04-12.md

Directories:
  wiki/           ← existing wiki (may be unstructured)
  .wiki/          ← hidden wiki (check what's inside)
  docs/           ← documentation
  papers/         ← research papers
  prompts/        ← prompt files
  skills/         ← markdown skill files (28 files per audit)
  .opencode/      ← OpenCode config/context
  .claude/        ← Claude config/context
  .cursor/        ← Cursor config/context
  data/           ← data files, JSONs
  config/         ← configuration files
  _archive/       ← archived content
```

### Audit Report Structure

For each directory and root .md file, record:

```markdown
## Audit: [path/filename]
- **Type**: raw_knowledge | wiki_article | config | code | archive
- **Status**: well_structured | needs_migration | duplicate | outdated | stub
- **Content Summary**: [1-2 sentences of what it actually contains]
- **Target Location**: [where it should live after restructure]
- **Wikilink Potential**: [list 3-5 concepts it should link to]
- **Action Required**: migrate | compile | move | archive | delete | keep_as_raw
```

### Duplicate Detection

Before moving anything, check for duplicates:
- Files with overlapping content (e.g., multiple audit files)
- Concepts described in 3+ different files with no canonical article
- Old versions of the same document (flag for archive)

Output the full duplicate map in the audit report.

---

## PHASE 1 — BUILD THE FINAL DIRECTORY STRUCTURE

After audit, create this exact structure.
Do NOT deviate from it. Every folder must exist even if initially empty.

```
wiki/                              ← THE SINGLE SOURCE OF TRUTH
│
├── SCHEMA.md                      ← Master constitution (see Phase 2)
├── INDEX.md                       ← Auto-maintained table of contents
│
├── raw/                           ← IMMUTABLE. Human-owned. LLM never edits.
│   ├── audits/                    ← All audit files (DEEP_AUDIT, etc.)
│   ├── roadmaps/                  ← Planning docs, phase documents
│   ├── prompts/                   ← All master prompts (OPENCODE_*, CLAUDE_*)
│   ├── changelogs/                ← CHANGELOG.md, CLEANUP_LOG, fix reports
│   ├── configs/                   ← .env.example snapshots, config summaries
│   ├── papers/                    ← Research papers (from papers/ dir)
│   ├── skills_ref/                ← The 28 markdown skill files from skills/
│   ├── docs/                      ← All docs/ content
│   └── snapshots/                 ← Point-in-time code snapshots of key files
│
├── concepts/                      ← Abstract ideas, algorithms, patterns
├── entities/                      ← Named things: tools, models, APIs, services
├── projects/                      ← One page per active project
├── decisions/                     ← Decision log with rationale + date
├── timelines/                     ← Chronological event/version history
├── architecture/                  ← System design, data flows, module maps
├── people/                        ← Key people, researchers, influences
│
├── output/                        ← Query results, health reports, exports
│   ├── queries/                   ← Answers to complex questions
│   └── health/                    ← Weekly lint reports
│
└── _meta/                         ← Compiler state, audit logs
    ├── SCHEMA.md                  ← Same as wiki/SCHEMA.md (symlink or copy)
    ├── compile_state.json         ← Tracks last processed timestamp per file
    ├── audit_report_YYYY-MM-DD.md ← Phase 0 audit output
    └── lint_log.md                ← History of all health check runs
```

### Critical Rule on .wiki/ Hidden Directory

Check `.wiki/` contents. If it contains structured articles → migrate to `wiki/`.
If it contains config/metadata only → leave in place, add a note in audit report.
Do NOT maintain two parallel wiki directories. Consolidate everything into `wiki/`.

---

## PHASE 2 — CREATE wiki/SCHEMA.md

This is the constitution. Every future LLM operation reads this first.
Create this file exactly as specified:

```markdown
---
title: Knowledge Base Schema
version: 3.0
owner: Bashara
repo: Babas_Swarms_bot
created: 2026-04-13
scope: universal — all projects, all folders, all future content
---

# KNOWLEDGE BASE SCHEMA v3.0

## PRIME DIRECTIVE

This wiki is the compiled, queryable knowledge layer for ALL of Bashara's work.
It covers: Legion bot, cekwajar.id, rumahlabuh.com, academic research,
and any future project added to this repo or linked from it.

Architecture (Karpathy pattern):
  raw/       = source code (immutable, human-owned, LLM never edits)
  wiki/      = compiled output (LLM-owned, never manually edited by human)
  output/    = query results and health reports
  _meta/     = compiler state and operational logs

---

## ARTICLE STRUCTURE

Every wiki/ article (except INDEX.md and SCHEMA.md) MUST have this frontmatter:

---
title: [Exact Concept Name]
type: concept | entity | project | decision | timeline | architecture | person
project: legion | cekwajar | rumahlabuh | academic | general | [multiple]
sources: [list of raw/ paths that this article is compiled from]
related: [[Article1]], [[Article2]], [[Article3]]
confidence: high | medium | low | disputed
last_compiled: YYYY-MM-DD
status: current | outdated | stub | deprecated | disputed
tags: [tag1, tag2, tag3]
word_count: [auto-computed]
---

Rules:
- title = singular noun/noun phrase ("Intent Router", not "How Intent Router Works")
- type = one of the 7 listed types above, no others
- project = which project(s) this knowledge applies to
- sources = at minimum 1 entry; "general knowledge" is not valid
- related = minimum 2 [[wikilinks]], maximum 10
- confidence:
    high     = ≥2 sources agree, recently compiled, no contradictions
    medium   = single source OR compiled >30 days ago
    low      = speculative, inferred, or unverified
    disputed = contradicted by another article (must cite both)
- status:
    current    = source files unchanged since last_compiled
    outdated   = source file modified after last_compiled date
    stub       = article exists but <150 words (needs enrichment)
    deprecated = concept no longer applies to active work
- word_count: computed after writing, enforced at 150–800 words
  Exception: architecture/ articles may go up to 1200 words
  Exception: project/ articles may go up to 1500 words

---

## ARTICLE BODY STRUCTURE

Every article must follow this structure:

## [Title]
[2-3 sentence definition. What this is, in plain language.]

## Context
[Why this matters. Where it appears. What problem it solves.]

## Key Properties
[Bullet list of the most important facts, numbers, constraints.]

## How It Works
[Mechanism, algorithm, flow, or process. Concrete, not vague.]

## Relationships
[How this connects to other concepts. NOT a duplicate of [[wikilinks]].]
[Write prose connections: "This is a dependency of [[X]] and a
prerequisite for [[Y]]. It conflicts with [[Z]] under conditions A, B.]

## Current Status
[What state is this in RIGHT NOW. Is it implemented? Planned? Broken?
For code concepts: note the actual file and line number if known.]

## See Also
[[Link1]] | [[Link2]] | [[Link3]] | [[Link4]]

---

## DIRECTORY RULES

wiki/concepts/       → Abstract ideas, methods, algorithms, patterns, frameworks
                       Examples: bayesian-smoothing.md, intent-routing.md,
                                 karpathy-kb-pattern.md, multi-task-learning.md

wiki/entities/       → Specific named things: tools, models, APIs, products, services
                       Examples: minimax-m2-7.md, openrouter.md, supabase.md,
                                 gpt-researcher.md, dify.md, obsidian.md

wiki/projects/       → One page per active project (see Project Article rules below)
                       Examples: legion-bot.md, cekwajar-id.md, rumahlabuh-com.md

wiki/decisions/      → Architectural and strategic decisions with full rationale
                       Naming: YYYY-MM-DD-[short-slug].md
                       Example: 2026-04-12-chose-opencode-over-cursor.md

wiki/timelines/      → Chronological event logs per topic
                       Examples: legion-version-history.md, cekwajar-phase-log.md

wiki/architecture/   → System design, data flows, module maps, dependency graphs
                       Examples: legion-module-map.md, memory-architecture.md,
                                 skill-registry-flow.md

wiki/people/         → Key people who influence the work
                       Examples: andrej-karpathy.md, relevant-researchers.md

---

## PROJECT ARTICLE RULES (wiki/projects/*.md)

Project articles have an extended structure:

---
title: [Project Name]
type: project
status_phase: [current phase or milestone]
kill_criteria: [list of conditions that would end/pivot this project]
gate_conditions: [what must be true before next phase]
tools: [[Tool1]], [[Tool2]]
depends_on: [[Concept1]], [[Concept2]]
---

## Overview
[What this project is and what problem it solves]

## Current Phase
[Exact current status, what's done, what's next]

## Architecture
[High-level technical design, key files, key modules]

## Key Decisions
[Link to wiki/decisions/ articles]

## Kill Criteria
[Copy verbatim from planning docs. Non-negotiable.]

## Phase Gates
[What must be true before proceeding to next phase]

## Open Questions
[Unresolved technical or strategic questions]

## See Also
[[links]]

---

## DECISION ARTICLE RULES (wiki/decisions/YYYY-MM-DD-slug.md)

---
title: [Decision: short description]
type: decision
date: YYYY-MM-DD
status: active | superseded | reversed
superseded_by: [[new-decision]] (if applicable)
affects: [[Project1]], [[Concept1]]
---

## Decision
[One sentence: what was decided]

## Context
[What situation forced this decision. What was unclear or at risk.]

## Options Considered
1. [Option A] — pros/cons
2. [Option B] — pros/cons
3. [Option C] — pros/cons

## Rationale
[Why the chosen option. Be honest about tradeoffs.]

## Consequences
[What this decision makes easier. What it makes harder.]

## Review Date
[When to revisit: YYYY-MM-DD or "when X condition is met"]

---

## NAMING CONVENTIONS

Files:       lowercase-hyphenated.md
             (bayesian-smoothing.md, NOT BayesianSmoothing.md)
Titles:      Title Case noun phrases
Tags:        lowercase, singular (algorithm, not algorithms)
Decisions:   YYYY-MM-DD-short-slug.md
Timelines:   topic-name-history.md or topic-name-log.md
Max depth:   wiki/[directory]/filename.md — NEVER nest deeper than 2 levels

---

## 5 OPERATIONS

### OPERATION 1: INGEST
Trigger: new/modified files appear anywhere in the repo
Steps:
  1. Read SCHEMA.md
  2. Scan ALL directories for files newer than _meta/compile_state.json
  3. Identify all concepts, entities, projects, decisions in new content
  4. For each identified item:
     a. If wiki/ article exists → update it, add new source to frontmatter
     b. If no article exists → create new article following SCHEMA rules
  5. Update [[wikilinks]] in related articles
  6. Rebuild wiki/INDEX.md (see INDEX rules below)
  7. Update _meta/compile_state.json with ISO timestamp

### OPERATION 2: COMPILE (full rebuild)
Trigger: run when starting from scratch OR after major structural changes
Steps:
  1. Read SCHEMA.md
  2. Move all source material to raw/ subdirectories per PHASE 1 structure
  3. Read ALL files in raw/ regardless of timestamp
  4. Extract: all concepts, entities, projects, decisions, timelines
  5. Build complete wiki/ from scratch
  6. Verify: every article has valid frontmatter
  7. Verify: every [[wikilink]] resolves to an existing file
  8. Build wiki/INDEX.md
  9. Write _meta/compile_state.json with current timestamp and article count

### OPERATION 3: QUERY
Trigger: user asks a question
Steps:
  1. Read SCHEMA.md
  2. Identify relevant articles in wiki/ by title + tag matching
  3. Read those articles + follow their [[wikilinks]] ONE level deep
  4. Synthesize answer ONLY from wiki/ content
  5. If insufficient info: state exactly what's missing + which raw/ files
     might contain the answer (suggest running INGEST on those files)
  6. Write answer to output/queries/YYYY-MM-DD-[slug].md for future reference

### OPERATION 4: LINT (weekly health check)
Trigger: run every Sunday or on demand
Steps:
  1. Read SCHEMA.md
  2. Check EVERY file in wiki/ for:
     a. Orphans: articles with 0 incoming [[wikilinks]] — flag
     b. Missing stubs: [[wikilinks]] pointing to non-existent articles — create stub
     c. Contradictions: two articles making incompatible claims — mark both disputed
     d. Stale: source file modified after article's last_compiled — mark outdated
     e. Empty stubs: articles <150 words — flag for enrichment
     f. Schema violations: missing frontmatter fields — fix or flag
     g. Oversized: articles >800 words (>1200 for architecture) — flag for split
     h. Missing sources: frontmatter sources field empty — flag
     i. Broken project refs: project field references non-existent project page — fix
  3. Output full report to output/health/lint_YYYY-MM-DD.md
  4. Summary line at top: "X orphans | X stubs | X contradictions | X stale |
     X violations | X oversized | X missing sources"
  5. Append summary line to _meta/lint_log.md

### OPERATION 5: MIGRATE (one-time restructure)
Trigger: THIS PROMPT — run once to restructure existing wiki
Steps:
  1. Complete PHASE 0 audit
  2. Create PHASE 1 directory structure
  3. Create wiki/SCHEMA.md (PHASE 2)
  4. Move all existing .md files to raw/ subdirectories per audit decisions
  5. Run OPERATION 2 (COMPILE) on the populated raw/
  6. Run OPERATION 4 (LINT) to verify output
  7. Report: X articles created, X stubs, X decisions logged, X raw files processed

---

## INDEX.md RULES

wiki/INDEX.md is the master table of contents. Auto-maintained.
Structure:

# Knowledge Base Index
Last compiled: [timestamp]
Total articles: [count]
Projects covered: [list]

## By Type
### Concepts ([count])
- [[concept-name]] — one-line description
...

### Entities ([count])
- [[entity-name]] — one-line description
...

### Projects ([count])
- [[project-name]] — status + current phase
...

### Decisions ([count]) — reverse chronological
- [[YYYY-MM-DD-slug]] — one-line summary
...

### Timelines ([count])
- [[timeline-name]] — date range
...

### Architecture ([count])
- [[architecture-name]] — system covered
...

## By Project
### Legion Bot
[list of all articles tagged project: legion]

### cekwajar.id
[list of all articles tagged project: cekwajar]

### rumahlabuh.com
[list of all articles tagged project: rumahlabuh]

### General / Multi-project
[list of articles not project-specific]

## Recently Updated (last 10)
[list of 10 most recently compiled articles]

## Stubs (needs enrichment)
[list of all status: stub articles]

---

## WHAT YOU NEVER DO

1. Edit raw/ files — they are immutable source of truth
2. Delete wiki/ articles — mark as deprecated instead, keep the file
3. Fabricate information not in raw/ sources — if you don't know, write a stub
4. Create an article without valid frontmatter — schema violation
5. Leave a [[wikilink]] pointing to a non-existent file — always create stub
6. Merge two articles into one without creating a redirect stub for the old title
7. Use nested folders beyond 2 levels (wiki/[dir]/file.md)
8. Write >800 words in a concepts/entities article
9. Mark status: current if the source file has been modified since last_compiled
10. Touch SOUL.md, CLAUDE.md, main.py, core/, handlers/ — these are not knowledge
    base content, they are live system files
```

---

## PHASE 3 — MIGRATE ALL EXISTING CONTENT

This is the core execution phase. Follow this exact migration map:

### Root-level .md files → raw/ targets

```
AGENTS.md                        → raw/docs/agents-overview.md
CHANGELOG.md                     → raw/changelogs/changelog.md
CLAUDE.md                        → raw/configs/claude-config.md
CLAUDE_DEEP_AUDIT_PROMPT.md      → raw/prompts/claude-deep-audit-prompt.md
CLEANUP_LOG.md                   → raw/changelogs/cleanup-log.md
CONCERNS_FIXED_REPORT.md         → raw/changelogs/concerns-fixed-report.md
CONTRIBUTING.md                  → raw/docs/contributing.md
DEEP_AUDIT_2026-04-12.md         → raw/audits/deep-audit-2026-04-12.md
DEPLOYMENT.md                    → raw/docs/deployment.md
IMPLEMENTATION_STATUS.md         → raw/docs/implementation-status.md
LEGION_CONCERNS_MASTER_PROMPT.md → raw/prompts/legion-concerns-master-prompt.md
LEGION_MASTER.md                 → raw/docs/legion-master.md
LEGION_PRODUCTION_HARDENING.md   → raw/prompts/legion-production-hardening.md
OPENCODE_DEPTH_UPGRADE_PROMPT.md → raw/prompts/opencode-depth-upgrade.md
OPENCODE_EXTERNAL_TOOLS_INTEGRATION.md → raw/prompts/opencode-external-tools.md
README.md                        → raw/docs/readme.md
SOUL.md                          → DO NOT MOVE (live system file)
SWARM_WIRING.md                  → raw/docs/swarm-wiring.md
TESTING.md                       → raw/docs/testing.md
WIRING_VERIFIED_2026-04-12.md    → raw/changelogs/wiring-verified-2026-04-12.md

IMPORTANT: Do NOT delete root-level files after copying to raw/.
           Root files stay where they are. raw/ gets COPIES.
           wiki/ gets COMPILED articles from raw/. 3-layer system.
```

### Directory content → raw/ targets

```
docs/           → raw/docs/        (copy all .md files)
papers/         → raw/papers/      (copy all files)
prompts/        → raw/prompts/     (copy all files)
skills/         → raw/skills_ref/  (copy all 28 .md files)
.opencode/      → raw/configs/opencode-config.md (extract key settings)
.claude/        → raw/configs/claude-config-dir.md (extract key settings)
.cursor/        → raw/configs/cursor-config.md (extract key settings)
data/           → raw/configs/data-snapshot.md (summary of data files)
config/         → raw/configs/config-snapshot.md (summary of config files)
_archive/       → raw/snapshots/archive-index.md (index only, don't copy archive content)
wiki/ (existing)→ Audit first. Well-structured articles → keep in wiki/.
                  Unstructured content → move to raw/docs/.
.wiki/ (hidden) → Audit first. Same rule as wiki/.
```

---

## PHASE 4 — COMPILE FROM raw/

After all files are in raw/, run OPERATION 2 (COMPILE).

### Minimum Required Wiki Articles to Create

These are non-negotiable. Every one of these must exist after compile:

**concepts/**
- intent-routing.md (from DEEP_AUDIT, LEGION_MASTER, main.py architecture)
- memory-architecture.md (8 subsystems, 4 facades, audit findings)
- reasoning-loop.md (the #1 missing capability from audit)
- skill-registry.md (dual-layer skill system)
- multi-agent-orchestration.md (4 orchestrators, LEGION_TEAM hardcode)
- self-improvement-loop.md (dead code issue from audit)
- karpathy-kb-pattern.md (this very system we're building)
- bayesian-blending.md (salary benchmark engine concept)
- freemium-gate.md (conversion mechanics concept)
- llm-cost-routing.md (model selection by complexity)
- vector-search.md (semantic vs FTS retrieval)
- context-window-budget.md (1500 token bloat problem)

**entities/**
- minimax-m2-7.md (100 TPS, 56% SWE-Pro, $0.30/$1.20 pricing)
- openrouter.md (model gateway, already in requirements.txt)
- supabase.md (backend, AP-SE1 region requirement for UU PDP)
- gpt-researcher.md (26k stars, MCP bridge, research replacement)
- dify.md (137k stars, self-hosted, Claude Max replacement)
- markitdown.md (Microsoft, doc → markdown conversion)
- opencode.md (terminal TUI, M2.7 native, MCP support)
- cursor.md (VS Code GUI, frontend use cases)
- obsidian.md (wiki viewer, Karpathy pattern)
- litellm.md (model abstraction layer in requirements.txt)
- chromadb.md (vector store, in requirements.txt)

**projects/**
- legion-bot.md (full project page, all phases, kill criteria)
- cekwajar-id.md (5 tools, phases 0-6, kill criteria)
- rumahlabuh-com.md (property rental platform)

**decisions/**
- 2026-04-12-opencode-over-cursor-for-backend.md
- 2026-04-12-gpt-researcher-for-deep-research.md
- 2026-04-12-dify-for-doc-analysis.md
- 2026-04-12-database-first-build-order.md
- 2026-04-13-karpathy-pattern-for-obsidian.md

**architecture/**
- legion-module-map.md (90 modules, key file relationships)
- memory-system-architecture.md (8 subsystems diagram in text)
- skill-execution-flow.md (intent → skill → result → memory)
- orchestrator-comparison.md (4 orchestrators, which does what)
- cekwajar-tech-stack.md (Next.js, Supabase, Midtrans, OCR pipeline)

**timelines/**
- legion-version-history.md (compiled from CHANGELOG.md)
- cekwajar-phase-log.md (Phase 0 → Phase 6 with dates and gates)

**people/**
- andrej-karpathy.md (researcher, LLM KB pattern source)

---

## PHASE 5 — WIRE OBSIDIAN

After wiki/ is fully compiled, make it Obsidian-ready:

### Obsidian Vault Setup

1. Open wiki/ as a new Obsidian vault (separate from any personal vault)
2. Install these plugins (list in wiki/_meta/obsidian-plugins.md):
   - **Dataview** — query frontmatter (e.g., all status:stub articles)
   - **Graph View** — visualize [[wikilink]] network
   - **Obsidian Web Clipper** — clip web articles → raw/articles/ (new subfolder)
   - **Templater** — enforce SCHEMA.md article templates on new files
   - **Calendar** — link daily notes to decisions/timelines

3. Create wiki/_meta/obsidian-plugins.md with install instructions

### Dataview Queries to Add to INDEX.md

Add these Dataview code blocks to wiki/INDEX.md:

```dataview
TABLE status, project, last_compiled
FROM "concepts"
WHERE status = "stub"
SORT last_compiled ASC
```

```dataview
TABLE status, last_compiled, confidence
FROM ""
WHERE status = "outdated"
SORT last_compiled ASC
```

```dataview
TABLE project, status
FROM "projects"
SORT title ASC
```

### Graph View Configuration

Create wiki/_meta/graph-config.json:
{
  "colorGroups": [
    {"query": "type:project",      "color": {"a":1,"rgb":16711680}},
    {"query": "type:concept",      "color": {"a":1,"rgb":255}},
    {"query": "type:entity",       "color": {"a":1,"rgb":65280}},
    {"query": "type:decision",     "color": {"a":1,"rgb":16776960}},
    {"query": "type:architecture", "color": {"a":1,"rgb":16711935}},
    {"query": "status:stub",       "color": {"a":1,"rgb":8421504}}
  ]
}

---

## PHASE 6 — VERIFICATION

Run these checks after all phases complete:

### Check 1: Schema Compliance
```bash
# Every wiki article (not INDEX or SCHEMA) has required frontmatter
grep -rL "^title:" wiki/concepts wiki/entities wiki/projects wiki/decisions wiki/timelines wiki/architecture wiki/people
# Expected output: empty (no files missing title)
```

### Check 2: Wikilink Integrity
```bash
# Every [[wikilink]] in wiki/ resolves to an existing file
# Write and run: python scripts/check_wikilinks.py wiki/
# Expected: 0 broken links
```

### Check 3: Article Count
- wiki/concepts/: minimum 12 articles
- wiki/entities/: minimum 11 articles
- wiki/projects/: minimum 3 articles
- wiki/decisions/: minimum 5 articles
- wiki/architecture/: minimum 5 articles
- wiki/timelines/: minimum 2 articles
- wiki/people/: minimum 1 article
- wiki/INDEX.md: exists and lists all articles
- wiki/SCHEMA.md: exists and matches this spec
- wiki/_meta/compile_state.json: exists with valid ISO timestamp

### Check 4: Run LINT
Run OPERATION 4. Report must show:
- 0 schema violations
- 0 broken wikilinks
- 0 articles without sources
- Stubs OK (expected — we'll enrich over time)

### Final Report

Write wiki/_meta/migration_report_YYYY-MM-DD.md with:
- Total raw/ files processed
- Total wiki/ articles created
- Total decisions logged
- Total stubs (to be enriched)
- Total [[wikilinks]] created
- Any files that could NOT be processed and why
- Estimated enrichment time for all stubs

---

## ONGOING OPERATIONS (post-migration)

### When You Add Any New File to This Repo

Run in OpenCode terminal from repo root:
```
INGEST: Read wiki/SCHEMA.md. Run OPERATION 1 (INGEST) on files
newer than wiki/_meta/compile_state.json timestamp. Report summary.
```

### When You Want to Ask a Complex Question

Run in OpenCode terminal:
```
QUERY: Read wiki/SCHEMA.md. Run OPERATION 3 (QUERY).
Question: [your question here]
```

### Every Sunday

Run in OpenCode terminal:
```
LINT: Read wiki/SCHEMA.md. Run OPERATION 4 (LINT).
Output to output/health/lint_[today].md
```

### When You Start a New Project

1. Create raw/roadmaps/[project-name]-roadmap.md with your planning
2. Run INGEST
3. OpenCode creates wiki/projects/[project-name].md automatically
4. All related concepts are linked automatically

---

## EXECUTION ORDER FOR THIS SESSION

OpenCode: execute the phases in this exact order.
Do NOT skip phases. Do NOT start Phase N+1 before Phase N is verified.

```
[ ] PHASE 0 — Audit all directories → write audit_report to wiki/_meta/
[ ] PHASE 1 — Create directory structure → verify all folders exist
[ ] PHASE 2 — Create wiki/SCHEMA.md → verify against this spec
[ ] PHASE 3 — Copy source files to raw/ → verify all targets populated
[ ] PHASE 4 — Run OPERATION 2 (COMPILE) → minimum article counts met
[ ] PHASE 5 — Wire Obsidian config → plugins list + graph config created
[ ] PHASE 6 — Verification → all 4 checks pass
[ ] Write wiki/_meta/migration_report_YYYY-MM-DD.md
[ ] Commit everything: git add wiki/ && git commit -m "feat: Karpathy KB pattern — full wiki restructure"
```

---

## HARD RULES (READ BEFORE TOUCHING ANYTHING)

1. SOUL.md, CLAUDE.md, main.py, core/, handlers/ → NEVER TOUCH
2. Raw files are COPIED to raw/, not moved. Originals stay in place.
3. Every article must have valid frontmatter or it does not get created
4. Never fabricate content not in source files. Write stubs instead.
5. If two source files contradict each other:
   - Mark both relevant wiki articles as confidence: disputed
   - Create a decision article documenting the contradiction
   - Do NOT silently pick one as truth
6. The word_count limit (800 / 1200 / 1500) is a hard cap, not a target
7. All timestamps in ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
8. Git commit after each phase with descriptive commit message
9. If any phase fails: stop, write a failure report to _meta/, ask for guidance
10. This prompt itself must be compiled into wiki/concepts/karpathy-kb-pattern.md
    after Phase 4. The meta-loop is intentional.
```
