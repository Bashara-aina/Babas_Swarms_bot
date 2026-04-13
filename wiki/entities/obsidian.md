---
title: obsidian
type: entity
status: active
tags: [notes, knowledge-base, markdown, vim]
created: 2026-04-13
updated: 2026-04-13
summary: Obsidian is the knowledge base platform for Legion's wiki, structured following the Karpathy KB pattern with Dataview queries.
wikilinks:
  - [[karpathy-kb-pattern]]
  - [[SCHEMA]]
confidence: high
source: implementation
---

# Obsidian

## TL;DR
Obsidian is the markdown-based note-taking app serving as Legion's wiki, configured with Dataview for automated indexing and backlinks for cross-referencing.

## Plugins Installed

| Plugin | Purpose |
|--------|---------|
| dataview | Query wiki pages via inline queries |
| backlinks | Show incoming links to each page |
| obsidian-git | Auto-backup to git |
| metadata extractor | Auto-frontmatter |

## Wiki Structure

Following Karpathy KB Pattern:
- `wiki/concepts/` — 12+ concept pages
- `wiki/entities/` — 11+ entity pages
- `wiki/projects/` — Project documentation
- `wiki/decisions/` — ADR collection
- `wiki/architecture/` — System docs

## Dataview Example

```dataview
TABLE title, status, tags
FROM "wiki/concepts"
WHERE status = "active"
SORT updated DESC
```

## Vault Structure

The vault root is `~/swarm-bot/wiki/`. Obsidian resolves all paths relative to this root:
- Dataview queries use `FROM "concepts"` (not `FROM "wiki/concepts"`)
- Wikilinks use relative paths without `.md` extension: `[[entities/litellm]]`
- Attachments stored in `raw/assets/` (not inline in articles)

## Plugin Configuration

Required plugins are configured in `wiki/.obsidian/`:
- `community-plugins.json`: `["dataview","obsidian-git","metadata-extractor","obsidian-advanced-tables"]`
- `graph.json`: Color groups per directory type
- `dataview/data.json`: Refresh interval 2500ms, inline query enabled

## Related Pages

- [[SCHEMA]] — Schema definition and frontmatter requirements
- [[karpathy-kb-pattern]] — Pattern reference for wiki article structure
