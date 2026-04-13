---
title: markitdown
type: entity
status: active
tags: [document, conversion, markdown, microsoft, pdf, docx]
created: 2026-04-13
updated: 2026-04-13
summary: Markitdown is Microsoft's document-to-markdown converter that handles PDF, DOCX, XLSX, PPTX, HTML, images with OCR, audio transcription, EPUB, and ZIP files for Legion's document processing pipeline.
wikilinks:
  - [[./entities/gpt-researcher]]
  - [[./entities/dify]]
  - [[./concepts/skill-registry]]
confidence: high
source: implementation
---

# Markitdown

## TL;DR
Markitdown is Microsoft's open-source document converter that transforms nearly any file format into clean markdown. Legion uses it in the document processing pipeline to convert PDFs, DOCX, spreadsheets, presentations, images with OCR, audio files, and even EPUB books into markdown for LLM context injection.

## Overview

Markitdown (from Microsoft) is a versatile document conversion tool that produces consistent markdown output from diverse source formats. Unlike pdfplumber or python-docx which produce structured but format-specific output, markitdown normalizes everything to a unified markdown representation.

**Repository**: https://github.com/microsoft/markitdown  
**License**: MIT  
**Language**: Python  
**Installation**: `pip install markitdown[all]>=0.1.0`

## Supported Formats

| Format | Input | Output | Notes |
|--------|-------|--------|-------|
| PDF | `.pdf` | Markdown | Text extraction, preserves structure |
| Word | `.docx` | Markdown | Headers, lists, tables |
| Excel | `.xlsx`, `.xls` | Markdown | Tabular representation |
| PowerPoint | `.pptx` | Markdown | Slide text extraction |
| HTML | `.html` | Markdown | Web page content |
| Images | `.png`, `.jpg` | Markdown | OCR via Tesseract |
| Audio | `.mp3`, `.wav` | Markdown | Transcription |
| EPUB | `.epub` | Markdown | E-book content |
| ZIP | `.zip` | Markdown | Archives extracted |

## Legion Integration

Markitdown is already integrated into Legion's document processing via `requirements.txt`:

```
markitdown[all]>=0.1.0
```

The `[all]` extras ensure all optional dependencies (OCR, audio transcription) are installed.

### Document Processing Pipeline

```
User sends document → Telegram
    → multimodal_processor.py
    → markitdown.convert(file_path)  # Converts to markdown
    → LLM context injection
    → Response generation
```

### Code Integration

```python
from markitdown import MarkItDown

markitdown = MarkItDown()

# Convert any document to markdown
result = markitdown.convert("document.pdf")
markdown_content = result.text_content

# For images with OCR
result = markitdown.convert("screenshot.png")  # Uses Tesseract OCR

# For audio transcription
result = markitdown.convert("recording.mp3")  # Uses Whisper
```

## Comparison with Alternatives

| Tool | Pros | Cons | Use in Legion |
|------|------|------|---------------|
| Markitdown | Universal, Microsoft-backed, OCR | Large dependency | Primary |
| pdfplumber | Fast PDF text extraction | PDF only | Fallback |
| python-docx | Clean DOCX handling | DOCX only | Fallback |
| PyMuPDF | Good PDF + images | PDF focus | Auxiliary |
| Tesseract | Standalone OCR | Separate setup | OCR only |

## Use Cases in Legion

### 1. PDF Document Analysis
When a user sends a PDF (research paper, contract, report), Legion uses markitdown to:
- Extract text content
- Preserve headings and structure
- Generate markdown for LLM context

### 2. Image OCR
Screenshots or scanned documents are processed with:
- Tesseract OCR integration
- Language detection
- Layout preservation

### 3. Spreadsheet Overview
Excel files are converted to markdown tables for:
- Quick data inspection
- Column/row structure awareness
- Summary generation

### 4. Audio Transcription
Voice notes and audio files use:
- Whisper integration via markitdown
- Timestamp preservation
- Speaker diarization (when available)

## Configuration

Markitdown requires no additional configuration in Legion. The `[all]` extras in requirements.txt ensure all format handlers are available:

```bash
pip install markitdown[all]
```

## Related Pages

- [[./entities/gpt-researcher]] — Research agent using markitdown for doc parsing
- [[./entities/dify]] — Dify workflow platform alternative
- [[./concepts/skill-registry]] — How skills are registered in Legion
