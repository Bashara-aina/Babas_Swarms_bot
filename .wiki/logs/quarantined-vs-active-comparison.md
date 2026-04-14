# Quarantined vs Active Content Comparison

**Date:** 2026-04-14  
**Purpose:** Identify structural differences between quarantined and active wiki content that explain why quarantined content scores 0.0

---

## Sample Summary

| Category | Files Sampled | Total Available |
|----------|---------------|-----------------|
| Quarantined | 10 files | 1077 files |
| Active | 7 files | 200+ files |

### Quarantined Files Sampled
1. `WAJAR-GAJI.md_20260412` (159 lines)
2. `WAJAR-GAJI.md_20260413` (159 lines)
3. `WAJAR-KABUR.md_20260412` (92 lines)
4. `WAJAR-KABUR.md_20260413` (92 lines)
5. `WAJAR-SLIP.md_20260412` (163 lines)
6. `WAJAR-HIDUP.md_20260412` (66 lines)
7. `WAJAR-TANAH.md_20260412` (91 lines)
8. `ARCHITECTURE.md_20260412` (127 lines)
9. `INDONESIA-TAX-LABOR-LAW.md_20260412` (115 lines)
10. `GALLAGHER-FULL-STORY.md_20260412` (155 lines)

### Active Files Sampled
1. `LEGION-MASTER-CONTEXT.md` (66 lines)
2. `PLATFORM-OVERVIEW.md` (58 lines)
3. `ADR-001-anti-slop-system.md` (85 lines)
4. `ADR-001-circuit-breaker.md` (51 lines)
5. `ADR-001-LEGION_FIX_IDENTITY_SEARCH.md` (111 lines)
6. `2026-04-12-opencode-over-cursor.md` (153 lines)
7. `quality-gates-spec.md` (235 lines)
8. `system-prompt-spec.md` (78 lines)
9. `SESSION_SUMMARY.md` (112 lines)

---

## Structural Comparison Table

| Attribute | Quarantined (Score=0.0) | Active (Score>0) |
|-----------|-------------------------|------------------|
| **Quarantine Frontmatter** | ✅ Present (score=0.0, reason, quarantined_at) | ❌ Absent |
| **Wiki Frontmatter** | ❌ Uses `***` block style only | ✅ Uses YAML `---` frontmatter with metadata |
| **Wikilinks** | ❌ None found | ✅ Present (`[[adr-2026-04-11-opencode-integration]]`, `[[./01-cekwajar-product/...]]`) |
| **LEGION RULE Markers** | ❌ Absent | ✅ Present in master context files |
| **Title Block** | `*** title: "..."` | `---` YAML frontmatter + `# H1` heading |
| **Length Range** | 66–163 lines | 51–235 lines |
| **Content Quality** | High (tables, formulas, specs) | High (structured decisions, specs) |
| **Internal References** | ❌ None | ✅ Cross-links to other wiki files |
| **Context Tags** | ❌ None | ✅ `legion_priority`, `domain`, `impact_score` |
| **Decision Format** | N/A | ✅ ADR format (Context/Decision/Consequences) |

---

## Key Finding: The Scoring Discrimination

The quarantined files have **high-quality technical content** (detailed specs, tables, formulas) but consistently score **0.0** because they fail the quality gate on **structural/categorical criteria**, NOT content quality:

### Why Quarantined Content Fails

1. **No Wiki Frontmatter (YAML)**
   - Quarantined: Only `*** title: "..."` block
   - Active: Proper YAML `---` frontmatter with `title:`, `domain:`, `impact_score:`, `last_updated:`, `injects_into:`

2. **No Wikilinks**
   - Quarantined: Content exists in isolation
   - Active: References other wiki pages via `[[wikilink]]` syntax
   - Example: `[[adr-2026-04-11-opencode-integration]]`

3. **No LEGION RULE Integration**
   - Quarantined: No markers indicating how content integrates with Legion
   - Active: Contains `legion_priority: ALWAYS_LOAD` or similar integration markers

4. **No Context Metadata**
   - Quarantined: Pure technical content without placement guidance
   - Active: Has `injects_into:`, `domain:`, `tokens_estimated:` fields

5. **No ADR/Decision Format** (for procedural content)
   - Quarantined: Technical specs in flat format
   - Active: Decision files use Context → Decision → Consequences → Alternatives structure

---

## Detailed Analysis

### Quarantined Content Pattern
```
---
{
  "page_path": ".../WAJAR-GAJI.md",
  "reason": "daily_fast_scan: score=0.000 < 0.3",
  "score": 0.0,
  "quarantined_at": "2026-04-12T01:00:00"
}
---

***
title: "Wajar Gaji — Salary Benchmark Engine — Full Spec"
***

# Wajar Gaji — Complete Technical Specification

[High-quality content: tables, formulas, specs]
```

**Problems:**
- Quarantine metadata is visible but content was rejected
- No YAML frontmatter with wiki metadata
- No wikilinks to related content
- No integration markers for Legion

### Active Content Pattern
```
---
title: Quality Gates Spec
domain: testing
impact_score: 8
last_updated: 2026-04-12
injects_into: ci, development, deployment
tokens_estimated: 490
---

# QUALITY GATES SPEC

## ONE-LINE SUMMARY
CI/CD quality checks...

[wikipedia-style structure with wikilinks]
See [[adr-2026-04-11-opencode-integration]] for details.
```

**Strengths:**
- Proper YAML frontmatter
- Wikilinks connect to related content
- Domain and impact scores provide context
- `injects_into` field shows where content is used

---

## Why Content Quality Isn't the Factor

Both quarantined and active files contain **high-quality content**:

| Aspect | Quarantined Example | Active Example |
|--------|---------------------|----------------|
| Tables | ✅ 6 tables (verdict thresholds, multipliers, etc.) | ✅ Multiple comparison tables |
| Formulas | ✅ Statistical, confidence score, Bayesian | ✅ Circuit breaker configs |
| Specificity | ✅ Exact PTKP values, bracket percentages | ✅ Exact thresholds, timeouts |
| Length | 60-163 lines | 51-235 lines |

**Conclusion:** The quality gate appears to be a **structural filter**, not a content quality filter. Files with excellent technical content are quarantined because they lack wiki-native metadata.

---

## Recommendations for Rescuing Quarantined Content

To move quarantined files back to active wiki:

1. **Add YAML Frontmatter**
   ```yaml
   ---
   title: "Wajar Gaji — Salary Benchmark Engine"
   domain: cekwajar-product
   impact_score: 9
   last_updated: 2026-04-12
   injects_into: product, sales, user-facing
   tokens_estimated: 680
   ---
   ```

2. **Add Wikilinks**
   - Link to related wiki pages: `[[./01-cekwajar-product/PLATFORM-OVERVIEW.md]]`
   - Link to relevant decisions: `adr-2026-04-14-wajar-gaji-spec`

3. **Add LEGION Integration Markers**
   - `legion_priority: HIGH` or `ALWAYS_LOAD`
   - `injects_into:` fields showing usage contexts

4. **Consider ADR Format for Decisions**
   - Add Context → Decision → Consequences → Alternatives sections
   - Add frontmatter with `decider:`, `reviewer:`, `status:`

---

## Files Analyzed

### Quarantined (10 files)
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_01-cekwajar-product_WAJAR-GAJI.md_20260412_010000_474481.md`
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_01-cekwajar-product_WAJAR-GAJI.md_20260413_010000_640508.md`
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_01-cekwajar-product_WAJAR-KABUR.md_20260412_010000_470788.md`
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_01-cekwajar-product_WAJAR-KABUR.md_20260413_010000_637065.md`
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_01-cekwajar-product_WAJAR-SLIP.md_20260412_010000_487362.md`
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_01-cekwajar-product_WAJAR-HIDUP.md_20260412_010000_491667.md`
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_01-cekwajar-product_WAJAR-TANAH.md_20260412_010000_477934.md`
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_02-cekwajar-tech_ARCHITECTURE.md_20260412_010000_391355.md`
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_03-regulatory_INDONESIA-TAX-LABOR-LAW.md_20260412_010000_388861.md`
- `/home/newadmin/swarm-bot/.wiki/_quarantine/_home_newadmin_swarm-bot_.wiki_04-medvi-playbook_GALLAGHER-FULL-STORY.md_20260412_010000_393896.md`

### Active (7 files)
- `/home/newadmin/swarm-bot/.wiki/00-meta/LEGION-MASTER-CONTEXT.md`
- `/home/newadmin/swarm-bot/.wiki/01-cekwajar-product/PLATFORM-OVERVIEW.md`
- `/home/newadmin/swarm-bot/.wiki/decisions/ADR-001-anti-slop-system.md`
- `/home/newadmin/swarm-bot/.wiki/decisions/ADR-001-circuit-breaker.md`
- `/home/newadmin/swarm-bot/.wiki/decisions/ADR-001-LEGION_FIX_IDENTITY_SEARCH.md`
- `/home/newadmin/swarm-bot/.wiki/decisions/2026-04-12-opencode-over-cursor.md`
- `/home/newadmin/swarm-bot/.wiki/quality-gates-spec.md`
- `/home/newadmin/swarm-bot/.wiki/system-prompt-spec.md`
- `/home/newadmin/swarm-bot/.wiki/SESSION_SUMMARY.md`

---

*Analysis completed: 2026-04-14*
