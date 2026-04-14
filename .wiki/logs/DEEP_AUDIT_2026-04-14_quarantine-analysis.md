---
title: Deep Audit 2026 04 14 Quarantine Analysis
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
summary: '**Analyst:** Worker Agent'
wikilinks: []
confidence: medium
source: research
---

# DEEP AUDIT: Why Good Information Is Being Quarantined

**Date:** 2026-04-14  
**Analyst:** Worker Agent  
**Contract:** #5 of 5 (Research synthesis)  
**Status:** COMPLETE

---

## Executive Summary

The wiki's quality gate system is systematically rejecting high-value content — including legitimate Indonesian regulatory documents, engineering specifications, and architectural decisions — not due to poor content quality, but due to **structural scoring biases** in `fast_gate()` that favor engineering-documentation patterns over other valid content types.

**Key findings:**

1. **1077 files quarantined** from `.wiki/_quarantine/` directory, representing ~32.8% of total wiki content
2. **Fast_gate has systematic biases** against non-engineering content (regulatory, reference, wisdom)
3. **Maximum achievable score for regulatory content is ~0.50**, falling 0.20 points short of the 0.70 PASS threshold
4. **Content quality is NOT the differentiator** — quarantined files contain tables, formulas, and detailed specs equal to active files
5. **The quarantine is a false positive problem** — good content is being rejected due to structural incompatibility, not quality issues

**Root cause:** The `fast_gate()` heuristic scorer rewards patterns specific to engineering documentation (LEGION RULE markers, Applied to: phrases, wiki-style `[[links]]`) that are inappropriate or inapplicable to other content types like regulatory documents, reference material, and session logs.

---

## 1. Root Cause Analysis: fast_gate Scoring Biases

### 1.1 The Scoring Architecture

The `fast_gate()` function in `core/wiki_quality_gate.py` (lines 84-188) uses a heuristic scoring system with:
- **Maximum possible score:** +0.85 (with LEGION RULE) or +0.70 (without)
- **PASS threshold:** score >= 0.70
- **Quarantine threshold:** score < 0.3 (via deep_gate rejection)

### 1.2 Scoring Bonuses That Bias Against Non-Engineering Content

| Bonus | Points | Content That Gets It | Content That Doesn't |
|-------|--------|---------------------|---------------------|
| `LEGION RULE` | +0.15 | Agent instructions, system docs | Regulatory, reference, wisdom |
| `Applied to:` | +0.10 | ADRs, implementation docs | Regulations, logs, knowledge |
| Wiki links `[[...]]` | +0.05 | Internal wiki cross-references | External sources, URLs |
| Markdown links `[text](url)` | +0.05 | Wiki-style references | Plain URL citations |
| Code blocks | +0.05 | Technical implementations | Prose, tables, formulas |

### 1.3 The Regulatory Content Scoring Gap

Indonesian regulatory content (tax, labor law, BPJS) can achieve at most ~0.50 on fast_gate:
- +0.05 for source URLs (plain URLs, not markdown links)
- +0.10 for word count > 200
- +0.05 for code blocks (TypeScript formulas trigger this)
- +0.10 for markdown headers
- +0.05 for bullet lists
- +0.10 for word count > 50
- +0.05 for word count > 100

**Total: 0.50 maximum vs 0.70 threshold = 0.20 point gap**

This gap exists because:
1. Regulatory content cannot use `LEGION RULE` markers (inappropriate for legal documents)
2. Regulatory content doesn't use `Applied to:` phrase (engineering artifact)
3. Regulations cite sources as plain URLs, not `[[wikilinks]]` or markdown links
4. The scoring has no recognition for `source_type: REGULATION` content type

### 1.4 The deep_gate Misclassification

When content falls below 0.15 on fast_gate, it's routed to `deep_gate` for LLM-based evaluation. The deep_gate prompt assumes all content should be "Legion-specific actionable knowledge." Regulatory content is reference material, not agent instructions — so deep_gate misclassifies it as "generic blog noise" and returns score=0.0.

**Evidence from quarantine metadata:** All sampled regulatory files show `score=0.000` in quarantine frontmatter, confirming deep_gate is returning complete rejection.

---

## 2. Evidence from Quarantine Content Analysis

### 2.1 Quarantine Directory Statistics

| Metric | Value |
|--------|-------|
| Total quarantined files | 1077 |
| Date range | 2026-04-11 to 2026-04-13 |
| Files quarantined on 2026-04-12 | 485 (45.0%) |
| Files quarantined on 2026-04-13 | 381 (35.3%) |

**Interpretation:** Heavy wiki growth produced corresponding quarantine entries. The system is functioning as designed — but the design has a bias problem.

### 2.2 Content Categories in Quarantine

| Category | Count | % of Total | Verdict |
|----------|-------|------------|---------|
| research | 298 | 27.7% | Legitimate deep research, just not currently actionable |
| logs | 167 | 15.5% | Ephemeral session content (appropriate quarantine) |
| knowledge | 163 | 15.1% | Business/technical knowledge, incomplete or generic |
| tools | 87 | 8.1% | Tool docs, often duplicated or superseded |
| decisions (ADR) | 63 | 5.9% | Some have score=0.000 — scoring may not weight decisions correctly |
| wisdom | 41 | 3.8% | General guidance, not project-specific |
| templates | 35 | 3.2% | Generic scaffolding vs specific content |
| candidate | 3 | 0.3% | Experimental drafts needing revision |

### 2.3 Common Quarantine Patterns

1. **Versioned duplicates:** Many files are timestamped versions of the same page (e.g., `WAJAR-GAJI.md_20260412`, `WAJAR-GAJI.md_20260413`). The scan re-scores unchanged files daily.

2. **Domain mismatch:** Content about cekwajar-product, regulatory, Indonesian labor law scores low because the wiki topic is Telegram bot development.

3. **Self-knowledge extraction failures:** Files with "SOURCE NOT FOUND" indicate broken pipelines for cross-repository knowledge extraction.

4. **Security-relevant rejections:** `candidate_browser-agent-architecture.md` was quarantined with score=0.000 because it documents SSRF vulnerabilities — not quality issue, but security review need.

---

## 3. Evidence from Active vs Quarantined Comparison

### 3.1 The Structural Discrimination

Comparing quarantined and active files reveals the discrimination is **structural, not qualitative:**

| Attribute | Quarantined | Active |
|-----------|-------------|--------|
| Wiki Frontmatter | ❌ `*** title: "..."` block style | ✅ YAML `---` frontmatter |
| Wikilinks | ❌ None | ✅ `[[page]]` format |
| LEGION RULE | ❌ Absent | ✅ Present in master context |
| Context Metadata | ❌ None | ✅ `injects_into:`, `domain:` |
| ADR Format | ❌ Flat technical specs | ✅ Context→Decision→Consequences |

### 3.2 Content Quality Is Equal

Both quarantined and active files contain high-quality content:

| Aspect | Quarantined Example | Active Example |
|--------|---------------------|----------------|
| Tables | ✅ 6 tables (verdict thresholds, multipliers) | ✅ Multiple comparison tables |
| Formulas | ✅ Statistical, confidence, Bayesian | ✅ Circuit breaker configs |
| Specificity | ✅ Exact PTKP values, bracket % | ✅ Exact thresholds, timeouts |
| Length | 60-163 lines | 51-235 lines |

**Conclusion:** The quality gate is a structural filter, not a content quality filter. Files with excellent technical content are quarantined because they lack wiki-native metadata.

### 3.3 Specific Examples

**WAJAR-GAJI.md (quarantined):**
- 159 lines of detailed salary benchmark specifications
- Tables for verdict thresholds, multipliers, PTKP values
- TypeScript formulas for salary calculations
- No YAML frontmatter, no wikilinks, no LEGION integration

**ADR-001-circuit-breaker.md (active):**
- 51 lines of circuit breaker implementation
- Proper YAML frontmatter with `domain:`, `impact_score:`
- Wikilinks to related decisions
- LEGION RULE integration markers

The difference is structural compliance, not content quality.

---

## 4. Impact Assessment: What Knowledge Is Lost

### 4.1 Regulatory Content Loss

Indonesian regulatory content being quarantined:
- PTKP 2024 tax tables (PMK 101/2016)
- UU 13/2003 labor law summaries
- BPJS Kesehatan contribution rules
- Indonesia tax and labor law references

**Impact:** cekwajar-product requires these regulations for payroll calculations. Losing them means the system cannot reference official government rules for salary calculations, tax deductions, or labor compliance.

### 4.2 Engineering Knowledge Loss

- Architectural decisions with complete specifications
- Technical specs for platform components
- Product documentation for Indonesian market

**Impact:** Future development loses context for why decisions were made. Architectural debt increases as knowledge is隔离隔离.

### 4.3 Research Content Loss

298 research files quarantined including:
- AI/ML papers (ResNet, FPN, FiLM)
- Academic deep-dives
- Technical research for future reference

**Impact:** Research content that doesn't meet current project relevance is quarantined, but may be needed later. The quarantine is preserving it, but it's not accessible in normal wiki flow.

### 4.4 The False Positive Rate

Based on content analysis, an estimated **40-60% of quarantined content is false positive** — legitimate content rejected due to structural incompatibility, not quality issues.

---

## 5. Specific Recommendations to Fix

### 5.1 Immediate: fast_gate Scoring Adjustments

**Recommendation 1: Add content-type-aware scoring modifier**

In `core/wiki_quality_gate.py`, add recognition for regulatory content:

```python
# Check for regulatory content marker
is_regulatory = re.search(r'source_type:\s*REGULATION', content, re.IGNORECASE) or \
                 re.search(r'authority:\s*OFFICIAL_GOV', content, re.IGNORECASE)

if is_regulatory:
    score += 0.20  # Compensate for inapplicable criteria
```

**Recommendation 2: Add frontmatter validation bonus**

The schema requires YAML frontmatter, but fast_gate doesn't reward it:

```python
has_proper_frontmatter = re.search(r'^---\n', content, re.MULTILINE)
if has_proper_frontmatter:
    score += 0.10
```

**Recommendation 3: Add table structure bonus**

Regulatory and knowledge content is table-heavy:

```python
has_markdown_table = re.search(r'\|.*\|.*\|', content)
if has_markdown_table:
    score += 0.05
```

### 5.2 Medium-term: deep_gate Prompt Refinement

**Recommendation 4: Add content-type context to deep_gate prompt**

The deep_gate prompt should recognize:
- `source_type: REGULATION` content is reference material, not agent instructions
- `source_type: KNOWLEDGE` content has different quality criteria than `AGENT_INSTRUCTION`
- Regulatory content quality = accuracy + completeness, not "actionability"

### 5.3 Long-term: Architectural Changes

**Recommendation 5: Implement category-specific thresholds**

Different content types need different thresholds:

```python
_THRESHOLDS = {
    'research': 0.50,      # Lower for deep research
    'regulatory': 0.50,    # Lower for reference material
    'logs': 0.80,          # Higher for ephemeral content
    'decisions': 0.60,     # ADRs have different format
    'default': 0.70        # Engineering docs
}
```

**Recommendation 6: Add quarantine review workflow**

Weekly review of quarantined content to:
- Identify false positives for re-scoring
- Surface content needing revision
- Track quarantine rate as quality metric

---

## 6. ADR(s) Required for Architectural Changes

### ADR-007: Content-Type-Aware Quality Scoring

**Status:** PROPOSED  
**Date:** 2026-04-14

**Context:**
The current fast_gate scoring system has systematic biases against non-engineering content types. Regulatory documents, reference material, and wisdom content consistently score below the 0.70 PASS threshold despite having equal or superior content quality to active wiki pages.

**Decision:**
Implement content-type-aware scoring in `core/wiki_quality_gate.py`:

1. Detect content type from frontmatter (`source_type`, `authority`, `category`)
2. Apply content-type-specific scoring modifiers
3. Lower thresholds for regulatory and research content (0.50)
4. Raise thresholds for ephemeral content (logs, templates)
5. Add frontmatter validation bonus (+0.10) for proper YAML structure
6. Add table structure bonus (+0.05) for markdown tables

**Consequences:**
- Existing quarantined content can be re-evaluated with new scoring
- Scoring becomes more complex but more accurate
- Category-specific thresholds require frontmatter validation
- Risk: content-type detection could be gamed

**Alternatives Considered:**
- Whitelist directories (rejected: too rigid)
- Remove thresholds (rejected: loses quality control)
- LLM-only scoring (rejected: too slow for daily scans)

---

### ADR-008: deep_gate Content-Type Context

**Status:** PROPOSED  
**Date:** 2026-04-14

**Context:**
The deep_gate LLM prompt assumes all content should be "Legion-specific actionable knowledge." This causes regulatory and reference content to be misclassified as "generic blog noise" and rejected with score=0.0.

**Decision:**
Add content-type context to deep_gate prompt:
- Include `source_type` in prompt context
- Add evaluation criteria for REGULATION content (accuracy, completeness, official citation)
- Add evaluation criteria for KNOWLEDGE content (clarity, structure, applicability)
- Keep existing AGENT_INSTRUCTION criteria for engineering docs

**Consequences:**
- Regulatory content will score based on accuracy, not actionability
- deep_gate processing time increases slightly (more context)
- Consistency between fast_gate and deep_gate improves

---

## 7. Action Items

| Priority | Action | Owner | Timeline |
|----------|--------|-------|----------|
| P0 | Add frontmatter validation bonus to fast_gate | @worker | Immediate |
| P0 | Add content-type detection for REGULATION | @worker | Immediate |
| P0 | Add table structure bonus | @worker | Immediate |
| P1 | Refine deep_gate prompt for content types | @planner | This sprint |
| P1 | Implement category-specific thresholds | @planner | This sprint |
| P2 | Add quarantine review workflow | @planner | Next sprint |
| P2 | Re-evaluate quarantined content with new scoring | @worker | After P0 changes |

---

## 8. Conclusion

The quarantine system is **functioning as designed but the design is flawed**. The fast_gate heuristic rewards engineering-documentation patterns that are inappropriate for other content types. The result is a false positive rate of 40-60% where legitimate, valuable content is quarantined not for quality reasons but for structural incompatibility.

The fix requires:
1. Content-type-aware scoring modifiers (+0.20 for REGULATION content)
2. Frontmatter validation bonus (+0.10 for proper YAML)
3. Table structure recognition (+0.05)
4. deep_gate prompt refinement for content types
5. ADR architectural changes for long-term solution

With these changes, the quarantine rate for false positives should drop from ~50% to ~10-15%, preserving valuable knowledge that is currently being lost.

---

*Analysis synthesized from:*
- `quarantine-content-analysis.md` (235 lines)
- `fastgate-scoring-bias-analysis.md` (164 lines)
- `quarantined-vs-active-comparison.md` (214 lines)
- `regulatory-content-quarantine-analysis.md` (265 lines)

*Report generated: 2026-04-14*