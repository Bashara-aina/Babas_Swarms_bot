# fast_gate() Scoring Bias Analysis

**Generated**: 2026-04-14  
**Source**: `core/wiki_quality_gate.py` lines 84–188  
**Purpose**: Identify systematic scoring biases that disadvantage certain content types

---

## Scoring Bonuses (+ points)

| Pattern | Bonus | Line | Regex/Trigger |
|---------|-------|------|----------------|
| `LEGION RULE` | +0.15 | 116-118 | `re.search(r"LEGION RULE", content, re.IGNORECASE)` |
| Source URL | +0.05 | 120-122 | `re.search(r"https?://\|Source:", content)` |
| Word count > 200 | +0.10 | 125-127 | `len(words) > 200` |
| Code blocks | +0.05 | 129-131 | `re.search(r"```\|`", content)` |
| `Applied to:` | +0.10 | 133-135 | `re.search(r"Applied to:", content)` |
| Headers (# h1-h3) | +0.10 | 138-140 | `re.search(r"^#{1,3}\s+\S", content, re.MULTILINE)` |
| Bullets (- or *) | +0.05 | 141-143 | `re.search(r"^[-*]\s+\S", content, re.MULTILINE)` |
| Wiki links `[[...]]` | +0.05 | 144-146 | `re.search(r"\[[\.\w\s/-]+\]", content)` |
| Markdown links | +0.05 | 147-149 | `re.search(r"\[[\.\w\s/-]+\]\([\.\w:/-]+\)", content)` |
| Word count > 50 | +0.10 | 152-154 | `len(words) > 50` |
| Word count > 100 | +0.05 | 155-157 | `len(words) > 100` |

**Maximum possible bonus**: +0.70 (without LEGION RULE) or +0.85 (with LEGION RULE)

---

## Scoring Penalties (- points)

| Pattern | Penalty | Line | Notes |
|---------|---------|------|-------|
| Filler phrases | -0.05 each | 160-164 | 21 phrases in `_FILLER_PHRASES` frozenset |
| `best practices` | -0.05 | 166-168 | Case-insensitive |
| `it depends` | -0.05 | 170-172 | Word-bounded regex |

**FILLER_PHRASES list** (from lines 56-79):
```
it goes without saying, as you know, as we all know, 
it is important to note, needless to say, in order to, 
at the end of the day, the fact of the matter is, 
it should be noted, with that being said, that being said, 
all things considered, in conclusion, to sum up, overall, 
generally speaking, in general, for the most part, 
as previously mentioned, as mentioned earlier
```

---

## Content Types That Score LOW (missing markers)

### Reference/raw content without wikilinks
- Raw documentation imports from external sources
- API documentation without `[[wikilinks]]`
- External paper summaries without `[[...]]` bracket links
- Content that correctly cites with bare URLs (penalized for not being `[[bracket links]]`)

**Why**: No `[[wikilinks]]` → -0.05, no `# headers` → -0.10, no bullets → -0.05

### Short technical content (50-100 words)
- Concise implementation notes
- Quick reference cards
- Bug fix records
- Error message guides

**Why**: `word_count > 200` bonus (+0.10) requires 200+ words; below 50 words also miss `substantial_content` bonus (+0.10)

### Structured data without narrative
- JSON/XML schema documentation
- Configuration file reference
- CSV data tables
- Database schema descriptions

**Why**: No `# headers`, no `- bullets` (data lines don't match `^[-*]\s+\S`), no prose narrative

### Decision records without "Applied to:"
- ADRs that don't use "Applied to:" phrasing
- Short decision notes (<200 words)
- Context-only decisions

**Why**: `Applied to:` marker gives +0.10; missing it is a significant gap

---

## Content Types That Are PENALIZED Despite Being Valid

### Well-written explanatory content with qualified statements
- Content containing `it depends` as a legitimate technical qualifier
- Comparative analysis explaining tradeoffs ("it depends on your use case")
- Nuanced technical explanations that correctly acknowledge variance

**Why**: `it depends` regex `\bit depends\b` triggers -0.05 even in appropriate contexts

### Reference material using "best practices" legitimately
- Standard engineering guidance that genuinely IS best practice
- Documentation that correctly identifies industry standards
- Training materials on recommended approaches

**Why**: `best practices` string triggers -0.05 regardless of context legitimacy

### Content using filler for stylistic flow
- Formal documentation using phrases like "it should be noted"
- Professional writing using "at the end of the day" for rhetorical structure
- Legacy content migrated from formal sources

**Why**: 21 filler phrases each deduct -0.05; using 3 filler phrases = -0.15 penalty

### Short valid content (50-100 words) with valid information
- Quick reference entries
- Single-sentence TL;DR summaries
- Minimal viable documentation for simple concepts

**Why**: Falls below word count thresholds; misses both `>50` (+0.10) and `>200` (+0.10) bonuses; maximum possible score is ~0.45 without these

---

## Threshold Analysis

| Score Range | Verdict | Verdict Logic |
|-------------|---------|---------------|
| score >= 0.70 | PASS | Good quality |
| score < 0.15 | NEEDS_IMPROVEMENT | Stricter threshold for truly broken content |
| 0.15 <= score < 0.70 | NEEDS_IMPROVEMENT | Route to deep_gate |

**Example maximum scores for disadvantaged content types**:

| Content Type | Max Possible Score | Notes |
|--------------|-------------------|-------|
| Short paragraph (30 words, no markers) | ~0.10 | REJECT on length (<50 chars) or NEEDS_IMPROVEMENT |
| Reference doc (150 words, URL, no markdown) | ~0.20 | URL +0.05, >50 words +0.10, >100 words +0.05 = 0.20 |
| ADR without "Applied to:" (180 words) | ~0.30 | 180 words (+0.10+0.05+0.05), headers +0.10, bullets +0.05 = 0.30 |
| Tutorial without code (300 words, headers, bullets) | ~0.30 | Headers +0.10, bullets +0.05, >200 words +0.10, >100 +0.05 = 0.30 |

---

## Schema Alignment Issues

Per `SCHEMA.md`, the Karpathy KB Pattern expects:
- TL;DR summary first
- Valid frontmatter (YAML)
- Wikilinks to related concepts
- Synthesized content, not raw dumps

**fast_gate bias against SCHEMA**:
1. `Applied to:` bonus (+0.10) is a specific phrase format not required by schema
2. No frontmatter validation bonus — presence/absence of frontmatter doesn't affect score
3. No TL;DR detection bonus
4. Code bonus (+0.05) but no bonus for narrative synthesis
5. Wikilink bonus requires `[[...]]` format but SCHEMA allows both `[[page]]` and bare `[[./path]]` — the regex `\[[\.\w\s/-]+\]` misses bare wikilinks without path

---

## Recommendations

1. **Add frontmatter detection bonus** (+0.05–0.10) — valid YAML frontmatter is a core schema requirement
2. **Add TL;DR detection bonus** (+0.05) — first paragraph containing "TL;DR" or summary is a schema pattern
3. **Refine "it depends" penalty** — only penalize standalone "it depends" without context, not legitimate technical qualifiers
4. **Add "Applied to:" as optional** — make it a structure bonus rather than a hard bonus; other ADR formats are valid
5. **Fix wikilink regex** — current `\[\./\.\.\]` pattern misses bare `[[page]]` wikilinks
6. **Add short-content carve-out** — content under 100 words that's well-structured (headers, code, bullets) should pass

---

*Analysis performed on fast_gate() heuristic gate — see `core/wiki_quality_gate.py` lines 84-188 for full implementation*