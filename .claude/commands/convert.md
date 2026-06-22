---
description: Convert files (PDF/PPTX/DOCX/XLSX/HTML/CSV/JSON/XML/images/audio/EPUB/ZIP/YouTube) to Markdown via microsoft/markitdown v0.1.6. Thin slash entry over the markitdown skill.
---

# /convert — markitdown (Claude Code shim)

Thin slash entry over the `markitdown` skill. For the full 22-converter
chain + plugin support, invoke the skill directly with the Skill tool.

## Usage

```
/convert <file>                      # convert one file → markdown to stdout
/convert file.pdf --out out.md       # write to file
/convert https://...                 # convert a remote URL
/convert --batch a.pdf b.docx        # batch convert
/convert file --detect               # magika content-type sniff
/convert file --meta                 # file metadata + conversion title
/convert --list                      # list all 22 supported formats
/convert file --json                 # result as JSON envelope
```

## What It Does

1. Resolve the `markitdown` skill (canonical: `markitdown/skills/markitdown/SKILL.md`)
2. Pick the narrowest API: `convert_local()` for files, `convert_url()` for URLs, `convert_stream()` for in-memory bytes
3. Optional `StreamInfo(mimetype=..., extension=...)` to override magika detection
4. Report: markdown text, byte length, detected title, mime used

## Content-Type Auto-Detect (magika)

| Detected mime | Converter | Notes |
|---|---|---|
| `application/pdf` | `_pdf_converter.py` | pdfminer.six + pdfplumber |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `_docx_converter.py` | mammoth |
| `application/vnd.openxmlformats-officedocument.presentationml.presentation` | `_pptx_converter.py` | python-pptx |
| `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | `_xlsx_converter.py` | pandas + openpyxl |
| `text/html` | `_html_converter.py` | beautifulsoup4 |
| `text/csv` | `_csv_converter.py` | pandas |
| `text/markdown` | `_markdownify.py` | markdownify (passthrough) |
| `image/*` | `_image_converter.py` | EXIF + Azure Document Intelligence OCR |
| `audio/*` | `_transcribe_audio.py` | SpeechRecognition + pydub |
| `application/zip` | `_zip_converter.py` | recurses into entries |
| `application/epub+zip` | `_epub_converter.py` | ebooklib |
| `application/vnd.ms-outlook` | `_outlook_msg_converter.py` | olefile |
| `application/json` / `text/xml` | `_json_converter.py` / `_rss_converter.py` | schema-aware |
| `text/plain` | `_plain_text_converter.py` | passthrough |

## Delegation

When the user types `/convert`, prefer invoking the `markitdown` skill
(canonical surface) for the full 22-converter chain. This file is just a
slash compatibility entry.

`ARGUMENTS: $ARGUMENTS`
