---
title: Planner Quarantine Revival 2026 04 14
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
summary: '- Total quarantined files: 635 unique entries'
wikilinks: []
confidence: medium
source: research
---
## Plan: Revive Quarantined Wiki Files
Date: 2026-04-14
Type: FILE_OPERATION

## Context Gathered
- Total quarantined files: 635 unique entries
- Files with score > 0.05: 169 (revive candidates)
- Files with score <= 0.05: 466 (remain in quarantine)
- Each quarantined file has YAML frontmatter with `score`, `page_path`, `reason`, `quarantined_at`
- Original location stored in `page_path` field (strip `/home/newadmin/swarm-bot/` prefix to get wiki path)
- Quarantine files are named with encoded original paths + timestamp

## Risk Assessment
1. **Path collision**: Multiple quarantine entries may map to same original path (different timestamps)
2. **Missing directories**: Original wiki subdirectories may not exist when reviving
3. **Overwrite risk**: If original file exists at destination, move will fail
4. **Frontmatter stripping**: Quarantined files have extra frontmatter that must be stripped before restoring

## Approach
1. Phase 1: Build a Python script to analyze and plan revive operations (avoid running arbitrary mv commands)
2. Phase 2: Execute the revival - strip quarantine frontmatter, move files to original locations
3. Phase 3: Verify revived files exist and quarantine is cleaned
4. Phase 4: Report results

## Files to Create
- `.wiki/logs/quarantine-revival-plan.md` - This plan
- `revive_quarantine.py` - Script to execute the revival

## Execution Strategy
- Serial execution due to file move dependencies
- 169 files to revive across various wiki subdirectories
- Need to handle path deduplication (some files appear multiple times with different timestamps)