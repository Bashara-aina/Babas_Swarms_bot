---
title: Adr 022 Markitdown
type: decision
status: active
tags:
- /
- home
- newadmin
- swarm-bot
- decisions
created: '2026-04-14'
updated: '2026-04-14'
summary: '**Decider**: @planner → @worker'
wikilinks: []
confidence: medium
source: research
---
# ADR-022: markitdown Document Parser Integration

**Date**: 2026-04-12  
**Status**: Accepted  
**Decider**: @planner → @worker

## Context

Legion needs to parse uploaded documents (PDF, DOCX, XLSX, PPTX, images) into markdown for RAG, memory injection, and analysis. Existing stack has pdfplumber for PDFs but no unified document parser for mixed formats.

`markitdown` is a Python library that converts 20+ document formats to markdown using python-mammoth (DOCX), openpyxl (XLSX), python-pptx (PPTX), and Pillow + pytesseract (images). It also supports EPUB, HTML, and more.

## Decision

1. Create `core/skills/doc_parser.py` as a skill module with:
   - `parse_file(path)` — synchronous file → markdown with fallback chain
   - `parse_telegram_document(bot, file_id)` — download from Telegram then parse
   - `SKILL_META` dict for registry wiring

2. Prefer `markitdown` when available; fall back to `pdfplumber` for PDFs; return error dict for unsupported types.

3. Register `doc_parser` in `core/skills/__init__.py`.

4. Add `markitdown[all]>=0.1.0` to `requirements.txt`.

5. Add `MARKITDOWN_LLM_VISION=False` to `.env.example` for future LLM-based image OCR.

## Consequences

**Positive**:
- Single unified API for all document types
- No extra API costs (local conversion)
- 3s avg latency, free tier

**Negative**:
- markitdown not installed by default — warning logged on import
- Large docx/xlsx files may hit memory on low-RAM machines

## Alternatives Considered

- **pdfplumber only**: only handles PDFs, not DOCX/PPTX/images
- **LangChain document loaders**: heavier dependency, more complex API
- **Direct mammoth/openpyxl/pptx调用**: works but no unified interface, more code to maintain