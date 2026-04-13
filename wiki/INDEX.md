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

- [[intent-routing]] — Message classification
- [[memory-architecture]] — Memory layers
- [[reasoning-loop]] — Step-by-step reasoning
- [[skill-registry]] — Capability catalog
- [[multi-agent-orchestration]] — Agent coordination
- [[self-improvement-loop]] — Learning from experience
- [[karpathy-kb-pattern]] — Wiki structure pattern
- [[bayesian-blending]] — Model selection
- [[freemium-gate]] — Access control
- [[llm-cost-routing]] — Cost optimization
- [[vector-search]] — Semantic search
- [[context-window-budget]] — Token management
- [[bpjs-reference]] — Indonesian social security (BPJS) reference data
- [[business-research]] — Business research methodology
- [[labor-law-indonesia]] — Indonesian labor law regulations
- [[market-data-indonesia]] — Indonesian market data sources
- [[tax-indonesia]] — Indonesian tax regulations

---

## Entities (External Services & Tools)

```dataview
TABLE title, status, summary
FROM "wiki/entities"
WHERE status = "active"
SORT title ASC
```

### Entity Map

- [[minimax-m2-7]] — Primary vision model
- [[openrouter]] — LLM gateway
- [[supabase]] — Database
- [[litellm]] — LLM client
- [[chromadb]] — Vector DB
- [[opencode]] — Code agent
- [[cursor]] — IDE (deprecated)
- [[obsidian]] — Wiki platform
- [[gpt-researcher]] — Research agent
- [[dify]] — Workflow platform
- [[markitdown]] — Document converter

---

## Projects

```dataview
TABLE title, status, summary
FROM "wiki/projects"
WHERE status = "active"
SORT title ASC
```

### Project Map

- [[legion-bot]] — Telegram AI bot
- [[cekwajar-id]] — Salary fairness tool
- [[rumahlabuh-com]] — Property rental platform

---

## Decisions (ADR)

```dataview
TABLE title, date(created) as Created
FROM "wiki/decisions"
SORT created DESC
LIMIT 10
```

### Decision Map

- [[adr-2026-04-12-opencode-over-cursor-for-backend]] — OpenCode selected
- [[adr-2026-04-11-opencode-integration]] — Initial integration
- [[adr-2026-04-12-legion-wiki-loop]] — Wiki strategy
- [[adr-2026-04-12-circuit-breaker]] — Resilience pattern
- [[adr-2026-04-12-multi-agent-pipeline]] — Three-agent pipeline

---

## Architecture

```dataview
TABLE title, status, summary
FROM "wiki/architecture"
WHERE status = "active"
SORT title ASC
```

### Architecture Map

- [[legion-module-map]] — Core modules
- [[memory-system-architecture]] — Memory system
- [[skill-execution-flow]] — Skill execution
- [[orchestrator-comparison]] — Orchestration patterns
- [[cekwajar-tech-stack]] — Cekwajar stack

---

## Timelines

```dataview
TABLE title, status
FROM "wiki/timelines"
WHERE status = "active"
SORT title ASC
```

### Timeline Map

- [[legion-version-history]] — Legion releases
- [[cekwajar-phase-log]] — Cekwajar phases

---

## People

```dataview
TABLE title, status, summary
FROM "wiki/people"
WHERE status = "active"
SORT title ASC
```

### People Map

- [[andrej-karpathy]] — AI researcher (pattern inspiration)

---

## Stubs (Status: Stub)

```dataview
TABLE title, status, summary
WHERE status = "stub"
SORT title ASC
```

---

## Raw Source Files

```dataview
TABLE title, file.folder as Folder
FROM "wiki/raw"
SORT file.folder ASC, title ASC
```

### Raw Structure

- [[raw/docs/readme]] — Documentation
- [[raw/skills_ref/AGENTS]] — Skills reference index
- [[raw/audits/deep-audit-2026-04-12]] — Latest audit

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

- [[SCHEMA]] — Schema definition
- [[_meta/obsidian-plugins]] — Plugin setup
- [[_meta/graph-config]] — Graph colors
- [[_meta/audit_report_2026-04-13]] — Migration audit