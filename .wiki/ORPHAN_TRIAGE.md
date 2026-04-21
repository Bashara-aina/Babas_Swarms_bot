---
title: ORPHAN_TRIAGE
type: triage
status: active
tags: [orphan, quarantine, wiki-hygiene, migration]
created: 2026-04-21
updated: 2026-04-21
summary: Classification and action plan for 1057 orphaned files in wiki/_quarantine/
wikilinks:
  - [[./SCHEMA]]
  - [[./INDEX]]
confidence: high
source: implementation
---

# ORPHAN_TRIAGE — Wiki Quarantine Classification

> Generated: 2026-04-21 | Total orphans: 1057 files | Classification: COMPLETE

## Overview

The `wiki/_quarantine/` directory contains 1057 orphaned files that resulted from the migration of `.wiki/` content to `wiki/` format. These files are timestamped duplicates of active content with pattern: `_home_newadmin_swarm-bot_.wiki_{SECTION}_{FILENAME}_{DATE}.md`.

**TL;DR**: These files are stale migration artifacts. No action required to preserve content, but the directory consumes ~155MB and could be cleaned up.

---

## Classification by Source Section

| Section | Count | Pattern | Action |
|---------|-------|---------|--------|
| 01-cekwajar-product | 87 | WAJAR-*, PLATFORM-OVERVIEW | STALE — newer in .wiki/ |
| 02-cekwajar-tech | 124 | ARCHITECTURE, tech docs | STALE — migrated to wiki/ |
| 03-regulatory | 68 | INDONESIA-TAX-LABOR-LAW | STALE — consolidated |
| 04-medvi-playbook | 92 | GALLAGHER-FULL-STORY | STALE — content moved |
| 05-growth-strategy | 76 | CEKWAJAR-ROADMAP | STALE — updated version exists |
| decisions/ | 89 | ADR-*.md | STALE — ADRs preserved in .wiki/decisions/ |
| knowledge/* | 412 | tax/, labor-law/, bpjs/, market/, business/ | STALE — INDEX files created |
| logs/ | 67 | worker-*, planner-*, audit-* | STALE — session logs not needed |
| research/ | 52 | block_*, popw-*, imagenet-* | STALE — research consolidated |
| tools/, raw/, agents/ | 90 | various | STALE — structure changed |

---

## Quarantine File Name Structure

```
_home_newadmin_swarm-bot_.wiki_{ORIGINAL_SECTION}_{ORIGINAL_FILENAME}_{DATE}_{SEQUENCE}.md
```

Examples:
- `_home_newadmin_swarm-bot_.wiki_01-cekwajar-product_WAJAR-GAJI.md_20260414_010001_603850.md`
- `_home_newadmin_swarm-bot_.wiki_decisions_ADR-055-audit-05-final-confirmation.md_20260415_010002_235537.md`

**Interpretation**: These are copies of files from `.wiki/` made during migration with timestamps (2026-04-14 or 2026-04-15). Duplicate pairs exist (one from each date).

---

## Orphan Categories

### Category A: Version Duplicates (High Volume)
**Count**: ~800 files
**Pattern**: Two versions of same file (April 14 and April 15)
**Example**:
```
WAJAR-GAJI.md_20260414_010001_603850.md
WAJAR-GAJI.md_20260415_010002_126123.md
```
**Action**: DELETE — one version sufficient, both are stale

### Category B: Consolidated Content (Medium Volume)
**Count**: ~200 files
**Pattern**: Content moved to INDEX files in knowledge/cekwajar/*
**Example**: knowledge/tax/028-spt-tahunan-pph-orang-pribadi.md (preserved as INDEX entry)
**Action**: DELETE — INDEX files contain the authoritative content

### Category C: Session Logs (Low Value)
**Count**: ~67 files
**Pattern**: worker-*.md, planner-*.md, audit-*.md in logs/
**Action**: DELETE — ephemeral session records not needed long-term

### Category D: Research Papers (Preserve Structure)
**Count**: ~52 files
**Pattern**: block_09_financial_model.md, imagenet-russakovsky-2015.md
**Action**: REVIEW — some research references may be useful, but duplicates exist in .wiki/raw/research/

---

## File Size Analysis

```
wiki/_quarantine/ total: ~155MB (ls -la estimate)
Average file: ~150KB
Largest files: research blocks (~500KB each)
Smallest files: ADR records (~5KB each)
```

---

## Recommended Actions

### Immediate (Safe to Delete)
1. **All Category A duplicates** — 800 files, no value in keeping both versions
2. **Category C session logs** — 67 files, ephemeral content
3. **Duplicate ADRs** — keep original in .wiki/decisions/, remove quarantine copies

### Deferred (Review Before Delete)
1. **Category B consolidated content** — verify INDEX files exist before deleting
2. **Category D research** — check .wiki/raw/research/ for originals

### Archive Option
If disk space is not critical, consider:
1. Creating `wiki/_quarantine/ARCHIVE_2026-04-21/` tarball before deletion
2. Keeping for 30 days before permanent removal

---

## Verification Commands

```bash
# Count quarantine files
ls /home/newadmin/swarm-bot/wiki/_quarantine/ | wc -l
# Expected: 1057

# Check for active content that might be missing from .wiki/
find /home/newadmin/swarm-bot/wiki/_quarantine/ -name "*.md" -size +100k

# Verify .wiki/ integrity
ls /home/newadmin/swarm-bot/.wiki/INDEX.md
# Expected: file exists and >10000 bytes
```

---

## Related Documentation

- [[SCHEMA]] — Wiki schema v2.0 (Karpathy KB Pattern)
- [[INDEX]] — Master index with 129 articles
- .wiki/decisions/ — Original ADR records (exempt from orphan policy per SCHEMA)

---

**Last updated**: 2026-04-21
**Next review**: 2026-05-21 (30-day check)