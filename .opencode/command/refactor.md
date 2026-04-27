---
allowed-tools: Read,Bash,Grep,Glob
argument-hint: <file-or-function>
description: "Refactor code safely. Analyzes blast radius, renames, extracts, or restructures with automated checks."
---

# /refactor — Safe refactoring

Refactor code with blast radius analysis and automated verification.

## Usage
```
/refactor rename get_fallback_chain to build_fallback_chain
/refactor extract memory utilities to core/memory/utils.py
/refactor split intent_router into separate modules
```

## Safety Protocol
```
1. gitnexus_impact — what depends on this?
2. Plan update order
3. Apply changes
4. gitnexus_detect_changes — verify scope
5. Run tests
```

## Refactoring Types

### Rename
- Uses gitnexus_rename for multi-file updates
- Graph edits (high confidence) applied automatically
- Text/AST search edits reviewed manually

### Extract
- Identifies all usages
- Extracts to new module
- Updates all imports

### Split
- Analyzes responsibility boundaries
- Splits function/class
- Updates callers

## Blast Radius Rules
| Depth | Risk | Action |
|-------|------|--------|
| d=1 | WILL BREAK | Must update all direct callers |
| d=2 | LIKELY AFFECTED | Should test |
| d=3 | MAY NEED TESTING | Test if critical |

## Swarm-Bot Refactoring Targets
- llm_client.py — avoid large refactors
- core/intent_router.py — high blast radius
- core/memory/memory_manager.py — test thoroughly
- handlers/loader.py — affects all handlers

## Constraints
- Always use gitnexus_impact before refactoring
- Verify scope with gitnexus_detect_changes
- Run tests after each significant change
