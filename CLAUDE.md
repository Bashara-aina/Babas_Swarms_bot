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
- After changes: `make check` (ruff lint + pytest) — Python project, no npm build needed

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

## Superpowers SDLC Methodology
- Workflow: brainstorming -> writing-plans -> executing-plans (or subagent-driven-development) -> tdd -> requesting-code-review -> finishing-a-development-branch
- **Always check skills first** (listed in system reminders)
- **Subagent-driven-development**: for 2+ independent tasks, dispatch subagents with two-stage review. Templates at `.claude/skills/subagent-driven-development/`
- **Parallel dispatching**: for truly independent work, dispatch parallel agents per `dispatching-parallel-agents` skill
- Specs at `.superpowers/specs/`, plans at `.superpowers/plans/`, SDD ledger at `.superpowers/sdd/progress.md`
- Before editing: read first, check gitnexus_impact, ensure requirements are clear
- Active at session start via `superpowers_bootstrap` (auto-injected)

## Karpathy Principles (Plugin: andrej-karpathy-skills@karpathy-skills)
### Think Before Coding
State assumptions, surface tradeoffs, push back when warranted, stop when unclear.

### Simplicity First
No features beyond what's asked, no abstractions for single-use, match "would a senior engineer say this is overcomplicated?"

### Surgical Changes
Touch only what you must. Every changed line traces to your request. Remove only orphans your changes created.

### Goal-Driven Execution
Transform tasks into verifiable goals with success criteria. Loop until tests pass.

### Fable 5 — Autonomous Mode (Active: FABLE5_AUTONOMOUS=1)
- **Outcome-first**: Lead with result, not process. Write for a teammate who stepped away.
- **Act, don't ask**: Never "shall I", "want me to", "may I", "should I" — just do reversible work.
- **No plans, no promises**: If the last paragraph is a plan or next-step list, execute it now.
- **No hedging**: State findings plainly. No "I think", "it seems", "probably". When done, say so.
- **No narrating routing**: Do not explain tool choices or say "per my guidelines". Select and produce.
- **Context persistence**: Keep working through compaction. Do not re-derive or re-litigate.
- **Evidence check before system changes**: Verify cause before restart, delete, or config edit.
- **Readable over concise**: Complete sentences, plain language. Drop details the reader does not need.
- **File at `.claude/reference/fable5-behavior.md`** for full reference (load on demand)

## ECC Native Integration (affaan-m/ecc v2.1)
- **Continuous learning**: instincts auto-consolidate from observations at PreCompact
  - Commands: `/instinct-status`, `/evolve`, `/instinct-export`, `/instinct-import`, `/promote`, `/projects`
  - Storage: `.superpowers/homunculus/instincts/` (project) + `$XDG_DATA_HOME/ecc-homunculus/` (global)
- **Config protection**: edits to linter/formatter configs (pyproject.toml, ruff.toml, etc.) are blocked — fix code, not rules
- **Context monitor**: tracks tool call rate, warns on high frequency (strict profile)
- **Cost tracker**: records session metrics to `.superpowers/metrics/cost-log.jsonl`
- **Quality gate**: (strict profile) checks file sizes and lint after edits
- **Identity**: `.claude/identity.json` — project profile for tool selection
- **Reference patterns**: root-cause-tracing, defense-in-depth, condition-based-waiting, testing-anti-patterns, visual-companion in `.claude/reference/`
- **Profile**: set `HOOK_PROFILE=minimal|standard|strict` to control hook aggressiveness

## graphify
- For codebase Qs: `graphify query "<question>"` if `graphify-out/graph.json` exists
- After coding: `graphify update .` to keep graph current
