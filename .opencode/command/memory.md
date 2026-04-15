---
description: >-
  Query or update cross-session memory. Read from memory to retrieve stored
  facts, preferences, and context. Write to memory to persist new learnings.
mode: primary
model: minimax-coding-plan/MiniMax-M2.7
---
# /memory — Cross-Session Memory Operations

## WHEN TO USE

Use `/memory` when:
- You need context from previous sessions
- You learn something that should persist
- You need to check user preferences or project facts
- You're about to make a decision that should consider past context

## MEMORY TYPES

| Type | Location | Purpose |
|------|----------|---------|
| project | `.opencode/memory/project/` | Architecture, key files, decisions |
| user | `.opencode/memory/user/` | Identity, preferences, hardware |
| feedback | `.opencode/memory/feedback/` | What to avoid/do based on past |
| reference | `.opencode/memory/reference/` | External system pointers |

## USAGE

```
/memory read [topic]
/memory write [type] [title] [content]
/memory search [query]
/memory list
/memory update [file] [new content]
```

## EXAMPLES

### Reading
```
/memory read swarm-bot-architecture
/memory read bashara-identity
/memory read project preferences
```

### Writing
```
/memory write project "new-feature-x" This feature does X...

/memory write feedback "avoid-recursive-merge" 
The recursive approach caused infinite loop in v1.
Always use iterative implementation for merge sorts.

/memory write user "prefer-pydantic"
Bashara prefers Pydantic over dataclasses for type validation.
Use pydantic.BaseModel not @dataclass for new code.
```

### Searching
```
/memory search "deployment"
/memory search "GitHub"
/memory search "mamba"  # finds POPW project context
```

### Listing
```
/memory list              # list all memory files
/memory list project      # list project memory only
/memory list user         # list user memory only
```

## MEMORY FILE FORMAT

```markdown
---
name: [memory-name]
description: [one-line description]
type: [user/project/feedback/reference]
---

[Content]

**Why:** [reason this matters]
**How to apply:** [when/where to use this memory]
```

## WHAT TO MEMORIZE

### Worth memorizing:
- Architecture decisions and why
- User preferences ("Bashara prefers X over Y")
- Past failures and their causes
- Key file paths or patterns
- External system URLs
- Team conventions

### Not worth memorizing:
- Routine boilerplate
- Temporary state
- Obvious facts (file extensions, etc.)
- Information already in code

## ANTI-HALLUCINATION RULES

1. **Check before writing** — don't duplicate existing memory
2. **Update stale memory** — check timestamps
3. **Verify writes** — cat file after writing
4. **Index new memory** — add to MEMORY.md if new topic
5. **Cite actual memory** — paste from file when referencing

## STATUS
```
MEMORY STATUS: ✅ [operation] | ❌ FAILED
Type: [type]
Topic: [topic]
Files: [count]
```
