---
### CONTRACT #1: Verify existing wiki files actually exist and have content

WHAT:
  Read-back verify 5 randomly selected wiki files from different directories to confirm they exist and contain valid frontmatter.

FILES:
  READ:  
    - wiki/concepts/intent-routing.md
    - wiki/concepts/memory-architecture.md
    - wiki/entities/supabase.md
    - wiki/projects/legion-bot.md
    - wiki/decisions/adr-2026-04-12-opencode-over-cursor-for-backend.md
  WRITE: none
  RUN:   none

DONE_WHEN:
  - All 5 files exist at exact paths
  - All 5 files contain "---" frontmatter delimiters on lines 1 and ~12
  - All 5 files contain "title:" field
  - All 5 files have >10 lines of content

PROOF_FORMAT:
  Command: `head -15 wiki/concepts/intent-routing.md && echo "---" && head -15 wiki/entities/supabase.md`
  Expected: Frontmatter visible with title, type, status, tags, created, updated, summary, wikilinks

BLOCKER_IF:
  - Any of the 5 files do not exist at specified path
  - Any file missing frontmatter delimiters "---"
  - Any file with <10 lines

DEPENDS_ON: none

---

### CONTRACT #2: Fix malformed wikilinks in existing wiki files

WHAT:
  Fix missing comma separators in wikilinks arrays in supabase.md and legion-bot.md.

FILES:
  READ:  
    - wiki/entities/supabase.md
    - wiki/projects/legion-bot.md
  WRITE:
    - wiki/entities/supabase.md (corrected wikilinks line)
    - wiki/projects/legion-bot.md (corrected wikilinks line)
  RUN:   none

DONE_WHEN:
  - supabase.md line 9: wikilinks: [[projects/rumahlabuh-com.md]], [[projects/cekwajar-id.md]]
  - legion-bot.md line 9: wikilinks: [[entities/opencode.md]], [[concepts/multi-agent-orchestration.md]], [[architecture/legion-module-map.md]]
  - Both files pass `grep -c "wikilinks:"` showing exactly 1 occurrence each

PROOF_FORMAT:
  Command: `grep "wikilinks:" wiki/entities/supabase.md wiki/projects/legion-bot.md`
  Expected output showing comma-separated wikilinks

BLOCKER_IF:
  - supabase.md wikilinks line not found
  - legion-bot.md wikilinks line not found
  - After edit, wikilinks still missing commas

DEPENDS_ON: 1

---

### CONTRACT #3: Add .gitkeep files to all 9 wiki/raw/ subdirectories

WHAT:
  Create empty .gitkeep file in each of the 9 wiki/raw/ subdirectories to ensure they are preserved in git.

FILES:
  READ:  none
  WRITE:
    - wiki/raw/audits/.gitkeep
    - wiki/raw/changelogs/.gitkeep
    - wiki/raw/configs/.gitkeep
    - wiki/raw/docs/.gitkeep
    - wiki/raw/papers/.gitkeep
    - wiki/raw/prompts/.gitkeep
    - wiki/raw/roadmaps/.gitkeep
    - wiki/raw/skills_ref/.gitkeep
    - wiki/raw/snapshots/.gitkeep
  RUN:   none

DONE_WHEN:
  - All 9 .gitkeep files exist at exact paths
  - Each file is empty (0 bytes)
  - `find wiki/raw/ -name ".gitkeep" | wc -l` returns 9

PROOF_FORMAT:
  Command: `find wiki/raw/ -name ".gitkeep" -empty | wc -l`
  Expected: 9

BLOCKER_IF:
  - Any of the 9 subdirectories missing .gitkeep
  - Any .gitkeep file has non-zero size

DEPENDS_ON: none

---

### CONTRACT #4: Copy 16 source files to wiki/raw/ one at a time with verification

WHAT:
  Copy 16 specified source files to their target locations in wiki/raw/, verifying each file exists at target after copy.

FILES:
  READ:  
    - AGENTS.md (source)
    - SOUL.md (source)
  WRITE:
    - wiki/raw/docs/AGENTS.md (copy 1)
    - wiki/raw/docs/SOUL.md (copy 2)
  RUN:
    - `cp AGENTS.md wiki/raw/docs/AGENTS.md && test -f wiki/raw/docs/AGENTS.md && echo "OK:AGENTS"`
    - `cp SOUL.md wiki/raw/docs/SOUL.md && test -f wiki/raw/docs/SOUL.md && echo "OK:SOUL"`

DONE_WHEN:
  - wiki/raw/docs/AGENTS.md exists and matches source (same line count)
  - wiki/raw/docs/SOUL.md exists and matches source (same line count)
  - Each cp command outputs "OK:" prefix on success
  - Total 14 more files to copy in subsequent calls

PROOF_FORMAT:
  Command: `wc -l wiki/raw/docs/AGENTS.md wiki/raw/docs/SOUL.md`
  Expected: Line counts matching originals

BLOCKER_IF:
  - Copy command does not output "OK:"
  - Target file does not exist after copy
  - Target file size is 0

DEPENDS_ON: none

---

### CONTRACT #5: Verify all wikilinks in 3 concept files resolve to existing files

WHAT:
  Extract all [[wikilinks]] from intent-routing.md, memory-architecture.md, and reasoning-loop.md and verify each linked file exists.

FILES:
  READ:
    - wiki/concepts/intent-routing.md
    - wiki/concepts/memory-architecture.md
    - wiki/concepts/reasoning-loop.md
  WRITE: none
  RUN:
    - `grep -oP '\[\[[^\]]+\]\]' wiki/concepts/intent-routing.md | tr -d '[]'`
    - `find wiki/ -name "*.md" -type f | xargs grep -l "intent-routing"`

DONE_WHEN:
  - All [[wikilinks]] extracted from 3 files
  - Each wikilink target verified to exist at exact path
  - Any missing targets logged to console with "MISSING:" prefix

PROOF_FORMAT:
  Command: `grep -oP '\[\[[^\]]+\]\]' wiki/concepts/intent-routing.md | while read link; do target="${link:2:-2}"; test -f "wiki/$target" && echo "OK: $target" || echo "MISSING: $target"; done`
  Expected: All links show "OK:" prefix, none show "MISSING:"

BLOCKER_IF:
  - Any wikilink target file does not exist
  - Wikilink syntax malformed (should be [[path.md]] not [[path.md|alias]])

DEPENDS_ON: 1

---

## Execution Order

Serial (must run in sequence): #1 → #2 → #3 → #4 → #5
- Contract #1 must pass before #2 (to ensure base files exist)
- Contract #2 must pass before continuing (wikilinks need fixing)
- Contract #3, #4, #5 can proceed in parallel after #1 passes

Final gate (must run last): Contract #5 (wikilink verification is final check)

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Files claimed created but not written | H | H | Read-back verification after every write |
| Malformed wikilinks break graph view | M | M | Contract #2 fixes known issues |
| Missing .gitkeep causes dir deletion | L | M | Contract #3 creates all 9 |
| compile_state.json never updated | H | M | Separate contract after file ops |
| Too many contracts for one batch | M | L | Split into 2 batches of 5 |
