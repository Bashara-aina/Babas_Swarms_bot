---
title: Legion Wiki Index
type: index
status: active
tags: [wiki, index, dataview]
created: 2026-04-13
updated: 2026-04-13
summary: Main index for Legion's wiki, queryable via Dataview.
---

# Legion Wiki Index

> Last updated: 2026-04-13 by WikiBot
> See [SCHEMA.md](SCHEMA.md) for page writing rules.

---

## Quick Stats

```dataview
TABLE length(file.ctags) as Tags, length(file.outlinks) as Links
WHERE file.folder = "wiki"
GROUP BY file.folder
```

**Total pages**: 45+  
**Concepts**: 12+ | **Entities**: 11+ | **Projects**: 3+ | **Decisions**: 5+

---

## Concepts (Knowledge)

```dataview
TABLE title, status, summary
FROM "wiki/concepts"
WHERE status = "active"
SORT title ASC
```

### Concept Map
- [[concepts/intent-routing.md]] — Message classification
- [[concepts/memory-architecture.md]] — Memory layers
- [[concepts/reasoning-loop.md]] — Step-by-step reasoning
- [[concepts/skill-registry.md]] — Capability catalog
- [[concepts/multi-agent-orchestration.md]] — Agent coordination
- [[concepts/self-improvement-loop.md]] — Learning from experience
- [[concepts/karpathy-kb-pattern.md]] — Wiki structure pattern
- [[concepts/bayesian-blending.md]] — Model selection
- [[concepts/freemium-gate.md]] — Access control
- [[concepts/llm-cost-routing.md]] — Cost optimization
- [[concepts/vector-search.md]] — Semantic search
- [[concepts/context-window-budget.md]] — Token management

---

## Entities (External Services & Tools)

```dataview
TABLE title, status, summary
FROM "wiki/entities"
WHERE status = "active"
SORT title ASC
```

### Entity Map
- [[entities/minimax-m2-7.md]] — Primary vision model
- [[entities/openrouter.md]] — LLM gateway
- [[entities/supabase.md]] — Database
- [[entities/litellm.md]] — LLM client
- [[entities/chromadb.md]] — Vector DB
- [[entities/opencode.md]] — Code agent
- [[entities/cursor.md]] — IDE (deprecated)
- [[entities/obsidian.md]] — Wiki platform
- [[entities/gpt-researcher.md]] — Research agent
- [[entities/dify.md]] — Workflow platform
- [[entities/markitdown.md]] — Document converter

---

## Projects

```dataview
TABLE title, status, summary
FROM "wiki/projects"
WHERE status = "active"
SORT title ASC
```

### Project Map
- [[projects/legion-bot.md]] — Telegram AI bot
- [[projects/cekwajar-id.md]] — Salary fairness tool
- [[projects/rumahlabuh-com.md]] — Property rental platform

---

## Decisions (ADR)

```dataview
TABLE title, date(created) as Created
FROM "wiki/decisions"
SORT created DESC
LIMIT 10
```

### Decision Map
- [[decisions/adr-2026-04-12-opencode-over-cursor-for-backend.md]] — OpenCode selected
- [[decisions/adr-2026-04-11-opencode-integration.md]] — Initial integration
- [[decisions/adr-2026-04-12-legion-wiki-loop.md]] — Wiki strategy
- [[decisions/adr-2026-04-12-circuit-breaker.md]] — Resilience pattern
- [[decisions/adr-2026-04-12-multi-agent-pipeline.md]] — Three-agent pipeline

---

## Architecture

```dataview
TABLE title, status, summary
FROM "wiki/architecture"
WHERE status = "active"
SORT title ASC
```

### Architecture Map
- [[architecture/legion-module-map.md]] — Core modules
- [[architecture/memory-system-architecture.md]] — Memory system
- [[architecture/skill-execution-flow.md]] — Skill execution
- [[architecture/orchestrator-comparison.md]] — Orchestration patterns
- [[architecture/cekwajar-tech-stack.md]] — Cekwajar stack

---

## Timelines

```dataview
TABLE title, status
FROM "wiki/timelines"
WHERE status = "active"
SORT title ASC
```

### Timeline Map
- [[timelines/legion-version-history.md]] — Legion releases
- [[timelines/cekwajar-phase-log.md]] — Cekwajar phases

---

## People

```dataview
TABLE title, status, summary
FROM "wiki/people"
WHERE status = "active"
SORT title ASC
```

### People Map
- [[people/andrej-karpathy.md]] — AI researcher (pattern inspiration)

---

## Raw Source Files

```dataview
TABLE title, file.folder as Folder
FROM "wiki/raw"
SORT file.folder ASC, title ASC
```

### Raw Structure
- [[wiki/raw/docs/]] — Documentation
- [[wiki/raw/skills_ref/]] — Skills documentation
- [[wiki/raw/decisions/]] — Decision archives
- [[wiki/raw/audits/]] — Audit reports

---

## Wiki Health

```dataview
TABLE title, status, date(updated) as Updated
WHERE status = "active"
SORT updated DESC
LIMIT 5
```

---

## Related

- [[wiki/SCHEMA.md]] — Schema definition
- [[wiki/_meta/obsidian-plugins.md]] — Plugin setup
- [[wiki/_meta/graph-config.json]] — Graph colors
- [[wiki/_meta/audit_report_2026-04-13.md]] — Migration audit
