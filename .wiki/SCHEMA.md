---
# Legion Wiki Schema v2.0 — Karpathy LLM KB Pattern

> The wiki is Legion's long-term memory. Every page is written for a smart AI reading it later.

---

## Core Philosophy

The wiki follows the **Karpathy LLM Knowledge Base Pattern**:
1. Every page has a **TL;DR summary** first (2-3 sentences)
2. Every page has **valid frontmatter** (Obsidian-compatible YAML)
3. Every page has **wikilinks** to related concepts, entities, and architecture
4. Pages are **synthesized**, not raw dumps — no conversation logs, no todo lists
5. The wiki is **queriable** via Dataview for automated indexing

---

## Frontmatter Schema

Every wiki page MUST have this frontmatter:

```yaml
---
title: Page Title
type: concept | entity | project | decision | architecture | timeline | person | skill | reference
status: active | completed | deprecated | legacy
tags: [tag1, tag2, tag3]
created: 2026-04-13
updated: 2026-04-13
summary: 2-3 sentence TL;DR for Dataview indexing
wikilinks:
  - [[karpathy-kb-pattern]]
  - [[INDEX]]
confidence: high | medium | low
source: conversation | research | implementation | external
---
```

---

## Directory Structure

```
wiki/
├── raw/                    # Source files organized by origin
│   ├── audits/            # Audit reports
│   ├── roadmaps/          # Roadmap documents
│   ├── prompts/           # Prompt engineering docs
│   ├── changelogs/        # Version history and fixes
│   ├── configs/           # Configuration references
│   ├── papers/            # Research papers
│   ├── skills_ref/        # Skills documentation
│   ├── docs/              # General documentation
│   └── snapshots/         # Point-in-time captures
├── concepts/               # Knowledge concepts (12+ required)
│   ├── intent-routing.md
│   ├── memory-architecture.md
│   ├── reasoning-loop.md
│   ├── skill-registry.md
│   ├── multi-agent-orchestration.md
│   ├── self-improvement-loop.md
│   ├── karpathy-kb-pattern.md
│   ├── bayesian-blending.md
│   ├── freemium-gate.md
│   ├── llm-cost-routing.md
│   ├── vector-search.md
│   └── context-window-budget.md
├── entities/               # External entities (11+ required)
│   ├── minimax-m2-7.md
│   ├── openrouter.md
│   ├── supabase.md
│   ├── gpt-researcher.md
│   ├── dify.md
│   ├── markitdown.md
│   ├── opencode.md
│   ├── cursor.md
│   ├── obsidian.md
│   ├── litellm.md
│   └── chromadb.md
├── projects/               # Active projects (3+ required)
│   ├── legion-bot.md
│   ├── cekwajar-id.md
│   └── rumahlabuh-com.md
├── decisions/              # Architecture Decision Records (5+ required)
│   └── adr-2026-04-12-opencode-over-cursor-for-backend.md
├── architecture/           # System architecture (5+ required)
│   ├── legion-module-map.md
│   ├── memory-system-architecture.md
│   ├── skill-execution-flow.md
│   ├── orchestrator-comparison.md
│   └── cekwajar-tech-stack.md
├── timelines/              # Version histories (2+ required)
│   ├── legion-version-history.md
│   └── cekwajar-phase-log.md
├── people/                 # People references (1+ required)
│   └── andrej-karpathy.md
├── output/                 # Generated/queried content
│   ├── queries/           # Dataview query results
│   └── health/            # System health reports
└── _meta/                  # Meta information
    ├── audit_report_2026-04-13.md
    ├── obsidian-plugins.md
    ├── graph-config.json
    └── migration_report_2026-04-13.md
```

---

## Page Type Definitions

### `concept` — Knowledge/Fact Pages
- Synthesized understanding of a topic
- TL;DR → Problem → Solution → Tradeoffs → Related
- Examples: "bayesian-blending", "intent-routing"

### `entity` — External Tool/Service Pages  
- What it is, how it works, how Legion uses it
- TL;DR → Overview → Integration → Alternatives → Related
- Examples: "supabase", "litellm", "openrouter"

### `project` — Project Documentation
- What the project is, tech stack, current status
- TL;DR → Goals → Tech Stack → Current Phase → Milestones → Related
- Examples: "cekwajar-id", "rumahlabuh-com"

### `decision` — Architecture Decision Records
- Context → Decision → Consequences → Alternatives Considered
- Must reference related decisions
- Format: `adr-YYYY-MM-DD-short-description.md`

### `architecture` — System Design Documents
- How a subsystem works
- TL;DR → Components → Data Flow → Failure Modes → Related
- Examples: "memory-system-architecture", "skill-execution-flow"

### `timeline` — Version/Event History
- Chronological progression
- TL;DR → Current Version → History → Upcoming → Related
- Examples: "legion-version-history"

### `person` — People Reference
- Who they are, relevance to projects
- TL;DR → Background → Contributions → Related
- Examples: "andrej-karpathy"

### `skill` — Skill Documentation
- How to execute a skill
- TL;DR → Triggers → Implementation → Examples → Related
- Examples: "rag-engineer", "prompt-engineer"

### `reference` — Raw/Reference Material
- Original documentation, minimal editing
- Source attribution required
- Examples: "indonesian-tax-2024"

---

## Wikilink Syntax

```markdown
# Basic link
[[memory-architecture]]

# Link to specific section  
[[memory-architecture#failure-modes]]

# Link with display text
[[supabase]]

# Link to entity
[[litellm]]

# Link to project
[[cekwajar-id]]
```

---

## Dataview Query Syntax (for INDEX.md)

```dataview
TABLE title, status, tags, summary
FROM "wiki/concepts"
WHERE status = "active"
SORT updated DESC
```

```dataview
TABLE title, type, status
FROM "wiki"
WHERE contains(tags, "legion")
SORT title ASC
```

---

## When to Create a New Page

1. A concept appears 3+ times across decisions/conversations
2. A new external entity (API/tool) is integrated
3. An architectural decision is made
4. A project phase completes
5. A significant bug is resolved and the fix is noteworthy

---

## When to UPDATE a Page

1. New information contradicts existing content → update + note change
2. Bashara corrects Legion → update immediately  
3. A project phase completes → update timeline
4. A decision is superseded → mark old decision deprecated, create new

---

## What NOT to Put in Wiki

- Raw conversation transcripts (use memory store)
- Temporary/one-off information
- Speculative information without `[uncertain]` tag
- Private credentials, API keys, tokens
- Pure draft ideas without any implementation reference

---

## Orphan Policy Exception

**ADRs (wiki/decisions/) are exempt from the orphan rule.**
Decision records are standalone documents by design. They record what was decided and why — they do not need to be cited elsewhere to be valid. The INDEX.md decisions section is their canonical entry point.

**ADRs are also exempt from word count minimums.**
A decision record is complete when it fully answers: what was decided, why, and what the consequences are. This can be 80 words or 800 words depending on complexity.

---

## Page Quality Checklist

- [ ] Has valid frontmatter with all required fields
- [ ] TL;DR summary is 2-3 sentences max
- [ ] Has at least one wikilink to related content
- [ ] No bare URLs (use footnotes or reference section)
- [ ] Uncertain claims marked with `[uncertain]`
- [ ] Source noted where applicable `[source: ...]`
- [ ] Internal cross-references use bracket link syntax

---

## Obsidian Plugin Requirements

- **Required**: dataview, backlinks
- **Recommended**: obsidian-git, metadata extractor
- **Optional**: pdf markdownify, mind map

---

## Graph Node Color Groups (graph-config.json)

```json
{
  "nodeColorGroups": [
    { "name": "concepts", "color": "#4a90d9" },
    { "name": "entities", "color": "#50c853" },
    { "name": "projects", "color": "#f44336" },
    { "name": "decisions", "color": "#ff9800" },
    { "name": "architecture", "color": "#9c27b0" },
    { "name": "people", "color": "#00bcd4" },
    { "name": "timelines", "color": "#795548" },
    { "name": "raw", "color": "#757575" }
  ]
}
```

---

## Migration Map (Phase 3)

| Source | Target |
|--------|--------|
| Root: LEGION_MASTER.md | wiki/raw/docs/legion-master.md |
| Root: LEGION_PRODUCTION_HARDENING.md | wiki/raw/docs/legion-production-hardening.md |
| Root: SWARM_WIRING.md | wiki/raw/docs/swarm-wiring.md |
| Root: IMPLEMENTATION_STATUS.md | wiki/raw/docs/implementation-status.md |
| wiki/legion/* | wiki/architecture/ |
| wiki/conversations/* | wiki/timelines/ |
| .wiki/decisions/ADR-*.md | wiki/decisions/ |
| .wiki/knowledge/tax/* | wiki/concepts/tax-indonesia/ |
| .wiki/knowledge/labor-law/* | wiki/concepts/labor-law-indonesia/ |
| .wiki/knowledge/market/* | wiki/concepts/market-data-indonesia/ |
| .wiki/knowledge/business/* | wiki/concepts/business-research/ |
| .wiki/knowledge/bpjs/* | wiki/concepts/bpjs-reference/ |
| skills/*.md | wiki/raw/skills_ref/ |
| docs/*.md | wiki/raw/docs/ |

---

**Last updated**: 2026-04-13  
**Schema version**: 2.0 (Karpathy KB Pattern)
