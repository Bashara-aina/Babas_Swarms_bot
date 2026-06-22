# GitNexus — Reference

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Tools Quick Reference

| Tool | When to use | Command |
|------|-------------|---------|
| `query` | Find code by concept | `gitnexus_query({query: "auth validation"})` |
| `context` | 360-degree view of one symbol | `gitnexus_context({name: "validateUser"})` |
| `impact` | Blast radius before editing | `gitnexus_impact({target: "X", direction: "upstream"})` |
| `detect_changes` | Pre-commit scope check | `gitnexus_detect_changes({scope: "staged"})` |
| `rename` | Safe multi-file rename | `gitnexus_rename({symbol_name: "old", new_name: "new", dry_run: true})` |
| `cypher` | Custom graph queries | `gitnexus_cypher({query: "MATCH ..."})` |

## Impact Risk Levels

| Depth | Meaning | Action |
|-------|---------|--------|
| d=1 | WILL BREAK — direct callers/importers | MUST update these |
| d=2 | LIKELY AFFECTED — indirect deps | Should test |
| d=3 | MAY NEED TESTING — transitive | Test if critical path |

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/swarm-bot/context` | Codebase overview, check index freshness |
| `gitnexus://repo/swarm-bot/clusters` | All functional areas |
| `gitnexus://repo/swarm-bot/processes` | All execution flows |
| `gitnexus://repo/swarm-bot/process/{name}` | Step-by-step execution trace |

## CLI Skill Files

| Task | Skill file |
|------|------------|
| Architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Refactoring | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

## Keeping the Index Fresh

```bash
npx gitnexus analyze           # Basic
npx gitnexus analyze --embeddings  # With embeddings (check .gitnexus/meta.json first)
```

> PostToolUse hook handles this automatically after `git commit` and `git merge`.
