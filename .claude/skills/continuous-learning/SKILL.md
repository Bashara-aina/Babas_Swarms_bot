---
name: continuous-learning
description: >-
  Instinct-based continuous learning from tool use patterns (ECC v2.1).
  Captures observations via hooks, generates instincts with confidence scoring
  (0.3/0.5/0.7/0.9), auto-promotes at 0.8+ across projects. Use commands below
  to view, export, and manage instincts.
trigger: instinct-status
---

This skill manages the instinct-based learning system. It does NOT run automatically — it is triggered by commands.

## How It Works

1. **Observation capture** — PostToolUse hooks write JSON/JSONL observation files to `.superpowers/homunculus/observations/`
2. **Consolidation** — PreCompact hook runs `instinct-cli.cjs consolidate` to find repeated patterns
3. **Instinct generation** — Atomic instincts with:
   - One trigger, one action pattern
   - 4-tier confidence: 0.3 (emerging) / 0.5 (developing) / 0.7 (established) / 0.9 (strong)
   - Domain categories: workflow, security, code-style, testing, debugging, architecture
4. **Auto-promotion** — Instinct at confidence >= 0.8 auto-promotes to global (stored at `$XDG_DATA_HOME/ecc-homunculus/instincts/`)
5. **Cross-project learning** — Global instincts apply across all projects via project registry at `$XDG_DATA_HOME/ecc-homunculus/projects.json`

## Commands

| Command | Description |
|---------|-------------|
| `/instinct-status` | Show current instincts with confidence scores |
| `/evolve` | Cluster related instincts into higher-level patterns |
| `/instinct-export` | Export instincts as JSON (for backup/sharing) |
| `/instinct-import` | Import instincts from another project's export |
| `/promote` | Manually promote high-confidence instincts to global |
| `/projects` | List all tracked projects with instinct counts |

## Observation Format

Observations are stored in `.superpowers/homunculus/observations/` as JSON files or JSONL streams:

```json
{
  "timestamp": "2026-06-23T12:00:00Z",
  "tool": "Edit",
  "tool_input": {"file_path": "src/main.py"},
  "result": "success",
  "session": "session-id"
}
```

## Storage

- **Project instincts**: `.superpowers/homunculus/instincts/`
- **Global instincts**: `$XDG_DATA_HOME/ecc-homunculus/instincts/`
- **Project registry**: `$XDG_DATA_HOME/ecc-homunculus/projects.json`
- **Consolidation cursor**: `.superpowers/homunculus/.consolidation-cursor`
