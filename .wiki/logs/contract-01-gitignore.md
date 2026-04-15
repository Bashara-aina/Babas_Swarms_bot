---
title: Contract 01 Gitignore
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
summary: Append `.mcp.json` and `.claude/settings.json` entries to `.gitignore` to
  prevent future secret commits.
wikilinks: []
confidence: medium
source: research
---
## CONTRACT #1: Add .mcp.json and .claude/settings.json to .gitignore

WHAT:
  Append `.mcp.json` and `.claude/settings.json` entries to `.gitignore` to prevent future secret commits.

FILES:
  READ:  /home/newadmin/swarm-bot/.gitignore
  WRITE: /home/newadmin/swarm-bot/.gitignore

DONE_WHEN:
  - `.gitignore` contains entry for `.mcp.json`
  - `.gitignore` contains entry for `.claude/settings.json`
  - `git diff .gitignore` shows only the two new entries added

PROOF_FORMAT:
  CONTENT: `grep -E "^\.(mcp\.json|claude/settings\.json)" /home/newadmin/swarm-bot/.gitignore`
  Expected output:
    .mcp.json
    .claude/settings.json

BLOCKER_IF:
  - `.gitignore` does not exist at expected path

DEPENDS_ON: none
