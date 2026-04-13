---
DEPENDS_ON: "2"
---
# ### CONTRACT #7: Verify and update wiki/_meta/migration_report_2026-04-13.md

WHAT:
  Read migration_report_2026-04-13.md, verify it accurately reflects actual file counts, update with corrected counts if needed.

FILES:
  READ:
    - wiki/_meta/migration_report_2026-04-13.md
    - wiki/concepts/
    - wiki/entities/
    - wiki/projects/
    - wiki/decisions/
  WRITE:
    - wiki/_meta/migration_report_2026-04-13.md (updated if counts wrong)
  RUN:
    - `find wiki/concepts/ -name "*.md" -type f | wc -l`
    - `find wiki/entities/ -name "*.md" -type f | wc -l`
    - `find wiki/projects/ -name "*.md" -type f | wc -l`
    - `find wiki/decisions/ -name "*.md" -type f | wc -l`

DONE_WHEN:
  - migration_report.md exists and has >100 lines
  - Phase 4 table shows article counts matching actual directories
  - Report header shows date 2026-04-13

PROOF_FORMAT:
  Command: `wc -l wiki/_meta/migration_report_2026-04-13.md && grep -c "Phase" wiki/_meta/migration_report_2026-04-13.md`
  Expected: >100 lines, >5 Phase mentions

BLOCKER_IF:
  - migration_report.md does not exist
  - migration_report.md has <50 lines
  - migration_report.md claims "Phase X ✅" but Phase X section missing content

DEPENDS_ON: 6

---

### CONTRACT #8: Verify wiki/INDEX.md has correct structure and wikilinks

WHAT:
  Read INDEX.md and verify it contains required sections (Concepts, Entities, Projects, Decisions, Architecture, Timelines, People, Raw), correct frontmatter, and no broken wikilinks.

FILES:
  READ:
    - wiki/INDEX.md
  WRITE: none
  RUN:
    - `grep -c "^## Concepts" wiki/INDEX.md`
    - `grep -c "^## Entities" wiki/INDEX.md`
    - `grep -c "^## Projects" wiki/INDEX.md`
    - `grep -c "^## Decisions" wiki/INDEX.md`

DONE_WHEN:
  - INDEX.md exists with frontmatter (title, type, status, tags)
  - All 7 required sections present (Concepts, Entities, Projects, Decisions, Architecture, Timelines, People)
  - Total lines >150
  - No literal "MISSING" or "TODO" in content

PROOF_FORMAT:
  Command: `head -12 wiki/INDEX.md && echo "---SECTION COUNT---" && grep "^## " wiki/INDEX.md | wc -l`
  Expected: Frontmatter visible, >6 sections

BLOCKER_IF:
  - INDEX.md missing frontmatter
  - Missing any of the 7 required sections
  - File has <100 lines

DEPENDS_ON: 6

---

### CONTRACT #9: Final comprehensive verification - find all wiki/*.md files

WHAT:
  Run `find wiki/ -name "*.md" -type f` and verify the count matches or exceeds expected minimum of 100 markdown files.

FILES:
  READ:  none
  WRITE: none
  RUN:
    - `find wiki/ -name "*.md" -type f | wc -l`
    - `find wiki/ -name "*.md" -type f > /tmp/wiki_files.txt`
    - `wc -l /tmp/wiki_files.txt`

DONE_WHEN:
  - Total .md files in wiki/ >= 100
  - All expected directories present in output (concepts/, entities/, projects/, decisions/, architecture/, timelines/, people/, raw/, _meta/)
  - No files listed from directories that should not exist

PROOF_FORMAT:
  Command: `find wiki/ -name "*.md" -type f | wc -l`
  Expected: >= 100

BLOCKER_IF:
  - Total .md files < 100
  - Missing any core directory (concepts/, entities/, etc.)
  - _meta/ directory not present

DEPENDS_ON: 7, 8

---

### CONTRACT #10: Create stub files for any wikilink targets that don't exist

WHAT:
  From contracts #5 and #9, identify any wikilink targets that don't exist as files, and create minimal stub .md files with frontmatter for each.

FILES:
  READ:
    - /tmp/wiki_files.txt (created in contract #9)
  WRITE:
    - wiki/[missing-directory]/[missing-file].md (stubs as needed)
  RUN:
    - For each wikilink in key files, verify target exists
    - If target missing, create stub

DONE_WHEN:
  - All wikilinks from intent-routing.md resolve to existing files
  - All wikilinks from memory-architecture.md resolve to existing files
  - All wikilinks from legion-bot.md resolve to existing files
  - Any created stub has valid frontmatter with title, type, status
  - Stub has at least 5 lines of content (including frontmatter)

PROOF_FORMAT:
  Command: `grep -oP '\[\[[^\]]+\]\]' wiki/concepts/intent-routing.md wiki/concepts/memory-architecture.md wiki/projects/legion-bot.md | sort -u | while read link; do target="wiki/${link:2:-2}"; test -f "$target" && echo "OK: $target" || echo "STUB_NEEDED: $target"; done`
  Expected: All show "OK:", none show "STUB_NEEDED:"

BLOCKER_IF:
  - More than 5 stubs needed (indicates systemic link rot)
  - Stub creation fails
  - Stub file still doesn't exist after creation attempt

DEPENDS_ON: 5, 9

---

## Execution Order

Serial (must run in sequence): #6 → #7 → #8 → #9 → #10
- #6 must complete before #7 (compile_state is pre-requisite)
- #7 and #8 can run in parallel after #6
- #9 is final gate before #10
- #10 is final completion check

Final gate (must run last): Contract #10 (stub creation)

---

## Summary

Total contracts: 10 (split into 2 batches of 5)
- Batch 1 (contracts 1-5): Foundation verification + early fixes
  - #1: Verify 5 wiki files exist with valid frontmatter
  - #2: Fix malformed wikilinks in supabase.md + legion-bot.md
  - #3: Add .gitkeep to all 9 wiki/raw/ subdirectories
  - #4: Copy 16 source files to wiki/raw/ with verification
  - #5: Verify wikilinks in 3 concept files resolve

- Batch 2 (contracts 6-10): State verification + completion
  - #6: Update compile_state.json with correct article counts
  - #7: Verify migration_report accuracy
  - #8: Verify INDEX.md structure
  - #9: Final find verification (expect >=100 .md files)
  - #10: Create stubs for any missing wikilink targets

## Anti-Hallucination Strategy

Each contract enforces:
1. READ-BACK after every WRITE (verify file exists at exact path)
2. EXACT counts as proof (not "files created successfully")
3. BLOCKER_IF conditions halt execution instead of continuing on error
4. PROOF_FORMAT shows exact command + expected output
5. No contract says "implement X" without specifying exact file paths
