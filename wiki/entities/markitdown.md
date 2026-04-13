---
title: markitdown
type: entity
status: active
tags: [document, conversion, pdf, markdown]
created: 2026-04-13
updated: 2026-04-13
summary: Markitdown converts various document formats (PDF, DOCX, PPTX) to clean markdown for LLM consumption.
wikilinks: [[entities/opencode.md], [concepts/vector-search.md]]
confidence: medium
source: implementation
---

# Markitdown

## TL;DR
Markitdown is a document conversion tool that extracts content from PDFs, DOCX, and other formats into clean markdown for processing.

## Supported Formats

| Input | Output |
|-------|--------|
| PDF | Markdown |
| DOCX | Markdown |
| PPTX | Markdown |
| EPUB | Markdown |

## How Legion Uses It

Used in document processing pipeline:
1. User uploads document
2. Markitdown converts to markdown
3. Content fed to LLM for analysis/summarization

## Installation

```bash
pip install markitdown
markitdown document.pdf
```

## Related Pages

- [[concepts/vector-search.md]] — Document indexing for search
- [[projects/legion-bot.md]] — Legion's document handling
