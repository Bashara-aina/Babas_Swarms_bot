---
description: Compress text or messages with claw-compactor's 14-stage Fusion Pipeline. Thin slash entry over the claw-compactor skill.
---

# /compress — claw-compactor Pipeline (Claude Code shim)

Thin slash entry over the `claw-compactor` skill. For the full pipeline + rewind support, invoke the skill directly with the Skill tool.

## Usage

```
/compress                              # interactive
/compress path/to/file.py              # compress a file (auto-detect type)
/compress "long prose block..."        # compress inline string
/compress messages.json --messages     # compress a list of chat messages
/compress --benchmark                  # run full benchmark on .session_state
```

## What It Does

1. Resolve the `claw-compactor` skill (canonical: `skills/claw-compactor/SKILL.md`)
2. Auto-detect content type: code, json, log, diff, search, text
3. Run `FusionEngine(enable_rewind=True).compress(text, content_type=...)`
4. Report original tokens, compressed tokens, savings %, stages fired, rewind id
5. On `--benchmark`, run `claw-compactor benchmark --json` and write to `.session_state/recalled_context.md`

## Tier Presets

| Tier | Stages | Typical Use |
|------|--------|-------------|
| `fast` | first 3 (QuantumLock → Cortex → Photon) | quick wins, <50ms |
| `balanced` (default) | first 8 (through Nexus) | daily conversation |
| `full` | all 14 (through Abbrev) | big rewinds, 1k+ tokens saved |

## Content-Type Auto-Detect

| Heuristic | Type |
|-----------|------|
| `import` / `def` / `class` / balanced braces | `code` |
| Starts with `[` or `{` and parses as JSON | `json` |
| `[ERROR]` / `[WARN]` / ISO timestamps / stack frames | `log` |
| `diff --git` / `@@ -` / `+`/`-` lines | `diff` |
| JSONL with `url`/`title` keys (search results) | `search` |
| everything else | `text` |

## Delegation

When the user types `/compress`, prefer invoking the `claw-compactor` skill (canonical surface) for the full 14-stage pipeline + rewind. This file is just a slash compatibility entry.

`ARGUMENTS: $ARGUMENTS`
