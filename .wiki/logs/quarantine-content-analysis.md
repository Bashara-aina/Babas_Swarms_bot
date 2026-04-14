---
title: "Quarantine Content Analysis"
date: 2026-04-14
status: active
category: wiki-maintenance
tags: [quarantine, wiki, content-analysis, quality-gate]
---

# Quarantine Content Analysis

**Date:** 2026-04-14  
**Analyzer:** @worker  
**Source:** `.wiki/_quarantine/` directory  
**Compile State:** 2211 articles, 309 without frontmatter, 1077 in quarantine

---

## Executive Summary

The quarantine directory contains **1077 files** that were rejected by the `daily_fast_scan` quality gate (score < 0.3). These are not deleted files — they are preserved for review because they represent rejected content that may still have value after revision.

**Top-level finding:** The quarantine is a **normal byproduct of active wiki growth** — 485 files quarantined on 2026-04-12 alone during heavy harvest sessions. The system correctly rejects low-quality content while preserving it for potential recovery.

---

## 1. Quarantine Directory Stats

| Metric | Value |
|--------|-------|
| Total quarantined files | 1077 |
| Date range | 2026-04-11 to 2026-04-13 |
| Files from 2026-04-11 | 212 (19.7%) |
| Files from 2026-04-12 | 485 (45.0%) |
| Files from 2026-04-13 | 381 (35.3%) |

**Interpretation:** Heavy wiki growth activity on April 12 (485 files) produced corresponding quarantine entries. This is proportional — higher harvest = higher quarantine count.

---

## 2. Content Categories by Source Directory

| Rank | Category | Count | % of Total |
|------|----------|-------|------------|
| 1 | research | 298 | 27.7% |
| 2 | logs | 167 | 15.5% |
| 3 | knowledge | 163 | 15.1% |
| 4 | tools | 87 | 8.1% |
| 5 | issues | 69 | 6.4% |
| 6 | decisions (ADR) | 63 | 5.9% |
| 7 | wisdom | 41 | 3.8% |
| 8 | templates | 35 | 3.2% |
| 9 | self-knowledge | 21 | 1.9% |
| 10 | founder-mindset | 21 | 1.9% |
| 11 | indexes | 15 | 1.4% |
| 12 | profiles | 12 | 1.1% |
| 13 | cekwajar-product | 12 | 1.1% |
| 14 | legion | 8 | 0.7% |
| 15 | projects | 7 | 0.7% |
| 16 | architecture | 7 | 0.7% |
| 17 | workflows | 3 | 0.3% |
| 18 | candidate | 3 | 0.3% |
| 19 | cekwajar-tech | 2 | 0.2% |
| 20 | regulatory | 2 | 0.2% |

---

## 3. Quarantine Rejection Patterns

### 3.1 Rejection Reason Format
All quarantined files follow this pattern in their frontmatter:
```yaml
{
  "page_path": "/path/to/original/file.md",
  "reason": "daily_fast_scan: score=X.XXX < 0.3",
  "score": X.XXX,
  "quarantined_at": "YYYY-MM-DDTHH:MM:SS.ssssss"
}
```

### 3.2 Score Distribution Observations
- **score=0.000**: Complete rejection — content found worthless or harmful
- **score=0.050 to 0.150**: Low quality — content exists but below threshold
- **score=0.150**: Most common threshold — borderline quality

### 3.3 Content-Type Specific Patterns

**Research (298 files):**
- Heavy content: AI/ML papers (ResNet, FPN, FiLM, etc.)
- Low scores often due to: narrow relevance to current project scope
- Example: `research/001-resnet-he-2016.md` quarantined with score=0.150 (legitimate deep research, just not currently actionable)

**Logs (167 files):**
- Session completion logs, planner/worker cycle reports
- Quarantine reason: ephemeral content with limited future reference value
- Example: `logs/2026-04-11-coding-references.md` — perfectly formatted but deemed session-specific

**Knowledge (163 files):**
- Business/technical knowledge files
- Lower scores often due to: incomplete coverage or generic content
- Example: `self-knowledge/cekwajar/001-formulas-from-code.md` — "SOURCE NOT FOUND" content

**Tools (87 files):**
- Tool documentation and integration guides
- Often quarantined for: duplication or superseded by newer versions

**Decisions/ADR (63 files):**
- Architecture Decision Records
- Some have score=0.000 (complete rejection)
- Pattern: ADRs with specific implementations tend to score higher than conceptual ones

**Candidate (3 files):**
- `candidate_browser-agent-architecture.md` — score=0.000, SSRF security concern
- `candidate_video-url-pipeline.md` — rejected
- `candidate_web-scraping-patterns.md` — rejected
- **Pattern:** Candidate files are experimental drafts that may become real wiki pages after revision

**Templates (35 files):**
- Claude Code, Codex, Cursor templates
- Low scores due to: generic scaffolding vs. specific project content

**Wisdom (41 files):**
- Philosophical/practical wisdom documents (chain-of-thought, resilience, etc.)
- Generally scores around 0.100-0.150
- **Pattern:** Wisdom content scores low because it's general guidance, not project-specific

---

## 4. Common Patterns in Quarantined Content

### Pattern 1: Daily Fast Scan Bulk Rejections
The system runs `daily_fast_scan` which rejects files with score < 0.3. This creates batch quarantines:
- 2026-04-12: 485 files quarantined in single batch
- 2026-04-13: 381 files quarantined in single batch
- **This is working as intended** — the system correctly identifies low-quality content

### Pattern 2: Versioned Duplicates
Many files are timestamped versions of the same page:
```
PLATFORM-OVERVIEW.md_20260412_010000_467311.md
PLATFORM-OVERVIEW.md_20260413_010000_632245.md
WAJAR-GAJI.md_20260412_010000_474481.md
WAJAR-GAJI.md_20260413_010000_640508.md
```
**Pattern:** Each day's scan creates a new version of the file, even if content hasn't changed. This may indicate the scan is re-scoring unchanged files.

### Pattern 3: Domain-Specific Content Failure
Content about specific domains (cekwajar-product, regulatory, tech) scores low because:
- The wiki is about a Telegram bot, not Indonesian payroll systems
- Content mismatch: articles about Indonesian labor law are not relevant to bot development

### Pattern 4: Self-Knowledge Extraction Failures
```yaml
page_path: "self-knowledge/cekwajar/001-formulas-from-code.md"
reason: "NOT-FOUND — source code not present in repository"
```
**Pattern:** Self-knowledge extraction attempts fail when the source (cekwajar codebase) doesn't exist in this repo.

### Pattern 5: Security-Relevant Rejections
`candidate_browser-agent-architecture.md` with score=0.000 explicitly documents SSRF vulnerabilities:
> **Finding: NO SSRF PROTECTION EXISTS anywhere in browser_agent.py**

This was quarantined not for quality but for security review — the file documents risks that need addressing.

---

## 5. Category-by-Category Analysis

### Research (298 quarantined)
- **Content type:** Academic papers, technical deep-dives
- **Why quarantined:** Score < 0.3 threshold
- **Verdict:** Legitimate research content that just doesn't meet current project relevance threshold. May need threshold adjustment for research documents.

### Logs (167 quarantined)
- **Content type:** Session logs, completion reports, audit trails
- **Why quarantined:** Ephemeral by nature
- **Verdict:** Appropriate quarantine — logs are session-specific and don't need permanent wiki presence

### Knowledge (163 quarantined)
- **Content type:** Business/technical knowledge files
- **Why quarantined:** Incomplete or generic content
- **Verdict:** Some files are stubs (309 files systemwide have no frontmatter), others are just below threshold

### Decisions (63 quarantined)
- **Content type:** Architecture Decision Records
- **Why quarantined:** Mixed — some score 0.000, others 0.150
- **Verdict:** ADRs should score higher — need to check if scoring algorithm weights decision content correctly

### Candidate (3 quarantined)
- **Content type:** Experimental drafts
- **Why quarantined:** Not ready for prime time
- **Verdict:** Correct quarantine — candidate files need revision before promotion to main wiki

---

## 6. Recommendations

### 6.1 For System Configuration
1. **Consider adjusting research category threshold** — research papers (ResNet, etc.) score 0.150 despite being well-formatted. The scoring may not account for long-form technical content.

2. **Add category-specific thresholds** — logs and templates could have higher thresholds, while research could be lower.

3. **Add "candidate" promotion workflow** — candidate files quarantined with score 0.000 (like browser-agent-architecture) should be reviewed and potentially promoted after revision.

### 6.2 For Content Cleanup
1. **Purge versioned duplicates** — many files are identical copies from different dates. The wiki loader could deduplicate.

2. **Review self-knowledge failures** — the "NOT-FOUND" extraction failures suggest broken pipelines that should be fixed or removed.

3. **Handle logs more aggressively** — logs are ephemeral. Consider a retention policy (7 days?) rather than indefinite quarantine.

### 6.3 For Wiki Health
1. **Address the 309 no-frontmatter files** — these are stubs that need completion or merging.

2. **Review orphaned content** — 410 orphans detected (though "real orphans" = 0, so links may still be valid).

3. **Consider quarantine review sessions** — weekly review of quarantined content could surface content that needs revision and promotion.

---

## 7. Conclusion

The quarantine directory is **functioning correctly** — it's capturing low-quality content before it pollutes the wiki. The 1077 quarantined files represent a small fraction of total wiki activity (1077 quarantine vs 2211 articles = 32.8% quarantine rate, but this includes versioned files from heavy harvest days).

**Key insight:** High quarantine counts on harvest days (485 on 2026-04-12) indicate the system is correctly filtering content during active growth phases.

**Action items:**
1. Review candidate files for potential promotion after revision
2. Consider adjusting research category scoring thresholds
3. Implement logs retention policy
4. Fix or remove broken self-knowledge extraction pipelines

---

## 8. Sample File Anthology (25 Examples)

Below are 25 actual quarantined files sampled from the 1077 total, showing filename, source category, score, and likely quarantine reason.

### 8.1 Research Papers (score=0.000 — complete rejection, narrow relevance)

| # | Filename | Category | Score | Likely Quarantine Reason |
|---|----------|----------|-------|--------------------------|
| 1 | `research/009-hrnet-wang-2020.md` | research | 0.000 | Academic paper on HRNet visual recognition — legitimate content but too domain-specific for Telegram bot context |
| 2 | `research/061-pointly-supervised-cheng-2022.md` | research | 0.000 | CVPR 2022 paper on instance segmentation via point annotations — narrow computer vision relevance |
| 3 | `research/071-slowfast-feichtenhofer-2019.md` | research | 0.000 | ICCV 2019 dual-path video model — temporal modeling research outside current project scope |
| 4 | `research/097-attention-vaswani-2017.md` | research | 0.000 | "Attention Is All You Need" — famous paper but too foundational/generic to score above threshold |
| 5 | `research/026-imtl-liu-2021.md` | research | 0.150 | Impartial multi-task learning paper — POPW protocol tier-3 content, borderline score |
| 6 | `research/034-mtgib-unet-li-2025.md` | research | 0.000 | 2025 MTGIB U-Net paper — very recent, limited citations, low relevance |
| 7 | `research/thesis-context.md` | research | 0.150 | WorkerNet/POPW thesis context — useful internal document but scored 0.150 (borderline) |
| 8 | `research/ai-dev-patterns/README.md` | research | 0.100 | Curated list of 522+ AI dev tools — too generic/encyclopedic, not project-specific |

**Pattern:** Research files score 0.000 when content is academically valid but not actionable for the current Telegram bot project. The scoring may not account for the value of foundational research.

### 8.2 Logs (score=0.000 — ephemeral session content)

| # | Filename | Category | Score | Likely Quarantine Reason |
|---|----------|----------|-------|--------------------------|
| 9 | `logs/audit-01-progress.md` | logs | 0.000 | LEGION AUDIT 01 handler registration — perfectly formatted but session-specific audit trail |
| 10 | `logs/worker-tax-progress.md` | logs | 0.179 | Worker task progress — ephemeral session tracking, limited future value |
| 11 | `logs/worker-fix-whitespace-bug-2026-04-12.md` | logs | 0.000 | Bug fix session log — single-incident debugging notes, not permanent knowledge |
| 12 | `logs/worker_concerns567.md` | logs | 0.000 | Worker concerns during session — informal session metadata |

**Pattern:** Logs are quarantined because they are session-scoped. Even well-formatted logs are inherently ephemeral.

### 8.3 Knowledge — Labor Law & Business (score=0.000 — domain mismatch)

| # | Filename | Category | Score | Likely Quarantine Reason |
|---|----------|----------|-------|--------------------------|
| 13 | `knowledge/labor-law/012-aturan-cuti.md` | knowledge | 0.000 | Indonesian leave entitlement regulations — content is accurate but wrong domain for bot wiki |
| 14 | `knowledge/business/065-levelsio-playbook.md` | knowledge | 0.000 | Pieter Levels solo founder playbook — general business inspiration, not technical bot content |
| 15 | `knowledge/engineering/086-nextjs14-app-router-saas.md` | knowledge | 0.000 | Next.js SaaS architecture patterns — engineering knowledge but outside Telegram bot scope |

**Pattern:** Knowledge about Indonesian payroll, solo founder playbooks, or Next.js SaaS is high-quality but fails relevance scoring because the wiki focuses on Telegram bot development, not general Indonesian business or web frameworks.

### 8.4 Decisions/ADRs (score=0.000 to 0.150 — mixed)

| # | Filename | Category | Score | Likely Quarantine Reason |
|---|----------|----------|-------|--------------------------|
| 16 | `decisions/ADR-SELF-KNOWLEDGE-001.md` | decisions | 0.150 | Master architecture overview ADR — borderline score, content is valid but perhaps too meta |
| 17 | `decisions/ADR-001-wiki-build-strategy.md` | decisions | 0.000 | cekwajar.id salary transparency wiki strategy — ADR about wrong project (cekwajar, not swarm-bot) |
| 18 | `decisions/ADR-001-coding-references-pipeline.md` | decisions | 0.000 | Coding references pipeline — ADR with score 0.000 despite being well-structured |

**Pattern:** ADRs that reference cekwajar.id specifically get score=0.000 because the wiki context is swarm-bot. ADRs about the current project should score higher.

### 8.5 Tools (score=0.000 to 0.200)

| # | Filename | Category | Score | Likely Quarantine Reason |
|---|----------|----------|-------|--------------------------|
| 19 | `tools/MINIMAX-MCP-GUIDE.md` | tools | 0.200 | MiniMax MCP usage guide — tool documentation but likely superseded or duplicated |
| 20 | `tools/openaugi/docs/plans/capture-tag-stream-loop.md` | tools | 0.000 | OpenAugi plan draft — draft status, not finalized content |
| 21 | `tools/openaugi/docs/plans/done/zzz-instructions.md` | tools | 0.000 | Inline block instructions draft — internal skill scaffolding, not user-facing docs |

**Pattern:** Tool docs in draft status or superseded by newer versions score 0.000.

### 8.6 Wisdom, Profiles, Templates & Other

| # | Filename | Category | Score | Likely Quarantine Reason |
|---|----------|----------|-------|--------------------------|
| 22 | `wisdom/domains/08-psychology-human-behavior.md` | wisdom | 0.200 | Kahneman "Thinking Fast and Slow" summary — general wisdom, not project-specific |
| 23 | `profiles/bashara-technical.md` | profiles | 0.200 | Bashara technical profile — personal profile, ephemeral or redundant with BASHARA-MASTER-PROFILE |
| 24 | `templates/Home Page.md` | templates | 0.000 | Generic Home Page template — bare-bones scaffolding, no project-specific content |
| 25 | `legion/refactoring-2026-04-11.md` | legion | 0.000 | Legion refactoring log — session-specific refactoring notes, not permanent architecture docs |
| 26 | `intent-routing-map.md` | root | 0.000 | Intent routing configuration — too generic/operational, likely superseded |
| 27 | `quality-gates-spec.md` | root | 0.000 | Quality gates specification — internal spec document, not wiki content |

**Pattern:** Wisdom content scores low (0.200) because it's general life/business guidance. Templates fail for lack of project-specific content. Operational docs (intent-routing, quality-gates) are too meta or superseded.

### 8.7 Score=0.000 Anomaly Note

The most common anomaly in the sample set: files with **score=0.000** that contain genuinely useful content:
- `research/097-attention-vaswani-2017.md` — the foundational Transformers paper
- `decisions/ADR-001-wiki-build-strategy.md` — a well-formed ADR about wiki building

The score=0.000 is not a quality judgment — it's a relevance threshold fail. These files may have been quarantined before content was fully developed or because the scoring algorithm weights "project-relevance" over "content quality."

---

*Analysis generated: 2026-04-14*
*Source data: `.wiki/_quarantine/` (1077 files) + `.wiki/_meta/compile_state.json`*