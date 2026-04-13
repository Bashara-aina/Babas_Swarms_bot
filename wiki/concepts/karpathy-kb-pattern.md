---
title: karpathy-kb-pattern
type: concept
status: active
tags: [wiki, knowledge-base, pattern, karpathy, schema, structure]
created: 2026-04-13
updated: 2026-04-13
summary: The Karpathy KB Pattern is a wiki structure methodology where every page is written for a smart AI reading it later — frontmatter metadata, TL;DR first, structured sections, and wikilinks throughout. It is the foundation of Legion's wiki organization.
wikilinks:
  - [[SCHEMA|schema]]
  - [[concepts/memory-architecture|memory-architecture]]
  - [[concepts/intent-routing|intent-routing]]
  - [[concepts/self-improvement-loop|self-improvement-loop]]
confidence: high
source: design
---

# Karpathy KB Pattern

## TL;DR
The Karpathy Knowledge Base Pattern is a wiki writing methodology where every article is structured for optimal AI comprehension: YAML frontmatter for machine indexing, a 2-3 sentence TL;DR first so the AI immediately knows what the page is about, structured body sections, and wikilinks to related concepts so the AI can navigate context. Pages are synthesized knowledge, not raw dumps.

## Overview

The pattern is named after Andrej Karpathy's practice of maintaining project wikis that a language model can read and understand without prior context. The key insight is that wiki pages are not for humans alone — they are training data and context for future AI reasoning. A page written for an AI needs different structural discipline than one written for a human who can ask clarifying questions.

## Context

Legion's wiki is its long-term memory system. When the bot restarts or encounters a new task, the wiki is the primary knowledge source beyond conversation context. The Karpathy KB Pattern ensures that:
1. Every page can be indexed by Dataview for automated queries
2. Every page has a machine-readable summary for quick relevance scoring
3. Every page links to related concepts so the AI can traverse context
4. The wiki is self-documenting and self-referencing, reducing孤岛 (isolation) between concepts

## Key Properties

- **TL;DR first**: 2-3 sentence summary before any detail — AI reads this to decide if the page is relevant
- **Valid frontmatter**: Obsidian-compatible YAML with title, type, status, tags, created, updated, summary, wikilinks, confidence, source
- **Wikilinks throughout**: Bracket syntax `[[page]]` for cross-references, not bare URLs
- **Synthesized content**: No raw conversation logs, no todo lists — distilled understanding
- **Dataview-compatible**: Pages are queryable via Dataview for automated indexing
- **Source attribution**: Every page notes where the information came from (implementation, design, external, conversation)
- **Schema enforcement**: The [[SCHEMA]] defines exact frontmatter and structure requirements
- **Quality checklist**: Every page should pass the Page Quality Checklist in SCHEMA.md

## Page Structure

```
---
title: Page Name
type: concept | entity | project | decision | architecture
status: active | completed | deprecated | legacy
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
summary: 2-3 sentence TL;DR
wikilinks: []
confidence: high | medium | low
source: implementation | design | external | conversation
---

# Page Title

## TL;DR
[Repeat TL;DR here — same as frontmatter summary]

## Overview
[What this is and why it matters]

## Context
[Why this matters in this specific project]

## Key Properties
[Bulet list of important facts]

## How It Works
[Mechanism, algorithm, or flow]

## Relationships
[Prose connections to other articles — not just links]

## Current Status
[Implemented? Planned? Broken?]

## See Also
- [[memory-architecture]]
- [[intent-routing]]
```

## Schema Requirements

Per [[SCHEMA]], every page MUST have:
- `title`: Page title
- `type`: One of concept, entity, project, decision, architecture, timeline, person, skill, reference
- `status`: active, completed, deprecated, legacy
- `tags`: Array of tags
- `created`: YYYY-MM-DD
- `updated`: YYYY-MM-DD
- `summary`: 2-3 sentence TL;DR
- `wikilinks`: Array of bracket-link references
- `confidence`: high, medium, low
- `source`: implementation, design, external, conversation

## Dataview Query Examples

```dataview
TABLE title, status, summary
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

## Relationships

The Karpathy KB Pattern is the structural foundation that makes [[memory-architecture]] traversable — without wikilinks, the AI wouldn't know how concepts relate. [[intent-routing]] benefits from the pattern when the intent classifier retrieves wiki context: structured pages with clear summaries are much faster to scan than unstructured notes. [[self-improvement-loop]] writes its learned outcomes to the wiki in this format, ensuring future reasoning loops can retrieve past learnings efficiently.

## Current Status

**Active and enforced.** All new wiki pages must follow this pattern. The schema is defined in [[SCHEMA]]. Obsidian plugins (dataview, backlinks) are configured to work with this structure. Wiki health checks in `.wiki/logs/` verify pages meet the quality checklist.

## See Also

- [[SCHEMA]] — Full schema definition with page type definitions
- [[memory-architecture]] — Memory system using wiki structure
- [[intent-routing]] — Intent routing that retrieves wiki context
