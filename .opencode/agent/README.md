---
name: opencode-root
description: OpenCode agent root directory - core agents and shared definitions
type: index
tags: [opencode, agents, swarm-bot]
created: 2026-04-28
updated: 2026-04-28
---

# OpenCode Agent Root

Core agents and shared definitions for swarm-bot OpenCode setup.

## Role

Index and documentation of available agents in the swarm-bot OpenCode setup.

## Trigger

When to use: Reference document for agent selection. Not a task-executing agent.

## Tools

Read (reference only)

## Output

This is a reference document. No task output.

## Structure

```
.opencode/
├── agent/        # Core system agents (16 files)
├── agents/       # 36 specialized agents (markdown-based)
├── command/      # 31 slash commands
├── memory/       # Persistent memory index
└── opencode.json # Configuration
```

## Core Agents (agent/)

| Agent | Purpose |
|-------|---------|
| `code-reviewer.md` | Unified code review |
| `coding.md` | Shared coding agent |
| `collaborator.md` | Pair programming |
| `deployment-engineer.md` | Deployments |
| `diff-analyzer.md` | Diff analysis |
| `explorer.md` | Code exploration |
| `focused-implementer.md` | Task execution |
| `lsp-reader.md` | LSP-based code analysis |
| `memory.md` | Memory management |
| `paper-wiki-writer.md` | Documentation |
| `research-agent.md` | Research tasks |
| `researcher.md` | Shared research agent |
| `reviewer.md` | Shared reviewer agent |
| `skill-creator.md` | Skill creation |
| `skill-reviewer.md` | Skill review |

## System Agents (agents/) - Hidden

| Agent | Purpose |
|-------|---------|
| `summary.md` | Session summarization |
| `compaction.md` | Context compaction |
| `title.md` | Session title generation |
| `hermes-*.md` | Hermes multi-agent system |
| `planner.md` | Task planning |
| `worker.md` | Task execution |
| `reviewer.md` | Code review |
| `verifier.md` | Hallucination detection |
| `wikibot.md` | Wiki documentation |

## Configuration

`opencode.json` controls:
- Model: `minimax-coding-plan/MiniMax-M2.7`
- Tool permissions: All set to `allow`
- MCP servers: gitnexus, obsidian, git, filesystem, exa
- Build steps: 60
- External directory: `/home/newadmin/**`

### Tool Permissions

All tools are set to `allow` globally:
- read, edit, glob, grep, list, bash
- webfetch, websearch, codesearch
- question, todowrite, skill, lsp

### Hidden System Agents

The summary, compaction, and title agents are overridden with full tool access via markdown agents.

## Known Limitations

### Summary Phase Tool Restriction

During **summary generation**, opencode.ai has an internal restriction that blocks the `read` tool. This is NOT a configuration issue - the config is correct with `read: allow`. This is an internal opencode infrastructure limitation.

**Status**: Config is optimally set. The restriction is in opencode's internal code, not configurable from outside.

## History

- 2026-04-28: Added summary/compaction/title agent overrides with full permissions
- 2026-04-28: Fixed opencode.json schema (top-level permission key)
- 2026-04-28: Compacted from 411 to 295 agents, 33 to 24 categories
- 2026-04-16: Created legiona shared agents