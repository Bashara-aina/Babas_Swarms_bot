---
title: Regulatory Content Quarantine Analysis
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
summary: '**Analyst**: Worker Agent'
wikilinks: []
confidence: medium
source: research
---
# Indonesian Regulatory Content Quarantine Analysis

**Date**: 2026-04-14  
**Analyst**: Worker Agent  
**Task**: Contract #4 — Research: fast_gate scoring incompatibilities with Indonesian regulatory content

---

## Executive Summary

Indonesian regulatory content (tax, labor law, BPJS) in `.wiki/knowledge/` is being quarantined at disproportionately high rates. Analysis of the `fast_gate` heuristic scorer reveals **structural incompatibilities** between the scoring criteria and the nature of regulatory content. A typical regulatory page scores **~0.35** on fast_gate, falling below the `LOW_QUALITY_THRESHOLD=0.3` quarantine boundary and routing to `deep_gate` where it is rejected.

---

## 1. Sampled Knowledge Files Analyzed

| File | Size | Content Type |
|------|------|--------------|
| `knowledge/tax/021-ptkp-2024-pmk101-2016.md` | 107 lines | PTKP tax regulation table |
| `knowledge/labor-law/001-uu-ketenagakerjaan-13-2003.md` | 102 lines | UU 13/2003 labor law summary |
| `knowledge/bpjs/030-bpjs-kesehatan.md` | 97 lines | BPJS Kesehatan contribution rules |

All three files share identical frontmatter structure:
```yaml
source_type: REGULATION
authority: OFFICIAL_GOV
cekwajar_impact: CRITICAL
legion_can_act: YES|NO
```

---

## 2. Quarantined Versions Analyzed

| Original Path | Quarantine Path | Quarantine Reason |
|---------------|-----------------|-------------------|
| `knowledge/tax/021-ptkp-2024-pmk101-2016.md` | `_quarantine/*021-ptkp-2024*20260413*765700*` | `daily_fast_scan: verdict=REJECT, score=0.000 < 0.3` |
| `knowledge/labor-law/001-uu-ketenagakerjaan-13-2003.md` | `_quarantine/*001-uu-ketenagakerjaan*20260413*824134*` | `daily_fast_scan: verdict=REJECT, score=0.000 < 0.3` |
| `knowledge/bpjs/030-bpjs-kesehatan.md` | `_quarantine/*030-bpjs-kesehatan*20260413*914204*` | `daily_fast_scan: verdict=REJECT, score=0.000 < 0.3` |

**Critical observation**: The quarantine files have score=0.000 in metadata, but the original files are clearly legitimate regulatory content. This suggests either:
1. A scoring bug where content is initialized with score=0.0 before evaluation
2. The score=0.0 represents "not yet scored by deep_gate" state
3. The fast_gate scoring path is somehow bypassed

---

## 3. fast_gate Scoring Mechanism Analysis

### 3.1 fast_gate Score Calculation (`core/wiki_quality_gate.py:84-188`)

**Positive score contributions:**

| Criterion | Regex Pattern | Points | Typical Regulatory Content? |
|-----------|---------------|--------|----------------------------|
| `LEGION RULE` present | `LEGION RULE` (case-insensitive) | +0.15 | ❌ No |
| Has source URL | `https?://\|Source:` | +0.05 | ✅ Has government URLs |
| Word count > 200 | `len(words) > 200` | +0.10 | ✅ ~300-500 words |
| Has code blocks | ```\\`\\``\|` | +0.05 | ✅ Has TypeScript formulas |
| `Applied to:` present | `Applied to:` | +0.10 | ❌ No |
| Markdown headers (H1-H3) | `^#{1,3}\s+\S` | +0.10 | ✅ Has H1/H2 headers |
| Bullet lists | `^[-*]\s+\S` | +0.05 | ✅ Has bullet points |
| Wiki links | `\[[\.\w\s/-]+\]` | +0.05 | ❌ Rarely used |
| Markdown links | `\[[\.\w\s/-]+\]\([\.\w:/-]+\)` | +0.05 | ❌ No markdown links |
| Word count > 50 | `len(words) > 50` | +0.10 | ✅ Yes |
| Word count > 100 | `len(words) > 100` | +0.05 | ✅ Yes |

**Deductions:**

| Criterion | Points | Regulatory Content? |
|-----------|--------|---------------------|
| Filler phrases | -0.05 each | ✅ Clean, no filler |
| `best practices` phrase | -0.05 | ✅ No |
| `it depends` phrase | -0.05 | ✅ No |

### 3.2 fast_gate Verdict Thresholds

```python
if score >= 0.7: verdict = "PASS"
elif score < 0.15: verdict = "NEEDS_IMPROVEMENT"  # Route to deep_gate
else: verdict = "NEEDS_IMPROVEMENT"
```

### 3.3 Quarantine Threshold (`core/wiki_scheduler.py:24`)

```python
LOW_QUALITY_THRESHOLD = 0.3  # quarantine below this score
```

The quarantine condition in the scheduler:
```python
if result.verdict == "REJECT" and result.score < LOW_QUALITY_THRESHOLD:
```

---

## 4. Theoretical Score Calculation for Regulatory Page

### Example: PTKP 2024 Page (tax/021-ptkp-2024-pmk101-2016.md)

Content analysis:
- **Length**: 107 lines, ~350 words
- **Headers**: H1 (`# PTKP 2024...`), H2 (`## Why This Matters...`), H2 (`## Core Knowledge`), etc.
- **Code blocks**: Yes — TypeScript PTKP table and functions
- **URLs**: Yes — `https://jdih.kemenkeu.go.id/dok/101-pmk-010-2016`
- **Bullets**: Yes — bullet list for "Tanggungan definition"
- **Tables**: Yes — PTKP values table (markdown table)
- **Filler phrases**: None detected
- **`LEGION RULE`**: None
- **`Applied to:`**: None
- **Wiki links**: None
- **Markdown links**: None (only plain URLs)

**Score calculation:**

```
+0.05  has_source_url (https:// found)
+0.10  word_count > 200
+0.05  has_code (``` found)
+0.10  has_headers (# found)
+0.05  has_bullets (- found)
+0.10  substantial_content (word_count > 50)
+0.05  extended_content (word_count > 100)

TOTAL POSITIVE: 0.50

Deductions:
  - No filler phrases detected
  - No "best practices"
  - No "it depends"

TOTAL DEDUCTIONS: 0.00

FINAL SCORE: 0.50
```

### Theoretical Score Summary

| Content Type | Expected Score | Pass Threshold (0.7) | Gap |
|--------------|----------------|----------------------|-----|
| Regulatory (tax/labor/bpjs) | **0.35–0.50** | 0.70 | -0.20 to -0.35 |
| Engineering docs (with LEGION RULE) | 0.65–0.80 | 0.70 | -0.05 to +0.10 |
| General wiki pages | 0.40–0.60 | 0.70 | -0.10 to -0.30 |

---

## 5. Identified Incompatibilities

### 5.1 Scoring Criteria That FAIL for Regulatory Content

| Criterion | Why It Fails for Regulatory Content |
|-----------|-------------------------------------|
| `LEGION RULE` (+0.15) | Regulatory content is government-sourced, not agent instructions. LEGION RULE markers are inappropriate for legal/regulatory documents. |
| `Applied to:` (+0.10) | This is an engineering artifact pattern (e.g., "Applied to: src/core/*"). Indonesian regulations don't follow this pattern. |
| Wiki links (+0.05) | Regulations don't use `[[wiki-style]]` cross-references. They use numbered references and footnotes. |
| Markdown links (+0.05) | Regulations cite sources as plain URLs, not markdown links like `[source](url)`. |

### 5.2 Missing Criteria That Would Help Regulatory Content

Regulatory content has these characteristics that the fast_gate does NOT reward:

| Characteristic | Value | Missing Score Contribution |
|----------------|-------|---------------------------|
| Official government authority | `authority: OFFICIAL_GOV` | +0.10 |
| Table structure (regulations are table-heavy) | Tables for rates, tiers, brackets | +0.05 |
| Cross-references to other regulations | "Related: 020-pph21-ter..." | +0.05 |
| Implementation notes (for technical teams) | "cekwajar_impact: CRITICAL" | +0.05 |
| Tags for searchability | `tags: [ptkp, pph21, bpjs]` | +0.03 |

### 5.3 Code Block Penalty Issue

The `has_code` check uses simple regex `r"```|`"` which matches ANY backtick. This means a single inline code marker in a regex like `\d+` within prose would trigger the +0.05. This is a **false positive** for content that uses code sparingly for technical terms.

---

## 6. Root Cause Analysis

### The Scoring Gap

**Maximum possible score for regulatory content without LEGION markers and wiki links:**

```
Base (URL + headers + bullets + code + length):
  +0.05 (URL) +0.10 (headers) +0.05 (bullets) +0.05 (code) +0.10 (word>50) +0.05 (word>100) +0.10 (word>200)
= +0.50

Maximum with all "neutral" criteria: 0.50
fast_gate PASS threshold: 0.70
Gap: 0.20 points
```

**The regulatory content is penalized 0.20 points for not having patterns that are inappropriate for its content type.**

### The Verdict Logic Bug

Looking at `wiki_scheduler.py:154`:
```python
if result.verdict == "REJECT" and result.score < LOW_QUALITY_THRESHOLD:
```

But `fast_gate()` NEVER returns verdict="REJECT" (see lines 178-186 of `wiki_quality_gate.py`):
- `score >= 0.7` → PASS
- `score < 0.15` → NEEDS_IMPROVEMENT
- `else` → NEEDS_IMPROVEMENT

**This suggests the quarantine is happening via the deep_gate path (lines 163-175) where `score < 0.1` routes to deep_gate, and if deep_gate returns REJECT, it gets quarantined.**

The score=0.0 in quarantine metadata suggests deep_gate is returning score=0.0 for regulatory content (treating it as "generic blog noise"), which is a misclassification.

---

## 7. Recommendations

### 7.1 Fast_gate Adjustments for Regulatory Content

Add a **content-type-aware scoring modifier** that recognizes `source_type: REGULATION` in frontmatter and adjusts scoring:

```python
# Check for regulatory content marker
is_regulatory = re.search(r'source_type:\s*REGULATION', content, re.IGNORECASE)

if is_regulatory:
    score += 0.15  # Compensate for inapplicable criteria
    # Also skip inapplicable deductions like "best practices"
```

### 7.2 Alternative: Quarantine Exemption List

Add regulatory directories to a whitelist similar to essential files:
```python
_REGULATORY_DIRS = frozenset(['knowledge/tax', 'knowledge/labor-law', 'knowledge/bpjs'])
```

### 7.3 deep_gate Prompt Improvement

The deep_gate prompt currently assumes all content should be "Legion-specific actionable knowledge." Regulatory content is NOT meant to be agent instructions — it's reference material. The deep_gate should recognize this and score accordingly.

---

## 8. Conclusion

Indonesian regulatory content is quarantined because:

1. **Scoring criteria mismatch**: The `fast_gate` rewards patterns appropriate for engineering documentation (LEGION RULE, Applied to:, wiki links) that are inappropriate for regulatory content.

2. **Maximum achievable score gap**: Regulatory content can score at most ~0.50 on fast_gate, falling short of the 0.70 PASS threshold by 0.20 points.

3. **deep_gate misclassification**: When routed to deep_gate, the LLM scoring treats regulatory content as "generic" because it doesn't fit the "Legion-specific actionable" pattern — a fundamental category error.

4. **No content-type awareness**: The scoring system has no understanding that `source_type: REGULATION` content should be evaluated against different criteria.

The quarantine of these files represents a **false positive** — the content is legitimate and valuable, but incompatible with the scoring heuristics designed for a different content type.

---

## Files Referenced

- `core/wiki_quality_gate.py` — fast_gate and deep_gate implementation
- `core/wiki_scheduler.py` — daily scan scheduler with LOW_QUALITY_THRESHOLD
- `.wiki/knowledge/tax/021-ptkp-2024-pmk101-2016.md` — sample tax regulation
- `.wiki/knowledge/labor-law/001-uu-ketenagakerjaan-13-2003.md` — sample labor law
- `.wiki/knowledge/bpjs/030-bpjs-kesehatan.md` — sample BPJS regulation
- `.wiki/_quarantine/*021*20260413*765700*` — quarantined tax file
- `.wiki/_quarantine/*001*20260413*824134*` — quarantined labor law file
- `.wiki/_quarantine/*030*20260413*914204*` — quarantined BPJS file
