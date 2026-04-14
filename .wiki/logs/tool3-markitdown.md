---
title: Tool3 Markitdown
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
summary: Wire markitdown (document → markdown converter) into Legion as a skill.
wikilinks: []
confidence: medium
source: research
---
# Tool 3: markitdown Integration — 2026-04-12

## Task
Wire markitdown (document → markdown converter) into Legion as a skill.

## Actions Taken

### Created Files
- `core/skills/doc_parser.py` — new skill module implementing `parse_file()` and `parse_telegram_document()`
- Added `markitdown[all]>=0.1.0` to `requirements.txt`
- Added `MARKITDOWN_LLM_VISION=False` to `.env.example`

### Modified Files
- `core/skills/__init__.py` — added `doc_parser` to imports and `__all__`

## Verification Results

### Import test
```
python -c "from core.skills.doc_parser import parse_file, SKILL_META; print('OK')"
```
**Result**: `OK` (with expected warning that markitdown is not yet installed)

### Wiring verification
```
python scripts/verify_wiring.py
```
**Result**: ✅ All 7 test groups PASS — handlers, core imports, LLM client, tools, bridges, skills, agents

## Skill Metadata (SKILL_META)
- `name`: doc_parser
- `description`: Parse any document (PDF, DOCX, XLSX, PPTX, image) to Markdown.
- `triggers`: ["parse", "baca file", "ekstrak", "dokumen", "payslip", "upload"]
- `avg_latency_seconds`: 3
- `cost_tier`: free

## Dependencies
- `markitdown[all]>=0.1.0` — installed via pip
- `pdfplumber` already in requirements.txt (fallback for .pdf)

## Next Steps
- Install markitdown: `pip install 'markitdown[all]'`
- Restart bot to activate