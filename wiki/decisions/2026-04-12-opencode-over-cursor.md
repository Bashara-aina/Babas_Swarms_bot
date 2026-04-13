---
title: "2026-04-12-opencode-over-cursor"
type: decision
status: accepted
tags: [opencode, cursor, backend, decision, coding-agent]
created: 2026-04-12
updated: 2026-04-12
summary: OpenCode was selected over Cursor for backend coding tasks due to superior CLI integration, native server mode, and direct Telegram workflow compatibility. OpenCode provides terminal TUI, native M2.7 model support, and MCP protocol compatibility essential for Legion's automation pipeline.
wikilinks: [[opencode]], [[cursor]], [[adr-2026-04-11-opencode-integration]]
confidence: high
source: decision
---

# ADR: OpenCode Over Cursor for Backend Coding Tasks

**Date**: 2026-04-12  
**Status**: ACCEPTED  
**Deciders**: Bashara, Legion (via audit)  
**Supersedes**: ADR-001-opencode-integration (initial decision)

---

## Context

Legion required a coding agent for autonomous backend coding tasks. Two primary candidates were evaluated:

1. **OpenCode** — CLI-first autonomous coding agent with server mode
2. **Cursor** — IDE-first coding assistant with agent mode

The evaluation criteria prioritized:
- CLI accessibility for Telegram bot integration
- Server mode for background task execution
- Self-hosting capability for cost control
- MCP (Model Context Protocol) compatibility

### Evaluation Criteria

| Criteria | Weight | OpenCode | Cursor |
|----------|--------|----------|--------|
| CLI access | High | ✅ Full CLI | ⚠️ Limited |
| Telegram integration | High | ✅ Direct | ❌ None |
| Server mode | High | ✅ Native | ❌ No |
| Agent pipeline | Medium | ✅ Built-in | ✅ Agent mode |
| Self-hosted | Medium | ✅ | ✅ |
| Context window streaming | Low | ✅ | ✅ |
| MCP compatibility | Medium | ✅ Native | ⚠️ Plugin |
| M2.7 native support | High | ✅ | ⚠️ Via API |

## Decision

Select **OpenCode** as the primary backend coding agent for Legion, integrated via `core/opencode_bridge.py`.

### OpenCode Key Features

From `wiki/raw/prompts/opencode-external-tools.md`:

```
REPO: OpenCode (terminal-native coding agent)
FEATURES:
- Terminal TUI for interactive coding sessions
- M2.7 native model support (primary in Legion)
- MCP (Model Context Protocol) for tool integration
- Server mode: opencode serve --port 4096
- Agent mode: opencode agent create, opencode run <task>
```

### Why Not Cursor

1. **No Telegram Integration Path**: Cursor is designed for desktop IDE use. While it has an agent mode, there's no CLI mechanism for Telegram-triggered execution.

2. **Server Mode Absence**: Cursor runs as a desktop application. OpenCode's `serve` command allows background task execution perfect for bot-triggered workflows.

3. **MCP Protocol**: OpenCode has native MCP support, essential for Legion's tool integration layer.

4. **M2.7 Model Support**: OpenCode has native MiniMax M2.7 integration, which is Legion's primary coding model.

## Implementation

### Architecture

```
[Telegram /opencode command]
    → [handlers/dev.py]
    → [core/opencode_bridge.py]
    → [opencode CLI subprocess]
    → [extract_report()]
    → [Telegram response]
```

### Key Files

| File | Purpose |
|------|---------|
| `core/opencode_bridge.py` | Bridge between Telegram and OpenCode CLI |
| `handlers/dev.py` | Handler registration (lines 181-219) |
| `LEGION_MASTER_PROMPT.md` | Master prompt for OpenCode sessions |

### OpenCode Commands Used

```bash
# Start server mode (background)
opencode serve --port 4096

# Create new agent
opencode agent create --name <agent_name>

# Execute task
opencode run <task_description>

# Extract report from session
opencode report <session_id>
```

## Consequences

### Positive

- Direct Telegram integration via `/opencode` command
- Full CLI control for scripting and automation
- Server mode enables background task queue
- Native MCP support for tool augmentation
- M2.7 model optimization for coding tasks
- Cost-effective self-hosted solution

### Negative

- Learning curve for new users unfamiliar with CLI
- Less visual debugging compared to IDE
- Session management requires additional handling
- No built-in code editor UI

## Alternatives Considered

| Alternative | Reason Not Selected |
|-------------|---------------------|
| Cursor Agent Mode | No server mode, IDE-dependent |
| GitHub Copilot | No autonomous agent mode |
| Claude Code | No self-hosted option |
| Devin | SaaS only, no self-hosting |

## Related Decisions

- [[adr-2026-04-11-opencode-integration]] — Initial integration decision
- [[opencode]] — OpenCode entity page
- [[cursor]] — Cursor entity page (alternative not selected)
- [[adr-2026-04-12-multi-agent-pipeline]] — Multi-agent context

---

*Last reviewed: 2026-04-12*
