---
title: karpathy-kb-pattern
type: concept
status: active
tags: [wiki, knowledge-base, pattern, karpathy]
created: 2026-04-13
updated: 2026-04-13
summary: The Karpathy KB Pattern is a wiki structure optimized for AI reading - every page has frontmatter, TL;DR summaries, and wikilinks to related content.
wikilinks: [[wiki/SCHEMA.md]], [[concepts/memory-architecture.md]]
confidence: high
source: design
---

# Karpathy KB Pattern

## TL;DR
The Karpathy Knowledge Base Pattern structures wiki pages for optimal AI comprehension: frontmatter metadata, TL;DR first, structured body, wikilinks throughout.

## Core Principles

1. **AI-first**: Every page readable by a smart AI with no prior context
2. **Frontmatter**: YAML metadata for Dataview queries
3. **TL;DR first**: 2-3 sentence summary before any detail
4. **Wikilinks**: Cross-reference everything with `[[page.md]]`
5. **Structured sections**: Consistent `## Headers` hierarchy

## Page Template

```yaml
---
title: Page Name
type: concept | entity | project | decision | architecture
status: active
tags: [tag1, tag2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
summary: 2-3 sentence TL;DR
wikilinks: [[related.md]], [[another.md]]
confidence: high | medium | low
source: implementation | design | external
---

# Page Title

## TL;DR
[Repeat TL;DR here]

## Section 1
[Content]

## Related
- [[related-concept.md]]
- [[another-concept.md]]
```

## Dataview Integration

Pages are queryable:
```dataview
TABLE title, status, summary
FROM "wiki/concepts"
WHERE status = "active"
SORT updated DESC
```

## Related Pages

- [[wiki/SCHEMA.md]] — Full schema definition
