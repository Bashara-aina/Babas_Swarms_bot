---
name: hermes-agent
description: Auto-trigger for Hermes Agent — activates on terminal, web search, browser, delegate subagent, vision, or cross-session recall tasks. For tasks requiring shell commands, web scraping, browser automation, spawning isolated subagents, or searching past conversations.
---

# Hermes Agent — Tool Registry + Delegate + Session Recall

## When This Skill Auto-Activates

This skill activates when your task involves:
- Terminal/shell commands (`run`, `exec`, `bash`, `terminal`)
- Web search or content extraction (`search web`, `browse`, `scrape`, `extract from url`)
- Browser automation (`navigate`, `click`, `fill form`, `browser`)
- Spawning subagents (`delegate`, `spawn`, `subagent`, `parallel agents`)
- Vision/image analysis (`analyze image`, `vision`)
- Cross-session recall (`search past sessions`, `remember what we did`)
- Code execution sandbox (`execute code`, `run python`)

## What Hermes Provides

**~50 tools across 15 toolssets**:

| Toolset | Tools |
|---------|-------|
| terminal | `terminal`, `process` |
| file | `read_file`, `write_file`, `patch`, `search_files` |
| web | `web_search`, `web_extract` |
| browser | `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_scroll`, `browser_vision` |
| vision | `vision_analyze` |
| delegate | `delegate_task` (spawns isolated subagents) |
| session_search | `session_search` (FTS5 across all conversations) |
| skills | `skills_list`, `skill_view`, `skill_manage` |
| todo | `todo` |
| code_execution | `execute_code` |

## How to Use the Delegate Tool

**For parallel work** — split a complex task into independent chunks:

```
hermes_delegate(goal="Analyze module X for bottlenecks", context="Project at /path", toolsets="terminal,file")
hermes_delegate(goal="Analyze module Y for bottlenecks", context="Project at /path", toolsets="terminal,file")
```

**For isolated context** — when a task needs to not see your current context:

```
hermes_delegate(goal="Security audit of /home/newadmin/project", context="...", toolsets="terminal,file")
```

The subagent runs with fresh context — no parent context leakage.

## How to Use Session Search

```
hermes_session_search(query="memory leak evaluate.py")
# Returns: matching sessions with snippets
```

## Quick Reference

| Tool | When to use |
|------|-------------|
| `hermes_terminal` | Shell commands, git, npm, python -c |
| `hermes_web_search` | Research, fact-finding |
| `hermes_web_extract` | Pull content from a specific URL |
| `hermes_browser_navigate` | JS-rendered pages, auth-gated content |
| `hermes_delegate` | Complex multi-part tasks, parallel work |
| `hermes_session_search` | Recall from previous sessions |
| `hermes_vision_analyze` | Images, screenshots, diagrams |
| `hermes_execute_code` | Python/JS sandbox execution |
| `claude_code_task` | Full Claude Code CLI with tool access via MCP |
| `claude_code_agent` | Autonomous Claude Code agent (coder/reviewer/architect) |
| `claude_code_read` | Read + analyze files with Claude Code |
| `claude_code_search` | Search code with Claude Code grep + context |
| `claude_code_git` | Git operations via Claude Code |
| `claude_code_list_tools` | List all Claude Code bridge tools |

## NOT for these — use other agents:

- Simple file edits → Edit tool directly
- Code implementation → Coder agent
- Bug finding → Auditor/Independent-Auditor skill
- Security scan → security-architect agent

## Anti-Patterns

- **Don't delegate trivial tasks** — delegate overhead only worth it for complex, multi-step work
- **Don't use vision on text pages** — `hermes_web_extract` is faster and more accurate
- **Don't use terminal for file edits** — use Edit tool, preserves diff context