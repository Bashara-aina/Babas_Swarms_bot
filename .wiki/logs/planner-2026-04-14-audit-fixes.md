---
title: Planner 2026 04 14 Audit Fixes
type: concept
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- logs
created: '2026-04-14'
updated: '2026-04-14'
summary: 'Type: BUG_FIX + FEATURE'
wikilinks: []
confidence: medium
source: research
---
## Plan: Audit Fixes — GitIgnore, Wiki Frontmatter, OpenCode Pipeline
Date: 2026-04-14
Type: BUG_FIX + FEATURE

## Context Gathered
1. **GitIgnore Issue**: `.mcp.json` and `.claude/settings.json` exist at repo root but are NOT in `.gitignore`. This risks committing secrets/API keys.

2. **Wiki Frontmatter Issue**: 
   - Audit report said 214 articles missing frontmatter
   - `batch_fix_frontmatter.py` already ran and fixed 34 files
   - Current state: only 1 file missing frontmatter (`logs/2026-04-14-opencode-deep-audit.md`)
   - The "9" in the task description may be stale from earlier audit state

3. **OpenCode Session Write Pipeline Issue**:
   - Current: `run_opencode_task()` in `core/opencode_bridge.py` runs opencode subprocess
   - Session writes happen via hook system (`opencode_session_start_hook`, `opencode_session_end_hook` in `core/builtin_hooks.py`)
   - Hooks register on `pre_tool_use` and `post_tool_use` events
   - Problem: Hooks are generic and the opencode session context may not flow correctly through them
   - Fix: Replace hook-based approach with direct post-subprocess callback - after subprocess completes, directly call `opencode_write_session_summary()`

## Risk Assessment
- GitIgnore: Low risk, straightforward addition
- Frontmatter: The batch_fix script already ran, only 1 file remains. Risk of re-fixing files already fixed.
- OpenCode Pipeline: Medium risk - need to ensure session summaries still get written after the change

## Approach
1. Contract 1: Add entries to `.gitignore`
2. Contract 2: Run health scan to identify remaining missing frontmatter files, then fix them
3. Contract 3: Modify `run_opencode_task()` to call `opencode_write_session_summary()` directly after subprocess completes, and remove the hook-based approach for opencode sessions

## Execution Order
1. GitIgnore (Contract 1) - can run first
2. Frontmatter (Contract 2) - depends on health scan output
3. OpenCode Pipeline (Contract 3) - modify `opencode_bridge.py` and `builtin_hooks.py`
