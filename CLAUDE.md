# Ruflo — Claude Code Configuration

## Hard Rules
- Do what's asked; no extra files, docs, or tests in root
- Read before edit; never commit secrets/.env
- Keep files under 500 lines; validate input at boundaries
- **All agents: OpenCode Go via oc-cc-proxy only — no direct Anthropic/MiniMax API calls.**

## Swarm
- YES: 3+ files, new features, cross-module refactors, API, security, perf
- NO: single-file edits, 1-2 line fixes, docs, config, questions
- Topology: hierarchical-mesh (anti-drift), max 15 agents, HNSW + Neural enabled

## Build & Test
- After changes: `npm run build && npm test`

## GitNexus (required)
- **Before edit**: `gitnexus_impact({target, direction: "upstream"})` — warn on HIGH/CRITICAL
- **Before commit**: `gitnexus_detect_changes()` — verify scope
- **Rename**: `gitnexus_rename({dry_run: true})` only, never find-and-replace
- **Verify**: all modified symbols had impact run, d=1 dependents updated

## On-Demand Reference
- Model routing: `.claude/reference/model-routing.md`
- GitNexus: `.claude/reference/gitnexus-reference.md`
- Setup: `.claude/reference/setup.md`
- UI/UX: `.claude/reference/taste-router.md` + `ui-ux-excellence.md` (BOTH before UI work)
- Agent skills: `docs/agents/issue-tracker.md`, `triage-labels.md`, `domain.md`
- Full agent list: `.claude/agents/` (update count via `ls`)

## graphify
- For codebase Qs: `graphify query "<question>"` if `graphify-out/graph.json` exists
- After coding: `graphify update .` to keep graph current
