
This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **swarm-bot** (74107 symbols, 178422 relationships, 300 execution flows).

## Always Do

- **MUST run `gitnexus_impact` before editing any symbol.** Report blast radius and risk level.
- **MUST run `gitnexus_detect_changes()` before committing.** Verify changes match expected scope.
- **MUST warn** if impact analysis returns HIGH/CRITICAL risk.
- Use `gitnexus_query({query: "concept"})` for exploration, `gitnexus_context({name: "symbol"})` for full context.

## Tools Quick Reference

| Tool | When | Command |
|------|------|---------|
| `query` | Find by concept | `gitnexus_query({query: "auth"})` |
| `context` | 360° view of symbol | `gitnexus_context({name: "Foo"})` |
| `impact` | Blast radius | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit check | `gitnexus_detect_changes()` |
| `rename` | Safe rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph query | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK | MUST update |
| d=2 | LIKELY AFFECTED | Should test |
| d=3 | MAY NEED TESTING | Test if critical |

## Self-Check

Before completing code changes, verify:
1. `gitnexus_impact` run for all modified symbols
2. No HIGH/CRITICAL warnings ignored
3. `gitnexus_detect_changes()` confirms scope

## Keeping Fresh

After commits: `npx gitnexus analyze` (add `--embeddings` if index had them; check `.gitnexus/meta.json`)
<!-- gitnexus:end -->
