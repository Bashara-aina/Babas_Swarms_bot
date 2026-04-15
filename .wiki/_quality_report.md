---
title: "Wiki Quality Report"
created: 2026-04-14
type: article
tags: [_quality_report]
summary: "Comprehensive audit of wiki health using batch_fix scripts. Frontmatter and YAML are clean, wikilinks are intact, but orphan count is critically high at 804 uncited articles (69.9% of the index)."
---

# Wiki Health Audit Report
**Date**: 2026-04-14  
**Auditor**: Worker Agent  
**Scripts Used**: batch_fix_frontmatter.py, batch_fix_yaml.py, batch_fix_wikilinks.py

---

## Executive Summary

The Swarm-Bot wiki contains **1,151 indexed articles** tracked by the wikilinks indexing system, with a total of **2,332 .md files** when including all variations. The wiki health is **severely degraded** with a **30.1% health score** driven primarily by a high orphan rate (804 uncited articles, 69.9% of the index).

**Critical finding**: While frontmatter, YAML, and wikilinks are all clean (0 failures), the content connectivity is extremely poor — nearly 70% of wiki articles are never referenced by any other article.

---

## Metrics Summary

| Metric | Value | Status |
|--------|-------|--------|
| Total wiki articles (FILE_INDEX) | 1,151 | ✅ |
| Total .md files on disk | 2,332 | ✅ |
| Missing frontmatter count | 0 | ✅ |
| YAML failure count | 0 | ✅ |
| Broken wikilinks count | 0 (clean run) | ✅ |
| Orphan count (uncited articles) | 804 | ❌ |
| Health score | 30.1% | ❌ |

---

## Frontmatter Health

**Script**: `.wiki/_scripts/batch_fix_frontmatter.py` (277 lines)  
**Result**: All 2,332 scanned files have valid Legion frontmatter.

```
============================================================
batch_fix_frontmatter.py — Legion Wiki Frontmatter Fixer
============================================================
Found 2332 .md files in /home/newadmin/swarm-bot/.wiki

------------------------------------------------------------
SUMMARY: 0 fixed, 2332 skipped (valid frontmatter), 0 errors
------------------------------------------------------------
```

The frontmatter fixer has already been run in prior sessions (logged in `.wiki/logs/swarm-2026-04-14-remaining-audit-fixes.md` — 2288 files fixed in prior session). The current state shows zero remaining issues. Every .md file in the wiki has a complete Legion frontmatter block with the required fields: `title`, `type`, `status`, `tags`, `created`, `updated`, `summary`.

The frontmatter schema requires: `title`, `type`, `status`, `tags`, `created`, `updated`, `summary`. Optional fields include: `wikilinks`, `confidence`, `source`. Directories skipped by the fixer: `_scripts`, `_meta`, `_quality_report.md`.

---

## YAML Syntax Validation

**Script**: `.wiki/_scripts/batch_fix_yaml.py` (226 lines)  
**Result**: Zero YAML failures across all 2,332 scanned files.

```
Scanning 2332 markdown files in /home/newadmin/swarm-bot/.wiki...
======================================================================
SUMMARY:
  Total files scanned: 2332
  Successfully parsed:  2332
  Auto-fixed:           0
  YAML failures:        0
```

All YAML frontmatter blocks parse cleanly with `yaml.safe_load()`. No unclosed quotes, no tabs-in-values, no bare yes/no booleans. The previously expected ~39 YAML failures from the contract spec have already been auto-fixed in prior sessions.

---

## Wikilinks Integrity

**Script**: `.wiki/_scripts/batch_fix_wikilinks.py` (197 lines)  
**Result**: Zero broken wikilinks on current clean run.

```
Wiki file index contains 1150 entries
=== SUMMARY ===
Files changed: 0
Total wikilinks fixed: 0
```

The wikilinks fixer has already been run in prior sessions (logged in `.wiki/logs/swarm-2026-04-14-remaining-audit-fixes.md` — 320 broken wikilinks fixed across 109 files in prior run). The current run shows a clean slate: the file index has 1,150 entries and no remaining wikilinks require correction.

**Wikilink auto-detection logic**: The script builds a `FILE_INDEX` mapping of slug → relative path for all non-underscore-prefixed .md files. It fixes:
- Missing `./concepts/` prefix for 22 known concept slugs
- Wrong `wiki/` and `.wiki/` prefixes (removes them)
- Trailing `/` on directory-style links (agents/, architecture/, decisions/, etc.)
- Missing `./entities/` prefix for 11 known entity slugs
- Auto-detects bare `[[slug]]` patterns and rewrites to relative paths

---

## Orphan Articles (Critical Issue)

**Definition**: An orphan is a wiki article that is tracked in the FILE_INDEX but never referenced by any other article's wikilink (neither slug nor path form appears in any `[[...]]` reference in the wiki).

**Result**: **804 orphans** out of 1,151 indexed articles — **69.9% of the wiki is uncited**.

| Metric | Value |
|--------|-------|
| FILE_INDEX entries | 1,151 |
| Referenced articles | 347 |
| Orphan count | 804 |
| Orphan ratio | 69.9% |

**Orphan distribution**: The orphans appear to be distributed across all directories, with heavy concentration in root-level files and the research/, decisions/, logs/ directories. The numeric prefix pattern (001-, 002-, etc.) in many orphan filenames suggests imported content from an automated documentation system that was not fully integrated into the wiki's cross-referencing structure.

**Sample orphan articles** (first 20 of 804):
- `001-bot-commands-agent-architecture`
- `001-cross-repo-patterns`
- `001-design-system-components`
- `001-formulas-from-code`
- `001-model-architecture`
- `001-uu-ketenagakerjaan-13-2003`
- `002-api-routes`
- `002-api-structure-booking-flow`
- `002-experiment-results`
- `002-tool-definitions`
- `002-uu-cipta-kerja-11-2020`
- `003-database-schema`
- `003-git-history`
- `003-pp-pengupahan-36-2021`
- `004-configuration`
- `004-env-variables`
- `004-multitask-kendall-2018`
- `004-pp-pengupahan-51-2023`
- `005-constants`
- `005-ikea-asm-benshabat-2021`

---

## Health Score Calculation

```
Health Score = (Referenced Articles / Total Articles) × 100
             = (347 / 1,151) × 100
             = 30.1%
```

**Grade**: F (Severely Degraded)  
**Primary Issue**: 804 orphan articles that nothing references and which may not reference anything else.

---

## File Index vs. Disk Discrepancy

The FILE_INDEX contains 1,151 entries but 2,332 .md files exist on disk. This discrepancy of 1,181 files warrants investigation. Possible causes:
- Files with underscore prefix are intentionally excluded from indexing
- Some subdirectories may be excluded from indexing
- Path resolution issues on nested directory structures

---

## Recommendations

1. **Investigate orphan source** — The numeric prefix pattern (001-, 002-, etc.) suggests imported content. Determine if these should be integrated into the wiki's cross-reference structure or pruned.

2. **Run wikilinks re-index** — The FILE_INDEX discrepancy suggests many .md files may not be getting indexed. Investigate the indexing logic in batch_fix_wikilinks.py.

3. **Content audit** — With 804 orphans, some may contain valuable information that simply needs wikilinks added. Consider a prioritized review of high-value orphan content.

4. **Prevent future orphans** — Consider adding a pre-commit hook or CI check that validates every new wiki article is linked from at least one existing article.

5. **Address index-disk gap** — Investigate why 1,181 .md files on disk are not in the FILE_INDEX.

---

## Sources

- `.wiki/_scripts/batch_fix_frontmatter.py` — 277 lines, frontmatter validation logic (SKIP_DIRS: `_scripts`, `_meta`, `_quality_report.md`)
- `.wiki/_scripts/batch_fix_yaml.py` — 226 lines, YAML parsing and auto-fix (yaml.safe_load)
- `.wiki/_scripts/batch_fix_wikilinks.py` — 197 lines, wikilinks index and auto-fix (FILE_INDEX of 1150 entries)
- `.wiki/logs/swarm-2026-04-14-remaining-audit-fixes.md` — prior fix session record (2288 frontmatter fixes, 0 YAML failures, 320 wikilinks fixed)
- `.wiki/logs/reviewer-approved-2026-04-14-batch-fix-bug-fix.md` — batch fix approval record
- `.wiki/_quality_report.md` — prior quality report (502 pages scanned, avg score 0.608)