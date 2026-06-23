# graphify
- **graphify** (`.claude/skills/graphify/SKILL.md`) — knowledge graph for codebase queries.
  Auto-updated via git post-commit hook (AST-only rebuild on changed files, no LLM cost).
  Trigger: `/graphify` for full pipeline (docs/images), or `/graphify query "<question>"` for graph search.
- Graph at `graphify-out/graph.json` (225K nodes, 342K edges) — rebuilt incrementally on every `git commit`.
- Rebuild logs: `~/.cache/graphify-rebuild.log` (background, non-blocking).
- Skip per-commit: `GRAPHIFY_SKIP_HOOK=1 git commit`.
- MCP server enabled in `config/mcp_config.json` — graphify tools available during session.

# Obsidian vault
- Wiki at `.wiki/` — auto-synced from session end hooks.
- Session logs: `.wiki/Sessions/YYYY-MM-DD.md` (auto-appended).
- Memory files mirrored to `.wiki/memories/claude-*.md` (33 memory files).
- Git commit log: `.wiki/logs/git-log.md`.
- Daily cron at 23:23 ensures at least one entry on no-session days.
- Obsidian MCP server (`@iflow-mcp/kynlos-obsidian-mcp-server`) enabled — use `search_notes`/`read_note` during sessions.

# Design rules (load on demand only)
- UI/UX excellence + taste-router live in `.claude/reference/` (NOT auto-loaded — saves ~28 KB/session).
- When the user asks for a landing page, redesign, dashboard, or any visual/interaction work, Read both files first:
  - `.claude/reference/ui-ux-excellence.md` (forbidden patterns, component quality)
  - `.claude/reference/taste-router.md` (variant picker + 3-dial system)
- Do not auto-load them for non-UI work (Telegram bot logic, ML training, backend code, etc.).
