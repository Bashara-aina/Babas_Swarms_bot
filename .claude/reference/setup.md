# Setup (one-time)

```bash
claude mcp add claude-flow -- npx -y @claude-flow/cli@latest
npx @claude-flow/cli@latest daemon start && npx @claude-flow/cli@latest doctor --fix
```

Agent tool = execution (agents, files, code, git). MCP tools = coordination (swarm, memory, hooks). CLI = same via Bash.
