---
title: Planner 2026 04 13 Wiki Enrichment
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
summary: 'Type: RESEARCH / FILE_OPERATION'
wikilinks: []
confidence: medium
source: research
---
## Plan: Wiki Enrichment and Quality Improvement
Date: 2026-04-13
Type: RESEARCH / FILE_OPERATION

## Context Gathered
- SCHEMA.md exists at wiki/SCHEMA.md with full schema definition
- 5 nested directories inside wiki/concepts/ (bpjs-reference, business-research, labor-law-indonesia, market-data-indonesia, tax-indonesia)
- 22 stub articles under 200 words across concepts, entities, projects
- compile_state.json is stale: `{"last_compiled": "1970-01-01T00:00:00Z", "articles": 0}`
- INDEX.md exists with 193 lines but may need rebuild

## Risk Assessment
1. **Schema violations**: 64 files nested in 5 directories need flattening - high effort but straightforward
2. **Stub articles**: 22 files need enrichment - moderate effort
3. **Wikilinks**: Need to scan and fix - may be complex to determine correct targets
4. **Missing articles**: Need to verify which from SCHEMA.md are actually missing

## Approach
Split into 6 contracts as specified:
1. Fix schema violations (flatten 5 nested directories)
2. Enrich stub articles (22 stubs under 200 words)
3. Create/verify missing critical articles (verify against SCHEMA.md entity/project/architecture requirements)
4. Fix broken wikilinks (scan and repair)
5. Rebuild INDEX.md and update compile_state.json
6. Run lint and verify

## Execution Order
- Contracts 1, 2, 3 can run in parallel on different file sets
- Contract 4 depends on contracts 1-3 (targets must exist)
- Contract 5 depends on contracts 1-4 (INDEX must reflect final state)
- Contract 6 runs last as final gate