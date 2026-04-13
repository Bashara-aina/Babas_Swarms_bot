# ADR-001: Archive cekwajar.id Planning Docs

**Date:** 2026-04-11  
**Status:** Accepted  
**Deciders:** SwarmBot Team  

## Context

The `.wiki/` directory has accumulated planning documents from the cekwajar.id project (a separate FnB venture from the SwarmBot Telegram bot). These files were mixed with SwarmBot core documentation, creating confusion about project boundaries.

## Decision

Archive all cekwajar.id planning documents to separate from SwarmBot core documentation.

## KEEP (12 files) → moved to `.wiki/research/` and `.wiki/architecture/`

| File | Destination |
|------|-------------|
| `vc_evaluation_cekwajar.md` | `.wiki/research/` |
| `block_01_verdict_algorithm.md` | `.wiki/research/` |
| `block_03_pph21_bpjs_engine.md` | `.wiki/research/` |
| `block_04_legal_compliance.md` | `.wiki/research/` |
| `block_05_monetization_pricing.md` | `.wiki/research/` |
| `block_06_gtm_execution.md` | `.wiki/research/` |
| `block_08_competitive_intelligence.md` | `.wiki/research/` |
| `block_09_financial_model.md` | `.wiki/research/` |
| `block_10_premortem_kill_criteria.md` | `.wiki/research/` |
| `readme.md` | `.wiki/research/` |
| `block_02_database_schema.md` | `.wiki/architecture/` |
| `block_07_technical_architecture.md` | `.wiki/architecture/` |

## ARCHIVE (30 files) → moved to `.wiki/_archive/cekwajar/`

| Category | Files |
|----------|-------|
| FnB Strategy Analyses (HTML) | `Analisis-Strategi-FnB-Pajang-Solo.html`, `Business-Discovery-Validation-Analysis.html`, `dapur_solo_strategy_analysis.html`, `Deep-Dive-Sate-Padang-Premium.html`, `dried_meal_master_checklist_answers.html`, `dried_ready_meal_deep_dive.html`, `film-popw-viz.html`, `home_manufacturing_deep_analysis.html`, `popw-v14-ground-truth.html`, `rumahlabuh_pricing_analysis.html` |
| Presentation Slides | `slide-01.png` through `slide-12.png` (12 files) |
| RTF Documents | `cekwajar.rtf`, `cekwajar (1).rtf` |
| Temp Files | `lu5300dfhk.tmp` |
| Business Documents | `cekwajar_BMC_Worksheet.xlsx`, `cekwajar_VPC_Worksheet.xlsx`, `cekwajar_SIF_Summary.pdf`, `cekwajar_SIF_Summary.pptx`, `cekwajar_strategic_blueprint.docx` |

## Rationale

1. **Project Separation**: cekwajar.id is a separate FnB venture from SwarmBot (Telegram bot)
2. **Clarity**: SwarmBot core docs should not be mixed with unrelated project materials
3. **Future Reference**: Keep technical architecture and VC evaluation docs for potential future reference
4. **Clean Workspace**: Reduce noise in `additional_information/` and `.wiki/`

## Consequences

- SwarmBot documentation now only contains bot-relevant materials
- cekwajar.id docs preserved in `.wiki/_archive/cekwajar/` for historical reference
- Technical reference docs (architecture, financial model, legal) accessible in `.wiki/research/` and `.wiki/architecture/`
