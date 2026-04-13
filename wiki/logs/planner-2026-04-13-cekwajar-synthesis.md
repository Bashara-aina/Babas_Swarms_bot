## Plan: cekwajar.id Wiki Synthesis
Date: 2026-04-13
Type: FILE_OPERATION (wiki synthesis from source documents)
Context gathered:
- Read SCHEMA.md (Karpathy KB Pattern, frontmatter schema, word count minimums)
- Read INDEX.md (175 articles, 23 stubs, 129 cekwajar-tagged)
- Read all 3 source documents: master_analysis_cekwajar.md (773 lines), req_01_master_prd.md (347 lines), block_01_verdict_algorithm.md (1588+ lines)
- Read existing stubs: bpjs-reference.md (543w), labor-law-indonesia.md (732w), market-data-indonesia.md (439w), tax-indonesia.md (363w), cekwajar-id.md (143w)
- Read existing cekwajar-tech-stack.md (116w - very thin)

Risk assessment:
- 4 concept stubs need significant expansion with regulatory formulas from source docs
- 1 project stub needs 500+ word expansion
- 3 new architecture files needed (verdict engine ~350w, OCR pipeline, data sources)
- 2 new ADRs needed (MVP scope lock, tech stack)
- 1 raw reference doc needed
- Total: 11 files to create/update + health pulse + compile_state + git commit

Approach:
- Split into 3 contract batches (max 5 contracts per batch)
- Batch 1: Expand 2 concepts + create 1 architecture + create 1 ADR
- Batch 2: Expand 2 concepts + create 1 architecture + create 1 ADR
- Batch 3: Expand 1 project + create 1 architecture + create 1 raw + final steps
- Note: No explicit health pulse command found in SCHEMA.md - will check for broken links manually
