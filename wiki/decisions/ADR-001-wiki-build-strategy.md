# ADR-001: cekwajar.id Salary Transparency Wiki Build Strategy

**Date**: 2026-04-11  
**Status**: ACCEPTED  
**Deciders**: @planner, @worker  
**Task**: Build 100+ wiki knowledge pages for cekwajar.id salary transparency platform

---

## Context

cekwajar.id is an Indonesian salary transparency platform. The platform needs comprehensive wiki documentation covering Indonesian employment law, tax regulations, BPJS (social security), market salary data, product information, business operations, and engineering topics.

**Domains and Page Ranges**:
| Domain | Range | Description | Count |
|--------|-------|-------------|-------|
| labor-law | 019 | Indonesian labor law (UU Ketenagakerjaan) | ~10 pages |
| tax | 020-029 | PPh, PPn, tax regulations | 10 pages |
| bpjs | 030-039 | BPJS Kesehatan, BPJS TK, JHT, JP | 10 pages |
| market | 040-054 | Salary benchmarks, compensation research | 15 pages |
| product | 055-064 | Platform features, salary calculation tools | 10 pages |
| business | 065-074 | Company operations, hiring best practices | 10 pages |
| engineering | 085-091 | Technical infrastructure, data pipelines | 7 pages |

**Total**: ~72 pages minimum, expandable to 100+

---

## Decision

Execute parallel domain-based wiki construction with centralized template enforcement.

### Architecture

```
.wiki/knowledge/
├── 019-labor-law/
│   ├── 019-01-upah-minimum.md
│   ├── 019-02-cuti-dan-cut-off.md
│   ├── 019-03-pkwt-pkwt-terminasi.md
│   └── ...
├── 020-tax/
│   ├── 020-01-pph-21-gaji.md
│   ├── 020-02-pph-26-foreign-worker.md
│   └── ...
├── 030-bpjs/
│   ├── 030-01-bpjs-kesehatan-aturan.md
│   ├── 030-02-bpjs-ketenagakerjaan.md
│   └── ...
├── 040-market/
│   ├── 040-01- salary-benchmark-2024.md
│   ├── 040-02-remote-worker-salary.md
│   └── ...
├── 055-product/
│   ├── 055-01-salary-calculator.md
│   ├── 055-02-company-profile.md
│   └── ...
├── 065-business/
│   ├── 065-01-hiring-checklist.md
│   ├── 065-02-employee-benefits-id.md
│   └── ...
├── 085-engineering/
│   ├── 085-01-data-pipeline.md
│   ├── 085-02-api-architecture.md
│   └── ...
└── INDEX.md
```

---

## Wiki Page Template (MANDATORY)

Every wiki page MUST follow this exact structure:

```yaml
---
title: "[Page Title]"
domain: "[domain-name]"
code: "[3-digit-code]"
tags: [tag1, tag2, tag3]
sources: [source-reference]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# [Page Title]

## Ringkasan (Summary)
[2-3 sentence overview]

## Definisi (Definition)
[What is this topic]

## Regulasi / Aturan (Regulation)
[Applicable laws, regulations, or rules]

## Perhitungan / Formula (Calculation/Formula)
[If applicable: step-by-step calculation]

## Contoh Kasus (Example)
[Concrete example with numbers]

## Relevansi Gaji (Salary Relevance)
[How this relates to salary transparency]

## Sumber (Sources)
- [Source 1 with link]
- [Source 2 with link]

## Lihat Juga (See Also)
- [[related-page-1]]
- [[related-page-2]]
```

---

## Subtask Decomposition (8 Groups)

### GROUP 1: labor-law (019) → @worker-1
**Pages**: 019-01 through 019-10
**Search queries**: Indonesian labor law 2024, UU Ketenagakerjaan terbaru, upah minimum 2025, cuti melahirkan UU 13/2003, PKWT vs PKWTT

### GROUP 2: tax (020-029) → @worker-2
**Pages**: 020-01 through 020-10
**Search queries**: PPh 21 terbaru 2024, perhitungan PPh 26 expatriate, PTKP 2025, BPOM tax compliance Indonesia

### GROUP 3: bpjs (030-039) → @worker-3
**Pages**: 030-01 through 030-10
**Search queries**: BPJS Kesehatan iuran 2024, BPJS Ketenagakerjaan JHT JP, cara hitung BPJS karyawan, BPJS mandiri vs perusahaan

### GROUP 4: market (040-054) → @worker-4
**Pages**: 040-01 through 040-15
**Search queries**: Salary survey Indonesia 2024, Gadjian salary benchmark, Glassdoor Indonesia gaji, remote worker salary Indonesia

### GROUP 5: product (055-064) → @worker-5
**Pages**: 055-01 through 055-10
**Search queries**: cekwajar.id features, salary calculator Indonesia, company salary database, employee benefits platform

### GROUP 6: business (065-074) → @worker-6
**Pages**: 065-01 through 065-10
**Search queries**: Indonesia hiring best practices, employee benefits Indonesia, kompensasi karyawan startup, onboarding checklist Indonesia

### GROUP 7: engineering (085-091) → @worker-7
**Pages**: 085-01 through 085-07
**Search queries**: data pipeline salary platform, Indonesia tech stack salary, API architecture compensation database

---

## Dependency Constraints

1. **No inter-domain dependencies** — all 7 groups can execute in parallel
2. **INDEX.md** must be created AFTER all domain groups complete
3. **Quality gate** — all pages must pass wiki-schema.md validation before write

---

## Execution Order

```
[GROUP 1-7] ─── parallel execution ──→ All domain pages written
                                          ↓
                              [INDEX.md aggregation]
                                          ↓
                              [.wiki/logs/planner-progress.md update]
```

---

## Critical Path

1. **First**: Create `.wiki/knowledge/` directory structure
2. **Then**: All 7 groups execute in parallel
3. **Finally**: INDEX.md aggregation (single point of serialization)

---

## Consequences

### Positive
- Parallel execution reduces total time by ~7x
- Domain grouping enables specialized research per topic
- Standardized template ensures consistency across 100+ pages

### Negative
- Some topics may overlap across domains (mitigate with cross-links)
- Indonesian tax/labor law changes frequently (mitigate: note "as of 2024" in pages)

### Mitigations
- Each page includes `sources` tag for traceability
- `updated` field tracks freshness
- INDEX.md provides single entry point for navigation

---

## References

- Wiki schema: `.wiki/templates/wiki-schema.md`
- Quality gate: `.wiki/decisions/ADR-006-wiki-quality-gate.md`
- Existing POPW pipeline: `.wiki/decisions/ADR-007-popw-wiki-pipeline.md`
