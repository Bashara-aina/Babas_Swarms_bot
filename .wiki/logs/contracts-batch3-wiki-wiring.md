---
title: "Wiki Wiring Fix — Batch 3"
type: contract
status: active
tags: [wiring-fix, wiki]
created: 2026-04-13
summary: Fix template placeholders, stub links, and code path references
---

## CONTRACT #7: Remove Stub/Test Links

WHAT:
  Remove or replace 12 stub/template links that have no real target

FILES:
  READ:
    - .wiki/decisions/ADR-001-wiki-build-strategy.md
    - .wiki/decisions/fix-kb-duplicate-link-2026-04-13.md
  WRITE:
    - .wiki/decisions/ADR-001-wiki-build-strategy.md
    - .wiki/decisions/fix-kb-duplicate-link-2026-04-13.md

DONE_WHEN:
  - `[[related-page-1]]` removed from ADR-001-wiki-build-strategy.md
  - `[[related-page-2]]` removed from ADR-001-wiki-build-strategy.md
  - `[[link]]`, `[[link1]]`, `[[link2]]`, `[[link3]]` removed from fix-kb-duplicate-link-2026-04-13.md
  - `[[path.md]]` removed or replaced in planner log file
  - `[[slug]]` removed from _meta/MASTER_AUDIT_2026-04-13.md

PROOF_FORMAT:
  Bash command: `grep -E '\[\[(related-page|link\d?|path\.md|slug)\]\]' .wiki/decisions/ .wiki/logs/ .wiki/_meta/ 2>/dev/null`
  Expected output: no matches

BLOCKER_IF:
  - Links are used for actual reference purpose (not just stub)

DEPENDS_ON: none

---

## CONTRACT #8: Remove Ellipsis and Invalid Link Placeholders

WHAT:
  Remove invalid `[[...]]` links that appear in openaugi docs and issue review files

FILES:
  READ:
    - .wiki/tools/openaugi/docs/plans/from-capture-to-jarvis.md
    - .wiki/issues/review-fix-2026-04-13.md
  WRITE:
    - .wiki/tools/openaugi/docs/plans/from-capture-to-jarvis.md
    - .wiki/issues/review-fix-2026-04-13.md

DONE_WHEN:
  - All `[[...]]` links removed from from-capture-to-jarvis.md
  - All `[[...]]` links removed from review-fix-2026-04-13.md

PROOF_FORMAT:
  Bash command: `grep -n '\[\[\.\.\.\]\]' .wiki/tools/openaugi/docs/plans/from-capture-to-jarvis.md .wiki/issues/review-fix-2026-04-13.md`
  Expected output: no matches

BLOCKER_IF:
  - `[[...]]` is used intentionally for ellipsis notation

DEPENDS_ON: none

---

## CONTRACT #9: Fix Code Path References to Code Paths

WHAT:
  Convert 12 wikilinks that reference code modules (core/, handlers/, etc.) to proper code path format or remove them

FILES:
  READ:
    - .wiki/legion/harvester/harvest-system.md
    - .wiki/wisdom/domains/20-ai-agent-design.md
    - .wiki/wisdom/domains/14-ethics-ai-safety.md
    - .wiki/wisdom/domains/02-systems-complexity.md
  WRITE:
    - .wiki/legion/harvester/harvest-system.md
    - .wiki/wisdom/domains/20-ai-agent-design.md
    - .wiki/wisdom/domains/14-ethics-ai-safety.md
    - .wiki/wisdom/domains/02-systems-complexity.md

DONE_WHEN:
  - `[[core/daily_harvester/harvest-pipeline]]` → removed or converted to code reference
  - `[[core/daily_harvester/scorer]]` → removed or converted
  - `[[core/intent-classifier]]` → removed or converted
  - `[[core/intent_router]]` → removed or converted
  - `[[core/memory/memory_manager]]` → removed or converted
  - `[[core/nexus_orchestrator]]` → removed or converted
  - `[[core/soul_engine]]` → removed or converted
  - `[[core/task_orchestrator]]` → removed or converted
  - `[[handlers/harvest-review]]` → removed or converted
  - `[[legion/harvester/harvest-log]]` → removed or converted
  - `[[data/beliefs.json]]` → removed or converted

PROOF_FORMAT:
  Bash command: `grep -E '\[\[(core/|handlers/|legion/harvester/|data/)' .wiki/legion/ .wiki/wisdom/ 2>/dev/null`
  Expected output: no matches for code paths within wisdom/legion context

BLOCKER_IF:
  - Code paths are intentional cross-references

DEPENDS_ON: none

---

## CONTRACT #10: Fix Malformed Popw Decision References

WHAT:
  Fix references to non-existent decision files in popw research project

FILES:
  READ:
    - .wiki/projects/popw-research.md
  WRITE:
    - .wiki/projects/popw-research.md

DONE_WHEN:
  - `[[decisions/popw-conference-strategy]]` → checked if file exists, if not, link removed or replaced
  - `[[decisions/popw-pdd-pivot]]` → checked if file exists, if not, link removed or replaced

PROOF_FORMAT:
  Bash command: `ls .wiki/decisions/popw-* 2>/dev/null || echo "No popw decision files exist"`
  If files exist: links are correct
  If not: links should be removed

BLOCKER_IF:
  - Files exist and links are valid

DEPENDS_ON: none

---

## CONTRACT #11: Fix Missing Decision File Links (ADR prefix)

WHAT:
  Fix 3 broken links to decision files that exist but are linked without `.md` extension

FILES:
  READ:
    - .wiki/architecture/opencode-integration-2026-04-11.md
    - .wiki/decisions/2026-04-12-opencode-over-cursor.md
    - .wiki/timelines/cekwajar-phase-log.md
    - .wiki/timelines/legion-version-history.md
    - .wiki/entities/opencode.md
  WRITE:
    - .wiki/architecture/opencode-integration-2026-04-11.md
    - .wiki/decisions/2026-04-12-opencode-over-cursor.md
    - .wiki/timelines/cekwajar-phase-log.md
    - .wiki/timelines/legion-version-history.md
    - .wiki/entities/opencode.md

DONE_WHEN:
  - `[[adr-2026-04-11-opencode-integration]]` → `[[adr-2026-04-11-opencode-integration]]` (file exists at adr-2026-04-11-opencode-integration.md, link is correct format)
  - `[[adr-2026-04-12-multi-agent-pipeline]]` → same, file exists
  - `[[adr-2026-04-12-opencode-over-cursor-for-backend]]` → same, file exists

PROOF_FORMAT:
  Bash command: `python3 -c "
import os
links = ['adr-2026-04-11-opencode-integration', 'adr-2026-04-12-multi-agent-pipeline', 'adr-2026-04-12-opencode-over-cursor-for-backend']
for link in links:
    path = f'.wiki/decisions/{link}.md'
    print(f'{link}: {\"EXISTS\" if os.path.exists(path) else \"MISSING\"}')"
  Expected: all three show EXISTS

BLOCKER_IF:
  - Decision file doesn't exist

DEPENDS_ON: none

---

## Execution Order
Contracts #7-11 can be parallelized since they operate on different files