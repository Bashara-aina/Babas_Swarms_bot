---
title: Fix KB Duplicate Link and Obsidian Broken Links
type: decision
status: resolved
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
- obsidian
- mcp
created: '2026-04-14'
updated: '2026-05-16'
summary: 'Two issues fixed in the wiki knowledge base: (1) duplicate memory-architecture.md files resolved, (2) obsidian broken_links tool path bug fixed.'
wikilinks: []
confidence: high
source: research
---
# ADR-006: Fix KB Duplicate memory-architecture.md and Obsidian broken_links Tool

**Date**: 2026-04-13 (original), **Updated**: 2026-05-16 (merged)
**Status**: Resolved

## Context

Two issues were identified in the wiki knowledge base and Obsidian MCP server:

1. **Duplicate `memory-architecture.md` files** in `wiki/architecture/` and `wiki/concepts/` (2026-04-13)
2. **Obsidian `broken_links` tool path-resolution bug** — flags valid `[[subdir/file]]` links as broken (2026-05-16)

---

## Issue 1: Duplicate memory-architecture.md (Resolved 2026-04-13)

### Problem
Duplicate `memory-architecture.md` files in `wiki/architecture/` and `wiki/concepts/`, plus malformed wikilink in `wiki/projects/legion-bot.md` line 9.

### Resolution
- `wiki/architecture/memory-architecture.md` renamed → `wiki/architecture/memory-gaps-analysis.md`
- Malformed wikilink `[[entities/opencode.md],` fixed to proper `[[entities/opencode.md]]`
- Only `wiki/concepts/memory-architecture.md` remains

### See Also
- [[concepts/memory-architecture]]
- [[architecture/memory-gaps-analysis]]

---

## Issue 2: Obsidian broken_links Path Bug (Resolved 2026-05-16)

### Problem
The `broken_links` tool in `mcp_servers/obsidian-patched/index.js` (line ~3269) flags valid `[[subdir/file]]` wikilinks as broken. The check `noteNames.has(linkName)` only matches filenames directly in the vault root — it does not handle:
- Subdirectory paths like `[[architecture/memory-architecture]]`
- Aliases like `[[architecture/memory-architecture|alias]]`
- Backslash path separators on Windows (`\`)

### Root Cause
```javascript
// BEFORE — only matches root-level note names
const linkName = link.slice(2, -2).split('|')[0].trim();
if (!noteNames.has(linkName)) { brokenLinks.push(...) }
```

### Resolution
`mcp_servers/obsidian-patched/index.js` line ~3269 updated to:
```javascript
const linkName = link.slice(2, -2).split('|')[0].trim().replace(/\\/g, '/');
const normalizedLinkName = linkName.replace(/\//g, path.sep);
if (!noteNames.has(linkName) && !noteNames.has(normalizedLinkName)) {
  const pathParts = linkName.split('/');
  const fileExists = pathParts.some((_, i) => {
    const subPath = pathParts.slice(i).join(path.sep);
    return noteNames.has(subPath);
  });
  if (!fileExists) {
    brokenLinks.push({ in_file: file, broken_link: linkName, full_syntax: link });
  }
}
```

This handles:
1. Subdirectory paths — checks if any suffix of the path exists as a note
2. Backslash normalization — converts `\` to `/` for cross-platform
3. Alias aliases — strips `|alias` suffix before checking

### File Changed
- `mcp_servers/obsidian-patched/index.js` (line ~3269)

---

## Consequences

- `[[architecture/memory-architecture]]` and similar subdirectory links are now correctly recognized as valid
- Alias wikilinks like `[[some/path|Display Text]]` no longer falsely reported as broken
- The `broken_links` tool now accurately identifies truly broken links

## See Also

- [[concepts/memory-architecture]]
- [[architecture/memory-gaps-analysis]]
- [[mcp-servers/obsidian-patched/index.js|obsidian-patched MCP server]]