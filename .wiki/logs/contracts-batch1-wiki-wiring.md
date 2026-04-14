---
title: Contracts Batch1 Wiki Wiring
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
summary: Fix 10 wikilinks that incorrectly use `wiki/` or `.wiki/` prefix by removing
  the prefix
wikilinks: []
confidence: medium
source: research
---

## CONTRACT #1: Fix `wiki/` Prefix Wikilinks

WHAT:
  Fix 10 wikilinks that incorrectly use `wiki/` or `.wiki/` prefix by removing the prefix

FILES:
  READ:
    - .wiki/issues/review-fix-2026-04-13.md
    - .wiki/issues/review-2026-04-13-wiki-obsidian-restructure.md
    - .wiki/issues/review-2026-04-13-verify.md
    - .wiki/_meta/obsidian-plugins.md
    - .wiki/output/health/lint_2026-04-13.md
  WRITE:
    - .wiki/issues/review-fix-2026-04-13.md
    - .wiki/issues/review-2026-04-13-wiki-obsidian-restructure.md
    - .wiki/issues/review-2026-04-13-verify.md
    - .wiki/_meta/obsidian-plugins.md
    - .wiki/output/health/lint_2026-04-13.md

DONE_WHEN:
  - All `wiki/INDEX` links changed to `INDEX`
  - All `wiki/SCHEMA.md` links changed to `SCHEMA.md`
  - All `wiki/conversations.md` links changed to `conversations`
  - All `wiki/conversations/support.md` links changed to `conversations/support`
  - All `wiki/legion/conversation_processing.md` links changed to `legion/conversation_processing`
  - All `wiki/legion/faq.md` links changed to `legion/faq`
  - All `wiki/legion/interactions.md` links changed to `legion/interactions`
  - All `wiki/mental_health.md` links changed to `mental_health`
  - All `wiki/research/_template` links changed to `research/_template`
  - `.wiki/decisions/...` links changed to `decisions/...`

PROOF_FORMAT:
  Bash command: `grep -r "\[\[wiki/" .wiki/issues/ .wiki/_meta/ .wiki/output/ 2>/dev/null || echo "No wiki/ prefix links found"`
  Expected output: "No wiki/ prefix links found"

BLOCKER_IF:
  - File containing link has changed since analysis
  - Replacement target file doesn't exist

DEPENDS_ON: none

---

## CONTRACT #2: Fix Directory-Style Wikilinks

WHAT:
  Fix 7 wikilinks that incorrectly end with `/` (directory-style) in README.md

FILES:
  READ:
    - .wiki/README.md
  WRITE:
    - .wiki/README.md

DONE_WHEN:
  - `[[agents]]` changed to `[[agents]]`
  - `[[architecture]]` changed to `[[architecture]]`
  - `[[decisions]]` changed to `[[decisions]]`
  - `[[issues]]` changed to `[[issues]]`
  - `[[logs]]` changed to `[[logs]]`
  - `[[prompts]]` changed to `[[prompts]]`
  - `[[research]]` changed to `[[research]]`

PROOF_FORMAT:
  Bash command: `grep -E '\[\[.*/\]\]' .wiki/README.md`
  Expected output: no output (no directory-style links)

BLOCKER_IF:
  - README.md has unexpected format

DEPENDS_ON: none

---

## CONTRACT #3: Fix YAML Frontmatter in Log File

WHAT:
  Fix malformed YAML frontmatter in planner log file that contains a backtick in a field

FILES:
  READ:
    - .wiki/logs/planner-2026-04-13-hallucination-fix-contracts-batch1.md
  WRITE:
    - .wiki/logs/planner-2026-04-13-hallucination-fix-contracts-batch1.md

DONE_WHEN:
  - YAML frontmatter parses without error
  - `python3 -c "import yaml; yaml.safe_load(open('.wiki/logs/planner-2026-04-13-hallucination-fix-contracts-batch1.md').read().split('---')[1])"` succeeds

PROOF_FORMAT:
  Bash command: `python3 -c "import yaml; f=open('.wiki/logs/planner-2026-04-13-hallucination-fix-contracts-batch1.md').read().split('---'); yaml.safe_load(f[1])" 2>&1`
  Expected output: no error

BLOCKER_IF:
  - File doesn't exist or has been deleted

DEPENDS_ON: none

---

## Execution Order
Serial: Contract #1 → Contract #2 → Contract #3 (independent files, sequential for safety)