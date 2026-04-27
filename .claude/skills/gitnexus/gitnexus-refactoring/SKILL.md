---
name: gitnexus-refactoring
description: "Use when the user wants to rename, extract, split, move, or restructure code safely. Examples: \"Rename this function\", \"Extract this into a module\", \"Refactor this class\", \"Move this to a separate file\""
---

# Refactoring with GitNexus

## When to Use

- "Rename this function safely"
- "Extract this into a module"
- "Split this service"
- "Move this to a new file"
- Any task involving renaming, extracting, splitting, or restructuring code

## Workflow

```
1. gitnexus_impact({target: "X", direction: "upstream"})  → Map all dependents
2. gitnexus_query({query: "X"})                           → Find execution flows involving X
3. gitnexus_context({name: "X"})                          → See all incoming/outgoing refs
4. Plan update order: interfaces → implementations → callers → tests
```

> If "Index is stale" → run `npx gitnexus analyze` in terminal.

## Checklists

### Rename Symbol

```
- [ ] gitnexus_rename({symbol_name: "oldName", new_name: "newName", dry_run: true}) — preview all edits
- [ ] Review graph edits (high confidence) and ast_search edits (review carefully)
- [ ] If satisfied: gitnexus_rename({..., dry_run: false}) — apply edits
- [ ] gitnexus_detect_changes() — verify only expected files changed
- [ ] Run tests for affected processes
```

### Extract Module

```
- [ ] gitnexus_context({name: target}) — see all incoming/outgoing refs
- [ ] gitnexus_impact({target, direction: "upstream"}) — find all external callers
- [ ] Define new module interface
- [ ] Extract code, update imports
- [ ] gitnexus_detect_changes() — verify affected scope
- [ ] Run tests for affected processes
```

### Split Function/Service

```
- [ ] gitnexus_context({name: target}) — understand all callees
- [ ] Group callees by responsibility
- [ ] gitnexus_impact({target, direction: "upstream"}) — map callers to update
- [ ] Create new functions/services
- [ ] Update callers
- [ ] gitnexus_detect_changes() — verify affected scope
- [ ] Run tests for affected processes
```

## Tools

**gitnexus_rename** — automated multi-file rename:

```
gitnexus_rename({symbol_name: "get_fallback_chain", new_name: "build_fallback_chain", dry_run: true})
→ 8 edits across 5 files
→ 6 graph edits (high confidence), 2 ast_search edits (review)
→ Changes: [{file_path, edits: [{line, old_text, new_text, confidence}]}]
```

**gitnexus_impact** — map all dependents first:

```
gitnexus_impact({target: "get_fallback_chain", direction: "upstream"})
→ d=1: chat, agent_loop, handle_rate_limit
→ Affected Processes: LLMFallbackChain, AgentLoop
```

**gitnexus_detect_changes** — verify your changes after refactoring:

```
gitnexus_detect_changes({scope: "all"})
→ Changed: 5 files, 8 symbols
→ Affected processes: LLMFallbackChain, AgentLoop
→ Risk: MEDIUM
```

**gitnexus_cypher** — custom reference queries:

```cypher
MATCH (caller)-[:CodeRelation {type: 'CALLS'}]->(f:Function {name: "get_fallback_chain"})
RETURN caller.name, caller.filePath ORDER BY caller.filePath
```

## Risk Rules

| Risk Factor         | Mitigation                                |
| ------------------- | ----------------------------------------- |
| Many callers (>5)   | Use gitnexus_rename for automated updates |
| Cross-area refs     | Use detect_changes after to verify scope  |
| String/dynamic refs | gitnexus_query to find them               |
| External/public API | Version and deprecate properly            |

## Swarm-Bot Refactoring Targets

Common refactoring scenarios in swarm-bot:

| Scenario                        | Key files to check                    |
| ------------------------------- | ------------------------------------- |
| Rename handler function         | handlers/*.py, router.py              |
| Extract LLM client utilities    | llm_client.py, agents.py              |
| Split intent router             | core/intent_router.py, agents.py     |
| Move memory utilities           | core/memory/*.py, core/legion_memory_facade.py |

## Example: Rename `get_fallback_chain` to `build_fallback_chain`

```
1. gitnexus_rename({symbol_name: "get_fallback_chain", new_name: "build_fallback_chain", dry_run: true})
   → 8 edits: 6 graph (safe), 2 ast_search (review)
   → Files: llm_client.py, agents.py, task_orchestrator.py...

2. Review ast_search edits (config/*.yaml: dynamic reference!)

3. gitnexus_rename({symbol_name: "get_fallback_chain", new_name: "build_fallback_chain", dry_run: false})
   → Applied 8 edits across 5 files

4. gitnexus_detect_changes({scope: "all"})
   → Affected: LLMFallbackChain, AgentLoop
   → Risk: MEDIUM — run tests for these flows
```