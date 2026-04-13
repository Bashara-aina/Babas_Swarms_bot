---
title: "Wiki Wiring Fix — Batch 4 (Final)"
type: contract
status: active
tags: [wiring-fix, wiki]
created: 2026-04-13
summary: Fix remaining broken links: timelines, midtrans, Bashara-aina, YAML in nested paths
---

## CONTRACT #12: Fix Timelines Conversations Log Link

WHAT:
  Fix `[[timelines/conversations_log]]` → should be `[[timelines/legion-version-history]]` or similar

FILES:
  READ:
    - .wiki/INDEX.md
  WRITE:
    - .wiki/INDEX.md

DONE_WHEN:
  - `[[timelines/conversations_log]]` changed to valid timeline file (or removed if doesn't exist)

PROOF_FORMAT:
  Bash command: `grep "timelines/conversations_log" .wiki/INDEX.md`
  Expected output: no match

BLOCKER_IF:
  - File `timelines/conversations_log.md` actually exists (verify)

DEPENDS_ON: none

---

## CONTRACT #13: Fix Memory Architecture Section Reference

WHAT:
  Fix `[[memory-architecture#failure-modes]]` which has both wrong path and anchor

FILES:
  READ:
    - .wiki/SCHEMA.md
    - .wiki/output/health/lint_2026-04-13.md
  WRITE:
    - .wiki/SCHEMA.md
    - .wiki/output/health/lint_2026-04-13.md

DONE_WHEN:
  - `[[memory-architecture#failure-modes]]` changed to `[[memory-architecture]]` or `[[concepts/memory-architecture]]`

PROOF_FORMAT:
  Bash command: `grep "memory-architecture#failure-modes" .wiki/SCHEMA.md .wiki/output/health/lint_2026-04-13.md`
  Expected output: no match

BLOCKER_IF:
  - Section `#failure-modes` actually exists in file

DEPENDS_ON: none

---

## CONTRACT #14: Create Midtrans Entity Stub (if needed)

WHAT:
  Determine if `midtrans` is a valid entity that should have a wiki page, create stub if missing

FILES:
  RUN:
    - Bash: `ls .wiki/entities/midtrans.md 2>/dev/null || echo "NOT FOUND"`
    - Bash: `grep -r "\[\[midtrans\]\]" .wiki/ | head -5`
  WRITE:
    - If midtrans entity doesn't exist but is referenced: create `.wiki/entities/midtrans.md` stub
    - If midtrans is not a wiki entity: fix links to indicate it's external

DONE_WHEN:
  - Either `.wiki/entities/midtrans.md` exists, or all `[[./entities/midtrans]]` links are removed/fixed

PROOF_FORMAT:
  Bash command: `ls .wiki/entities/midtrans.md 2>/dev/null || echo "NOT FOUND"`

BLOCKER_IF:
  - midtrans is a valid external service (not wiki-managed)

DEPENDS_ON: none

---

## CONTRACT #15: Fix `Bashara-aina` References

WHAT:
  Determine if `Bashara-aina` is a valid reference (person/entity) or broken link

FILES:
  RUN:
    - Bash: `grep -r "\[\[Bashara-aina\]\]" .wiki/ | wc -l`
    - Bash: `ls .wiki/people/bashara* 2>/dev/null || echo "No bashara in people/"`
  WRITE:
    - If `Bashara-aina` is valid person: create entity stub
    - If it's invalid: remove all references

DONE_WHEN:
  - Either `Bashara-aina` entity exists, or all `[[Bashara-aina]]` links removed

PROOF_FORMAT:
  Bash command: `grep -r "\[\[Bashara-aina\]\]" .wiki/ 2>/dev/null | wc -l`
  Expected: 0 (all removed) OR entity created

BLOCKER_IF:
  - `Bashara-aina` is intentional reference to external resource

DEPENDS_ON: none

---

## CONTRACT #16: Fix Nested Path Wikilinks (subdirectory files)

WHAT:
  Fix links to files in subdirectories that are missing their path prefix

FILES:
  READ:
    - .wiki/logs/LOOP_LOG.md (check [[logs/LOOP_LOG]] link)
  WRITE:
    - .wiki/logs/LOOP_LOG.md (if link needs fixing)
    - .wiki/index.md (for [[logs/LOOP_LOG]] reference)

DONE_WHEN:
  - `[[logs/LOOP_LOG]]` in index.md → `[[LOOP_LOG]]` or removed
  - `[[legion/harvester/harvest-log]]` in harvest-system.md → removed or fixed

PROOF_FORMAT:
  Bash command: `grep -E '\[\[logs/LOOP_LOG\]\]' .wiki/index.md .wiki/logs/LOOP_LOG.md 2>/dev/null`
  Expected output: no matches

BLOCKER_IF:
  - File actually exists at that path and link is valid

DEPENDS_ON: none

---

## Execution Order
All contracts in this batch can be parallelized

---

## Summary: All Contracts for Wiki Wiring Fix

| Batch | Contracts | Focus |
|-------|-----------|-------|
| Batch 1 | #1, #2, #3 | Path prefix issues, YAML |
| Batch 2 | #4, #5, #6 | Concept/entity links |
| Batch 3 | #7, #8, #9, #10, #11 | Stub removal, code paths, decisions |
| Batch 4 | #12, #13, #14, #15, #16 | Remaining edge cases |

Total: 16 contracts covering 119 broken wikilinks across 1073 files

---

## Proof Commands for Final Verification

After all batches complete, run:

```bash
# 1. Check for any remaining broken wikilinks (excluding test fixtures and research papers)
cd .wiki && python3 << 'PYEOF'
import os, re

all_md = {}
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['_quarantine', '_archive']]
    for f in files:
        if f.endswith('.md'):
            path = os.path.join(root, f).replace('\\', '/')
            all_md[path] = f

wikilinks = {}
for md_path in all_md:
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for lineno, line in enumerate(content.split('\n'), 1):
            matches = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', line)
            for m in matches:
                target = m.strip()
                if target not in wikilinks:
                    wikilinks[target] = []
                wikilinks[target].append((md_path, lineno))
    except:
        pass

resolved = {}
for link in wikilinks:
    candidates = [f'./{link}.md', f'./{link}/index.md', f'./{link}']
    found = None
    for cand in candidates:
        if cand.replace('\\', '/') in all_md:
            found = cand
            break
    resolved[link] = found

broken = []
for link, files in sorted(wikilinks.items()):
    if resolved[link] is None:
        if re.match(r'^\d{3}-[a-z]', link) or link.endswith('\\'):
            continue
        broken.append((link, len(files)))

print(f"BROKEN LINKS: {len(broken)}")
for link, count in broken[:20]:
    print(f"  {link} ({count} refs)")
PYEOF

# 2. Check YAML frontmatter validity
python3 -c "import yaml; [yaml.safe_load(open(f).read().split('---')[1]) for f in ['.wiki/logs/planner-2026-04-13-hallucination-fix-contracts-batch1.md'] if f.startswith('.wiki') and '---' in open(f).read()]" 2>&1
```