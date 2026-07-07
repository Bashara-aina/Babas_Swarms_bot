# graphify
- **graphify** (`.claude/skills/graphify/SKILL.md`) — knowledge graph for codebase queries.
  Auto-updated via git post-commit hook (AST-only rebuild on changed files, no LLM cost).
  Trigger: `/graphify` for full pipeline (docs/images), or `/graphify query "<question>"` for graph search.
- Graph at `graphify-out/graph.json` (6061 nodes, 9007 links) — rebuilt incrementally on every `git commit`.
- Rebuild logs: `~/.cache/graphify-rebuild.log` (background, non-blocking).
- Skip per-commit: `GRAPHIFY_SKIP_HOOK=1 git commit`.
- MCP server enabled in `config/mcp_config.json` + `.claude/settings.json` — graphify tools available during session.

# Session management
- `session.js` (`.claude/helpers/session.js`) — session lifecycle: start/restore/end/update/metric/trackFile.
- Writes `current.json` (`.claude-flow/data/`) on start and `last-session.json` (`.claude-flow/metrics/`) on end.
- `store-user-query` hook captures user prompt into session context for obsidian sync.
- `dreaming-consolidate` hook fires at session end for hippocampal replay via `.claude-flow/mcp/dreaming_consolidation.py`.

# Obsidian vault
- Wiki at `.wiki/` — auto-synced from session end hooks.
- Session logs: `.wiki/Sessions/YYYY-MM-DD.md` (auto-appended).
- Memory files mirrored to `.wiki/memories/claude-*.md` (32 source files, 32 synced + cleanup on source delete).
- Git commit log: `.wiki/logs/git-log.md`.
- Daily cron at 23:23 ensures at least one entry on no-session days.
- Weekly cron Mon 9:57 checks graph freshness.
- Obsidian MCP server (`@iflow-mcp/kynlos-obsidian-mcp-server`) enabled — use `search_notes`/`read_note` during sessions.

# Cognee (L7 Knowledge Graph Memory)
- **Cognee** (`cognee-mcp-server.py`) adds a knowledge-graph memory layer (L7) on top of existing L1-L6
- MCP tools: `cognee_remember` (ingest), `cognee_recall` (search), `cognee_sync`, `cognee_status`, `cognee_forget`, `cognee_graph_stats`
- Bridge at `.claude/helpers/cognee-bridge.mjs` — auto-imports auto-memory to cognee at SessionStart, syncs at SessionEnd
- Configured for oc-cc-proxy (`deepseek-v4-flash`), LanceDB vector store at `data/cognee/`, system DB at `data/cognee/system/`
- First `cognee_remember` call creates databases; subsequent calls are faster

# Design rules (load on demand only)
- UI/UX excellence + taste-router live in `.claude/reference/` (NOT auto-loaded — saves ~28 KB/session).
- When the user asks for a landing page, redesign, dashboard, or any visual/interaction work, Read both files first:
  - `.claude/reference/ui-ux-excellence.md` (forbidden patterns, component quality)
  - `.claude/reference/taste-router.md` (variant picker + 3-dial system)
- Do not auto-load them for non-UI work (Telegram bot logic, ML training, backend code, etc.).

# Fable 5 Session Patterns
- Fable 5 reference files in `.claude/reference/fable5-*.md` loaded ON DEMAND
- Core behavioral DNA in root CLAUDE.md (always loaded) and user global CLAUDE.md (~/.claude/CLAUDE.md)
- **fable5-behavior.md** — identity, outcome-first communication, autonomous execution (not watching), context management, evidence/tool rules. Load when Fable 5 behavior needs reinforcement mid-session
- **fable5-safety.md** — copyright hard limits (15+ words = severe violation), harmful content blocking, citation rules, visual content safety, evenhandedness
- **fable5-memory.md** — past_chats recognition cues (possessives, definite articles, past-tense verbs), query construction, memory attribution (never narrate retrieval), user preferences
- **fable5-workflow.md** — agent dispatch patterns: pipeline/parallel, adversarial verification, judge panel, loop-until-dry, completeness critic, budget-aware execution
- **fable5-tools.md** — tool choice discipline, monitor coverage (widen alternations, --line-buffered), read/edit discipline. NEVER use CronCreate/CronDelete.
- Hooks enforce Fable 5 at runtime: `.claude/hooks/ecc-fable5-pre.sh` (blocks permission-asking), `.claude/hooks/ecc-fable5-post.sh` (warns on promise-endings)
