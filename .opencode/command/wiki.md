---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <topic>
description: "Generate or update wiki documentation. Saves to .wiki/. Usage: /wiki <topic>"
---

# /wiki — Wiki documentation

Generate or update wiki documentation in the .wiki/ directory.

## Steps

1. Parse the topic argument to determine wiki subdirectory and filename
2. Check if the wiki page already exists: `ls .wiki/<subdir>/`
3. If existing: read current content to understand what's already covered
4. Research the topic using available tools (grep, read, web search if needed)
5. Write new content to `.wiki/<subdir>/<topic>.md` with YAML frontmatter
6. Frontmatter must include: `title:`, `date:`, `tags:`, `created_by:` fields
7. Use Obsidian wikilinks `[[...]]` for internal references
8. Run `obsidian.update_note` or `obsidian.create_note` to persist

## Usage
```
/wiki intent routing
/wiki LLM fallback strategy
/wiki memory system architecture
/wiki decisions ADR-055
```

## Wiki Structure
```
.wiki/
├── decisions/     # ADRs
├── logs/         # Session logs
├── architecture/ # System docs
├── projects/     # Project docs
├── research/     # Research notes
└── knowledge/    # General knowledge
```

## ADR Format (Architecture Decision Records)
```markdown
# ADR-055: Use mem0ai for Memory

## Status
Accepted — 2024-04-20

## Context
We needed a memory system for agent context.

## Decision
Use mem0ai for episodic + semantic memory.

## Consequences
+ Fast vector search
+ Managed service
- Vendor lock-in
- Cost at scale
```

## Session Log Format
```markdown
# Session: 2024-04-25 — Implement LLM Fallbacks

## Goal
Implement fallback chain for LLM calls.

## What was done
- Added groq → cerebras → claud fallback
- Updated llm_client.py

## Key decisions
- Fallback order: groq > cerebras > claude

## Next steps
- Add tests for fallback scenarios
- Monitor error rates
```

## Constraints
- Saves to .wiki/ directory
- Does not commit automatically
- File name: kebab-case, descriptive
- Include frontmatter (title, date, tags)
