---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/indexes/opencode-index.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-11T18:14:42.445302"
}
---

# Awesome OpenCode Index
Source: ~/swarm-bot/.wiki/research/opencode (README.md)

## Top 20 Plugins for OpenCode

| Plugin | Purpose | Key Feature |
|--------|---------|-------------|
| opencode-agent-identity | Agent self-identity | Per-message attribution for multi-agent |
| opencode-agent-memory | Persistent memory | Letta-inspired self-editable memory blocks |
| opencode-agent-skills | Dynamic skills loader | Discovers skills from project directories |
| opencode-background | Background processes | Process management for long tasks |
| opencode-background-agents | Async delegation | Claude Code-style background agents |
| opencode-dynamic-context-pruning | Token optimization | Prunes obsolete tool outputs |
| opencode-envsitter-guard | Security | Prevents .env file leaks |
| opencode-froggy | Hooks system | Claude Code-style hooks and specialized agents |
| opencode-handoff | Session handoff | Creates focused prompts for new sessions |
| opencode-mcp | MCP integration | Model Context Protocol server support |
| opencode-model-announcer | Model awareness | Injects current model name into context |
| opencode-morph-fast-apply | Fast editing | 10,500+ tokens/sec code editing |
| opencode-oh-my-opencode | Agent orchestration | Pre-built tools, LSP/AST/MCP, Claude layer |
| opencode-openai-codex-auth | OpenAI auth | ChatGPT Plus/Pro OAuth |
| opencode-agent-tmux | Tmux integration | Real-time agent panes with auto-launch |
| opencode-canvas | Interactive UI | tmux splits with canvases |
| opencode-opencode-mem | Vector memory | Persistent memory with local vector DB |
| opencode-snippets | Text expansion | DRY prompt engineering |
| opencode-swarm-plugin | Swarm coordination | Swarm-based agent coordination |
| opencode-tokenscope | Cost tracking | Token usage analysis |

## Top 10 Tips

1. **Use /handoff** to create focused prompts when switching sessions
2. **Install opencode-snip** to reduce LLM token consumption by 60-90%
3. **Use opencode-dynamic-context-pruning** to keep context lean
4. **Configure opencode-model-announcer** so agent knows which model it's using
5. **Use tmux integration plugins** for real-time multi-agent visibility
6. **Leverage background agents** for parallel task execution
7. **Use opencode-envsitter-guard** to prevent .env leaks
8. **Install opencode-workspace** for bundled 16-component orchestration
9. **Use opencode-oh-my-opencode-slim** for lightweight token-efficient orchestration
10. **Use opencode-tokenscope** to track and optimize token costs

## Top 5 Workflows

1. **Multi-Agent Swarm**: Use opencode-swarm-plugin + background-agents for parallel agent coordination
2. **Context Pruning Loop**: Use dynamic-context-pruning + tokenscope for lean sessions
3. **Session Handoff**: Create handoff → new session → immediate productivity
4. **Safe .env Workflow**: envsitter-guard + opencode-mem for secure secret management
5. **Background Processing**: background plugin + tmux panes for long-running tasks
